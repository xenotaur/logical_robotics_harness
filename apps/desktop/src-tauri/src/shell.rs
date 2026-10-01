//! The LRH Console shell: windows, menus, navigation policy, and settings.
//!
//! The main window shows either a bundled status page or, while the owned
//! backend runs, that backend's verified loopback origin. Web content there
//! gets no app commands (`capabilities/main-window.json`), and navigation is
//! limited to bundled pages and the current backend's exact origin. External
//! `http(s)` links are handed to a browser instead (rate-limited).
//!
//! The Settings / Server Details window shows only bundled pages and is the
//! one window granted app commands (`capabilities/settings-window.json`).
//!
//! Lifecycle actions run on one worker thread, so they are serialized and
//! never block the UI thread.

use std::ffi::OsString;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{self, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread;
use std::time::Duration;

use serde::Serialize;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::webview::{NewWindowResponse, WebviewWindowBuilder};
use tauri::{AppHandle, Manager, Runtime, Url, WebviewUrl, WebviewWindow};

use crate::browser::{self, Handoff, RateLimiter};
use crate::settings::{self, BrowserChoice, Config, ConfigStore, FieldError};
use crate::supervisor::{ErrorKind, LaunchConfig, State, Status, Supervisor};

/// Label of the one default content window.
pub const MAIN_WINDOW: &str = "main";
/// Label of the Settings / Server Details window.
pub const SETTINGS_WINDOW: &str = "settings";

/// Developer launch override. When any of these is set at startup it wins
/// over the saved configuration for that session. Paths must be absolute;
/// nothing is looked up on PATH.
pub const ENV_EXECUTABLE: &str = "LRH_CONSOLE_LRH_EXECUTABLE";
/// Alternative to [`ENV_EXECUTABLE`]: a Python interpreter that runs
/// `-m lrh.cli.main`, for a source checkout.
pub const ENV_PYTHON: &str = "LRH_CONSOLE_PYTHON";
/// Optional `PYTHONPATH` for the [`ENV_PYTHON`] form (for example `<repo>/src`).
pub const ENV_PYTHONPATH: &str = "LRH_CONSOLE_PYTHONPATH";
/// The workspace to serve.
pub const ENV_WORKSPACE: &str = "LRH_CONSOLE_WORKSPACE";

/// Menu item IDs.
pub mod menu_id {
    pub const SETTINGS: &str = "app-settings";
    pub const START: &str = "server-start";
    pub const STOP: &str = "server-stop";
    pub const RESTART: &str = "server-restart";
    pub const DETAILS: &str = "server-details";
    pub const DASHBOARD: &str = "view-dashboard";
    pub const META: &str = "view-meta";
    pub const RELOAD: &str = "view-reload";
    pub const OPEN_CHROME: &str = "view-open-chrome";
    pub const OPEN_BROWSER: &str = "view-open-browser";
    pub const SHOW_MAIN: &str = "window-show-main";
}

/// How often the worker checks for a backend that exited on its own. A
/// crashed backend's origin stays allowed until the next check (or until the
/// current action finishes), so keep this short.
const STATUS_POLL_INTERVAL: Duration = Duration::from_millis(250);

/// True if any developer launch variable is set.
pub fn dev_settings_present(env: impl Fn(&str) -> Option<OsString>) -> bool {
    [ENV_EXECUTABLE, ENV_PYTHON, ENV_PYTHONPATH, ENV_WORKSPACE]
        .iter()
        .any(|name| env(name).is_some_and(|value| !value.is_empty()))
}

/// Builds a launch config from the developer settings in `env`.
///
/// Exactly one of [`ENV_EXECUTABLE`] or [`ENV_PYTHON`] must be set, plus
/// [`ENV_WORKSPACE`]; every path must be absolute. The error explains what is
/// missing and is safe to show (it names variables, not their values).
pub fn dev_launch_config(env: impl Fn(&str) -> Option<OsString>) -> Result<LaunchConfig, String> {
    let absolute = |name: &str| -> Result<Option<PathBuf>, String> {
        match env(name).filter(|value| !value.is_empty()) {
            None => Ok(None),
            Some(value) => {
                let path = PathBuf::from(value);
                if path.is_absolute() {
                    Ok(Some(path))
                } else {
                    Err(format!("{name} must be an absolute path"))
                }
            }
        }
    };
    let executable = absolute(ENV_EXECUTABLE)?;
    let python = absolute(ENV_PYTHON)?;
    let workspace = absolute(ENV_WORKSPACE)?
        .ok_or_else(|| format!("set {ENV_WORKSPACE} to an absolute LRH workspace path"))?;
    let config = match (executable, python) {
        (Some(_), Some(_)) => {
            return Err(format!("set only one of {ENV_EXECUTABLE} or {ENV_PYTHON}"))
        }
        (None, None) => {
            return Err(format!(
                "set {ENV_EXECUTABLE} (or {ENV_PYTHON}) to an absolute path"
            ))
        }
        (Some(executable), None) => LaunchConfig::new(executable, workspace),
        (None, Some(python)) => {
            let mut config = LaunchConfig::new(python, workspace);
            config.program_args = vec!["-m".into(), "lrh.cli.main".into()];
            if let Some(pythonpath) = env(ENV_PYTHONPATH).filter(|value| !value.is_empty()) {
                // A relative entry would resolve against the app's launch
                // directory and could import the wrong checkout.
                if !std::env::split_paths(&pythonpath).all(|entry| entry.is_absolute()) {
                    return Err(format!(
                        "every {ENV_PYTHONPATH} entry must be an absolute path"
                    ));
                }
                config.env.push(("PYTHONPATH".into(), pythonpath));
            }
            config
        }
    };
    // Keep the program path exactly as given. Canonicalizing would resolve a
    // virtualenv's `python` symlink to the base interpreter and lose the venv.
    Ok(config)
}

/// The origin bundled app pages are served from on this platform.
pub fn bundled_base() -> Url {
    #[cfg(windows)]
    let base = "http://tauri.localhost/";
    #[cfg(not(windows))]
    let base = "tauri://localhost/";
    Url::parse(base).expect("bundled base URL")
}

/// True for URLs of pages bundled with the app.
///
/// `tauri://` is not a special scheme, so its `Url::origin()` is opaque and
/// never compares equal; match scheme, host, and port explicitly instead.
pub fn is_bundled(url: &Url) -> bool {
    let base = bundled_base();
    url.scheme() == base.scheme()
        && url.host_str() == base.host_str()
        && url.port_or_known_default() == base.port_or_known_default()
}

/// The bundled status page for a state, with an optional error code.
///
/// Only the state name and a machine error code go in the URL, never a
/// message or stderr text, which can contain local paths.
pub fn status_url(state: &str, code: Option<&str>) -> Url {
    let mut url = bundled_base().join("index.html").expect("status page URL");
    {
        let mut query = url.query_pairs_mut();
        query.append_pair("state", state);
        if let Some(code) = code.filter(|code| is_machine_code(code)) {
            query.append_pair("code", code);
        }
    }
    url
}

fn is_machine_code(code: &str) -> bool {
    !code.is_empty()
        && code.len() <= 64
        && code
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte == b'_')
}

/// Where the main window may navigate: bundled pages, plus the current owned
/// backend's exact origin while it runs. Cloning shares the same policy.
#[derive(Clone, Default)]
pub struct NavigationPolicy {
    backend: Arc<Mutex<Option<Url>>>,
}

impl NavigationPolicy {
    /// True if the main window may load `url`.
    pub fn allows(&self, url: &Url) -> bool {
        if is_bundled(url) {
            return true;
        }
        lock(&self.backend)
            .as_ref()
            .is_some_and(|backend| backend.origin() == url.origin())
    }

    /// Sets the running backend's endpoint, or clears it. A previous origin
    /// is dropped, so a restarted backend's old port is refused.
    pub fn set_backend(&self, endpoint: Option<&Url>) {
        *lock(&self.backend) = endpoint.cloned();
    }

    /// The running backend's endpoint, if any.
    pub fn backend(&self) -> Option<Url> {
        lock(&self.backend).clone()
    }
}

/// True for a link that should open in a browser rather than in the app: a
/// valid `http(s)` URL on a non-loopback host. Loopback links are never
/// handed off, so a stale backend port is not opened in a browser either.
pub fn is_external_link(url: &Url) -> bool {
    browser::validate_url(url).is_ok()
        && !matches!(
            url.host_str(),
            Some("127.0.0.1" | "localhost" | "[::1]" | "::1")
        )
}

/// Popups and `target=_blank` links never open inside the app.
pub fn new_window_response<R: Runtime>(_url: &Url) -> NewWindowResponse<R> {
    NewWindowResponse::Deny
}

/// Hands external links to the browser, at most one per second.
#[derive(Default)]
pub struct LinkHandoff {
    limiter: RateLimiter,
    browser: Mutex<BrowserChoice>,
    last: Mutex<Option<Result<Handoff, String>>>,
}

impl LinkHandoff {
    /// Opens `url` in the chosen browser on a background thread, if it is an
    /// external link and the rate limit allows.
    pub fn offer(self: &Arc<Self>, url: &Url) {
        if !is_external_link(url) || !self.limiter.try_acquire() {
            return;
        }
        self.open_now(url.clone());
    }

    /// Opens `url` without the external-link filter (menu actions on the
    /// backend's own pages). Still validated and rate-limited.
    fn open_requested(self: &Arc<Self>, url: Url, choice: BrowserChoice) {
        if !self.limiter.try_acquire() {
            return;
        }
        let this = Arc::clone(self);
        thread::spawn(move || {
            *lock(&this.last) = Some(browser::open(&url, choice));
        });
    }

    fn open_now(self: &Arc<Self>, url: Url) {
        let choice = *lock(&self.browser);
        let this = Arc::clone(self);
        thread::spawn(move || {
            *lock(&this.last) = Some(browser::open(&url, choice));
        });
    }

    fn set_browser(&self, choice: BrowserChoice) {
        *lock(&self.browser) = choice;
    }

    fn last(&self) -> Option<Result<Handoff, String>> {
        lock(&self.last).clone()
    }
}

/// Which menu items are enabled.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MenuEnablement {
    pub start: bool,
    pub stop: bool,
    pub restart: bool,
    /// Dashboard, Meta, Open in Chrome, and Open in Browser.
    pub running_views: bool,
}

impl MenuEnablement {
    /// Every server action disabled, while one is in progress.
    pub const BUSY: MenuEnablement = MenuEnablement {
        start: false,
        stop: false,
        restart: false,
        running_views: false,
    };

    /// The enablement for a settled supervisor state.
    pub fn for_state(state: State, configured: bool) -> Self {
        match state {
            State::Running => MenuEnablement {
                start: false,
                stop: true,
                restart: true,
                running_views: true,
            },
            State::Starting | State::Stopping => Self::BUSY,
            State::Stopped | State::Failed => MenuEnablement {
                start: configured,
                stop: false,
                restart: false,
                running_views: false,
            },
        }
    }
}

/// The page the main window should show for a supervisor status.
pub fn page_for_status(status: &Status, configured: bool) -> Url {
    match (status.state, &status.handshake) {
        (State::Running, Some(handshake)) => {
            Url::parse(&handshake.url).unwrap_or_else(|_| status_url("failed", None))
        }
        (State::Starting, _) => status_url("starting", None),
        (State::Stopping, _) => status_url("stopping", None),
        (State::Failed, _) | (State::Running, None) => match &status.last_error {
            Some(error)
                if matches!(
                    error.kind,
                    ErrorKind::IncompatibleBackend
                        | ErrorKind::WorkspaceMismatch
                        | ErrorKind::NonLoopbackEndpoint
                        | ErrorKind::LaunchIdMismatch
                ) =>
            {
                status_url("incompatible", Some(error.kind.code()))
            }
            Some(error) => status_url("failed", Some(&failure_code(error))),
            None => status_url("failed", None),
        },
        (State::Stopped, _) if !configured => status_url("setup", None),
        (State::Stopped, _) => status_url("stopped", None),
    }
}

/// The most specific machine code for a failure: the backend's own code
/// (for example `workspace_not_lrh_project`) when it reported one.
fn failure_code(error: &crate::supervisor::SupervisorError) -> String {
    error
        .backend_error
        .as_ref()
        .and_then(|backend| backend.get("code"))
        .and_then(|code| code.as_str())
        .filter(|code| is_machine_code(code))
        .unwrap_or(error.kind.code())
        .to_string()
}

/// A serialized lifecycle action.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Start,
    Stop,
    Restart,
}

/// Where the running configuration came from.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ConfigSource {
    /// No configuration yet: first run, or the saved file is unusable.
    None,
    /// The saved configuration file.
    File,
    /// The developer environment override.
    Environment,
}

/// Handles to the menu items whose enablement follows state.
struct StateItems<R: Runtime> {
    start: MenuItem<R>,
    stop: MenuItem<R>,
    restart: MenuItem<R>,
    running_views: Vec<MenuItem<R>>,
}

impl<R: Runtime> StateItems<R> {
    fn apply(&self, enablement: MenuEnablement) {
        let _ = self.start.set_enabled(enablement.start);
        let _ = self.stop.set_enabled(enablement.stop);
        let _ = self.restart.set_enabled(enablement.restart);
        for item in &self.running_views {
            let _ = item.set_enabled(enablement.running_views);
        }
    }
}

/// App-wide shell state, stored with [`Manager::manage`].
pub struct ShellState {
    pub supervisor: Arc<Supervisor>,
    pub policy: NavigationPolicy,
    pub links: Arc<LinkHandoff>,
    store: Option<ConfigStore>,
    config: Mutex<Option<Config>>,
    source: Mutex<ConfigSource>,
    /// Why the saved configuration could not be used, if it could not.
    problem: Mutex<Option<String>>,
    chrome_available: bool,
    actions: Mutex<Sender<Action>>,
    exiting: AtomicBool,
}

impl ShellState {
    /// Queues a lifecycle action for the worker. Actions run one at a time.
    pub fn request(&self, action: Action) {
        let _ = lock(&self.actions).send(action);
    }

    /// Stops the owned backend and refuses any later launch. Used on Quit:
    /// a Start or Restart still queued for the worker then fails instead of
    /// spawning a new backend.
    pub fn shutdown(&self) {
        self.supervisor.shutdown();
    }

    /// Marks the app as exiting. Returns true the first time only.
    pub fn begin_exit(&self) -> bool {
        !self.exiting.swap(true, Ordering::SeqCst)
    }
}

/// Builds the main window with the navigation, handoff, and popup policy.
pub fn build_main_window<R: Runtime, M: Manager<R>>(
    manager: &M,
    policy: NavigationPolicy,
    links: Arc<LinkHandoff>,
    initial: &Url,
) -> tauri::Result<WebviewWindow<R>> {
    let path = initial
        .as_str()
        .strip_prefix(bundled_base().as_str())
        .unwrap_or("index.html")
        .to_string();
    let popup_links = Arc::clone(&links);
    WebviewWindowBuilder::new(manager, MAIN_WINDOW, WebviewUrl::App(PathBuf::from(path)))
        .title("LRH Console")
        .inner_size(1100.0, 760.0)
        .on_navigation(move |url| {
            if policy.allows(url) {
                return true;
            }
            links.offer(url);
            false
        })
        .on_new_window(move |url, _features| {
            popup_links.offer(&url);
            new_window_response(&url)
        })
        .build()
}

/// Builds the Settings / Server Details window. It may show only bundled
/// pages and never opens popups.
pub fn build_settings_window<R: Runtime, M: Manager<R>>(
    manager: &M,
) -> tauri::Result<WebviewWindow<R>> {
    WebviewWindowBuilder::new(
        manager,
        SETTINGS_WINDOW,
        WebviewUrl::App(PathBuf::from("settings.html")),
    )
    .title("LRH Console Settings")
    .inner_size(720.0, 760.0)
    .on_navigation(is_bundled)
    .on_new_window(|url, _features| new_window_response(&url))
    .build()
}

/// Shows the Settings window, creating it once and focusing it afterwards.
pub fn show_settings<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window(SETTINGS_WINDOW) {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
        return;
    }
    if let Err(error) = build_settings_window(app) {
        eprintln!("LRH Console: could not open Settings: {error}");
    }
}

/// Builds the app menu: the platform app menu, Edit, Server, View, Window.
fn build_menu<R: Runtime>(
    app: &AppHandle<R>,
    chrome_available: bool,
) -> tauri::Result<(Menu<R>, StateItems<R>)> {
    let item = |id: &str, text: &str, enabled: bool, accelerator: Option<&str>| {
        MenuItem::with_id(app, id, text, enabled, accelerator)
    };
    let chrome_label = if chrome_available {
        "Open in Chrome"
    } else {
        "Open in Chrome (not found: uses default browser)"
    };
    let items = StateItems {
        start: item(menu_id::START, "Start Server", false, None)?,
        stop: item(menu_id::STOP, "Stop Server", false, None)?,
        restart: item(menu_id::RESTART, "Restart Server", false, None)?,
        running_views: vec![
            item(menu_id::DASHBOARD, "Dashboard", false, Some("CmdOrCtrl+0"))?,
            item(menu_id::META, "Meta", false, Some("CmdOrCtrl+Shift+M"))?,
            item(menu_id::OPEN_CHROME, chrome_label, false, None)?,
            item(
                menu_id::OPEN_BROWSER,
                "Open in Default Browser",
                false,
                None,
            )?,
        ],
    };
    let settings = item(menu_id::SETTINGS, "Settings…", true, Some("CmdOrCtrl+,"))?;
    let details = item(
        menu_id::DETAILS,
        "Server Details…",
        true,
        Some("CmdOrCtrl+I"),
    )?;
    let reload = item(menu_id::RELOAD, "Reload", true, Some("CmdOrCtrl+R"))?;
    let show_main = item(
        menu_id::SHOW_MAIN,
        "LRH Console Window",
        true,
        Some("CmdOrCtrl+1"),
    )?;
    let app_menu = Submenu::with_items(
        app,
        "LRH Console",
        true,
        &[
            &PredefinedMenuItem::about(app, None, None)?,
            &PredefinedMenuItem::separator(app)?,
            &settings,
            &PredefinedMenuItem::separator(app)?,
        ],
    )?;
    // Hide, Hide Others, and Show All exist only on macOS.
    #[cfg(target_os = "macos")]
    app_menu.append_items(&[
        &PredefinedMenuItem::hide(app, None)?,
        &PredefinedMenuItem::hide_others(app, None)?,
        &PredefinedMenuItem::show_all(app, None)?,
        &PredefinedMenuItem::separator(app)?,
    ])?;
    app_menu.append(&PredefinedMenuItem::quit(app, None)?)?;
    let edit = Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(app, None)?,
            &PredefinedMenuItem::redo(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, None)?,
            &PredefinedMenuItem::copy(app, None)?,
            &PredefinedMenuItem::paste(app, None)?,
            &PredefinedMenuItem::select_all(app, None)?,
        ],
    )?;
    let server = Submenu::with_items(
        app,
        "Server",
        true,
        &[
            &items.start,
            &items.stop,
            &items.restart,
            &PredefinedMenuItem::separator(app)?,
            &details,
        ],
    )?;
    let [dashboard, meta, open_chrome, open_browser] = &items.running_views[..] else {
        unreachable!("four running views");
    };
    let view = Submenu::with_items(
        app,
        "View",
        true,
        &[
            dashboard,
            meta,
            &reload,
            &PredefinedMenuItem::separator(app)?,
            open_chrome,
            open_browser,
        ],
    )?;
    let window = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(app, None)?,
            &PredefinedMenuItem::close_window(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &show_main,
        ],
    )?;
    let menu = Menu::with_items(app, &[&app_menu, &edit, &server, &view, &window])?;
    Ok((menu, items))
}

/// The configuration chosen at startup: the developer override if any
/// variable is set, otherwise the saved file.
struct StartupConfig {
    launch: Option<LaunchConfig>,
    config: Option<Config>,
    source: ConfigSource,
    problem: Option<String>,
}

fn startup_config(store: Option<&ConfigStore>) -> StartupConfig {
    let env = |name: &str| std::env::var_os(name);
    if dev_settings_present(env) {
        return match dev_launch_config(env) {
            Ok(launch) => StartupConfig {
                launch: Some(launch),
                config: None,
                source: ConfigSource::Environment,
                problem: None,
            },
            Err(problem) => StartupConfig {
                launch: None,
                config: None,
                source: ConfigSource::None,
                problem: Some(format!("developer settings: {problem}")),
            },
        };
    }
    let none = |problem: Option<String>| StartupConfig {
        launch: None,
        config: None,
        source: ConfigSource::None,
        problem,
    };
    let Some(store) = store else {
        return none(Some(
            "the app configuration directory is unavailable".into(),
        ));
    };
    match store.load() {
        Ok(None) => none(None),
        Err(problem) => none(Some(problem)),
        Ok(Some(config)) => match settings::validate(&config) {
            Ok(()) => StartupConfig {
                launch: Some(settings::launch_config(&config)),
                config: Some(config),
                source: ConfigSource::File,
                problem: None,
            },
            Err(errors) => {
                let detail = errors
                    .iter()
                    .map(|error| format!("{}: {}", error.field, error.message))
                    .collect::<Vec<_>>()
                    .join("; ");
                StartupConfig {
                    launch: None,
                    config: Some(config),
                    source: ConfigSource::None,
                    problem: Some(format!(
                        "the saved configuration is no longer valid ({detail})"
                    )),
                }
            }
        },
    }
}

/// Sets up the shell: configuration, menu, windows, and the action worker.
pub fn setup<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let store = app
        .path()
        .app_config_dir()
        .ok()
        .map(|dir| ConfigStore::in_dir(&dir));
    let startup = startup_config(store.as_ref());
    if let Some(problem) = &startup.problem {
        eprintln!("LRH Console: {problem}");
    }
    let supervisor = Arc::new(Supervisor::unconfigured());
    if let Some(launch) = startup.launch.clone() {
        supervisor.set_config(launch);
    }
    let configured = supervisor.is_configured();
    let start_on_open = startup
        .config
        .as_ref()
        .is_none_or(|config| config.start_on_open);

    let chrome_available = browser::chrome_available();
    let (menu, items) = build_menu(app, chrome_available)?;
    app.set_menu(menu)?;

    let links = Arc::new(LinkHandoff::default());
    if let Some(config) = &startup.config {
        links.set_browser(config.browser);
    }
    let policy = NavigationPolicy::default();
    let initial = match (configured, start_on_open) {
        (false, _) => status_url("setup", None),
        (true, true) => status_url("starting", None),
        (true, false) => status_url("stopped", None),
    };
    build_main_window(app, policy.clone(), Arc::clone(&links), &initial)?;

    let (sender, receiver) = mpsc::channel();
    app.manage(ShellState {
        supervisor: Arc::clone(&supervisor),
        policy: policy.clone(),
        links,
        store,
        config: Mutex::new(startup.config.clone()),
        source: Mutex::new(startup.source),
        problem: Mutex::new(startup.problem.clone()),
        chrome_available,
        actions: Mutex::new(sender),
        exiting: AtomicBool::new(false),
    });

    let worker_app = app.clone();
    thread::Builder::new()
        .name("lrh-console-actions".into())
        .spawn(move || {
            let mut last_shown: Option<(State, Option<u64>, bool)> = None;
            loop {
                let action = match receiver.recv_timeout(STATUS_POLL_INTERVAL) {
                    Ok(action) => Some(action),
                    Err(RecvTimeoutError::Timeout) => None,
                    Err(RecvTimeoutError::Disconnected) => return,
                };
                if let Some(action) = action {
                    if supervisor.is_shut_down() {
                        continue;
                    }
                    items.apply(MenuEnablement::BUSY);
                    let transient = match action {
                        Action::Stop => State::Stopping,
                        Action::Start | Action::Restart => State::Starting,
                    };
                    // Drop the old origin before anything else can navigate.
                    policy.set_backend(None);
                    navigate_main(&worker_app, &status_url(state_name(transient), None));
                    let _ = match action {
                        Action::Start => supervisor.start().map(|_| ()),
                        Action::Restart => supervisor.restart().map(|_| ()),
                        Action::Stop => {
                            supervisor.stop();
                            Ok(())
                        }
                    };
                    last_shown = None;
                }
                if supervisor.is_shut_down() {
                    continue;
                }
                let status = supervisor.status();
                let configured = supervisor.is_configured();
                let key = (
                    status.state,
                    status.handshake.as_ref().map(|h| h.generation),
                    configured,
                );
                if last_shown.as_ref() != Some(&key) {
                    last_shown = Some(key);
                    show_status(&worker_app, &policy, &items, &status, configured);
                }
            }
        })
        .expect("failed to spawn the LRH Console action worker");

    if configured && start_on_open {
        app.state::<ShellState>().request(Action::Start);
    }
    if !configured {
        // First run, or the saved configuration needs fixing.
        show_settings(app);
    }
    Ok(())
}

fn state_name(state: State) -> &'static str {
    match state {
        State::Stopped => "stopped",
        State::Starting => "starting",
        State::Running => "running",
        State::Stopping => "stopping",
        State::Failed => "failed",
    }
}

/// Updates the policy, the main window, and the menu for `status`.
fn show_status<R: Runtime>(
    app: &AppHandle<R>,
    policy: &NavigationPolicy,
    items: &StateItems<R>,
    status: &Status,
    configured: bool,
) {
    let endpoint = match (status.state, &status.handshake) {
        (State::Running, Some(handshake)) => Url::parse(&handshake.url).ok(),
        _ => None,
    };
    // Allow the new origin before navigating to it; it was cleared earlier.
    policy.set_backend(endpoint.as_ref());
    navigate_main(app, &page_for_status(status, configured));
    items.apply(MenuEnablement::for_state(status.state, configured));
}

fn navigate_main<R: Runtime>(app: &AppHandle<R>, url: &Url) {
    if let Some(window) = app.get_webview_window(MAIN_WINDOW) {
        let _ = window.navigate(url.clone());
    }
}

/// Shows the "Stopping…" page while Quit shuts the backend down.
pub fn show_stopping<R: Runtime>(app: &AppHandle<R>) {
    navigate_main(app, &status_url("stopping", None));
}

/// Shows and focuses the main window (Dock reopen, Window menu).
pub fn show_main<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window(MAIN_WINDOW) {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

/// The URL of a page on the running backend, if it runs.
fn backend_page(state: &ShellState, path: &str) -> Option<Url> {
    state
        .policy
        .backend()
        .and_then(|endpoint| endpoint.join(path).ok())
}

/// The current page of the main window, if it is the backend's.
fn current_backend_page<R: Runtime>(app: &AppHandle<R>, state: &ShellState) -> Option<Url> {
    let url = app.get_webview_window(MAIN_WINDOW)?.url().ok()?;
    let backend = state.policy.backend()?;
    (url.origin() == backend.origin()).then_some(url)
}

/// Handles a menu event by ID.
pub fn handle_menu<R: Runtime>(app: &AppHandle<R>, id: &str) {
    let state = app.state::<ShellState>();
    match id {
        menu_id::SETTINGS | menu_id::DETAILS => show_settings(app),
        menu_id::START => state.request(Action::Start),
        menu_id::STOP => state.request(Action::Stop),
        menu_id::RESTART => state.request(Action::Restart),
        menu_id::DASHBOARD => {
            if let Some(url) = backend_page(&state, "") {
                navigate_main(app, &url);
            }
        }
        menu_id::META => {
            if let Some(url) = backend_page(&state, "meta") {
                navigate_main(app, &url);
            }
        }
        menu_id::RELOAD => {
            if let Some(window) = app.get_webview_window(MAIN_WINDOW) {
                if let Ok(url) = window.url() {
                    if state.policy.allows(&url) {
                        let _ = window.navigate(url);
                    }
                }
            }
        }
        menu_id::OPEN_CHROME | menu_id::OPEN_BROWSER => {
            let page = current_backend_page(app, &state).or_else(|| backend_page(&state, ""));
            if let Some(url) = page {
                let choice = if id == menu_id::OPEN_CHROME {
                    BrowserChoice::Chrome
                } else {
                    BrowserChoice::DefaultBrowser
                };
                state.links.open_requested(url, choice);
            }
        }
        menu_id::SHOW_MAIN => show_main(app),
        _ => {}
    }
}

// ---------------------------------------------------------------------------
// Settings window commands. Only the `settings` window is granted these
// (capabilities/settings-window.json); every argument is validated here.
// ---------------------------------------------------------------------------

/// What the Settings window shows about the configuration.
#[derive(Debug, Clone, Serialize)]
pub struct SettingsView {
    pub config: Option<Config>,
    pub source: ConfigSource,
    pub problem: Option<String>,
    pub config_path: Option<String>,
}

/// The outcome of saving settings.
#[derive(Debug, Clone, Serialize)]
pub struct SaveOutcome {
    /// The backend must restart for the change to take effect.
    pub restart_required: bool,
    /// A backend was started because none was running.
    pub started: bool,
}

/// What Server Details shows.
#[derive(Debug, Clone, Serialize)]
pub struct ServerDetails {
    pub state: &'static str,
    pub owned_pid: Option<u32>,
    pub endpoint: Option<String>,
    pub served_workspace: Option<serde_json::Value>,
    pub configured_workspace: Option<String>,
    pub protocol_version: Option<u64>,
    pub backend: Option<serde_json::Value>,
    pub last_error_code: Option<String>,
    pub last_error_message: Option<String>,
    pub last_exit_code: Option<i32>,
    pub stderr_tail: String,
    pub chrome_available: bool,
    pub last_handoff: Option<serde_json::Value>,
}

/// Returns the saved configuration and where the running one came from.
#[tauri::command]
pub fn get_settings(state: tauri::State<'_, ShellState>) -> SettingsView {
    SettingsView {
        config: lock(&state.config).clone(),
        source: *lock(&state.source),
        problem: lock(&state.problem).clone(),
        config_path: state
            .store
            .as_ref()
            .map(|store| store.path().display().to_string()),
    }
}

/// Validates and saves the configuration. An invalid change is rejected and
/// the last working configuration stays in effect.
#[tauri::command]
pub fn save_settings(
    state: tauri::State<'_, ShellState>,
    config: Config,
) -> Result<SaveOutcome, Vec<FieldError>> {
    let store = state.store.as_ref().ok_or_else(|| {
        vec![FieldError {
            field: "file",
            message: "the app configuration directory is unavailable".into(),
        }]
    })?;
    store.save(&config)?;
    let previous = lock(&state.config).replace(config.clone());
    *lock(&state.source) = ConfigSource::File;
    *lock(&state.problem) = None;
    state.links.set_browser(config.browser);
    let was_configured = state.supervisor.is_configured();
    let launch_changed = settings::needs_restart(previous.as_ref(), &config)
        || !was_configured
        || state.supervisor.config() != Some(settings::launch_config(&config));
    state
        .supervisor
        .set_config(settings::launch_config(&config));
    let status = state.supervisor.status();
    let running = matches!(status.state, State::Running | State::Starting);
    let started = !running && launch_changed;
    if started {
        state.request(Action::Start);
    }
    Ok(SaveOutcome {
        restart_required: running && launch_changed,
        started,
    })
}

/// Reports the owned backend's identity, endpoint, and diagnostics.
#[tauri::command]
pub fn get_server_details(state: tauri::State<'_, ShellState>) -> ServerDetails {
    let status = state.supervisor.status();
    let handshake = status.handshake.as_ref();
    ServerDetails {
        state: state_name(status.state),
        owned_pid: state.supervisor.child_pid(),
        endpoint: handshake.map(|h| h.url.clone()),
        served_workspace: handshake.map(|h| h.workspace.clone()),
        configured_workspace: state
            .supervisor
            .config()
            .map(|config| config.project_root.display().to_string()),
        protocol_version: handshake.map(|h| h.protocol_version),
        backend: handshake.map(|h| h.backend.clone()),
        last_error_code: status.last_error.as_ref().map(failure_code),
        last_error_message: status
            .last_error
            .as_ref()
            .map(|error| error.message.clone()),
        last_exit_code: status.last_exit_code,
        stderr_tail: state.supervisor.stderr_tail(),
        chrome_available: state.chrome_available,
        last_handoff: state.links.last().map(|result| match result {
            Ok(handoff) => serde_json::json!({"ok": true, "handoff": handoff}),
            Err(error) => serde_json::json!({"ok": false, "error": error}),
        }),
    }
}

/// Restarts the owned backend (for example after a workspace change).
#[tauri::command]
pub fn restart_server(state: tauri::State<'_, ShellState>) {
    state.request(Action::Restart);
}

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    mutex
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::supervisor::SupervisorError;
    use std::collections::HashMap;

    fn env_of(pairs: &[(&str, &str)]) -> impl Fn(&str) -> Option<OsString> {
        let map: HashMap<String, OsString> = pairs
            .iter()
            .map(|(key, value)| (key.to_string(), OsString::from(value)))
            .collect();
        move |name| map.get(name).cloned()
    }

    #[test]
    fn dev_settings_need_an_absolute_program_and_workspace() {
        assert!(!dev_settings_present(env_of(&[])));
        assert!(dev_settings_present(env_of(&[(ENV_WORKSPACE, "/w")])));
        assert!(dev_launch_config(env_of(&[])).is_err());
        assert!(dev_launch_config(env_of(&[(ENV_WORKSPACE, "/w")])).is_err());
        assert!(
            dev_launch_config(env_of(&[(ENV_EXECUTABLE, "lrh"), (ENV_WORKSPACE, "/w")])).is_err(),
            "a bare name would need a PATH lookup"
        );
        assert!(
            dev_launch_config(env_of(&[(ENV_EXECUTABLE, "/x/lrh"), (ENV_WORKSPACE, "w")])).is_err()
        );
        assert!(dev_launch_config(env_of(&[
            (ENV_EXECUTABLE, "/x/lrh"),
            (ENV_PYTHON, "/x/python"),
            (ENV_WORKSPACE, "/w"),
        ]))
        .is_err());
        assert!(
            dev_launch_config(env_of(&[
                (ENV_PYTHON, "/x/python"),
                (ENV_PYTHONPATH, "/repo/src:src"),
                (ENV_WORKSPACE, "/w"),
            ]))
            .is_err(),
            "a relative PYTHONPATH entry must be refused"
        );
    }

    #[test]
    fn dev_settings_build_the_executable_and_python_forms() {
        let config =
            dev_launch_config(env_of(&[(ENV_EXECUTABLE, "/x/lrh"), (ENV_WORKSPACE, "/w")]))
                .unwrap();
        assert_eq!(config.program, PathBuf::from("/x/lrh"));
        assert!(config.program_args.is_empty());

        let config = dev_launch_config(env_of(&[
            (ENV_PYTHON, "/x/python"),
            (ENV_PYTHONPATH, "/repo/src"),
            (ENV_WORKSPACE, "/w"),
        ]))
        .unwrap();
        assert_eq!(
            config.program_args,
            vec![OsString::from("-m"), "lrh.cli.main".into()]
        );
        assert_eq!(config.env, vec![("PYTHONPATH".into(), "/repo/src".into())]);
        assert_eq!(config.project_root, PathBuf::from("/w"));
    }

    #[test]
    fn status_urls_are_bundled_and_carry_only_state_and_a_machine_code() {
        let url = status_url("failed", Some("startup_timeout"));
        assert!(is_bundled(&url));
        assert_eq!(url.query(), Some("state=failed&code=startup_timeout"));
        let url = status_url("failed", Some("/Users/me/secret path"));
        assert_eq!(url.query(), Some("state=failed"), "non-codes are dropped");
    }

    #[test]
    fn menu_enablement_follows_state() {
        let running = MenuEnablement::for_state(State::Running, true);
        assert!(!running.start && running.stop && running.restart && running.running_views);
        assert_eq!(
            MenuEnablement::for_state(State::Starting, true),
            MenuEnablement::BUSY
        );
        let stopped = MenuEnablement::for_state(State::Stopped, true);
        assert!(stopped.start && !stopped.stop && !stopped.restart && !stopped.running_views);
        assert!(!MenuEnablement::for_state(State::Failed, false).start);
    }

    fn status(state: State, error: Option<SupervisorError>) -> Status {
        Status {
            state,
            handshake: None,
            last_error: error,
            last_exit_code: None,
        }
    }

    fn error(kind: ErrorKind, backend_code: Option<&str>) -> SupervisorError {
        let mut error = crate::supervisor::SupervisorError {
            kind,
            message: "x".into(),
            backend_error: None,
            exit_code: None,
            stderr_tail: String::new(),
        };
        if let Some(code) = backend_code {
            error.backend_error = Some(serde_json::json!({"code": code}));
        }
        error
    }

    #[test]
    fn pages_follow_state_and_failure_kind() {
        assert_eq!(
            page_for_status(&status(State::Stopped, None), false).query(),
            Some("state=setup")
        );
        assert_eq!(
            page_for_status(&status(State::Stopped, None), true).query(),
            Some("state=stopped")
        );
        assert_eq!(
            page_for_status(&status(State::Starting, None), true).query(),
            Some("state=starting")
        );
        let incompatible = status(
            State::Failed,
            Some(error(ErrorKind::IncompatibleBackend, None)),
        );
        assert_eq!(
            page_for_status(&incompatible, true).query(),
            Some("state=incompatible&code=incompatible_backend")
        );
        let bad_workspace = status(
            State::Failed,
            Some(error(
                ErrorKind::BackendFailed,
                Some("workspace_not_lrh_project"),
            )),
        );
        assert_eq!(
            page_for_status(&bad_workspace, true).query(),
            Some("state=failed&code=workspace_not_lrh_project")
        );
    }

    #[test]
    fn only_non_loopback_web_links_are_external() {
        let url = |text: &str| Url::parse(text).unwrap();
        assert!(is_external_link(&url("https://github.com/xenotaur")));
        assert!(!is_external_link(&url("http://127.0.0.1:50543/meta")));
        assert!(!is_external_link(&url("http://localhost:50543/")));
        assert!(!is_external_link(&url("http://[::1]:50543/")));
        assert!(!is_external_link(&url("file:///etc/passwd")));
        assert!(!is_external_link(&status_url("stopped", None)));
    }
}

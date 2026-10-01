//! The LRH Console shell: main window, lifecycle menus, and navigation policy.
//!
//! The main window shows either the bundled status page or, while the owned
//! backend runs, that backend's verified loopback origin. Menu actions run on
//! one worker thread, so they are serialized and never block the UI thread.
//! Web content in the main window gets no app commands (see
//! `capabilities/main-window.json`), and navigation is limited to bundled
//! pages and the current backend's exact origin.

use std::ffi::OsString;
use std::path::PathBuf;
use std::sync::mpsc::{self, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread;
use std::time::Duration;

use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::webview::{NewWindowResponse, WebviewWindowBuilder};
use tauri::{AppHandle, Manager, Runtime, Url, WebviewUrl, WebviewWindow};

use crate::supervisor::{LaunchConfig, State, Status, Supervisor};

/// Label of the one default content window.
pub const MAIN_WINDOW: &str = "main";

/// Developer launch settings. They are read once at startup and replaced by
/// private configuration in WI-LRH-CONSOLE-DESKTOP-SETTINGS. Paths must be
/// absolute; nothing is looked up on PATH.
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
    pub const START: &str = "server-start";
    pub const STOP: &str = "server-stop";
    pub const RESTART: &str = "server-restart";
    pub const DASHBOARD: &str = "view-dashboard";
    pub const RELOAD: &str = "view-reload";
    pub const SHOW_MAIN: &str = "window-show-main";
}

/// How often the worker checks for a backend that exited on its own.
const STATUS_POLL_INTERVAL: Duration = Duration::from_millis(500);

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
        if let Some(code) = code {
            query.append_pair("code", code);
        }
    }
    url
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

/// Popups and `target=_blank` links never open inside the app. Browser
/// handoff is WI-LRH-CONSOLE-DESKTOP-SETTINGS.
pub fn new_window_response<R: Runtime>(_url: &Url) -> NewWindowResponse<R> {
    NewWindowResponse::Deny
}

/// Which lifecycle menu items are enabled.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MenuEnablement {
    pub start: bool,
    pub stop: bool,
    pub restart: bool,
    pub dashboard: bool,
}

impl MenuEnablement {
    /// Every server action disabled, while one is in progress.
    pub const BUSY: MenuEnablement = MenuEnablement {
        start: false,
        stop: false,
        restart: false,
        dashboard: false,
    };

    /// The enablement for a settled supervisor state.
    pub fn for_state(state: State, configured: bool) -> Self {
        match state {
            State::Running => MenuEnablement {
                start: false,
                stop: true,
                restart: true,
                dashboard: true,
            },
            State::Starting | State::Stopping => Self::BUSY,
            State::Stopped | State::Failed => MenuEnablement {
                start: configured,
                stop: false,
                restart: false,
                dashboard: false,
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
        (State::Failed, _) | (State::Running, None) => status_url(
            "failed",
            status.last_error.as_ref().map(|error| error.kind.code()),
        ),
        (State::Stopped, _) if !configured => status_url("unconfigured", None),
        (State::Stopped, _) => status_url("stopped", None),
    }
}

/// A serialized lifecycle action.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Start,
    Stop,
    Restart,
}

/// Handles to the lifecycle menu items.
struct LifecycleItems<R: Runtime> {
    start: MenuItem<R>,
    stop: MenuItem<R>,
    restart: MenuItem<R>,
    dashboard: MenuItem<R>,
}

impl<R: Runtime> LifecycleItems<R> {
    fn apply(&self, enablement: MenuEnablement) {
        let _ = self.start.set_enabled(enablement.start);
        let _ = self.stop.set_enabled(enablement.stop);
        let _ = self.restart.set_enabled(enablement.restart);
        let _ = self.dashboard.set_enabled(enablement.dashboard);
    }
}

/// App-wide shell state, stored with [`Manager::manage`].
pub struct ShellState {
    supervisor: Option<Arc<Supervisor>>,
    /// Why the backend cannot be launched, when the settings are incomplete.
    pub setup_problem: Option<String>,
    pub policy: NavigationPolicy,
    actions: Mutex<Sender<Action>>,
}

impl ShellState {
    /// Queues a lifecycle action for the worker. Actions run one at a time.
    pub fn request(&self, action: Action) {
        let _ = lock(&self.actions).send(action);
    }

    /// Stops the owned backend, if any. Used on Quit.
    pub fn shutdown(&self) {
        if let Some(supervisor) = &self.supervisor {
            supervisor.stop();
        }
    }
}

/// Builds the main window with the navigation and popup policy attached.
pub fn build_main_window<R: Runtime, M: Manager<R>>(
    manager: &M,
    policy: NavigationPolicy,
    initial: &Url,
) -> tauri::Result<WebviewWindow<R>> {
    let path = initial
        .as_str()
        .strip_prefix(bundled_base().as_str())
        .unwrap_or("index.html")
        .to_string();
    WebviewWindowBuilder::new(manager, MAIN_WINDOW, WebviewUrl::App(PathBuf::from(path)))
        .title("LRH Console")
        .inner_size(1100.0, 760.0)
        .on_navigation(move |url| policy.allows(url))
        .on_new_window(|url, _features| new_window_response(&url))
        .build()
}

/// Builds the app menu: the platform app menu, Edit, Server, View, Window.
fn build_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<(Menu<R>, LifecycleItems<R>)> {
    let items = LifecycleItems {
        start: MenuItem::with_id(app, menu_id::START, "Start Server", false, None::<&str>)?,
        stop: MenuItem::with_id(app, menu_id::STOP, "Stop Server", false, None::<&str>)?,
        restart: MenuItem::with_id(app, menu_id::RESTART, "Restart Server", false, None::<&str>)?,
        dashboard: MenuItem::with_id(
            app,
            menu_id::DASHBOARD,
            "Dashboard",
            false,
            Some("CmdOrCtrl+0"),
        )?,
    };
    let reload = MenuItem::with_id(app, menu_id::RELOAD, "Reload", true, Some("CmdOrCtrl+R"))?;
    let show_main = MenuItem::with_id(
        app,
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
            &PredefinedMenuItem::hide(app, None)?,
            &PredefinedMenuItem::hide_others(app, None)?,
            &PredefinedMenuItem::show_all(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::quit(app, None)?,
        ],
    )?;
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
        &[&items.start, &items.stop, &items.restart],
    )?;
    let view = Submenu::with_items(app, "View", true, &[&items.dashboard, &reload])?;
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

/// Sets up the shell: settings, menu, main window, and the action worker.
/// Starts the backend when the developer settings are complete.
pub fn setup<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let launch = dev_launch_config(|name| std::env::var_os(name));
    let configured = launch.is_ok();
    let (supervisor, setup_problem) = match launch {
        Ok(config) => (Some(Arc::new(Supervisor::new(config))), None),
        Err(problem) => (None, Some(problem)),
    };
    if let Some(problem) = &setup_problem {
        eprintln!("LRH Console: backend not configured: {problem}");
    }

    let (menu, items) = build_menu(app)?;
    app.set_menu(menu)?;

    let policy = NavigationPolicy::default();
    let initial = if configured {
        status_url("starting", None)
    } else {
        status_url("unconfigured", None)
    };
    build_main_window(app, policy.clone(), &initial)?;

    let (sender, receiver) = mpsc::channel();
    app.manage(ShellState {
        supervisor: supervisor.clone(),
        setup_problem,
        policy: policy.clone(),
        actions: Mutex::new(sender),
    });

    let worker_app = app.clone();
    thread::Builder::new()
        .name("lrh-console-actions".into())
        .spawn(move || {
            let mut last_shown: Option<(State, Option<u64>)> = None;
            let render = |status: &Status, last: &mut Option<(State, Option<u64>)>| {
                let key = (
                    status.state,
                    status.handshake.as_ref().map(|h| h.generation),
                );
                if last.as_ref() == Some(&key) {
                    return;
                }
                *last = Some(key);
                show_status(&worker_app, &policy, &items, status, configured);
            };
            loop {
                let action = match receiver.recv_timeout(STATUS_POLL_INTERVAL) {
                    Ok(action) => Some(action),
                    Err(RecvTimeoutError::Timeout) => None,
                    Err(RecvTimeoutError::Disconnected) => return,
                };
                let Some(supervisor) = supervisor.as_ref() else {
                    continue;
                };
                if let Some(action) = action {
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
                render(&supervisor.status(), &mut last_shown);
            }
        })
        .expect("failed to spawn the LRH Console action worker");

    if configured {
        app.state::<ShellState>().request(Action::Start);
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
    items: &LifecycleItems<R>,
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

/// Shows and focuses the main window (Dock reopen, Window menu).
pub fn show_main<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window(MAIN_WINDOW) {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

/// Handles a menu event by ID.
pub fn handle_menu<R: Runtime>(app: &AppHandle<R>, id: &str) {
    let state = app.state::<ShellState>();
    match id {
        menu_id::START => state.request(Action::Start),
        menu_id::STOP => state.request(Action::Stop),
        menu_id::RESTART => state.request(Action::Restart),
        menu_id::DASHBOARD => {
            if let Some(endpoint) = state.policy.backend() {
                navigate_main(app, &endpoint);
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
        menu_id::SHOW_MAIN => show_main(app),
        _ => {}
    }
}

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    mutex
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

#[cfg(test)]
mod tests {
    use super::*;
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
    fn status_urls_are_bundled_and_carry_only_state_and_code() {
        let url = status_url("failed", Some("startup_timeout"));
        assert!(is_bundled(&url));
        assert_eq!(url.query(), Some("state=failed&code=startup_timeout"));
    }

    #[test]
    fn menu_enablement_follows_state() {
        let running = MenuEnablement::for_state(State::Running, true);
        assert!(!running.start && running.stop && running.restart && running.dashboard);
        assert_eq!(
            MenuEnablement::for_state(State::Starting, true),
            MenuEnablement::BUSY
        );
        let stopped = MenuEnablement::for_state(State::Stopped, true);
        assert!(stopped.start && !stopped.stop && !stopped.restart);
        assert!(!MenuEnablement::for_state(State::Failed, false).start);
    }

    #[test]
    fn pages_follow_state() {
        let mut status = Status {
            state: State::Stopped,
            handshake: None,
            last_error: None,
            last_exit_code: None,
        };
        assert_eq!(
            page_for_status(&status, false).query(),
            Some("state=unconfigured")
        );
        assert_eq!(
            page_for_status(&status, true).query(),
            Some("state=stopped")
        );
        status.state = State::Starting;
        assert_eq!(
            page_for_status(&status, true).query(),
            Some("state=starting")
        );
    }
}

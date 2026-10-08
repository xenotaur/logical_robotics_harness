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
use tauri::{AppHandle, Manager, Runtime, Theme, Url, WebviewUrl, WebviewWindow};

use crate::browser::{self, Handoff, RateLimiter};
use crate::settings::{self, Appearance, BrowserChoice, Config, ConfigStore, FieldError};
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
    pub const QUIT: &str = "app-quit";
    pub const START: &str = "server-start";
    pub const STOP: &str = "server-stop";
    pub const RESTART: &str = "server-restart";
    pub const DETAILS: &str = "server-details";
    pub const DASHBOARD: &str = "view-dashboard";
    pub const META: &str = "view-meta";
    pub const RELOAD: &str = "view-reload";
    pub const BACK: &str = "view-back";
    pub const FORWARD: &str = "view-forward";
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

/// The main window's Back/Forward history, kept by the app.
///
/// The webview's own history also holds bundled status pages ("Starting…",
/// "Stopping…") and pages of earlier backends, which Back must never reach.
/// This one records only pages on the current backend's origin. Any other
/// navigation, such as the status page every start, restart, stop, or Quit
/// shows, ends it, so a restarted backend never revisits old pages even on
/// the same port. Every move is still checked by [`NavigationPolicy`].
///
/// Navigations are observed through the main window's navigation handler,
/// which also sees the webview's own Back (the Delete key or a gesture) and
/// sees rapid moves late. A navigation to the page just behind or ahead is
/// therefore taken as that move, not as a new page; a link to the previous
/// page (Serve's "Back to project viewer") acts as Back too. Pages are
/// recorded without their fragment, so in-page anchor links are not pages.
/// The handler cannot tell subframes apart; Serve's pages have none.
#[derive(Debug, Default)]
pub struct PageHistory {
    /// The backend endpoint whose origin the recorded pages belong to.
    origin: Option<Url>,
    back: Vec<Url>,
    current: Option<Url>,
    forward: Vec<Url>,
    /// The stacks as they were before the last new page was recorded, so a
    /// navigation that turns out to be a download can be undone.
    before_last: Option<(Vec<Url>, Option<Url>, Vec<Url>)>,
}

impl PageHistory {
    /// The most pages remembered in each direction.
    const LIMIT: usize = 100;

    /// Records an allowed main-window navigation to `url` while `backend`
    /// runs. A navigation anywhere but the backend's origin ends the history.
    pub fn visited(&mut self, url: &Url, backend: Option<&Url>) {
        let mut url = url.clone();
        url.set_fragment(None);
        let url = &url;
        let Some(backend) = backend.filter(|backend| backend.origin() == url.origin()) else {
            *self = PageHistory::default();
            return;
        };
        if !self.belongs_to(Some(backend)) {
            *self = PageHistory {
                origin: Some(backend.clone()),
                ..PageHistory::default()
            };
        }
        if self.current.as_ref() == Some(url) {
            // A reload, or the page a Back/Forward move already went to.
            return;
        }
        self.before_last = None;
        if self.back.last() == Some(url) {
            self.shift(true);
            return;
        }
        if self.forward.last() == Some(url) {
            self.shift(false);
            return;
        }
        self.before_last = Some((
            self.back.clone(),
            self.current.clone(),
            self.forward.clone(),
        ));
        if let Some(previous) = self.current.replace(url.clone()) {
            push_bounded(&mut self.back, previous);
        }
        self.forward.clear();
    }

    /// Undoes the record of `url` when its navigation became a download.
    ///
    /// The navigation handler sees a `?download=1` link before the response
    /// shows it is a download, which the app hands to the browser instead of
    /// displaying, so the page on screen never changed.
    pub fn download_started(&mut self, url: &Url) {
        let mut url = url.clone();
        url.set_fragment(None);
        if self.current.as_ref() == Some(&url) {
            if let Some((back, current, forward)) = self.before_last.take() {
                self.back = back;
                self.current = current;
                self.forward = forward;
            }
        }
    }

    /// True if Back has a page to go to on the current backend.
    pub fn can_go_back(&self, backend: Option<&Url>) -> bool {
        self.belongs_to(backend) && !self.back.is_empty()
    }

    /// True if Forward has a page to go to on the current backend.
    pub fn can_go_forward(&self, backend: Option<&Url>) -> bool {
        self.belongs_to(backend) && !self.forward.is_empty()
    }

    /// Moves back one page and returns it, if there is one on `backend`.
    pub fn go_back(&mut self, backend: Option<&Url>) -> Option<Url> {
        self.step(backend, true)
    }

    /// Moves forward one page and returns it, if there is one on `backend`.
    pub fn go_forward(&mut self, backend: Option<&Url>) -> Option<Url> {
        self.step(backend, false)
    }

    fn step(&mut self, backend: Option<&Url>, back: bool) -> Option<Url> {
        self.before_last = None;
        if !self.belongs_to(backend) {
            // The backend stopped or changed: these pages are gone.
            *self = PageHistory::default();
            return None;
        }
        self.shift(back)
    }

    /// Makes the page behind (or ahead) current and returns it.
    fn shift(&mut self, back: bool) -> Option<Url> {
        let (from, to) = if back {
            (&mut self.back, &mut self.forward)
        } else {
            (&mut self.forward, &mut self.back)
        };
        let target = from.pop()?;
        if let Some(current) = self.current.replace(target.clone()) {
            push_bounded(to, current);
        }
        Some(target)
    }

    fn belongs_to(&self, backend: Option<&Url>) -> bool {
        matches!(
            (&self.origin, backend),
            (Some(origin), Some(backend)) if origin.origin() == backend.origin()
        )
    }
}

fn push_bounded(pages: &mut Vec<Url>, page: Url) {
    pages.push(page);
    if pages.len() > PageHistory::LIMIT {
        pages.remove(0);
    }
}

/// The Back and Forward menu items, in that order.
type HistoryItems<R> = [MenuItem<R>; 2];

/// The main window's history together with the Back and Forward menu items
/// it enables. Cloning shares the same history.
pub struct MainWindowHistory<R: Runtime> {
    pages: Arc<Mutex<PageHistory>>,
    items: Option<HistoryItems<R>>,
}

impl<R: Runtime> Clone for MainWindowHistory<R> {
    fn clone(&self) -> Self {
        MainWindowHistory {
            pages: Arc::clone(&self.pages),
            items: self.items.clone(),
        }
    }
}

impl<R: Runtime> Default for MainWindowHistory<R> {
    /// A history with no menu items, for tests and headless use.
    fn default() -> Self {
        MainWindowHistory {
            pages: Arc::default(),
            items: None,
        }
    }
}

impl<R: Runtime> MainWindowHistory<R> {
    /// Records an allowed navigation and updates Back and Forward.
    fn record(&self, url: &Url, backend: Option<&Url>) {
        let mut pages = lock(&self.pages);
        pages.visited(url, backend);
        self.refresh(&pages, backend);
    }

    /// Undoes the record of a navigation that became a download.
    fn download_started(&self, url: &Url, backend: Option<&Url>) {
        let mut pages = lock(&self.pages);
        pages.download_started(url);
        self.refresh(&pages, backend);
    }

    fn refresh(&self, pages: &PageHistory, backend: Option<&Url>) {
        if let Some([back, forward]) = &self.items {
            let _ = back.set_enabled(pages.can_go_back(backend));
            let _ = forward.set_enabled(pages.can_go_forward(backend));
        }
    }
}

/// Which way a menu item moves through the history: `Some(true)` for Back,
/// `Some(false)` for Forward, `None` for any other item.
fn history_direction(id: &str) -> Option<bool> {
    match id {
        menu_id::BACK => Some(true),
        menu_id::FORWARD => Some(false),
        _ => None,
    }
}

/// Moves through `pages` and returns the page to show, only if the current
/// policy allows it.
fn history_target(pages: &mut PageHistory, policy: &NavigationPolicy, back: bool) -> Option<Url> {
    let backend = policy.backend();
    let target = if back {
        pages.go_back(backend.as_ref())
    } else {
        pages.go_forward(backend.as_ref())
    };
    target.filter(|url| policy.allows(url))
}

/// True for a link that should open in a browser rather than in the app: a
/// valid `http(s)` URL on a non-loopback host. Loopback links are never
/// handed off, so a stale backend port is not opened in a browser either.
pub fn is_external_link(url: &Url) -> bool {
    browser::validate_url(url).is_ok() && !is_local_host(url)
}

/// True for loopback, unspecified, and `localhost` hosts (any spelling).
fn is_local_host(url: &Url) -> bool {
    let Some(host) = url.host_str() else {
        return true;
    };
    let host = host
        .trim_start_matches('[')
        .trim_end_matches(']')
        .trim_end_matches('.')
        .to_ascii_lowercase();
    match host.parse::<std::net::IpAddr>() {
        Ok(std::net::IpAddr::V4(ip)) => ip.is_loopback() || ip.is_unspecified(),
        Ok(std::net::IpAddr::V6(ip)) => {
            ip.is_loopback()
                || ip.is_unspecified()
                || ip
                    .to_ipv4_mapped()
                    .is_some_and(|v4| v4.is_loopback() || v4.is_unspecified())
        }
        Err(_) => host == "localhost" || host.ends_with(".localhost"),
    }
}

/// Popups and `target=_blank` links never open inside the app.
pub fn new_window_response<R: Runtime>(_url: &Url) -> NewWindowResponse<R> {
    NewWindowResponse::Deny
}

/// Hands external links to the browser, at most one per second.
#[derive(Default)]
pub struct LinkHandoff {
    /// Limits handoffs that page content triggers.
    limiter: RateLimiter,
    /// Limits menu-triggered handoffs separately, so a recent link handoff
    /// never swallows an explicit menu choice.
    menu_limiter: RateLimiter,
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
        if !self.menu_limiter.try_acquire() {
            return;
        }
        let this = Arc::clone(self);
        thread::spawn(move || {
            *lock(&this.last) = Some(browser::open(&url, choice));
        });
    }

    /// Hands a download to the browser (validated and rate-limited); the app
    /// itself never downloads.
    pub fn offer_download(self: &Arc<Self>, url: &Url) {
        if browser::validate_url(url).is_err() || !self.limiter.try_acquire() {
            return;
        }
        self.open_now(url.clone());
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
    history: Arc<Mutex<PageHistory>>,
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
    history: MainWindowHistory<R>,
    initial: &Url,
) -> tauri::Result<WebviewWindow<R>> {
    let path = initial
        .as_str()
        .strip_prefix(bundled_base().as_str())
        .unwrap_or("index.html")
        .to_string();
    let popup_links = Arc::clone(&links);
    let download_links = Arc::clone(&links);
    let download_history = history.clone();
    let download_policy = policy.clone();
    WebviewWindowBuilder::new(manager, MAIN_WINDOW, WebviewUrl::App(PathBuf::from(path)))
        .title("LRH Console")
        .inner_size(1100.0, 760.0)
        .on_navigation(move |url| {
            if policy.allows(url) {
                history.record(url, policy.backend().as_ref());
                return true;
            }
            links.offer(url);
            false
        })
        .on_new_window(move |url, _features| {
            popup_links.offer(&url);
            new_window_response(&url)
        })
        // Downloads (Serve's `?download=1` prompt Markdown) open in the
        // browser, which saves them; the app never writes files itself.
        .on_download(move |_webview, event| {
            if let tauri::webview::DownloadEvent::Requested { url, .. } = event {
                download_history.download_started(&url, download_policy.backend().as_ref());
                download_links.offer_download(&url);
            }
            false
        })
        .build()
}

/// The part of the Settings / Server Details window a menu item shows.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SettingsSection {
    /// The settings form, at the top.
    Settings,
    /// Server Details.
    Details,
}

impl SettingsSection {
    /// The section a menu item shows, if it is Settings… or Server Details….
    pub fn for_menu(id: &str) -> Option<Self> {
        match id {
            menu_id::SETTINGS => Some(SettingsSection::Settings),
            menu_id::DETAILS => Some(SettingsSection::Details),
            _ => None,
        }
    }

    fn name(self) -> &'static str {
        match self {
            SettingsSection::Settings => "settings",
            SettingsSection::Details => "details",
        }
    }

    /// Script that brings the section into view in an open window. It calls
    /// a function of the bundled page only; no app command is involved.
    fn show_script(self) -> String {
        format!(
            "window.lrhShowSection && window.lrhShowSection({:?});",
            self.name()
        )
    }
}

/// Builds the Settings / Server Details window, showing `section` first. It
/// may show only bundled pages and never opens popups.
pub fn build_settings_window<R: Runtime, M: Manager<R>>(
    manager: &M,
    section: SettingsSection,
) -> tauri::Result<WebviewWindow<R>> {
    WebviewWindowBuilder::new(
        manager,
        SETTINGS_WINDOW,
        WebviewUrl::App(PathBuf::from("settings.html")),
    )
    .title("LRH Console Settings")
    // Two columns: every field, both buttons, and the details fit without
    // scrolling on a 1440×900 display.
    .inner_size(1120.0, 760.0)
    .initialization_script(format!("window.lrhInitialSection = {:?};", section.name()))
    .on_navigation(is_bundled)
    .on_new_window(|url, _features| new_window_response(&url))
    .on_download(|_webview, _event| false)
    .build()
}

/// Shows the Settings window at `section`, creating it once and focusing it
/// afterwards.
pub fn show_settings<R: Runtime>(app: &AppHandle<R>, section: SettingsSection) {
    if let Some(window) = app.get_webview_window(SETTINGS_WINDOW) {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
        let _ = window.eval(section.show_script());
        return;
    }
    if let Err(error) = build_settings_window(app, section) {
        eprintln!("LRH Console: could not open Settings: {error}");
    }
}

/// Builds the app menu: the platform app menu, Edit, Server, View, Window.
fn build_menu<R: Runtime>(
    app: &AppHandle<R>,
    chrome_available: bool,
) -> tauri::Result<(Menu<R>, StateItems<R>, HistoryItems<R>)> {
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
    // Enabled by the main window's history as pages are visited.
    let back = item(menu_id::BACK, "Back", false, Some("CmdOrCtrl+["))?;
    let forward = item(menu_id::FORWARD, "Forward", false, Some("CmdOrCtrl+]"))?;
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
    // A custom Quit: the predefined one sends `terminate:`, which skips
    // ExitRequested, so the "Stopping…" page and the off-main-thread stop
    // would never run.
    app_menu.append(&item(
        menu_id::QUIT,
        "Quit LRH Console",
        true,
        Some("CmdOrCtrl+Q"),
    )?)?;
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
            &back,
            &forward,
            &PredefinedMenuItem::separator(app)?,
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
    Ok((menu, items, [back, forward]))
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
            // An invalid override still owns this session: Settings saves
            // only write the file, and the error stays visible.
            Err(problem) => StartupConfig {
                launch: None,
                config: None,
                source: ConfigSource::Environment,
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

/// The native theme for an appearance; `None` follows the system.
fn native_theme(appearance: Appearance) -> Option<Theme> {
    match appearance {
        Appearance::Light => Some(Theme::Light),
        Appearance::Dark => Some(Theme::Dark),
        Appearance::System => None,
    }
}

/// Applies the appearance to every window. Bundled pages, and pages from a
/// server started with `--theme system`, follow it through
/// `prefers-color-scheme`, with no script or capability. A restart passes the
/// new `--theme`, so other browsers and a pinned server match too.
fn apply_appearance<R: Runtime>(app: &AppHandle<R>, appearance: Appearance) {
    app.set_theme(native_theme(appearance));
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
    if let Some(config) = &startup.config {
        apply_appearance(app, config.appearance);
    }
    let start_on_open = startup
        .config
        .as_ref()
        .is_none_or(|config| config.start_on_open);

    let chrome_available = browser::chrome_available();
    let (menu, items, history_items) = build_menu(app, chrome_available)?;
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
    let history = MainWindowHistory {
        pages: Arc::default(),
        items: Some(history_items),
    };
    let pages = Arc::clone(&history.pages);
    build_main_window(app, policy.clone(), Arc::clone(&links), history, &initial)?;

    let (sender, receiver) = mpsc::channel();
    app.manage(ShellState {
        supervisor: Arc::clone(&supervisor),
        policy: policy.clone(),
        links,
        history: pages,
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
                    if action == Action::Start && supervisor.state() == State::Running {
                        // Already running: nothing to do, keep the current page.
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
        show_settings(app, SettingsSection::Settings);
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
        menu_id::SETTINGS | menu_id::DETAILS => {
            if let Some(section) = SettingsSection::for_menu(id) {
                show_settings(app, section);
            }
        }
        menu_id::QUIT => app.exit(0),
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
        menu_id::BACK | menu_id::FORWARD => {
            let back = history_direction(id) == Some(true);
            // The lock is released before navigating, which re-enters the
            // history through the navigation handler.
            let target = history_target(&mut lock(&state.history), &state.policy, back);
            if let Some(url) = target {
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
    /// A backend was started because this was the first configuration.
    pub started: bool,
    /// The developer environment override is active, so the saved file
    /// takes effect only in a later session without those variables.
    pub env_override_active: bool,
}

/// What Server Details shows.
#[derive(Debug, Clone, Serialize)]
pub struct ServerDetails {
    pub state: &'static str,
    pub owned_pid: Option<u32>,
    pub endpoint: Option<String>,
    pub served_workspace: Option<serde_json::Value>,
    pub configured_workspace: Option<String>,
    /// Whether the configured and served workspaces are the same directory
    /// once symlinks are resolved; `None` if either cannot be resolved.
    pub same_workspace: Option<bool>,
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
pub fn save_settings<R: Runtime>(
    app: AppHandle<R>,
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
    state.links.set_browser(config.browser);
    apply_appearance(&app, config.appearance);
    if *lock(&state.source) == ConfigSource::Environment {
        // The developer override stays in charge for this session.
        return Ok(SaveOutcome {
            restart_required: false,
            started: false,
            env_override_active: true,
        });
    }
    *lock(&state.source) = ConfigSource::File;
    *lock(&state.problem) = None;
    let was_configured = state.supervisor.is_configured();
    let launch = settings::launch_config(&config);
    let launch_changed = settings::needs_restart(previous.as_ref(), &config)
        || state.supervisor.config().as_ref() != Some(&launch);
    state.supervisor.set_config(launch);
    let running = matches!(state.supervisor.state(), State::Running | State::Starting);
    // Only the first configuration starts the backend; a later change while
    // stopped waits for an explicit Start.
    let started = !was_configured && config.start_on_open;
    if started {
        state.request(Action::Start);
    }
    Ok(SaveOutcome {
        restart_required: running && launch_changed,
        started,
        env_override_active: false,
    })
}

/// Reports the owned backend's identity, endpoint, and diagnostics. It never
/// waits for an operation in flight, so the UI stays responsive during a
/// start or stop.
#[tauri::command]
pub fn get_server_details(state: tauri::State<'_, ShellState>) -> ServerDetails {
    let status = state.supervisor.status();
    let handshake = status.handshake.as_ref();
    let (owned_pid, stderr_tail) = state.supervisor.try_diagnostics().unwrap_or((
        None,
        "(an operation is in progress; refresh shortly)".into(),
    ));
    let configured = state.supervisor.config().map(|config| config.project_root);
    let served =
        handshake.and_then(|h| h.workspace.get("project_root")?.as_str().map(PathBuf::from));
    ServerDetails {
        state: state_name(status.state),
        owned_pid,
        endpoint: handshake.map(|h| h.url.clone()),
        served_workspace: handshake.map(|h| h.workspace.clone()),
        same_workspace: match (&configured, &served) {
            (Some(configured), Some(served)) => same_directory(configured, served),
            _ => None,
        },
        configured_workspace: configured.map(|path| path.display().to_string()),
        protocol_version: handshake.map(|h| h.protocol_version),
        backend: handshake.map(|h| h.backend.clone()),
        last_error_code: status.last_error.as_ref().map(failure_code),
        last_error_message: status
            .last_error
            .as_ref()
            .map(|error| error.message.clone()),
        last_exit_code: status.last_exit_code,
        stderr_tail,
        chrome_available: state.chrome_available,
        last_handoff: state.links.last().map(|result| match result {
            Ok(handoff) => serde_json::json!({"ok": true, "handoff": handoff}),
            Err(error) => serde_json::json!({"ok": false, "error": error}),
        }),
    }
}

/// True if `a` and `b` are the same directory once symlinks are resolved, or
/// `None` if either cannot be resolved.
pub fn same_directory(a: &std::path::Path, b: &std::path::Path) -> Option<bool> {
    Some(std::fs::canonicalize(a).ok()? == std::fs::canonicalize(b).ok()?)
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

    fn page(path: &str) -> Url {
        Url::parse(&format!("http://127.0.0.1:50543{path}")).unwrap()
    }

    #[test]
    fn history_goes_back_and_forward_over_backend_pages() {
        let backend = page("/");
        let mut history = PageHistory::default();
        assert!(!history.can_go_back(Some(&backend)));
        for path in ["/", "/health", "/meta"] {
            history.visited(&page(path), Some(&backend));
        }
        assert!(history.can_go_back(Some(&backend)));
        assert!(!history.can_go_forward(Some(&backend)));

        assert_eq!(history.go_back(Some(&backend)), Some(page("/health")));
        history.visited(&page("/health"), Some(&backend));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));
        history.visited(&page("/"), Some(&backend));
        assert!(!history.can_go_back(Some(&backend)));
        assert_eq!(history.go_back(Some(&backend)), None);

        assert_eq!(history.go_forward(Some(&backend)), Some(page("/health")));
        history.visited(&page("/health"), Some(&backend));
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/meta")));
        assert!(!history.can_go_forward(Some(&backend)));
    }

    #[test]
    fn a_new_page_clears_forward_and_a_reload_changes_nothing() {
        let backend = page("/");
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        history.visited(&page("/health"), Some(&backend));
        history.go_back(Some(&backend));
        history.visited(&page("/"), Some(&backend));
        assert!(history.can_go_forward(Some(&backend)));

        history.visited(&page("/"), Some(&backend));
        assert!(
            history.can_go_forward(Some(&backend)),
            "a reload keeps Forward"
        );
        history.visited(&page("/meta"), Some(&backend));
        assert!(!history.can_go_forward(Some(&backend)));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));
    }

    #[test]
    fn history_never_holds_status_pages_or_another_origin() {
        let backend = page("/");
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        history.visited(&status_url("starting", None), Some(&backend));
        history.visited(&page("/health"), None);
        let other = Url::parse("http://127.0.0.1:60000/meta").unwrap();
        history.visited(&other, Some(&backend));
        assert!(
            !history.can_go_back(Some(&backend)),
            "nothing else was recorded"
        );
    }

    #[test]
    fn a_restarted_backend_starts_a_fresh_history() {
        let old = page("/");
        let new = Url::parse("http://127.0.0.1:60000/").unwrap();
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&old));
        history.visited(&page("/health"), Some(&old));

        // Stopped: nothing to go back to, and the old pages are dropped.
        assert!(!history.can_go_back(None));
        assert_eq!(history.go_back(None), None);
        assert!(!history.can_go_back(Some(&old)));

        history.visited(&page("/"), Some(&old));
        history.visited(&page("/health"), Some(&old));
        assert!(
            !history.can_go_back(Some(&new)),
            "the new origin has no history"
        );
        assert_eq!(history.go_back(Some(&new)), None);
        history.visited(&new, Some(&new));
        history.visited(&new.join("meta").unwrap(), Some(&new));
        assert_eq!(history.go_back(Some(&new)), Some(new.clone()));
    }

    #[test]
    fn the_webviews_own_back_and_rapid_moves_stay_consistent() {
        let backend = page("/");
        let mut history = PageHistory::default();
        for path in ["/", "/health", "/meta"] {
            history.visited(&page(path), Some(&backend));
        }
        // The Delete key: the webview goes back without the menu.
        history.visited(&page("/health"), Some(&backend));
        assert!(history.can_go_forward(Some(&backend)));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));

        // Back twice before either navigation is seen, then both arrive.
        history.visited(&page("/"), Some(&backend));
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/health")));
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/meta")));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/health")));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));
        history.visited(&page("/health"), Some(&backend));
        history.visited(&page("/"), Some(&backend));
        assert!(!history.can_go_back(Some(&backend)));
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/health")));
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/meta")));
    }

    #[test]
    fn a_status_page_ends_the_history_even_on_the_same_port() {
        let backend = page("/");
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        history.visited(&page("/health"), Some(&backend));
        // A restart that reuses the port still shows "Starting…" first.
        history.visited(&status_url("starting", None), None);
        history.visited(&page("/"), Some(&backend));
        assert!(!history.can_go_back(Some(&backend)));
    }

    #[test]
    fn in_page_anchor_links_are_not_pages() {
        let backend = page("/");
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        history.visited(&page("/health"), Some(&backend));
        for anchor in ["/health#a", "/health#b", "/health#a"] {
            history.visited(&page(anchor), Some(&backend));
        }
        assert!(!history.can_go_forward(Some(&backend)));
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));
        assert!(!history.can_go_back(Some(&backend)));
    }

    #[test]
    fn a_navigation_that_becomes_a_download_is_undone() {
        let backend = page("/");
        let mut history = PageHistory::default();
        for path in ["/", "/health", "/meta"] {
            history.visited(&page(path), Some(&backend));
        }
        history.go_back(Some(&backend));
        history.visited(&page("/health"), Some(&backend));
        let download = page("/workbench/prompt?work_item=WI-1&download=1");
        history.visited(&download, Some(&backend));
        history.download_started(&download);
        assert!(
            history.can_go_forward(Some(&backend)),
            "Forward is restored"
        );
        assert_eq!(history.go_back(Some(&backend)), Some(page("/")));

        // A download of a page that was never recorded changes nothing.
        history.download_started(&download);
        assert_eq!(history.go_forward(Some(&backend)), Some(page("/health")));
    }

    #[test]
    fn a_download_after_a_reload_or_a_move_restores_only_what_it_should() {
        let backend = page("/");
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        let download = page("/p?download=1");
        history.visited(&download, Some(&backend));
        history.visited(&download, Some(&backend)); // a reload keeps the snapshot
        history.download_started(&download);
        assert!(
            !history.can_go_back(Some(&backend)),
            "back to just the first page"
        );

        history.visited(&page("/health"), Some(&backend));
        history.go_back(Some(&backend));
        history.download_started(&page("/"));
        assert!(
            history.can_go_forward(Some(&backend)),
            "a move is never undone"
        );
    }

    #[test]
    fn menu_items_map_to_history_directions() {
        assert_eq!(history_direction(menu_id::BACK), Some(true));
        assert_eq!(history_direction(menu_id::FORWARD), Some(false));
        assert_eq!(history_direction(menu_id::RELOAD), None);
    }

    #[test]
    fn history_moves_only_to_pages_the_current_policy_allows() {
        let backend = page("/");
        let policy = NavigationPolicy::default();
        policy.set_backend(Some(&backend));
        let mut history = PageHistory::default();
        history.visited(&page("/"), Some(&backend));
        history.visited(&page("/health"), Some(&backend));

        assert_eq!(history_target(&mut history, &policy, true), Some(page("/")));
        assert_eq!(
            history_target(&mut history, &policy, false),
            Some(page("/health"))
        );

        // A restarted backend on another port: the history no longer belongs
        // to the running backend, so it is dropped. (The policy re-check in
        // `history_target` is defense in depth; a page on the history's own
        // origin always passes it.)
        let new = Url::parse("http://127.0.0.1:60000/").unwrap();
        policy.set_backend(Some(&new));
        assert_eq!(history_target(&mut history, &policy, true), None);
        policy.set_backend(Some(&backend));
        assert_eq!(
            history_target(&mut history, &policy, true),
            None,
            "they are gone"
        );

        // Stopped: nothing is allowed.
        history.visited(&page("/"), Some(&backend));
        history.visited(&page("/health"), Some(&backend));
        policy.set_backend(None);
        assert_eq!(history_target(&mut history, &policy, true), None);
    }

    #[test]
    fn history_is_bounded() {
        let backend = page("/");
        let mut history = PageHistory::default();
        for index in 0..(PageHistory::LIMIT + 10) {
            history.visited(&page(&format!("/p{index}")), Some(&backend));
        }
        let mut steps = 0;
        while history.go_back(Some(&backend)).is_some() {
            steps += 1;
        }
        assert_eq!(steps, PageHistory::LIMIT);
    }

    #[test]
    fn settings_and_server_details_show_their_own_section() {
        assert_eq!(
            SettingsSection::for_menu(menu_id::SETTINGS),
            Some(SettingsSection::Settings)
        );
        assert_eq!(
            SettingsSection::for_menu(menu_id::DETAILS),
            Some(SettingsSection::Details)
        );
        assert_eq!(SettingsSection::for_menu(menu_id::RELOAD), None);
        assert_eq!(
            SettingsSection::Details.show_script(),
            r#"window.lrhShowSection && window.lrhShowSection("details");"#
        );
    }

    #[test]
    fn appearance_maps_to_the_native_theme() {
        assert_eq!(native_theme(Appearance::Light), Some(Theme::Light));
        assert_eq!(native_theme(Appearance::Dark), Some(Theme::Dark));
        assert_eq!(native_theme(Appearance::System), None);
    }

    #[test]
    fn the_settings_page_provides_what_show_script_calls() {
        // The eval is guarded, so a renamed function or element would fail
        // silently; pin the contract with the bundled page.
        let script = include_str!("../../ui/settings.js");
        let page = include_str!("../../ui/settings.html");
        assert!(script.contains("window.lrhShowSection = "));
        assert!(script.contains("window.lrhInitialSection === \"details\""));
        assert!(script.contains("$(\"server-details\")"));
        assert!(page.contains("id=\"server-details\""));
    }

    #[cfg(unix)]
    #[test]
    fn a_symlinked_workspace_is_the_same_directory() {
        let root = std::env::temp_dir().join(format!(
            "lrh-console-same-dir-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        // A run that panicked may have left this behind.
        let _ = std::fs::remove_dir_all(&root);
        let real = root.join("real");
        let link = root.join("link");
        let other = root.join("other");
        std::fs::create_dir_all(&real).unwrap();
        std::fs::create_dir_all(&other).unwrap();
        std::os::unix::fs::symlink(&real, &link).unwrap();

        assert_eq!(same_directory(&link, &real), Some(true));
        assert_eq!(same_directory(&real, &real), Some(true));
        assert_eq!(same_directory(&link, &other), Some(false));
        assert_eq!(same_directory(&root.join("missing"), &real), None);
        std::fs::remove_dir_all(&root).unwrap();
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
        for local in [
            "http://localhost.:50543/",
            "http://127.0.0.2:50543/",
            "http://0.0.0.0:50543/",
            "http://[::ffff:127.0.0.1]:50543/",
            "http://app.localhost/",
        ] {
            assert!(!is_external_link(&url(local)), "{local} is local");
        }
        assert!(!is_external_link(&url("file:///etc/passwd")));
        assert!(!is_external_link(&status_url("stopped", None)));
    }
}

//! Private, explicit LRH Console configuration.
//!
//! The configuration names the `lrh` program to supervise, the workspace to
//! serve, the browser to hand links to, whether to start the backend when the
//! app opens, and the appearance (light, dark, or the system's). It lives in
//! one JSON file in the app's private config directory (mode `0600` on Unix).
//! Nothing is resolved through shell `PATH` or Conda activation: every path is
//! absolute and checked before it is saved. An invalid change is rejected and
//! the last working file is kept.

use std::ffi::OsString;
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::supervisor::LaunchConfig;

/// File name of the configuration inside the app config directory.
pub const CONFIG_FILE: &str = "config.json";

/// How the backend is launched.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum LaunchSpec {
    /// An installed `lrh` executable.
    Executable { path: PathBuf },
    /// A Python interpreter that runs `-m lrh.cli.main`, for a source checkout.
    Python {
        interpreter: PathBuf,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        pythonpath: Option<String>,
    },
}

/// Where handed-off links open. A fixed application choice, never a command.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BrowserChoice {
    #[default]
    Chrome,
    DefaultBrowser,
}

/// The `lrh serve` flag that turns on its packaged scripts.
pub const INTERACTIVE_FLAG: &str = "--interactive";

/// The page theme: light, dark, or following the system appearance.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Appearance {
    Light,
    Dark,
    #[default]
    System,
}

impl Appearance {
    /// The value `lrh serve --theme` takes.
    pub fn as_theme(self) -> &'static str {
        match self {
            Appearance::Light => "light",
            Appearance::Dark => "dark",
            Appearance::System => "system",
        }
    }
}

/// The saved configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Config {
    pub launch: LaunchSpec,
    pub workspace: PathBuf,
    #[serde(default)]
    pub browser: BrowserChoice,
    #[serde(default = "default_true")]
    pub start_on_open: bool,
    #[serde(default)]
    pub appearance: Appearance,
}

fn default_true() -> bool {
    true
}

/// A problem with one field, safe to show next to that field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FieldError {
    pub field: &'static str,
    pub message: String,
}

fn field_error(field: &'static str, message: impl Into<String>) -> FieldError {
    FieldError {
        field,
        message: message.into(),
    }
}

/// Checks every value. Returns all problems, not just the first.
pub fn validate(config: &Config) -> Result<(), Vec<FieldError>> {
    let mut errors = Vec::new();
    match &config.launch {
        LaunchSpec::Executable { path } => check_program(path, "launch.path", &mut errors),
        LaunchSpec::Python {
            interpreter,
            pythonpath,
        } => {
            check_program(interpreter, "launch.interpreter", &mut errors);
            if let Some(pythonpath) = pythonpath.as_deref().filter(|value| !value.is_empty()) {
                for entry in std::env::split_paths(pythonpath) {
                    if !entry.is_absolute() {
                        errors.push(field_error(
                            "launch.pythonpath",
                            "every PYTHONPATH entry must be an absolute path",
                        ));
                        break;
                    }
                    if !entry.is_dir() {
                        errors.push(field_error(
                            "launch.pythonpath",
                            format!("{} is not a directory", entry.display()),
                        ));
                        break;
                    }
                }
            }
        }
    }
    let workspace = &config.workspace;
    if !workspace.is_absolute() {
        errors.push(field_error("workspace", "must be an absolute path"));
    } else if !workspace.is_dir() {
        errors.push(field_error(
            "workspace",
            format!("{} is not a directory", workspace.display()),
        ));
    } else if !is_lrh_workspace(workspace) {
        errors.push(field_error(
            "workspace",
            "not an LRH workspace: expected project/focus and project/work_items inside it",
        ));
    }
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

fn check_program(path: &Path, field: &'static str, errors: &mut Vec<FieldError>) {
    if !path.is_absolute() {
        errors.push(field_error(field, "must be an absolute path"));
    } else if !path.is_file() {
        errors.push(field_error(
            field,
            format!("{} is not a file", path.display()),
        ));
    } else if !is_executable(path) {
        errors.push(field_error(
            field,
            format!("{} is not executable", path.display()),
        ));
    }
}

#[cfg(unix)]
fn is_executable(path: &Path) -> bool {
    use std::os::unix::fs::PermissionsExt;
    std::fs::metadata(path).is_ok_and(|meta| meta.permissions().mode() & 0o111 != 0)
}

#[cfg(not(unix))]
fn is_executable(path: &Path) -> bool {
    path.is_file()
}

/// True for what the backend accepts as a workspace (mirrors
/// `lrh.control.loader.find_project_dir`): a control directory with `focus/`
/// and `work_items/`, or a repository root whose `project/` has both.
fn is_lrh_workspace(path: &Path) -> bool {
    let is_control = |dir: &Path| dir.join("focus").exists() && dir.join("work_items").exists();
    is_control(path) || is_control(&path.join("project"))
}

/// The supervisor launch config for a validated configuration.
///
/// Paths are used exactly as saved. Canonicalizing would resolve a
/// virtualenv's `python` symlink to the base interpreter and lose the venv.
pub fn launch_config(config: &Config) -> LaunchConfig {
    let mut launch = match &config.launch {
        LaunchSpec::Executable { path } => LaunchConfig::new(path, &config.workspace),
        LaunchSpec::Python {
            interpreter,
            pythonpath,
        } => {
            let mut launch = LaunchConfig::new(interpreter, &config.workspace);
            launch.program_args = vec!["-m".into(), "lrh.cli.main".into()];
            if let Some(pythonpath) = pythonpath.as_deref().filter(|value| !value.is_empty()) {
                launch
                    .env
                    .push((OsString::from("PYTHONPATH"), OsString::from(pythonpath)));
            }
            launch
        }
    };
    // The app always runs Serve's interactive mode (owner decision,
    // WI-LRH-CONSOLE-INTERACTIVE); the pages still work without scripts.
    launch.serve_args = vec![
        "--theme".into(),
        config.appearance.as_theme().into(),
        INTERACTIVE_FLAG.into(),
    ];
    launch
}

/// True if switching from `before` to `after` changes what the running
/// backend serves or runs, so it takes effect only after a restart.
pub fn needs_restart(before: Option<&Config>, after: &Config) -> bool {
    before.is_none_or(|before| {
        before.launch != after.launch
            || before.workspace != after.workspace
            || before.appearance != after.appearance
    })
}

/// Reads and writes the configuration file.
#[derive(Debug, Clone)]
pub struct ConfigStore {
    path: PathBuf,
}

impl ConfigStore {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        ConfigStore { path: path.into() }
    }

    /// The store inside an app config directory.
    pub fn in_dir(dir: &Path) -> Self {
        Self::new(dir.join(CONFIG_FILE))
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Loads the saved configuration. `Ok(None)` means there is none yet.
    /// A file that does not parse is an error, never silently replaced.
    pub fn load(&self) -> Result<Option<Config>, String> {
        match std::fs::read_to_string(&self.path) {
            Ok(text) => serde_json::from_str(&text).map(Some).map_err(|error| {
                format!(
                    "{} is not valid configuration: {error}",
                    self.path.display()
                )
            }),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(error) => Err(format!("could not read {}: {error}", self.path.display())),
        }
    }

    /// Validates, then writes atomically. On any failure the previous file
    /// is left exactly as it was.
    pub fn save(&self, config: &Config) -> Result<(), Vec<FieldError>> {
        validate(config)?;
        self.write(config)
            .map_err(|error| vec![field_error("file", error)])
    }

    fn write(&self, config: &Config) -> Result<(), String> {
        let dir = self
            .path
            .parent()
            .ok_or_else(|| "configuration path has no directory".to_string())?;
        std::fs::create_dir_all(dir)
            .map_err(|error| format!("could not create {}: {error}", dir.display()))?;
        let text = serde_json::to_string_pretty(config)
            .map_err(|error| format!("could not encode configuration: {error}"))?;
        let temp = self.path.with_extension("json.tmp");
        let mut options = std::fs::OpenOptions::new();
        options.write(true).create(true).truncate(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        // A leftover temp file would keep its old permissions; start fresh.
        let _ = std::fs::remove_file(&temp);
        let mut file = options
            .open(&temp)
            .map_err(|error| format!("could not write {}: {error}", temp.display()))?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(&temp, std::fs::Permissions::from_mode(0o600))
                .map_err(|error| format!("could not secure {}: {error}", temp.display()))?;
        }
        file.write_all(text.as_bytes())
            .and_then(|()| file.write_all(b"\n"))
            .and_then(|()| file.sync_all())
            .map_err(|error| format!("could not write {}: {error}", temp.display()))?;
        std::fs::rename(&temp, &self.path)
            .map_err(|error| format!("could not replace {}: {error}", self.path.display()))
    }
}

/// File holding the main window's last size and position.
pub const WINDOW_STATE_FILE: &str = "window-state.json";
/// The main window's default size, about 1.4 times the original 1100 by 760.
pub const DEFAULT_WINDOW_WIDTH: f64 = 1540.0;
pub const DEFAULT_WINDOW_HEIGHT: f64 = 1064.0;
/// The default never takes more than this share of a display's work area.
const DEFAULT_WINDOW_SHARE: f64 = 0.9;
/// A saved frame smaller than this is treated as corrupt.
const MIN_WINDOW_WIDTH: f64 = 400.0;
const MIN_WINDOW_HEIGHT: f64 = 300.0;

/// A rectangle in logical (point) screen coordinates: a window's content
/// area (its inner position and inner size, which is what the window
/// builder's position and size set on macOS) or a display's work area.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct WindowFrame {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}

impl WindowFrame {
    /// Whether this is a usable frame or work area (finite, at least the
    /// minimum size). Displays reporting less, mid-reconfiguration, are
    /// skipped.
    pub fn is_plausible(&self) -> bool {
        [self.x, self.y, self.width, self.height]
            .iter()
            .all(|value| value.is_finite())
            && self.width >= MIN_WINDOW_WIDTH
            && self.height >= MIN_WINDOW_HEIGHT
    }

    fn contains(&self, inner: &WindowFrame) -> bool {
        inner.x >= self.x
            && inner.y >= self.y
            && inner.x + inner.width <= self.x + self.width
            && inner.y + inner.height <= self.y + self.height
    }

    fn overlap(&self, other: &WindowFrame) -> f64 {
        let width = (self.x + self.width).min(other.x + other.width) - self.x.max(other.x);
        let height = (self.y + self.height).min(other.y + other.height) - self.y.max(other.y);
        width.max(0.0) * height.max(0.0)
    }
}

/// The default frame on a display: the default size, never more than 90% of
/// the work area, centered in it.
pub fn default_window_frame(area: &WindowFrame) -> WindowFrame {
    // Never smaller than the plausible minimum, even on a degenerate area.
    let width = DEFAULT_WINDOW_WIDTH
        .min(area.width * DEFAULT_WINDOW_SHARE)
        .max(MIN_WINDOW_WIDTH);
    let height = DEFAULT_WINDOW_HEIGHT
        .min(area.height * DEFAULT_WINDOW_SHARE)
        .max(MIN_WINDOW_HEIGHT);
    WindowFrame {
        x: area.x + (area.width - width) / 2.0,
        y: area.y + (area.height - height) / 2.0,
        width,
        height,
    }
}

/// The main window's saved state: its frame, and the display it was on with
/// its offset from that display's work area, so it can return to that
/// display even after the displays are rearranged. Older files hold only
/// the frame.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SavedWindow {
    #[serde(flatten)]
    pub frame: WindowFrame,
    /// The display's name, as the system reports it.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display: Option<String>,
    /// The frame's offset from that display's work-area origin.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub offset: Option<(f64, f64)>,
}

impl SavedWindow {
    /// The state for `frame` on `display` (None if it is not known).
    pub fn on(frame: WindowFrame, display: Option<&Display>) -> Self {
        SavedWindow {
            frame,
            display: display.and_then(|display| display.name.clone()),
            offset: display.map(|display| (frame.x - display.area.x, frame.y - display.area.y)),
        }
    }
}

/// A connected display: its name, if it reports one, and its work area.
#[derive(Debug, Clone, PartialEq)]
pub struct Display {
    pub name: Option<String>,
    pub area: WindowFrame,
}

/// `frame` moved (and shrunk if needed) to lie fully inside `area`.
fn fit_into(frame: &WindowFrame, area: &WindowFrame) -> WindowFrame {
    let width = frame.width.min(area.width);
    let height = frame.height.min(area.height);
    WindowFrame {
        x: frame.x.clamp(area.x, area.x + area.width - width),
        y: frame.y.clamp(area.y, area.y + area.height - height),
        width,
        height,
    }
}

/// Where the main window opens:
///
/// 1. On the display it was saved on, if a display with that name is still
///    connected, at the same offset from its work area (wherever that
///    display now sits in the arrangement), fitted inside it.
/// 2. Otherwise at the saved frame, if that is fully on a connected display.
/// 3. Otherwise the saved frame fitted onto the display it overlaps most, or
///    the primary one.
/// 4. With no usable saved state, the default on the primary display.
pub fn place_window(
    saved: Option<&SavedWindow>,
    displays: &[Display],
    primary: &WindowFrame,
) -> WindowFrame {
    let Some(saved) = saved.filter(|saved| saved.frame.is_plausible()) else {
        return default_window_frame(primary);
    };
    if let (Some(name), Some((dx, dy))) = (&saved.display, saved.offset) {
        if let Some(display) = displays
            .iter()
            .find(|display| display.name.as_deref() == Some(name.as_str()))
        {
            let moved = WindowFrame {
                x: display.area.x + dx,
                y: display.area.y + dy,
                ..saved.frame
            };
            if moved.is_plausible() {
                return fit_into(&moved, &display.area);
            }
        }
    }
    let frame = saved.frame;
    if displays.iter().any(|display| display.area.contains(&frame)) {
        return frame;
    }
    let area = displays
        .iter()
        .map(|display| &display.area)
        .filter(|area| frame.overlap(area) > 0.0)
        .max_by(|a, b| frame.overlap(a).total_cmp(&frame.overlap(b)))
        .unwrap_or(primary);
    fit_into(&frame, area)
}

/// Reads and writes the main window's saved frame. It holds only geometry,
/// never leaves this machine, and a missing or unreadable file just means
/// the default frame is used.
#[derive(Debug, Clone)]
pub struct WindowStateStore {
    path: PathBuf,
}

impl WindowStateStore {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        WindowStateStore { path: path.into() }
    }

    /// The store inside an app config directory, next to the configuration.
    pub fn in_dir(dir: &Path) -> Self {
        Self::new(dir.join(WINDOW_STATE_FILE))
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// The saved state, or None if there is none or it cannot be used.
    pub fn load(&self) -> Option<SavedWindow> {
        let text = std::fs::read_to_string(&self.path).ok()?;
        serde_json::from_str::<SavedWindow>(&text)
            .ok()
            .filter(|saved| saved.frame.is_plausible())
    }

    /// Writes the frame atomically, so a crash never leaves half a file.
    pub fn save(&self, saved: &SavedWindow) -> Result<(), String> {
        let dir = self
            .path
            .parent()
            .ok_or_else(|| "window state path has no directory".to_string())?;
        std::fs::create_dir_all(dir)
            .map_err(|error| format!("could not create {}: {error}", dir.display()))?;
        let text = serde_json::to_string(saved)
            .map_err(|error| format!("could not encode window state: {error}"))?;
        // A unique temp file, so overlapping saves never share one.
        static SAVES: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let count = SAVES.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let temp = self
            .path
            .with_extension(format!("json.{}.{count}.tmp", std::process::id()));
        std::fs::write(&temp, format!("{text}\n"))
            .map_err(|error| format!("could not write {}: {error}", temp.display()))?;
        std::fs::rename(&temp, &self.path)
            .map_err(|error| format!("could not replace {}: {error}", self.path.display()))
    }

    /// Forgets the saved frame. Having none is not an error.
    pub fn clear(&self) -> Result<(), String> {
        match std::fs::remove_file(&self.path) {
            Ok(()) => Ok(()),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
            Err(error) => Err(format!("could not remove {}: {error}", self.path.display())),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn frame(x: f64, y: f64, width: f64, height: f64) -> WindowFrame {
        WindowFrame {
            x,
            y,
            width,
            height,
        }
    }

    #[test]
    fn the_default_window_is_larger_but_fits_the_display() {
        let big = frame(0.0, 25.0, 2560.0, 1415.0);
        assert_eq!(
            default_window_frame(&big),
            frame(510.0, 200.5, 1540.0, 1064.0),
            "1.4 times 1100 by 760, centered"
        );
        let degenerate = default_window_frame(&frame(0.0, 0.0, 0.0, 0.0));
        assert!(degenerate.is_plausible(), "never a zero-size window");
        let laptop = frame(0.0, 25.0, 1440.0, 875.0);
        let small = default_window_frame(&laptop);
        assert_eq!(
            (small.width, small.height),
            (1296.0, 787.5),
            "90% of the area"
        );
        assert!(laptop.contains(&small));
    }

    fn display(name: &str, area: WindowFrame) -> Display {
        Display {
            name: Some(name.to_string()),
            area,
        }
    }

    fn saved(frame: WindowFrame) -> SavedWindow {
        SavedWindow {
            frame,
            display: None,
            offset: None,
        }
    }

    #[test]
    fn a_saved_frame_on_a_connected_display_is_restored_as_is() {
        let displays = [
            display("Built-in", frame(0.0, 25.0, 1440.0, 875.0)),
            display("Studio", frame(1440.0, 0.0, 2560.0, 1440.0)),
        ];
        let state = saved(frame(1600.0, 100.0, 1500.0, 1000.0));
        assert_eq!(
            place_window(Some(&state), &displays, &displays[0].area),
            state.frame
        );
    }

    #[test]
    fn the_window_follows_its_display_when_the_displays_are_rearranged() {
        let built_in = display("Built-in", frame(0.0, 25.0, 1440.0, 875.0));
        let studio_right = display("Studio", frame(1440.0, 0.0, 2560.0, 1440.0));
        let window = frame(1600.0, 100.0, 1500.0, 1000.0);
        let state = SavedWindow::on(window, Some(&studio_right));
        assert_eq!(state.offset, Some((160.0, 100.0)));
        // The same display, now arranged to the left of the built-in one.
        let studio_left = display("Studio", frame(-2560.0, 0.0, 2560.0, 1440.0));
        let placed = place_window(
            Some(&state),
            &[built_in.clone(), studio_left],
            &built_in.area,
        );
        assert_eq!(placed, frame(-2400.0, 100.0, 1500.0, 1000.0));
    }

    #[test]
    fn a_frame_off_every_display_moves_fully_onto_one() {
        let laptop = display("Built-in", frame(0.0, 25.0, 1440.0, 875.0));
        // Saved on an external display that is now gone.
        let gone = SavedWindow::on(
            frame(1600.0, 100.0, 1500.0, 1000.0),
            Some(&display("Studio", frame(1440.0, 0.0, 2560.0, 1440.0))),
        );
        let placed = place_window(Some(&gone), std::slice::from_ref(&laptop), &laptop.area);
        assert!(laptop.area.contains(&placed), "{placed:?}");
        assert_eq!(
            (placed.width, placed.height),
            (1440.0, 875.0),
            "shrunk to fit"
        );
        // Hanging half off the right edge of the one display it overlaps.
        let hanging = saved(frame(1000.0, 100.0, 800.0, 600.0));
        let placed = place_window(Some(&hanging), std::slice::from_ref(&laptop), &laptop.area);
        assert_eq!(placed, frame(640.0, 100.0, 800.0, 600.0));
    }

    #[test]
    fn an_implausible_saved_frame_falls_back_to_the_default() {
        let area = frame(0.0, 25.0, 2560.0, 1415.0);
        let displays = [display("Studio", area)];
        for bad in [
            frame(f64::NAN, 0.0, 1500.0, 1000.0),
            frame(0.0, 0.0, 10.0, 10.0),
            frame(0.0, 0.0, f64::INFINITY, 1000.0),
        ] {
            assert_eq!(
                place_window(Some(&saved(bad)), &displays, &area),
                default_window_frame(&area)
            );
        }
        assert_eq!(
            place_window(None, &displays, &area),
            default_window_frame(&area)
        );
    }

    #[test]
    fn window_state_round_trips_and_a_corrupt_file_is_ignored() {
        let dir = TempDir::new("window-state");
        let store = WindowStateStore::in_dir(&dir.0);
        assert_eq!(store.load(), None);
        let state = SavedWindow::on(
            frame(10.0, 40.0, 1500.0, 1000.0),
            Some(&display("Built-in", frame(0.0, 25.0, 1440.0, 875.0))),
        );
        store.save(&state).unwrap();
        assert_eq!(store.load(), Some(state));
        // A file from before display names were saved still loads.
        std::fs::write(
            store.path(),
            r#"{"x":10.0,"y":40.0,"width":1500.0,"height":1000.0}"#,
        )
        .unwrap();
        assert_eq!(store.load(), Some(saved(frame(10.0, 40.0, 1500.0, 1000.0))));
        std::fs::write(store.path(), "{not json").unwrap();
        assert_eq!(store.load(), None, "corrupt: the default is used, no error");
        store.clear().unwrap();
        store.clear().unwrap();
        assert!(!store.path().exists());
    }

    struct TempDir(PathBuf);

    impl TempDir {
        fn new(name: &str) -> Self {
            let dir = std::env::temp_dir().join(format!(
                "lrh-console-settings-{name}-{}",
                std::process::id()
            ));
            let _ = std::fs::remove_dir_all(&dir);
            std::fs::create_dir_all(&dir).unwrap();
            TempDir(std::fs::canonicalize(dir).unwrap())
        }
    }

    impl Drop for TempDir {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.0);
        }
    }

    /// A fake workspace and executable inside `dir`.
    fn fixture(dir: &Path) -> Config {
        let workspace = dir.join("ws");
        std::fs::create_dir_all(workspace.join("project/focus")).unwrap();
        std::fs::create_dir_all(workspace.join("project/work_items")).unwrap();
        let program = dir.join("lrh");
        std::fs::write(&program, "#!/bin/sh\n").unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(&program, std::fs::Permissions::from_mode(0o755)).unwrap();
        }
        Config {
            launch: LaunchSpec::Executable { path: program },
            workspace,
            browser: BrowserChoice::Chrome,
            start_on_open: true,
            appearance: Appearance::System,
        }
    }

    #[test]
    fn a_complete_config_validates_and_round_trips() {
        let dir = TempDir::new("roundtrip");
        let config = fixture(&dir.0);
        let store = ConfigStore::in_dir(&dir.0.join("app"));

        assert_eq!(store.load().unwrap(), None, "no file yet");
        store.save(&config).unwrap();
        assert_eq!(store.load().unwrap(), Some(config));
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mode = std::fs::metadata(store.path())
                .unwrap()
                .permissions()
                .mode();
            assert_eq!(mode & 0o777, 0o600, "the configuration file is private");
        }
    }

    #[test]
    fn an_invalid_change_is_rejected_and_the_last_working_file_kept() {
        let dir = TempDir::new("reject");
        let good = fixture(&dir.0);
        let store = ConfigStore::in_dir(&dir.0.join("app"));
        store.save(&good).unwrap();

        let mut bad = good.clone();
        bad.workspace = dir.0.join("missing");
        bad.launch = LaunchSpec::Executable {
            path: PathBuf::from("lrh"),
        };
        let errors = store.save(&bad).unwrap_err();
        let fields: Vec<_> = errors.iter().map(|error| error.field).collect();
        assert_eq!(fields, vec!["launch.path", "workspace"]);
        assert_eq!(store.load().unwrap(), Some(good), "previous values kept");
    }

    #[test]
    fn workspaces_must_contain_an_lrh_control_directory() {
        let dir = TempDir::new("workspace");
        let mut config = fixture(&dir.0);
        config.workspace = dir.0.clone();
        let errors = validate(&config).unwrap_err();
        assert_eq!(errors[0].field, "workspace");
        assert!(errors[0].message.contains("not an LRH workspace"));
    }

    #[test]
    fn an_empty_project_directory_is_not_a_workspace() {
        let dir = TempDir::new("emptyproject");
        let mut config = fixture(&dir.0);
        let bare = dir.0.join("bare");
        std::fs::create_dir_all(bare.join("project")).unwrap();
        config.workspace = bare;
        assert_eq!(validate(&config).unwrap_err()[0].field, "workspace");
    }

    #[test]
    fn pythonpath_entries_must_be_absolute_directories() {
        let dir = TempDir::new("pythonpath");
        let mut config = fixture(&dir.0);
        let interpreter = match &config.launch {
            LaunchSpec::Executable { path } => path.clone(),
            LaunchSpec::Python { interpreter, .. } => interpreter.clone(),
        };
        config.launch = LaunchSpec::Python {
            interpreter,
            pythonpath: Some("src".into()),
        };
        assert_eq!(validate(&config).unwrap_err()[0].field, "launch.pythonpath");
    }

    #[test]
    fn launch_configs_keep_paths_exactly_as_saved() {
        let config = Config {
            launch: LaunchSpec::Python {
                interpreter: PathBuf::from("/venv/bin/python"),
                pythonpath: Some("/repo/src".into()),
            },
            workspace: PathBuf::from("/repo"),
            browser: BrowserChoice::DefaultBrowser,
            start_on_open: false,
            appearance: Appearance::Dark,
        };
        let launch = launch_config(&config);
        assert_eq!(launch.program, PathBuf::from("/venv/bin/python"));
        assert_eq!(
            launch.program_args,
            vec![OsString::from("-m"), "lrh.cli.main".into()]
        );
        assert_eq!(launch.env, vec![("PYTHONPATH".into(), "/repo/src".into())]);
        assert_eq!(
            launch.serve_args,
            vec![
                OsString::from("--theme"),
                "dark".into(),
                "--interactive".into()
            ]
        );
    }

    #[test]
    fn a_file_without_appearance_loads_as_system() {
        let config: Config = serde_json::from_str(
            r#"{"launch": {"kind": "executable", "path": "/usr/local/bin/lrh"},
                "workspace": "/repo", "browser": "chrome", "start_on_open": true}"#,
        )
        .unwrap();
        assert_eq!(config.appearance, Appearance::System);
        assert_eq!(
            launch_config(&config).serve_args,
            vec![
                OsString::from("--theme"),
                "system".into(),
                "--interactive".into()
            ]
        );
        let saved = serde_json::to_value(&config).unwrap();
        assert_eq!(saved["appearance"], "system");
    }

    #[test]
    fn only_launch_workspace_or_appearance_changes_need_a_restart() {
        let dir = TempDir::new("restart");
        let config = fixture(&dir.0);
        assert!(needs_restart(None, &config));

        let mut browser_only = config.clone();
        browser_only.browser = BrowserChoice::DefaultBrowser;
        browser_only.start_on_open = false;
        assert!(!needs_restart(Some(&config), &browser_only));

        let mut moved = config.clone();
        moved.workspace = dir.0.join("elsewhere");
        assert!(needs_restart(Some(&config), &moved));

        let mut dark = config.clone();
        dark.appearance = Appearance::Dark;
        assert!(needs_restart(Some(&config), &dark));
    }

    #[test]
    fn a_corrupt_file_is_an_error_not_a_reset() {
        let dir = TempDir::new("corrupt");
        let store = ConfigStore::in_dir(&dir.0);
        std::fs::write(store.path(), "{not json").unwrap();
        assert!(store.load().is_err());
    }
}

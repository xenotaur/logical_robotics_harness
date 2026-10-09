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

#[cfg(test)]
mod tests {
    use super::*;

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

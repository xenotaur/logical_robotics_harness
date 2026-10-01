//! LRH Console desktop shell.
//!
//! The [`shell`] owns the main window, the lifecycle menus, and the
//! navigation policy, and drives the owned-server [`supervisor`]
//! (WI-LRH-CONSOLE-DESKTOP-SHELL, WI-LRH-CONSOLE-DESKTOP-SUPERVISOR). Private
//! configuration, Settings/Details, recovery pages, and browser handoff arrive
//! with WI-LRH-CONSOLE-DESKTOP-SETTINGS.

pub mod shell;
pub mod supervisor;

use serde::Serialize;
use tauri::{Manager, RunEvent, WindowEvent};

/// Static identity of this desktop build.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AppInfo {
    pub name: &'static str,
    pub version: &'static str,
    pub stage: &'static str,
}

/// Returns the identity of this desktop build.
pub fn app_info() -> AppInfo {
    AppInfo {
        name: "LRH Console",
        version: env!("CARGO_PKG_VERSION"),
        stage: "L0 shell",
    }
}

/// Registered so its permission is generated, but granted to no window: the
/// main window's content gets no app commands. The Settings window
/// (WI-LRH-CONSOLE-DESKTOP-SETTINGS) is its intended caller.
#[tauri::command]
fn get_app_info() -> AppInfo {
    app_info()
}

/// Registers this app's commands on a builder for any runtime.
pub fn with_commands<R: tauri::Runtime>(builder: tauri::Builder<R>) -> tauri::Builder<R> {
    builder.invoke_handler(tauri::generate_handler![get_app_info])
}

/// The compiled app context (config, capabilities, and bundled pages).
///
/// `generate_context!` embeds platform metadata and may be expanded only once
/// per crate, so the app and the tests share this single expansion.
#[doc(hidden)]
pub fn context<R: tauri::Runtime>() -> tauri::Context<R> {
    tauri::generate_context!()
}

/// Runs the desktop app.
pub fn run() {
    let app = with_commands(tauri::Builder::default())
        .setup(|app| {
            shell::setup(app.handle())?;
            Ok(())
        })
        .on_menu_event(|app, event| shell::handle_menu(app, event.id().as_ref()))
        .on_window_event(|window, event| {
            // On macOS, closing the main window keeps the app and its server
            // running; the Dock icon brings the window back.
            if cfg!(target_os = "macos") && window.label() == shell::MAIN_WINDOW {
                if let WindowEvent::CloseRequested { api, .. } = event {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .build(context())
        .expect("error while building LRH Console");
    app.run(|app, event| match event {
        #[cfg(target_os = "macos")]
        RunEvent::Reopen { .. } => shell::show_main(app),
        // Quit stops the owned server, within the supervisor's bounds.
        RunEvent::Exit => app.state::<shell::ShellState>().shutdown(),
        _ => {}
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn app_info_reports_package_version() {
        let info = app_info();
        assert_eq!(info.name, "LRH Console");
        assert_eq!(info.version, env!("CARGO_PKG_VERSION"));
    }
}

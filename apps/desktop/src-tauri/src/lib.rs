//! LRH Console desktop shell.
//!
//! The [`shell`] owns the windows, menus, navigation policy, and Settings
//! commands, and drives the owned-server [`supervisor`]. [`settings`] holds
//! the private configuration and [`browser`] the narrow link handoff
//! (WI-LRH-CONSOLE-DESKTOP-SUPERVISOR, -SHELL, and -SETTINGS).

pub mod browser;
pub mod settings;
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

/// Granted only to the Settings window, like every app command; the main
/// window's content gets none.
#[tauri::command]
fn get_app_info() -> AppInfo {
    app_info()
}

/// Registers this app's commands on a builder for any runtime.
pub fn with_commands<R: tauri::Runtime>(builder: tauri::Builder<R>) -> tauri::Builder<R> {
    builder.invoke_handler(tauri::generate_handler![
        get_app_info,
        shell::get_settings,
        shell::save_settings,
        shell::get_server_details,
        shell::restart_server,
        shell::reset_window_state,
    ])
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
            if window.label() != shell::MAIN_WINDOW {
                return;
            }
            match event {
                // The main window remembers its size and position.
                WindowEvent::Moved(_) | WindowEvent::Resized(_) => {
                    shell::main_window_changed(window);
                }
                WindowEvent::CloseRequested { api, .. } => {
                    shell::save_main_window(window);
                    // On macOS, closing the main window keeps the app and its
                    // server running; the Dock icon brings the window back.
                    if cfg!(target_os = "macos") {
                        api.prevent_close();
                        let _ = window.hide();
                    }
                }
                _ => {}
            }
        })
        .build(context())
        .expect("error while building LRH Console");
    app.run(|app, event| match event {
        #[cfg(target_os = "macos")]
        RunEvent::Reopen { .. } => shell::show_main(app),
        // Quit shows "Stopping…" and stops the owned server off the main
        // thread, then exits, so the UI never freezes during the stop. The
        // state is absent only if setup failed, and then nothing was started.
        RunEvent::ExitRequested { api, .. } => {
            if let Some(state) = app.try_state::<shell::ShellState>() {
                if state.begin_exit() {
                    api.prevent_exit();
                    shell::show_stopping(app);
                    let app = app.clone();
                    std::thread::spawn(move || {
                        app.state::<shell::ShellState>().shutdown();
                        app.exit(0);
                    });
                }
            }
        }
        // Covers exits that skip ExitRequested (Dock "Quit", AppleScript
        // quit, logout). It never blocks the main thread: if an operation is
        // in flight, the exiting process closes the child's stdin and the
        // child stops itself under the protocol's parent-loss rule.
        RunEvent::Exit => {
            if let Some(state) = app.try_state::<shell::ShellState>() {
                state.supervisor.try_shutdown();
            }
        }
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

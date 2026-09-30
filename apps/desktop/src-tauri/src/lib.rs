//! LRH Console desktop shell.
//!
//! One bundled window and one read-only command, plus the owned-server
//! [`supervisor`] (WI-LRH-CONSOLE-DESKTOP-SUPERVISOR). Native menus,
//! Settings/Details, and recovery pages that drive the supervisor arrive with
//! WI-LRH-CONSOLE-DESKTOP-SHELL.

pub mod supervisor;

use serde::Serialize;

/// Static identity of this desktop build, safe to show in bundled pages.
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
        stage: "L0 toolchain skeleton",
    }
}

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
fn context<R: tauri::Runtime>() -> tauri::Context<R> {
    tauri::generate_context!()
}

/// Runs the desktop app.
pub fn run() {
    with_commands(tauri::Builder::default())
        .run(context())
        .expect("error while running LRH Console");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn build_app() -> tauri::App<tauri::test::MockRuntime> {
        with_commands(tauri::test::mock_builder())
            .build(context())
            .expect("failed to build mock app")
    }

    /// The origin Tauri serves bundled pages from on this platform.
    #[cfg(not(windows))]
    const LOCAL_ORIGIN: &str = "tauri://localhost";
    #[cfg(windows)]
    const LOCAL_ORIGIN: &str = "http://tauri.localhost";

    fn invoke_request(cmd: &str, origin: &str) -> tauri::webview::InvokeRequest {
        tauri::webview::InvokeRequest {
            cmd: cmd.into(),
            callback: tauri::ipc::CallbackFn(0),
            error: tauri::ipc::CallbackFn(1),
            url: origin.parse().unwrap(),
            body: tauri::ipc::InvokeBody::default(),
            headers: Default::default(),
            invoke_key: tauri::test::INVOKE_KEY.to_string(),
        }
    }

    #[test]
    fn app_info_reports_package_version() {
        let info = app_info();
        assert_eq!(info.name, "LRH Console");
        assert_eq!(info.version, env!("CARGO_PKG_VERSION"));
    }

    #[test]
    fn main_window_may_read_app_info() {
        let app = build_app();
        let window = tauri::WebviewWindowBuilder::new(&app, "main", Default::default())
            .build()
            .expect("failed to build main window");

        let response =
            tauri::test::get_ipc_response(&window, invoke_request("get_app_info", LOCAL_ORIGIN))
                .expect("bundled pages in the main window may call get_app_info");
        let value: serde_json::Value = response.deserialize().expect("json response");
        assert_eq!(value["name"], "LRH Console");
    }

    #[test]
    fn unlisted_window_is_denied_app_commands() {
        let app = build_app();
        let window = tauri::WebviewWindowBuilder::new(&app, "untrusted", Default::default())
            .build()
            .expect("failed to build untrusted window");

        let error =
            tauri::test::get_ipc_response(&window, invoke_request("get_app_info", LOCAL_ORIGIN))
                .expect_err("a window without a capability must not reach app commands");
        assert!(
            format!("{error:?}").contains("not allowed"),
            "expected an ACL denial, got {error:?}"
        );
    }

    #[test]
    fn remote_origin_in_main_window_is_denied_app_commands() {
        // The dashboard will be the owned loopback Serve origin; content from
        // that (or any non-bundled) origin must get no native commands.
        let app = build_app();
        let window = tauri::WebviewWindowBuilder::new(&app, "main", Default::default())
            .build()
            .expect("failed to build main window");

        let error = tauri::test::get_ipc_response(
            &window,
            invoke_request("get_app_info", "http://127.0.0.1:8765/"),
        )
        .expect_err("loopback server content must not reach app commands");
        assert!(
            format!("{error:?}").contains("not allowed"),
            "expected an ACL denial, got {error:?}"
        );
    }
}

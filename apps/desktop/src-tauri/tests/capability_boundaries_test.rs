//! Capability and navigation boundaries of the app's windows.
//!
//! The main window shows bundled status pages or the owned Serve origin.
//! Neither may invoke app commands, and the window may only navigate to
//! bundled pages and the current backend's exact origin. The Settings window
//! is the only one granted the app's (narrow, validated) commands. These tests
//! use the Tauri mock runtime, so no real window opens.

use std::sync::Arc;

use lrh_console_lib::shell::{self, LinkHandoff, NavigationPolicy};
use tauri::webview::NewWindowResponse;
use tauri::Url;

fn build_app() -> tauri::App<tauri::test::MockRuntime> {
    lrh_console_lib::with_commands(tauri::test::mock_builder())
        .build(lrh_console_lib::context())
        .expect("failed to build mock app")
}

fn invoke_request(cmd: &str, origin: &Url) -> tauri::webview::InvokeRequest {
    tauri::webview::InvokeRequest {
        cmd: cmd.into(),
        callback: tauri::ipc::CallbackFn(0),
        error: tauri::ipc::CallbackFn(1),
        url: origin.clone(),
        body: tauri::ipc::InvokeBody::default(),
        headers: Default::default(),
        invoke_key: tauri::test::INVOKE_KEY.to_string(),
    }
}

/// Every app command, as registered.
const APP_COMMANDS: [&str; 5] = [
    "get_app_info",
    "get_settings",
    "save_settings",
    "get_server_details",
    "restart_server",
];

fn assert_denied(window: &tauri::WebviewWindow<tauri::test::MockRuntime>, origin: &Url) {
    for command in APP_COMMANDS {
        let error = tauri::test::get_ipc_response(window, invoke_request(command, origin))
            .expect_err("this content must not reach app commands");
        assert!(
            format!("{error:?}").contains("not allowed"),
            "expected an ACL denial for {command} from {origin}, got {error:?}"
        );
    }
}

fn url(text: &str) -> Url {
    Url::parse(text).unwrap()
}

#[test]
fn bundled_status_page_in_the_main_window_gets_no_app_commands() {
    let app = build_app();
    let initial = shell::status_url("stopped", None);
    let window = shell::build_main_window(
        &app,
        NavigationPolicy::default(),
        Arc::new(LinkHandoff::default()),
        shell::MainWindowHistory::default(),
        &initial,
        Arc::new(shell::LoadingCue::default()),
    )
    .expect("main window");

    assert_denied(&window, &shell::bundled_base());
}

#[test]
fn owned_serve_origin_in_the_main_window_gets_no_app_commands() {
    let app = build_app();
    let window = shell::build_main_window(
        &app,
        NavigationPolicy::default(),
        Arc::new(LinkHandoff::default()),
        shell::MainWindowHistory::default(),
        &shell::status_url("stopped", None),
        Arc::new(shell::LoadingCue::default()),
    )
    .expect("main window");

    assert_denied(&window, &url("http://127.0.0.1:50543/"));
}

#[test]
fn an_unlisted_window_gets_no_app_commands() {
    let app = build_app();
    let window = tauri::WebviewWindowBuilder::new(&app, "untrusted", Default::default())
        .build()
        .expect("untrusted window");

    assert_denied(&window, &shell::bundled_base());
}

#[test]
fn the_settings_window_may_call_its_commands_from_bundled_pages() {
    let app = build_app();
    let window = shell::build_settings_window(&app, shell::SettingsSection::Settings)
        .expect("settings window");

    let response = tauri::test::get_ipc_response(
        &window,
        invoke_request("get_app_info", &shell::bundled_base()),
    )
    .expect("the Settings window may call get_app_info");
    let value: serde_json::Value = response.deserialize().expect("json response");
    assert_eq!(value["name"], "LRH Console");

    // The other commands pass the ACL; they fail later only because this mock
    // app has no managed shell state.
    for command in &APP_COMMANDS[1..] {
        let result =
            tauri::test::get_ipc_response(&window, invoke_request(command, &shell::bundled_base()));
        if let Err(error) = result {
            assert!(
                !format!("{error:?}").contains("not allowed"),
                "{command} must be allowed in the Settings window, got {error:?}"
            );
        }
    }
}

#[test]
fn remote_content_in_the_settings_window_gets_no_app_commands() {
    let app = build_app();
    let window = shell::build_settings_window(&app, shell::SettingsSection::Settings)
        .expect("settings window");

    assert_denied(&window, &url("http://127.0.0.1:50543/"));
    assert_denied(&window, &url("https://example.com/"));
}

#[test]
fn navigation_allows_bundled_pages_and_only_the_current_backend_origin() {
    let policy = NavigationPolicy::default();
    let endpoint = url("http://127.0.0.1:50543/");

    assert!(policy.allows(&shell::status_url("starting", None)));
    assert!(!policy.allows(&endpoint), "no backend yet");

    policy.set_backend(Some(&endpoint));
    assert!(policy.allows(&url("http://127.0.0.1:50543/meta?project=lrh")));
    for refused in [
        "http://127.0.0.1:50544/",
        "http://localhost:50543/",
        "https://127.0.0.1:50543/",
        "https://example.com/",
        "file:///etc/passwd",
        "data:text/html,hello",
        "javascript:alert(1)",
    ] {
        assert!(!policy.allows(&url(refused)), "{refused} must be refused");
    }
}

#[test]
fn a_restart_drops_the_previous_backend_origin() {
    let policy = NavigationPolicy::default();
    let first = url("http://127.0.0.1:50543/");
    let second = url("http://127.0.0.1:50999/");

    policy.set_backend(Some(&first));
    policy.set_backend(None);
    assert!(!policy.allows(&first), "stopped: the old origin is gone");

    policy.set_backend(Some(&second));
    assert!(!policy.allows(&first), "the stale origin stays refused");
    assert!(policy.allows(&second));
    assert!(policy.allows(&shell::status_url("stopped", None)));
}

#[test]
fn clones_share_one_policy() {
    let policy = NavigationPolicy::default();
    let handed_to_window = policy.clone();
    policy.set_backend(Some(&url("http://127.0.0.1:50543/")));

    assert!(handed_to_window.allows(&url("http://127.0.0.1:50543/")));
}

#[test]
fn popups_and_new_windows_are_refused() {
    for target in [
        "https://example.com/",
        "http://127.0.0.1:50543/",
        "tauri://localhost/index.html",
    ] {
        let response = shell::new_window_response::<tauri::test::MockRuntime>(&url(target));
        assert!(
            matches!(response, NewWindowResponse::Deny),
            "{target} must not open a window"
        );
    }
}

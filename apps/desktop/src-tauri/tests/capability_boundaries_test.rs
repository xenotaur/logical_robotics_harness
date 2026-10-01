//! Capability and navigation boundaries of the main window.
//!
//! The main window shows bundled status pages or the owned Serve origin.
//! Neither may invoke app commands, and the window may only navigate to
//! bundled pages and the current backend's exact origin. These tests use the
//! Tauri mock runtime, so no real window opens.

use lrh_console_lib::shell::{self, NavigationPolicy};
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

fn assert_denied(window: &tauri::WebviewWindow<tauri::test::MockRuntime>, origin: &Url) {
    let error = tauri::test::get_ipc_response(window, invoke_request("get_app_info", origin))
        .expect_err("main-window content must not reach app commands");
    assert!(
        format!("{error:?}").contains("not allowed"),
        "expected an ACL denial for {origin}, got {error:?}"
    );
}

fn url(text: &str) -> Url {
    Url::parse(text).unwrap()
}

#[test]
fn bundled_status_page_in_the_main_window_gets_no_app_commands() {
    let app = build_app();
    let initial = shell::status_url("stopped", None);
    let window =
        shell::build_main_window(&app, NavigationPolicy::default(), &initial).expect("main window");

    assert_denied(&window, &shell::bundled_base());
}

#[test]
fn owned_serve_origin_in_the_main_window_gets_no_app_commands() {
    let app = build_app();
    let window = shell::build_main_window(
        &app,
        NavigationPolicy::default(),
        &shell::status_url("stopped", None),
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

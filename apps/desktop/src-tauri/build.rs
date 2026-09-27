fn main() {
    // Declare the app's own commands so they are subject to capability ACLs.
    // Without an app manifest, commands registered via invoke_handler are
    // allowed in every window by default.
    let attributes = tauri_build::Attributes::new()
        .app_manifest(tauri_build::AppManifest::new().commands(&["get_app_info"]));
    tauri_build::try_build(attributes).expect("failed to run tauri-build");
}

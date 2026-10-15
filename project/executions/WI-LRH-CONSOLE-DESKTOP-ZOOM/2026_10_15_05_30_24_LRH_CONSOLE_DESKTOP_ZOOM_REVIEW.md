---
execution_id: 2026_10_15_05_30_24_LRH_CONSOLE_DESKTOP_ZOOM_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-ZOOM:LRH_CONSOLE_DESKTOP_ZOOM_REVIEW)[2026-10-15T05:30:24+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-ZOOM
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/846
commit:
created_at: 2026-10-15T05:30:24+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/846
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers review-response round 1 for PR #846 (`WI-LRH-CONSOLE-DESKTOP-ZOOM`), run as part of `/lrh-land` inside `/lrh-execute`. CI passed 7/7 on the first push. Codex left one thread, and Copilot left none. The owner approved the fix.

# Result

- **Codex P2 (raise the macOS minimum before using page zoom):** valid, and more serious than stated.
  - **Problem:** the app did not set `bundle.macOS.minimumSystemVersion`, so it used Tauri's default of macOS 10.13. In wry 0.57 (`wkwebview/mod.rs:954`), `zoom` calls `setPageZoom:` unconditionally and always returns `Ok(())`, but WKWebView `pageZoom` exists only on macOS 11+. On 10.13–10.15 that would most likely raise an unrecognized-selector exception: a crash when zooming, or at launch with a saved level. Codex suggested only updating state after a successful call, which cannot help, because the call never reports failure.
  - **Fix:**
    - `tauri.conf.json` sets `bundle.macOS.minimumSystemVersion` to `"11.0"`.
    - A test in `capability_boundaries_test.rs` pins the setting.
    - The dogfood how-to notes the requirement.
    - The rebuilt bundle's Info.plist has `LSMinimumSystemVersion = 11.0`.
  - **Impact:** the owner runs macOS 27, and LRH Console is a locally built, unsigned app, so no real users lose support.

# Validation

- `scripts/format --check --diff --desktop`: clean.
- `scripts/lint --desktop`: clean.
- `scripts/test --desktop`: Python 2360 OK; Rust 89, 14 and 23 tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- The bundle's `LSMinimumSystemVersion` is `11.0` (PlistBuddy).

# Follow-up

- Confirm-fixes with a substitute cold review.

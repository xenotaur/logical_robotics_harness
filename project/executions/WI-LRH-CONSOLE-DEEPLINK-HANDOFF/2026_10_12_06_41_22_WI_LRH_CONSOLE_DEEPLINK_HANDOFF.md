---
execution_id: 2026_10_12_06_41_22_WI_LRH_CONSOLE_DEEPLINK_HANDOFF
prompt_id: PROMPT(WI-LRH-CONSOLE-DEEPLINK-HANDOFF:WI_LRH_CONSOLE_DEEPLINK_HANDOFF)[2026-10-12T06:02:37+00:00]
work_item: WI-LRH-CONSOLE-DEEPLINK-HANDOFF
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/833
commit: a4bde3346cf509ef86cbfa6d1ea668471a0faf05
created_at: 2026-10-12T06:41:22+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CONSOLE-DEEPLINK-HANDOFF.md
session_transcript: claude-app:d71d7175-7d16-4509-8b96-cdbaa1e937b5
---

# Summary

Implement WI-LRH-CONSOLE-DEEPLINK-HANDOFF: an allowlisted session deep-link handoff in the LRH Console's Tauri shell, built from the shared route definition.

# Result

Opened the PR on xenotaur/feat/wi-lrh-console-deeplink-handoff. Changed:

- apps/desktop/src-tauri/src/browser.rs: validate_session_link (exact scheme/host/path shape, UUID id, no credentials/port/query/fragment) over routes parsed fail-closed from src/lrh/conversations/session_links.json via include_str! and serde_json; open_session_link with a fixed per-platform opener; new Opened::VendorApp; run refactored into run_opener with unchanged browser error text. No vendor route is written in Rust (a test enforces that). validate_url is unchanged.
- apps/desktop/src-tauri/src/shell.rs: LinkHandoff::offer routes an allowlisted session link to the session opener after is_external_link fails, under the same limiter, recording the result in last; injectable opener so tests never launch an app.
- apps/desktop/src-tauri/tests/capability_boundaries_test.rs: session links widen no window boundary; capability file and CSP asserted unchanged.
- docs/reference/desktop-server-protocol.md: paragraph on the allowlisted handoff.

Not verified end to end: no Console page can render a session link yet, so a real click was not tested. The allowlist (against the shared vectors), the rate limit and the recorded result are covered by unit tests, and a command-construction test asserts the fixed per-platform program (/usr/bin/open on macOS, /usr/bin/xdg-open on other unix; both CI desktop jobs run it) and that the validated URL is its only argument. Launching an application is deliberately not exercised by any test, and the opener command itself was verified by hand earlier with `open` for both routes.

# Validation

Dedicated conda env bound to this worktree (ruff 0.15.12, black 26.3.1; Rust toolchain 1.95.0, tauri-cli 2.12.0). apps/desktop/scripts/run fmt --check, lint and test pass (library 83, capability boundaries 12, supervisor 23); scripts/format --check --diff and scripts/lint clean; scripts/test 2288 tests OK; lrh validate 0 errors and 0 warnings. pyright is not installed in the env (not a gating check). Diff-mode self-review: no blocking findings (record 2026_10_12_06_37_44_WI_LRH_CONSOLE_DEEPLINK_HANDOFF_SELFREVIEW).

# Follow-up

Rendering session links in Console pages (the first thing a click check needs) is a separate, not yet created work item. session_transcript is pending until closeout.

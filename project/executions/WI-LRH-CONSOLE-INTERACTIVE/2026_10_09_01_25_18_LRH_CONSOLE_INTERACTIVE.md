---
execution_id: 2026_10_09_01_25_18_LRH_CONSOLE_INTERACTIVE
prompt_id: PROMPT(WI-LRH-CONSOLE-INTERACTIVE:LRH_CONSOLE_INTERACTIVE)[2026-10-09T00:02:17+00:00]
work_item: WI-LRH-CONSOLE-INTERACTIVE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/801
commit:
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated, with the desktop app passing --interactive\")"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-09T01:25:18+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-INTERACTIVE` through `/lrh-execute`:
the opt-in `lrh serve --interactive` mode with packaged same-origin scripts, which LRH Console
always passes. The owner approved the chain, the run plan, and the desktop default ("Approve as
stated, with the desktop app passing --interactive").

# Result

- **`src/lrh/serve.py`:**
  - `ServeConfig.interactive` and the `--interactive` flag, also accepted with
    `--desktop-protocol` and reported by `--show-config`.
  - `content_security_policy` adds only `script-src 'self'`.
  - `apply_interactive` adds the early theme script at the start of `<head>` and the deferred
    main script before `</head>`.
  - `_write_static` returns 404 for both scripts unless the flag is set, and serves scripts
    with `no-cache`.
  - The desktop factory passes the flag on, and the map page renders in interactive mode.
- **`src/lrh/ux/static/lrh-interactive.js` (new):**
  - the theme switch, hidden when the server pins a theme, with storage always in try/catch;
  - tracing: hover and focus previews, click selection without a reload, the URL and page
    links following the selection, and Escape to close;
  - filters by state that transitively keep unfinished needs visible.

  It never uses `eval`, `innerHTML` or `fetch`.
- **`src/lrh/ux/static/lrh-theme-early.js` (new):** applies a stored theme before first paint,
  marking its choice with `data-lrh-theme-source`, so pinning is still detected.
- **`src/lrh/dependency_maps/render.py`:**
  - in interactive mode, every drawer is pre-rendered hidden, with unique heading IDs;
  - `data-id`, `data-state` and `data-unmet` on cards, rows and list items, and
    `data-source` and `data-item` on lines;
  - CSS for previews, filtered items, filters and hidden drawers.
- **`src/lrh/ux/frame.py`:** a theme slot in the top bar, the script entries, and the switch
  styles.
- **Desktop:** `settings.rs` adds `INTERACTIVE_FLAG` to `launch_config`'s `serve_args`, and
  `shell.rs` adds it on the developer-override path. Tests are updated. `supervisor.rs` was
  unchanged because it already appends `serve_args`.
- **Docs:** the `lrh serve` reference, the desktop server protocol, and the how-to.
- **View:** MAP-OUTLINE-LAYOUT and STATUS-SHAPES are placed in `lrh-console-l1`'s map phase.
- **Tests:** `tests/ux_tests/interactive_script_test.py` (new), plus additions to
  `serve_test.py` and `render_test.py`.

**Pre-push cold review.** Verdict: safe to push. It found no security issues: titles are
escaped, so `</head>` injection is impossible; the main window has no capabilities; and the
script's tracing matches the server's for all 19 cards. Its should-fixes are applied in
`0457a8f7`:

- the early no-flash theme script;
- links that follow a script selection;
- previews that no longer look like selections;
- Alt-click passing through;
- no-cache scripts;
- docs on the per-address theme and preview-only-when-unselected;
- broader no-inline-script coverage, including map pages and the 422 page;
- pinned and system tests, and stricter storage checks.

**Found in passing:** any validation error empties the core project state, so one malformed
view file makes work-item and workbench pages report "not available". This was flagged as a
separate task, and the test writes its broken view only after the other routes are checked.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and
  `scripts/test --desktop` pass: 2132 Python tests, and desktop tests 45, 9 and 23.
- `tests/smoke/desktop_protocol_smoke.py` passes.
- `lrh validate`: 0 errors, 0 warnings.
- Browser pane, on the real view:
  - filters hid Done and kept the needed items;
  - selection showed one drawer and updated the URL;
  - Escape cleared it;
  - the theme switch stored and applied the choice;
  - the pinned dark theme hid the switch and won over a stored Light;
  - no console errors.
- Runtime DOM behavior has no automated test; it was checked by hand.

# Follow-up

- The owner checks it hands-on in this branch's rebuilt LRH Console.
- The invalid-view isolation is handled in the separate task.

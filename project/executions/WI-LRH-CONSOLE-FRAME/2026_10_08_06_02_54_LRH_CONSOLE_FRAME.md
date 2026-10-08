---
execution_id: 2026_10_08_06_02_54_LRH_CONSOLE_FRAME
prompt_id: PROMPT(WI-LRH-CONSOLE-FRAME:LRH_CONSOLE_FRAME)[2026-10-08T02:24:01+00:00]
work_item: WI-LRH-CONSOLE-FRAME
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/792
commit: bf4f8f248e15e2319d6adce9c777c3f54db105f3
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated, including the Lucide download\")"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-08T06:02:54+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-FRAME` through `/lrh-execute`: the
script-free LRH Console app frame on every Serve page. The owner approved the chain, the run
plan, and the pinned Lucide download in this session.

# Result

- **`src/lrh/ux/frame.py` (new):** `apply_frame` wraps every HTML response.
  - Top bar: the LRH icon links home to `/meta`; then the page name and scope, the render
    time, refresh, the gear to `/settings`, and a search slot.
  - Sidebar: a Meta-registry scope switcher and the current scope's views. A CSS checkbox
    collapses it to a labelled icon rail; it is a rail by default when narrow, with a flyout
    switcher there.
  - Drawer: opened by `?item=<id>`, with a full-page link. It overlays the page.
  - Also: a skip link and exactly one `<main>` landmark per page.
  - The module also defines `STATIC_FILES`, `read_static`, inline Lucide icons and
    `FRAME_STYLES`.
- **Assets (`src/lrh/ux/static/`):**
  - the LRH icon at 64 and 128 px, from the repo source;
  - `fonts/montserrat-latin.woff2`, a Latin subset of the owner's installed Montserrat
    variable font, version 8.000;
  - `fonts/OFL-montserrat.txt`: the font's own copyright line and the full OFL 1.1 text, from
    a local Inconsolata package;
  - 12 Lucide SVGs and `LICENSE-lucide.txt`, downloaded from `lucide-icons/lucide` at tag
    `1.52.0` with the owner's approval (about 6 KB).
  - `pyproject.toml` package data covers all of them.
- **`src/lrh/serve.py`:**
  - The frame is applied in `_write_text`.
  - `_frame_projects` is best-effort: resolution, registry, `OSError` and `ValueError`
    failures give an empty list.
  - `/static/<asset>` serves the allowlist only, with GET and HEAD and `max-age=3600`.
  - `/settings` is a display and about page.
  - The CSP adds only `img-src 'self'` and `font-src 'self'`.
  - The viewport meta tag is added in `_base_styles`.
- **`apps/desktop/src-tauri/src/shell.rs`:** `NavigationPolicy::is_settings_request` and
  `SETTINGS_PAGE_PATH`. The main window's `on_navigation` opens native Settings through
  `run_on_main_thread`, rate-limited, and cancels the load. The capability boundary is
  unchanged: `main-window.json` is untouched and the existing tests pass, so
  `capability_boundaries_test.rs` needed no change.
- **Tests:**
  - `tests/ux_tests/frame_test.py` (new, 15 tests).
  - `serve_test.py` additions: frame on index, detail and workbench pages; one main
    landmark; the viewport tag; the exact CSP; the static allowlist and 404s; `/settings`;
    the drawer; a broken registry; frame plus pinned theme.
  - A `shell.rs` unit test covers the gear-request matcher.
- **Docs:** the `lrh serve` reference and the dogfood how-to.

**Browser checks** found and fixed three layout problems before the push:

- long registry URLs pushed the page sideways inside the narrower main area;
- the drawer squeezed the page, so it became an overlay;
- pages had no viewport meta tag, so phones laid them out at 980 px.

**Pre-push cold review.** It found one must-fix (nested `<main>` landmarks), six should-fix
items and several nits. Applied in `90b6c16b`: the main-landmark fix, the skip link and drawer
order, title escaping, the broader registry error catch, heading fonts, more tests, the rail
flyout, tooltip anchoring, the current-view marker, scope-name truncation, the home-link name,
and static caching.

**Found in passing, not changed:** `render_design_detail_page` drops the connection when no
Meta workspace resolves, an uncaught `MetaWorkspaceResolutionError` already on `main`. It was
flagged as a separate task.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and
  `scripts/test --desktop` pass: 1998 Python tests, and desktop tests 45, 9 and 23.
- `lrh validate`: 0 errors, 0 warnings.
- A wheel built with `python -m build` contains every frame asset.
- Browser pane: light and dark, the scope switcher, keyboard rail collapse, tooltips, the
  drawer, Montserrat and the icon loading with no console errors, and no horizontal scroll on
  seven pages at desktop width and at 375 px.

# Follow-up

- The owner checks the gear in LRH Console, which should open the Settings window.
- `WI-LRH-CONSOLE-MAP-STATIC` fills the drawer, and `WI-LRH-CONSOLE-STATUSBOARD` restyles the
  home view.

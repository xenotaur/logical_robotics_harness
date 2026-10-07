---
id: "WI-LRH-CONSOLE-FRAME"
title: "Add the LRH Console app frame to Serve's pages"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on:
- "WI-LRH-CONSOLE-TOKENS"
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "Every Serve page shows the top bar, sidebar, and main area, in the app and in a browser, in both themes."
- "The LRH icon always links to the statusboard home view."
- "The sidebar shows the scope switcher and that scope's views, collapses to a labelled icon rail without scripts, and the frame works at phone width without horizontal page scrolling."
- "The CSP allows only same-origin images and fonts beyond the existing inline styles, and still allows no scripts. A test asserts the header."
- "In the desktop app the gear opens Settings with no new main-window permission (covered by the capability-boundary tests); in a browser it opens the display and about page."
- "Montserrat and the icons load locally, and the Montserrat OFL license ships with them."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "src/lrh/ux/ (frame template and static assets)"
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/src-tauri/tests/capability_boundaries_test.rs"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# LRH Console app frame

## Summary

Build the frame the owner approved from the Revision 2 mock (Q9) into Serve's pages, so it is shared by the desktop app and any browser. It has a top bar, a scoped sidebar that collapses to an icon rail, and a static detail drawer. It also bundles Montserrat and an icon subset locally.

## Problem / Context

Owner requests R1 (a top bar with the logo, page name, and settings gear) and R2 (a collapsible left sidebar) come from the L0 dogfood (`project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md:169`). Revision 2 of the visual-language proposal settles the frame:

- the LRH v8 icon returns to the default home view (the statusboard);
- the sidebar is scoped first (All projects or one project), then lists that scope's views;
- details open in a drawer, with a full-page link;
- the standard macOS title bar stays *(recommended)*.

Serve's content security policy (`default-src 'none'; style-src 'unsafe-inline'`, `src/lrh/serve.py:3034-3036`) blocks images and fonts as well as scripts. The icon and bundled fonts therefore need a narrow, same-origin extension. The main desktop window has no app-command permissions (`apps/desktop/src-tauri/capabilities/main-window.json`), so the gear cannot call Settings directly.

### Duplication search

In-repo: Serve pages use a horizontal control spine (`.lrh-control-spine` in `src/lrh/serve.py`), and no frame or sidebar exists. Recommendation: proceed.

## Scope

- A shared page frame for every Serve page.
- Static behavior with no scripts: a CSS-only rail collapse, and the drawer opened by a selected-item URL.
- Local assets: the LRH icon, Montserrat (SIL OFL, with its license), and a Lucide or Phosphor SVG subset.
- A narrow CSP extension for same-origin images and fonts only.
- The gear's behavior in the desktop app and in a browser.

## Required Changes

1. Add a frame template used by every Serve page. **Top bar:** the LRH icon as a link to the statusboard, the page name and scope, then snapshot freshness with refresh, and the gear. Leave a slot for search, which needs scripts or a CSP form-action change and is not part of this item. **Sidebar:** the scope switcher, fed from the Meta registry, then the current scope's views. **Main area.** **Drawer slot:** rendered when a `?item=<id>` parameter is present, with a full-page link.
2. Make the sidebar collapse to an icon rail with CSS only. Give every icon an accessible name that also shows on hover and focus. Collapse to the rail automatically on narrow screens, and turn the drawer into the full page there.
3. Serve the LRH icon, Montserrat (woff2 plus its OFL license file), and the icon SVGs as packaged same-origin static assets. Extend the CSP with `img-src 'self'` and `font-src 'self'` only. Scripts stay blocked.
4. Gear in the desktop app: link to a reserved in-origin path. The shell's navigation policy intercepts it and opens the native Settings window, without granting the main window any permission. In a browser, the same path serves a read-only display and about page that explains `--theme`, so there is one URL and no extra route.
5. Apply the type roles: Montserrat for titles and large numbers, the system font for body text, monospace for IDs.
6. Move existing pages into the frame without changing their content.

## Non-Goals

- No dependency map, statusboard bands, or drawer content (`WI-LRH-CONSOLE-MAP-STATIC`, `WI-LRH-CONSOLE-STATUSBOARD`).
- No scripts; interaction comes with `WI-LRH-CONSOLE-INTERACTIVE`.
- No overlay or merged macOS title bar.

## Acceptance Criteria

- Every Serve page shows the top bar, sidebar, and main area, in the app and in a browser, in both themes.
- The LRH icon always links to the statusboard home view.
- The sidebar shows the scope switcher and that scope's views, collapses to a labelled icon rail without scripts, and the frame works at phone width without horizontal page scrolling.
- The CSP allows only same-origin images and fonts beyond the existing inline styles, and still allows no scripts. A test asserts the header.
- In the desktop app the gear opens Settings with no new main-window permission (covered by the capability-boundary tests); in a browser it opens the display and about page.
- Montserrat and the icons load locally, and the Montserrat OFL license ships with them.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Check the frame by hand in the app and in Chrome, at desktop and narrow widths, with the keyboard only.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-TOKENS`.
- `WI-LRH-CONSOLE-MAP-STATIC` and `WI-LRH-CONSOLE-STATUSBOARD` depend on it.

## Risk Notes

- Loosening the CSP is a security change. Keep it to `'self'` images and fonts and test the exact header.
- Intercepting a reserved path must not let page content trigger other native actions. Allow exactly one path, and rate-limit it like the existing link handoff.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

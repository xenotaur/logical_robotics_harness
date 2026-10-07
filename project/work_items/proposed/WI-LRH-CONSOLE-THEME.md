---
id: "WI-LRH-CONSOLE-THEME"
title: "Make LRH Console follow the system theme by default, with --theme and an Appearance setting"
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
- "With no flag or setting, every Serve page and bundled app page follows the system appearance."
- "`lrh serve --theme dark` and `--theme light` force that theme on every page, and an invalid value is rejected."
- "The desktop Appearance setting persists, passes the matching `--theme` to the server, and applies to the app's own pages."
- "Tests cover the flag, the default, configuration serialization with an older file that has no `appearance` field, and the launch arguments."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "apps/desktop/src-tauri/src/settings.rs"
- "apps/desktop/src-tauri/src/supervisor.rs"
- "apps/desktop/ui/settings.html"
- "apps/desktop/ui/settings.js"
- "apps/desktop/src-tauri/tests/supervisor_test.rs"
- "tests/cli_tests/serve_test.py"
- "docs/reference/cli/serve.md"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# LRH Console theme selection

## Summary

Ship the Revision 2 theme plan (Q5). Every LRH Console surface defaults to the system appearance. Browser users can choose with `lrh serve --theme light|dark|system`, and desktop users with an Appearance setting.

## Problem / Context

Serve hard-codes `data-theme="light"` on its pages (`src/lrh/serve.py:165`, `444`, `494`, `583`, `1447`, `1500`), so its dark tokens are never used. The desktop app's bundled pages already follow `prefers-color-scheme`. So on a Mac in dark mode, the app's own pages are dark while Serve's content is light. The owner decided on three choices, Light, Dark, and System, defaulting to System. Because the static version has no script to remember a choice, the explicit choice comes from Settings in the app and from a flag in the browser.

### Duplication search

In-repo: no theme flag or setting exists. Recommendation: proceed.

## Scope

- The System default for every Serve page.
- The `lrh serve --theme` flag.
- An Appearance setting in desktop Settings, passed to the server it launches, and applied to the app's own bundled pages.

## Required Changes

1. Remove the hard-coded `data-theme` from Serve's page templates, so the token file's `prefers-color-scheme` rules apply.
2. Add `lrh serve --theme light|dark|system`, defaulting to `system`. An explicit value sets `data-theme` on each page's root element. Reject other values with a clear error.
3. Add an `appearance` field (light, dark, or system; default system) to the desktop configuration (`apps/desktop/src-tauri/src/settings.rs`). Give it a three-way control in Settings, apply it to the app's bundled pages, and pass `--theme` when the supervisor launches the server.
4. Apply an Appearance change the same way a program or workspace change applies today: at the next server restart, offering **Restart server now**. Add `appearance` to `settings::needs_restart`, which today compares only the launch and workspace fields. Bundled pages update immediately.
5. Document the flag and the setting in `docs/how-to/lrh-console-local-dogfood.md` and the `lrh serve` reference.

## Non-Goals

- No in-page theme switch; that arrives with `WI-LRH-CONSOLE-INTERACTIVE`.
- No new themes beyond light and dark.

## Acceptance Criteria

- With no flag or setting, every Serve page and bundled app page follows the system appearance.
- `lrh serve --theme dark` and `--theme light` force that theme on every page, and an invalid value is rejected.
- The desktop Appearance setting persists, passes the matching `--theme` to the server, and applies to the app's own pages.
- Tests cover the flag, the default, configuration serialization with an older file that has no `appearance` field, and the launch arguments.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Check Light, Dark, and System by hand on a Mac, in the app and in Chrome.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-TOKENS`.
- `WI-LRH-CONSOLE-INTERACTIVE` later adds the in-page switch.

## Risk Notes

- A configuration field added without a serde default would break older config files. Default it to System and test loading a file that has no `appearance` field.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

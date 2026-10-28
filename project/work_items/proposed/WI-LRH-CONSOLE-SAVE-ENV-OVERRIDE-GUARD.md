---
id: "WI-LRH-CONSOLE-SAVE-ENV-OVERRIDE-GUARD"
title: "Make LRH Console Settings non-destructive under a developer override"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-PROFILES"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-PROFILES"
related_design:
- "project/design/proposals/proposed/lrh-profiles/00_proposal.md"
depends_on: []
blocked_by: []
expected_actions:
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
- "Under an active LRH_CONSOLE_* override, Settings opens pre-filled with the saved configuration file's values (when a valid one exists) instead of an empty form."
- "Under an override, Settings shows a visible warning that the displayed values are the saved ones, this session is not using them, and Save updates the saved file only."
- "Save behavior is unchanged: it still writes the file, applies the browser choice and appearance now, and never reconfigures the running session."
- "An unreadable or invalid saved file under an override shows its problem and does not crash; Save is still possible."
- "Tests cover get_settings and save_settings in Environment and File modes. Format, lint, desktop tests, and lrh validate pass."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "apps/desktop/src-tauri/src/shell.rs"
- "apps/desktop/ui/settings.js"
- "apps/desktop/ui/settings.html"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# Make LRH Console Settings non-destructive under a developer override

## Summary

When LRH Console runs under an `LRH_CONSOLE_*` developer override, Settings
opens with an empty form even if a real saved configuration exists. A Save then
replaces the user's saved settings with whatever was typed. Show the saved
values in the form and warn that this session is not using them, so a Save is
a deliberate edit of the saved file and never a blind overwrite.

## Problem / Context

The `LRH_CONSOLE_*` variables (`apps/desktop/src-tauri/src/shell.rs:37-47`)
let a developer run the app against a checkout without touching the saved
Settings; `apps/desktop/scripts/run launch` is the usual route. They win over
the saved file for that session.

How Save behaves under an override came about in steps:

- `dd675175` (2026-10-01): `save_settings` always wrote the file and also
  switched the source to the file and reconfigured the supervisor, which
  dropped the override mid-session.
- `d52bd183` (2026-10-01, pre-push self-review fix): "Saving while the
  LRH_CONSOLE_* override is active only writes the file." Save no longer
  rewires the running session, but the file write stayed. No design note
  explains why a developer would want that write.
- PR #776 (`43779d1c`, 2026-10-05): a wording fix only. It made the Settings
  text say which saved changes apply now (the browser choice and appearance)
  and which wait for a later session. It did not decide whether to write.

The remaining hazard: in override mode the startup configuration is `None`
(`shell.rs` `StartupConfig` for `ConfigSource::Environment`), so `get_settings`
returns an empty form even when a saved `config.json` exists
(`shell.rs:1552-1562`). `save_settings` writes the file before it checks for
the override (`shell.rs:1578` versus `1582`). Validation requires real paths
(`settings.rs:101-149`), so a Save needs deliberate input, but a developer who
types their checkout's paths replaces the installed app's saved settings. The
damage is small and recoverable: one JSON file of about five fields.

Options considered (PROP-LRH-PROFILES Decision 8): refuse to save in override
mode (A), show the saved values and warn (B, chosen), or drop this item and
rely on profiles (C). B keeps documented behavior and removes the trap.
Once Console profiles land, the right behavior should be revisited (see the
design backlog entry "LRH Console: revisit Save-in-override once profiles land").

### Duplication search

- In-repo: no existing implementation or work item. Related, resolved:
  `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` (wording only).
- Sibling repos: none identified. External libraries: none identified.
- Recommendation: proceed.

### Demand search

- Work items: none found. Proposals: PROP-LRH-PROFILES Decision 8 (reworded
  alongside this item). Backlog: the follow-up entry added with this item.
- Recommendation: no action.

## Scope

- Settings shows the saved file's values under an override, with a warning.
- `get_settings` reads the saved file in override mode and tolerates a missing,
  unreadable, or invalid file.
- Save semantics are unchanged.

## Required Changes

1. Have `get_settings` return the saved configuration in override mode: load it
   through the existing `ConfigStore`, and report a missing file as empty and an
   unreadable or invalid file as a problem, without crashing.
2. Do not let the preloaded values drive the running override session. The
   supervisor configuration, `ConfigSource::Environment`, and the
   `needs_restart` comparison must behave as they do today.
3. Update the `SOURCES.environment` text in `apps/desktop/ui/settings.js` and add
   a visible warning in `settings.html` and `settings.js`: the values shown are
   the saved ones, this session is not using them, and Save updates the saved
   file only.
4. Keep `save_settings` behavior: validate, write the file, apply the browser
   choice and appearance now, and return `env_override_active: true`.
5. Add Rust tests in the existing mock-runtime tier for `get_settings` and
   `save_settings` in Environment mode (saved file present, absent, and invalid)
   and in File mode.
6. Update `docs/how-to/lrh-console-local-dogfood.md` to describe the behavior.

## Non-Goals

- No profile functionality (later work items in WS-LRH-PROFILES).
- No refusal to save under an override, and no change to which settings apply
  immediately.

## Acceptance Criteria

- Under an override, Settings opens pre-filled with the saved values when a
  valid saved file exists.
- A visible warning says the values are the saved ones, the session is not
  using them, and Save updates the saved file only.
- Save still writes the file, applies the browser choice and appearance now, and
  never reconfigures the running session.
- A missing, unreadable, or invalid saved file under an override is handled
  without a crash, and Save is still possible.
- Tests cover Environment and File modes; format, lint, desktop tests, and
  `lrh validate` pass.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- A manual Mac check on a branch build launched with `apps/desktop/scripts/run launch`:
  with a saved configuration present, open Settings and confirm the pre-filled
  values and the warning; Save and confirm the file changes but the session
  keeps using the override.

## Risk Notes

- Preloading the saved file must not change what the running session uses; the
  tests in Required Changes item 5 are the guard.
- The owner cannot build PR branches, so the branch's LRH Console app must be
  bundled and launched before asking for the Mac check.

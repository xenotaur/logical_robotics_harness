---
id: "WI-LRH-CONSOLE-INTERACTIVE"
title: "Add the opt-in lrh serve --interactive mode with packaged scripts"
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
- "WI-LRH-CONSOLE-THEME"
- "WI-LRH-CONSOLE-MAP-STATIC"
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
- "Without the flag, Serve's CSP and pages are unchanged and fully usable."
- "With `--interactive`, the CSP adds only `script-src 'self'`, and tests assert the exact headers in both modes."
- "Tracing, filters, and the theme switch work with the flag and degrade to the static behavior without it."
- "Under an explicit `--theme light` or `--theme dark` the in-page switch is hidden and the forced theme always applies, whatever the browser stored; under `system` the switch is shown."
- "No inline script or `eval` appears in any served page, and a test enforces it."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "src/lrh/ux/static/ (scripts)"
- "apps/desktop/src-tauri/src/supervisor.rs"
- "apps/desktop/src-tauri/tests/supervisor_test.rs"
- "tests/cli_tests/serve_test.py"
- "docs/reference/cli/serve.md"
- "docs/how-to/lrh-console-local-dogfood.md"
---

# Interactive mode

## Summary

Add the separate opt-in flag `lrh serve --interactive` (Revision 2, Q8). It allows only packaged same-origin scripts, which add client-side tracing, filtering, and the in-page theme switch on top of the static pages. The static version keeps working unchanged without the flag.

## Problem / Context

Serve's script-free policy was chosen to keep the first version safe, not as a permanent rule. The owner decided that static must always work and that interaction comes from a separate `--interactive` flag. The proposal recommends that the desktop app pass the flag too, and that the mode allow only `script-src 'self'`, with no inline script and no `eval`. Web assets ship prebuilt with Python, so users need no Node (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:138-139`).

### Duplication search

In-repo: no scripts are served today; the CSP is `default-src 'none'` (`src/lrh/serve.py:3034-3036`). Recommendation: proceed.

## Scope

- The `--interactive` flag and its mode-specific CSP.
- Packaged plain-JavaScript assets with no build step.
- Client-side tracing, filters, and an in-page theme switch, layered over the static markup.
- The desktop app passing the flag, as recommended in the proposal; confirm it with the owner in the PR.

## Required Changes

1. Add `lrh serve --interactive`. Only with it, extend the CSP with `script-src 'self'`; never allow `unsafe-inline` or `unsafe-eval`.
2. Serve packaged JavaScript as same-origin static assets with the correct content type. Use no inline script and no build step.
3. Use the scripts to add selection and tracing without page reloads, filters that never hide blockers, and the in-page Light, Dark, and System switch (stored per browser). An explicit server theme wins *(recommended)*: under `--theme light` or `--theme dark` the switch is hidden, and it appears only under `system`, which is also what the desktop app passes when Appearance is System. Every behavior degrades to the static version when scripts are off.
4. Have the desktop app pass `--interactive` when it launches the server, as recommended in the proposal, unless the owner decides otherwise in the PR.
5. Document the flag in the `lrh serve` reference and the desktop how-to.

## Non-Goals

- No framework or bundler without a separate design decision.
- No mutation; Serve stays read-only.
- No client-side search or keyboard shortcuts; they need a separate owner decision.

## Acceptance Criteria

- Without the flag, Serve's CSP and pages are unchanged and fully usable.
- With `--interactive`, the CSP adds only `script-src 'self'`, and tests assert the exact headers in both modes.
- Tracing, filters, and the theme switch work with the flag and degrade to the static behavior without it.
- Under an explicit `--theme light` or `--theme dark` the in-page switch is hidden and the forced theme always applies, whatever the browser stored; under `system` the switch is shown.
- No inline script or `eval` appears in any served page, and a test enforces it.

## Validation

- `scripts/format --check --diff --desktop`
- `scripts/lint --desktop`
- `scripts/test --desktop`
- `lrh validate`
- Check the interactive map by hand in the app and in Chrome, then repeat with the flag off.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-THEME` and `WI-LRH-CONSOLE-MAP-STATIC`.

## Risk Notes

- Any script widens the attack surface. Keep it same-origin, test the headers, and keep the main desktop window's capabilities empty.
- Client and server rendering can drift. The scripts must consume the same layout output as the static renderer.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

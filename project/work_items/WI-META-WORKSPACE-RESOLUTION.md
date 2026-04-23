---
id: WI-META-WORKSPACE-RESOLUTION
title: Meta workspace resolution and visibility contract
type: deliverable
status: in_progress
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on:
  - WI-META-CLI-MVP
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - run_cli
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - shared workspace-context resolution is implemented and used consistently by `lrh meta init`, `lrh meta register`, and `lrh meta list`
  - precedence is implemented as: explicit CLI flags → `LRH_CONFIG` → `LRH_WORKSPACE` → local auto-discovery → global auto-discovery → built-in defaults
  - global workspace defaults use XDG-style config/state/cache separation
  - local workspace mode remains explicitly supported via `.lrh/config.toml` plus sibling `projects/` and `private/`
  - `lrh meta init` prompts are TTY-aware and bypassable via `--yes`
  - active workspace/config resolution is visible and inspectable in user-facing command behavior
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - test_module
  - cli_output
---

## Summary

Define and then implement the shared workspace-resolution subsystem used across Meta CLI commands, with explicit precedence, XDG-style global defaults, explicit local workspace support, and inspectable behavior.

## Scope

- design/planning alignment across design/spec/roadmap/work-item artifacts
- shared workspace-context resolution helper for Meta CLI commands
- precedence-aware source handling (flags/env/discovery/defaults)
- TTY-aware prompting policy for `meta init` with `--yes` bypass
- output/help behavior that makes active workspace/config resolution visible

## Non-goals

- no expansion into orchestration flows
- no deep multi-user/server behavior
- no broad redesign of non-meta LRH runtime concerns

## Traceability

- Design: `project/design/design.md` (Workspace / Meta-Control Layer)
- Spec: `project/design/meta_control_plane_mvp_spec.md` (workspace-context resolution, global/local model, prompting)
- Roadmap: `project/roadmap/phase_02_runtime_and_workspace.md` (Near-Term Slice: Meta CLI MVP)
- Decision log: `project/memory/decision_log.md` (2026-04-22 workspace resolution adoption)

## Sequencing Notes

- This item separates workspace-resolution architecture from the already-landed baseline command slice in `WI-META-CLI-MVP`.
- Implementation should proceed after this design/planning alignment lands, so command behavior remains predictable and explainable.

## Progress Notes

- 2026-04-22: Implemented a shared `MetaWorkspace` resolution layer with documented precedence (flags → `LRH_CONFIG` → `LRH_WORKSPACE` → local discovery → global discovery), added minimal workspace config parsing for mode/path overrides, and wired `lrh meta register` / `lrh meta list` to the resolved workspace context.
- 2026-04-22: Added focused tests for precedence behavior, nested local discovery, XDG global defaults, command integration outside workspace roots, and explicit resolution-failure messaging.
- 2026-04-22: Updated Meta CLI UX so `lrh meta init` defaults to global initialization, added explicit `--mode {global,local}` on `meta init`, strengthened `meta`/`meta init` help text for workspace resolution + XDG defaults, and added `lrh help meta` / `lrh help meta init` aliases.

---
resolution: null
blocked_reason: null
blocked: false
id: WI-META-CLI-MVP
title: Meta CLI MVP: init / register / list
type: deliverable
status: active
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - run_cli
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - `lrh meta init` creates the expected workspace directory structure
  - `lrh meta register` creates a valid project record with a unique project_id
  - duplicate project registration is detected, with optional override via `--force`
  - `lrh meta list` displays registered projects clearly
  - registration and listing work for both LRH repos and repos without LRH `project/` directories
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - test_module
  - cli_output
---

## Summary

Implement the minimal meta-control-plane CLI slice for managing a workspace-level registry of projects.

## Scope

- `lrh meta init`
- `lrh meta register`
- `lrh meta list`
- validation/testing across real repositories

## Key Design Decisions

- `project_id` is stable and defines registry identity
- locators (`repo`, `project_dir`) are mutable
- labels (`display_name`, `short_name`) are mutable
- projects without LRH `project/` directories are supported
- `setup_state` is explicit (for example: `not_set_up`, `lrh_project_present`)

## Non-goals

- no web UI
- no agent orchestration
- no multi-repo automation
- no advanced inspection or editing commands
- no full shared workspace-context resolver in this item (tracked separately)

## Acceptance Criteria

- `meta init` creates expected directory structure
- `meta register` creates a valid project record with unique ID
- duplicate detection works (with optional `--force`)
- `meta list` displays registered projects clearly
- system works for both LRH and non-LRH repos

## Notes

- the workspace registry is authoritative only for dashboard catalog records
- each repository-local `project/` directory remains authoritative for project state


## Traceability

- Roadmap: `project/roadmap/phase_02_runtime_and_workspace.md` (Near-Term Slice: Meta CLI MVP)
- Spec: `project/design/meta_control_plane_mvp_spec.md` (Meta Control Plane MVP, Phase 1 executable slice)
- Follow-on work item: `project/work_items/active/WI-META-WORKSPACE-RESOLUTION.md` (shared workspace-context resolution and visibility behavior)


## Progress Notes

- 2026-04-21: Implemented the first executable slice, `lrh meta init`, including workspace scaffold generation, safety checks, and tests.
- 2026-04-22: Implemented `lrh meta list` as the first read path over `projects/*/project.toml` records with explicit field rendering and malformed-record failure behavior.
- Remaining scope in this work item: `lrh meta register`.
- 2026-04-22 (audit): Verified against `README.md`, `project/design/meta_control_plane_mvp_spec.md`, and Phase 2 roadmap/work-item acceptance that `lrh meta register` is still not implemented end-to-end. Current code includes `meta init` and `meta list` CLI wiring/runtime/tests only; missing pieces are register CLI exposure/dispatch, registration runtime/write path, stable `project_id` generation, duplicate handling (`--force`), setup-state detection, and register-focused tests.
- 2026-04-22: Implemented `lrh meta register` end-to-end (CLI exposure, runtime write path, stable `project_id`, duplicate detection with `--force`, setup-state detection, and focused tests) while keeping `meta inspect`/`meta deregister` as explicit follow-on commands outside this slice.
- 2026-04-22: Added explicit follow-on planning for shared workspace-context resolution (precedence order, XDG-style global defaults, local workspace support, and resolution visibility) before additional Meta CLI expansion.
- 2026-04-23: Landed deterministic Phase 1 metadata inference in `lrh meta register` so URL/path locators produce better default `directory_name`/`short_name`/`display_name` and inferred `project_dir` for GitHub tree URLs (while keeping explicit overrides authoritative and remaining fully offline/no-network).
- 2026-04-23: Fixed a `meta register` regression where GitHub tree URLs ending in `/project` could still collapse registration naming to `project`; repo slug is now preserved as naming identity while `project_dir` remains path identity, avoiding cross-repo collisions in `projects/<directory_name>/`.
- 2026-04-23: Refined Meta workspace/runtime handling to the three-mode model (`hybrid` default, `local`, `global`), updated `lrh meta init` hybrid positional catalog-root behavior, and normalized persisted workspace paths to absolute values while preserving `register`/`list` behavior through shared resolution.
- 2026-04-23: Refined `lrh meta where` as the primary three-mode workspace diagnostics surface, including explicit mode/source/path reporting and visibility into catalog (shareable) vs runtime private path scopes across hybrid/local/global modes.

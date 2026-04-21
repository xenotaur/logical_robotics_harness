---
id: WI-META-CLI-MVP
title: Meta CLI MVP: init / register / list
type: deliverable
status: proposed
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

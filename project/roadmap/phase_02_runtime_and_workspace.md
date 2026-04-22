---
id: ROADMAP-PHASE-02
title: Runtime and Workspace
status: proposed
parent: ROADMAP-CORE
order: 2
success_criteria:
  - workspace adapter base exists
  - LRH can target an external repo path
  - CLI can show goal, roadmap, focus, and work items
  - at least one sample project repo works end-to-end
---

# Phase 2 — Runtime and Workspace

This phase turns LRH from a document parser into a project-facing tool.

## Deliverables

- workspace adapter base class
- workspace discovery rules
- CLI entrypoints
- example project fixture(s)
- repo-local configuration conventions if needed

### Near-Term Slice: Meta CLI MVP

- implement `lrh meta init`
- implement `lrh meta register`
- implement `lrh meta list`
- test against real repositories (including repos with and without LRH `project/` directories)

Purpose:
- establish a workspace-level project registry
- validate a stable `project_id` plus mutable locator model (`repo`, `project_dir`)
- validate mutable labels (`display_name`, `short_name`)
- support repositories with and without LRH `project/` directories
- track explicit setup state (`not_set_up`, `lrh_project_present`)

Traceability:
- work item: `project/work_items/WI-META-CLI-MVP.md`
- spec alignment: Meta Control Plane MVP, Phase 1 (`init` / `register` / `list`)

Progress update (2026-04-21):
- `lrh meta init` implemented as the first executable slice.
- `lrh meta register` and `lrh meta list` remain in scope for the same MVP work item.

## Risks

- accidentally assuming all projects look like LRH itself
- over-coupling path discovery to one repo structure

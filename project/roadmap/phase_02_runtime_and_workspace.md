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

- align on workspace-context resolution design before further Meta CLI expansion
- implement shared workspace-resolution support used by `lrh meta init`, `lrh meta register`, and `lrh meta list`
- keep command behavior explicit about active workspace/config selection
- test against real repositories (including repos with and without LRH `project/` directories)

Purpose:
- establish a workspace-level project registry
- establish predictable, inspectable workspace resolution for meta commands
- validate a stable `project_id` plus mutable locator model (`repo`, `project_dir`)
- validate mutable labels (`display_name`, `short_name`)
- support repositories with and without LRH `project/` directories
- track explicit setup state (`not_set_up`, `lrh_project_present`)

Traceability:
- work item: `project/work_items/active/WI-META-CLI-MVP.md`
- work item: `project/work_items/active/WI-META-WORKSPACE-RESOLUTION.md`
- spec alignment: Meta Control Plane MVP, Phase 1 (`init` / `register` / `list`)

Progress update (2026-04-22):
- `lrh meta init` implemented as the first executable slice.
- `lrh meta list` implemented as the first explicit read path over registry records.
- `lrh meta register` implemented as the registry write path with stable `project_id`, duplicate detection, and setup-state capture.
- 2026-04-23: Landed hybrid/local/global runtime workspace resolution across `meta init`/`register`/`list`/`where`, including hybrid default init behavior, positional hybrid catalog root semantics, and normalized absolute path persistence in workspace configs.

### Near-Term Slice: Assist Packaging and Installability

Order of execution:

1. Preserve runtime assist templates in package-owned paths (`src/lrh/assist/templates/`).
2. Preserve template loading via package resources so installed-package usage does not depend on source-tree-relative paths.
3. Maintain packaging/build/install hardening and smoke checks for installed `lrh request` / `lrh snapshot` behavior.
4. Keep `lrh survey` canonical on package code (`src/lrh/assist/sourcetree_surveyor.py`).
5. Expand `sourcetree_surveyor` capabilities only as a separate follow-on item.

Rationale:

- Templates required at runtime should ship as package data.
- Installed-package behavior must be validated before wider collaborator adoption.
- Keeping canonical package ownership separate from capability growth keeps PRs small and reviewable.

Traceability:

- `project/work_items/proposed/WI-ASSIST-TEMPLATES-PACKAGING.md`
- `project/work_items/proposed/WI-ASSIST-INSTALLABILITY-HARDENING.md`
- `project/work_items/proposed/WI-ASSIST-SOURCETREE-SURVEYOR-EXPANSION.md`

## Risks

- accidentally assuming all projects look like LRH itself
- over-coupling path discovery to one repo structure

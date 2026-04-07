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

## Risks

- accidentally assuming all projects look like LRH itself
- over-coupling path discovery to one repo structure

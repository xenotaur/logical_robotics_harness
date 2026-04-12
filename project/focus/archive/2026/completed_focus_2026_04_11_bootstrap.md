---
id: FOCUS-BOOTSTRAP
title: Bootstrap the control plane and validation path
status: active
owner: anthony
related_roadmap:
  - ROADMAP-PHASE-01
start_date: 2026-04-03
review_date: 2026-04-17
success_criteria:
  - project directory schema is drafted
  - core model classes are defined
  - parser/loader/resolver skeleton exists
  - validation CLI can run on LRH's own project directory
active_contributors:
  - anthony
  - bootstrap-agent
priority: high
---

# Current Focus

The immediate priority is to make LRH able to understand and validate its own project directory.

## Why this is active now

Before LRH can orchestrate other repositories, it should be able to load and reason about its own
control plane. Self-hosting at the control-model level is the first meaningful milestone.

## Priorities

1. Define the repository and project schema clearly.
2. Implement models and loaders.
3. Validate the LRH project directory with LRH itself.
4. Keep this slice narrow and testable.

## Not Now

- deep agent integration
- complex workspace automation
- multiple providers
- rich UI

## Exit Criteria

A command like `lrh validate` should be able to load the LRH repository's own `project/` directory
and report a coherent result.

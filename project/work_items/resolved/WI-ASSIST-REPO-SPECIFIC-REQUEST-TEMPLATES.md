---
resolution: Resolved by package-owned request template override routing, fallback behavior, diagnostics, tests, and assist documentation; semantic audit evidence is recorded in project/evidence/EV-0010.md.
blocked_reason: null
blocked: false
id: WI-ASSIST-REPO-SPECIFIC-REQUEST-TEMPLATES
title: Support repository-specific assist request template behavior
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
depends_on: []
blocked_by: []
---

## Summary

Define a supported mechanism for repository-specific request template behavior so shared templates stay reusable across arbitrary target repositories while allowing opt-in project-local canonical command enforcement.

## Motivation

Review comments on PR `xenotaur/logical_robotics_harness#158` identified a reusability gap: the `review_response` prompt is rendered for arbitrary target PR repositories, but hard-coded LRH command expectations can fail on non-LRH repositories.

Referenced comments:
- https://github.com/xenotaur/logical_robotics_harness/pull/158#discussion_r3179099372
- https://github.com/xenotaur/logical_robotics_harness/pull/158#discussion_r3179101179

## Proposed Actions

- Design a template-variable or template-selection strategy that can express:
  - repository-agnostic canonical command discovery guidance
  - repository-specific command defaults when explicitly configured
- Define where repository-specific overrides live (for example, project control docs, config, or template variants).
- Add validation checks for missing/invalid repository-specific template command mappings.
- Add tests for default cross-repo behavior and configured repository-specific behavior.

## Acceptance Criteria

- Shared assist templates remain valid for arbitrary target repositories.
- Repository-specific canonical command guidance is supported through explicit configuration or template routing.
- Tests demonstrate fallback behavior and override behavior.
- Documentation explains how maintainers enable repository-specific template guidance.

## Notes

This work item captures the issue raised in review comments and is intentionally scoped as follow-on design + implementation work.

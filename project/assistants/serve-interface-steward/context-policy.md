---
kind: assistant_context_policy
assistant: ASST-SERVE-INTERFACE-STEWARD
supported_views:
  - orientation
  - current
  - status
  - blockers
  - questions
  - changes
  - decision_request
  - handoff
  - execute
default_human_view: current
default_machine_view: execute
required_authority_labels:
  - authoritative
  - derived
  - observed
  - reported
  - advisory
  - missing
required_metadata:
  - generated_at
  - effective_as_of
  - source_revision
  - provenance
  - sensitivity
  - completeness
  - omissions
compact_token_budget: 2000
standard_token_budget: 6000
full_token_budget: 16000
default_freshness_policy: current_project_state
external_observation_max_age: PT24H
context_loading_strategy:
  - stable_orientation_upfront
  - live_state_derived
  - accepted_memory_on_demand
  - logs_on_demand
  - historical_reports_on_demand
sensitivity_levels:
  - public
  - project_internal
  - owner_only
  - sensitive
---

# Serve Interface Steward — Context Policy

This file governs how context is **constructed**. It contains no live context.

Context is always **derived**, never hand-maintained. The assistant directory
must not store `state.yaml`, `tasks/`, `current.md`, or `blockers.md`. Instead,
a context bundle is composed on demand from the deterministic read-only
`CoreProjectState` plus the workstream binding, the managed subtree, work-item
readiness, run state and events, communications, and accepted memory.

Every context item carries provenance, an authority label, a timestamp,
sensitivity, and its inclusion rationale. Current state and historical change
are treated separately (`state:` answers "what is blocked now?"; a `changes
--since …` view answers "what became blocked this week?"). When event coverage
is incomplete, the bundle must say so rather than inventing a complete history.

Loading follows progressive disclosure: identity, effective scope/policy, the
binding, the current objective, active work, and immediate blockers load
upfront; full logs, historical reports, all accepted memory, old execution
records, and detailed references load only on demand.

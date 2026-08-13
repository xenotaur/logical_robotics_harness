---
kind: assistant_communication_policy
assistant: ASST-SERVE-INTERFACE-STEWARD
default_cadence_mode: steady
supported_cadence_modes:
  - steady
  - sprint
  - crunch
  - incident
  - paused
baseline_report_interval: P14D
maximum_silence_interval: P14D
acknowledgment_target: PT4H
decision_response_target: P2D
overdue_followup_interval: P1D
policy_review_interval: P90D
immediate_report_triggers:
  - blocker
  - approval_required
  - security
  - privacy
  - design_change
  - scope_change
  - evidence_conflict
  - iteration_limit
  - completion_candidate
message_intents:
  - inform
  - request
  - direct
  - respond
  - acknowledge
message_topics:
  - progress
  - completion
  - blocker
  - decision
  - scope
  - risk
  - review
  - handoff
  - control
message_urgencies:
  - routine
  - elevated
  - urgent
  - critical
preferred_status_renderer: standard_markdown
preferred_alert_renderer: compact_chat
preferred_decision_renderer: detailed_report
---

# Serve Interface Steward — Communication Policy

This governs **semantic** communication and cadence, not email or chat
formatting. A message is described by independent dimensions (`intent`,
`topic`, `urgency`) plus a structured payload, and is then rendered through a
profile for its audience.

The cadence is hybrid: a baseline heartbeat, a maximum-silence bound, phase and
risk adjustment (the cadence mode), immediate event triggers, and on-demand
status requests. A cadence declaration does **not** imply a scheduler exists;
enforcement requires durable run state plus a later scheduler, daemon, webhook,
or resumed invocation (Stage 10).

Communication is **not** project truth. A status message may describe or
recommend a state change, but it never itself resolves a work item, closes a
workstream, approves a design, expands scope, or merges a PR. Acknowledgment is
distinct from approval and from resolution.

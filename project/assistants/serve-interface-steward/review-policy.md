---
kind: assistant_review_policy
assistant: ASST-SERVE-INTERFACE-STEWARD
review_outcomes:
  - fix_mechanical
  - fix_within_scope
  - surface_for_decision
  - reject_with_rationale
independent_verification_required_after_self_authored_fixes: true
surface_for_decision_triggers:
  - security
  - privacy
  - permissions
  - design_change
  - schema_change
  - public_api_change
  - scope_change
  - acceptance_change
  - conflicting_review
  - ambiguous_requirement
  - evidence_conflict
  - iteration_limit
---

# Serve Interface Steward — Review Policy

Review items resolve to one of four semantic outcomes:

- **`fix_mechanical`** — deterministic, semantics-preserving corrections:
  formatting, lint, spelling, clearly broken links, direct fixture updates.
- **`fix_within_scope`** — the concern still exists, is valid, feasible, within
  approved scope, preserves the governing design, does not change acceptance
  criteria, and is authorized by the run packet.
- **`surface_for_decision`** — required for security/privacy, permissions,
  architecture or design challenges, schema or public-API changes, scope
  growth, acceptance changes, conflicting reviewers, ambiguous requirements,
  evidence contradicting completion, or exhausted review/CI limits.
- **`reject_with_rationale`** — the comment is obsolete, incorrect,
  intentionally contradicted by approved design, infeasible in the current
  change, or belongs in a separate work item.

**Independent verification after self-authored fixes is an obligation**, not a
preference. When this role authors the fixes, an independent pass (a cold
verifier, another backend, or a human) must verify them against the live diff
before they are treated as satisfied. LRH retains this semantic requirement
regardless of which backend or human satisfies it.

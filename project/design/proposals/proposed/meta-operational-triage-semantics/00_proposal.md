---
id: PROP-META-OPERATIONAL-TRIAGE-SEMANTICS
type: design_proposal
title: LRH Meta Operational Triage Semantics
status: proposed
created_on: 2026-05-24
updated_on: 2026-05-24
implementation_status: not_started
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md
  - project/design/meta_control_plane_mvp_spec.md
  - project/design/execution_framework_mvp.md
  - project/audits/2026-05-22-meta-dashboard-mvp-dogfood-audit.md
supersedes: []
superseded_by: null
---

# LRH Meta Operational Triage Semantics

## Summary

The LRH Meta Operational Triage Dashboard is an action-oriented portfolio
triage system. It shows all registered LRH projects, classifies each project by
the kind of human attention needed next, explains the evidence behind that
classification, and suggests the next useful action.

This proposal refines semantics for the existing LRH Serve operational-triage
MVP direction while preserving safe defaults. The dashboard is not a passive
reporting surface; it is a meta-level decision surface for safe, non-agentic
LRH project coordination.

## Problem / motivation

The current dashboard direction has useful lane grouping, but recent dogfood
showed semantic ambiguity in lane meaning, field naming, evidence visibility,
and suggested-action consistency. Operators need deterministic and auditable
triage outcomes rather than inferred or implicit interpretation.

Without explicit semantics:

- healthy-but-idle projects can be confused with archived projects;
- active focus with zero executable leaves is ambiguous;
- capability gaps can be conflated with project defects;
- validation and setup signals can appear contradictory or opaque.

## Goals

- Define deterministic, evidence-backed triage semantics for all registered
  projects.
- Separate portfolio/lifecycle state from operational triage lane assignment.
- Standardize target vocabulary and map current field names to target
  semantics.
- Require lane-level explainability through evidence and suggested actions.
- Distinguish project issues, LRH capability gaps, dashboard bugs, and operator
  warnings.
- Provide a migration sequence that preserves backward compatibility and keeps
  implementation PRs small.

## Non-goals

This proposal does not:

- implement dashboard semantics in code in this PR;
- add agent dispatch or autonomous execution;
- add write routes to `lrh serve`;
- make `lrh serve` follow remote URLs;
- require every maintenance bugfix to use a formal workstream;
- require archived projects to pass active validation;
- redesign the whole LRH planning model.

## Core semantic pipeline

Triage should follow an explicit, deterministic pipeline:

```text
registration
→ project source access
→ control-plane validation
→ portfolio/lifecycle state
→ work/readiness state
→ triage lane
→ evidence and suggested action
```

Projects should be classified only from explicit, evidence-backed facts.
Classifier logic should avoid hidden assumptions.

## Target vocabulary

Target internal vocabulary:

```text
project_source_access
registration_completeness
registration_check
control_plane_validation
portfolio_state
triage_lane
capability_gap
project_issue
operator_warning
```

Near-term UI may adopt clearer labels before all internal fields are renamed.
Backwards-compatible aliases can remain during migration.

Current/older names mapped to target semantics:

```text
source_state -> project_source_access
setup_state -> registration_completeness and/or registration_check
validation_status -> control_plane_validation.status
lane -> triage_lane
```

Recommended UI labels:

```text
Project source access
Registration completeness
Registration check
Control-plane validation
Triage lane
LRH capability gap
Project issue
Dashboard issue
Operator warning
```

## Portfolio/lifecycle state vs operational triage lane

Portfolio/lifecycle state and triage lane should be modeled separately.

Example portfolio-state vocabulary:

```text
active
paused
archived
```

`archived` must be explicit metadata, not inferred from inactivity:

> The project is intentionally retained for historical/reference purposes and
> is no longer expected to receive normal roadmap, feature, maintenance, or
> triage attention.

Archived projects should usually be pre-filtered:

```text
if portfolio_state == archived:
    triage_lane = archived
else:
    classify by normal operational triage
```

`Archived` is distinct from `No Action Needed`:

- `No Action Needed`: active portfolio project, configured and quiet.
- `Archived`: intentionally out of normal triage unless reactivated.

## Triage lane definitions and evidence requirements

Target lane set:

```text
Blocked
Needs Attention
Active Work
Ready for Work
No Action Needed
Archived
Unknown
```

`Awaiting Review` can be considered later only if LRH can detect review-ready
state reliably.

### Blocked

- Question answered: Can ordinary forward progress proceed?
- Meaning: No.
- Evidence examples:
  - configured checkout path missing;
  - project control-plane directory missing;
  - declared blocker exists;
  - required authority/prerequisite missing.
- Suggested action: unblock the project.

### Needs Attention

- Question answered: Can project state be trusted without intervention?
- Meaning: Not yet; human review/repair/decision is required.
- Evidence examples:
  - control-plane validation errors;
  - broken references;
  - contradictory metadata;
  - stale/ambiguous registration;
  - invalid project/control metadata.
- Suggested action: investigate and repair.

### Active Work

- Question answered: Is substantive work currently underway?
- Meaning: Yes, the project is actively being maintained or executed.
- Evidence examples:
  - active workstream/work item;
  - manual run in progress;
  - recent execution record;
  - branch/PR/review thread (if later integrated);
  - maintenance bugfix in progress.
- Suggested action: monitor ongoing work.

Nuance: small maintenance fixes should count as active work even without a full
formal workstream.

### Ready for Work

- Question answered: Should work start now?
- Meaning: Yes, but LRH does not detect active execution yet.
- Evidence examples:
  - active focus exists but no active execution is detected;
  - ready leaves exist;
  - workstream planned but not started;
  - selected maintenance backlog;
  - roadmap next step available.
- Suggested action: start, schedule, or prepare work.

This lane resolves the current ambiguity where a project is valid but has an
active planning focus with no active work items/leaves.

### No Action Needed

- Question answered: Is the project healthy and currently quiet?
- Meaning: Yes; periodic review only.
- Evidence examples:
  - control-plane validation valid;
  - source access available;
  - no blockers;
  - no active work;
  - no ready work;
  - no active focus requiring kickoff.
- Suggested action: no action now; periodic review.

This replaces vague `Stable` framing for active-portfolio projects.

### Archived

- Question answered: Is this project intentionally out of active portfolio flow?
- Meaning: Yes.
- Evidence example: `portfolio_state: archived`.
- Suggested action: none unless reactivating.

### Unknown

- Question answered: Is there enough information to classify confidently?
- Meaning: No.
- Evidence examples:
  - remote-only project with no local checkout binding;
  - source inaccessible with no known reason;
  - validation unavailable because source cannot be inspected;
  - missing registration metadata.
- Suggested action: provide missing setup/metadata.

## Classification precedence

Deterministic target ordering:

```text
if portfolio_state == archived:
    Archived

else if registration/access facts are insufficient:
    Unknown

else if blocking condition exists:
    Blocked

else if control_plane_validation has errors or contradictory metadata exists:
    Needs Attention

else if active execution/work is detected:
    Active Work

else if planned/ready work exists:
    Ready for Work

else if validation is valid and no action is needed:
    No Action Needed

else:
    Unknown
```

If implementation currently differs, this proposal is the target semantics for
follow-on dashboard iteration.

## Suggested-action model

Every lane assignment should produce one or more suggested actions that are
specific, bounded, and useful in manual mode (for example, inspect, validate,
repair, schedule, or monitor).

Suggested actions should prefer deterministic command or navigation hints where
possible and remain read-only with respect to safe-default serve boundaries.

## Evidence and suggested-action contract

Lane assignment must be explainable and accompanied by visible evidence:

```yaml
triage:
  lane: needs_attention
  reason: control_plane_validation_errors
  evidence:
    - kind: control_plane_validation
      status: error
      error_count: 23
      warning_count: 2
      top_messages:
        - "error CONTRIBUTOR_ROLES_INVALID ..."
  suggested_actions:
    - label: Run validation
      command: "cd /path/to/repo && lrh validate"
```

Field names can evolve, but the contract requirement is stable:
classification must expose evidence and the next useful action where possible.

## Capability gaps vs project issues vs dashboard bugs vs operator warnings

```text
project_issue:
  Something is wrong in the registered project or control plane.

lrh_capability_gap:
  LRH cannot yet derive or expose a useful fact.

dashboard_bug:
  Dashboard output contradicts itself or misrepresents known state.

operator_warning:
  Human should notice a risk/oddity that is not necessarily an error.
```

Examples:

- `project_issue`: broken work-item reference; missing required frontmatter.
- `lrh_capability_gap`: adopted-design implementation count not yet exposed.
- `dashboard_bug`: card says source access live and also says source access
  capability is not implemented.
- `operator_warning`: active focus exists but no executable leaves are exposed.

Project issues may affect lane assignment. Capability gaps should be visible but
should not mark a project as broken unless triage is blocked by the gap.

## Active focus with zero leaves

Recommended target behavior:

```text
If current_focus.status == active
and no active workstreams/items/leaves are exposed
and the focus is not explicitly marked observational/closeout/no-action:
    triage_lane = Ready for Work
    reason = active_focus_needs_kickoff
    operator_warning = active focus has no executable leaves exposed
```

If the focus is explicitly closeout/planning/observational/no-action, the
project may remain `No Action Needed` with an explanatory reason or warning.

## Migration strategy from current fields and labels

1. Land this semantics proposal (control-plane/design only).
2. Clean up UI labels for clarity without immediate internal renames.
3. Add view-model semantic fields with backward-compatible aliases.
4. Update lane classifier to target semantics.
5. Add explicit `portfolio_state` lifecycle metadata.
6. Add active-focus/no-leaves operator warning and/or `Ready for Work`
   classification.
7. Decide whether to implement or defer adopted-design implementation count on
   primary cards.

Avoid large all-at-once renames. Keep compatibility and PR scope small.

## Implementation sequence

1. Semantics alignment PRs (labels, lane definitions, precedence docs).
2. Shared classifier/data-contract update for evidence + suggested action.
3. Dashboard rendering updates (card/detail parity and explanation text).
4. Metadata additions (`portfolio_state`) and archived filtering.
5. Focus/no-leaves handling and associated operator-warning path.
6. Cleanup of stale capability-gap messaging.
7. Documentation and validation refresh across meta + serve docs/tests.

## Risks and mitigations

- Risk: semantic churn confuses operators.
  - Mitigation: stage migration; preserve aliases and clear labels.
- Risk: over-classification from incomplete data.
  - Mitigation: conservative fallback to `Unknown` with explicit missing facts.
- Risk: capability gaps misrepresented as project failures.
  - Mitigation: separate issue taxonomy and only escalate when triage is blocked.
- Risk: archived/no-action conflation.
  - Mitigation: explicit `portfolio_state` metadata and dedicated archived lane.

## Open questions

- Should `Awaiting Review` be retained as a first-class lane or modeled as an
  `Active Work`/`Needs Attention` subtype?
- Which minimal evidence payload is required on cards versus detail pages?
- Where should portfolio metadata live in project control docs for reliable
  parsing/validation?
- What is the exact threshold for "recent execution record" in `Active Work`?

## Relationship to existing designs and audit findings

This proposal is a companion refinement to the existing
`lrh-serve-operational-triage-mvp` proposal and the 2026-05-22 meta-dashboard
MVP dogfood audit. It narrows semantic definitions and migration scope without
changing safe-default/non-agentic boundaries.

It aligns with the meta control-plane and execution-framework MVP documents by
keeping the dashboard read-only, evidence-backed, and human-gated while
clarifying decision semantics for portfolio triage.

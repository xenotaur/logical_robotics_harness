---
id: PROP-WORKSTREAMS-RECURSIVE-PLANNING-TREE
type: design_proposal
title: Workstreams as first-class planning nodes with recursive planning-tree semantics
status: proposed
created_on: 2026-05-05
updated_on: 2026-05-05
---

## 1) Purpose

This proposal introduces **first-class workstreams** as LRH's next
visible planning concept while preserving a simple user-facing model:

```text
Project → Workstream → Work Item
```

Internally, LRH should remain architecture-ready for a longer-horizon
execution model:

```text
Recursive planning tree → executable leaves → controlled runs
```

The immediate proposal outcome is documentation alignment, not runtime
behavior changes.

## 2) Motivation

LRH already has strong support for project-control artifacts, prompt
workflow discipline, execution records, review-response assistance,
versioning, smoke testing, and validation. In practice, however,
substantial planning state still lives outside the repository in chat
history and private notes.

This proposal makes that planning layer explicit, versioned,
reviewable, and eventually automatable, while preserving the current
control-plane-first implementation priority.

## 3) Core design thesis

- Workstreams are user-facing planning nodes.
- Work items are executable leaves.
- Projects are root planning contexts.
- Metadata is authoritative.
- Directory placement is a human navigation aid.
- Validation reconciles metadata and directory placement.
- Automation is explicitly deferred until readiness and guardrails are
  validated.

## 4) User-facing artifacts

Proposed directory layout:

```text
project/workstreams/
  README.md
  proposed/
  active/
  resolved/
  abandoned/
```

This intentionally mirrors the work-item bucket strategy:

- frontmatter `status` is authoritative
- directories are convenience buckets
- validators may warn on drift
- organizer/tidy commands may later repair drift

## 5) Minimal workstream schema

Illustrative minimal frontmatter shape for a single-file workstream:

```yaml
---
id: WS-WORKSTREAMS-PLANNING-TREE
kind: planning_node
title: Add first-class workstreams and planning-tree semantics
status: active
stage: planned
origin: ad_hoc
parent_id: PROJECT-LRH
children:
  - WI-WORKSTREAM-DESIGN-DOC
  - WI-WORKSTREAM-SCHEMA
exit_criteria:
  - LRH documents workstreams as first-class artifacts.
  - LRH can validate workstream status and stage.
  - LRH can relate workstreams to child work items.
---
```

MVP-required fields (proposed):

- `id`
- `kind`
- `status`
- `stage`

MVP-recommended fields:

- `title`
- `origin`
- `parent_id`
- `children`
- `exit_criteria`

Future/optional fields can cover readiness, autonomy/risk,
closeout rationale, ownership, sequencing hints, and richer
constraints once implementation and validation guardrails exist.

## 6) Status versus stage

Define:

```text
status = coarse lifecycle / directory bucket
stage  = fine-grained planning position
```

Initial status set:

```text
proposed | active | resolved | abandoned
```

Initial stage set:

```text
conceived | assessed | designed | planned | executing | reviewing | closed | abandoned
```

Suggested status/stage mapping:

```text
proposed: conceived, assessed, designed, planned
active: executing, reviewing
resolved: closed
abandoned: abandoned
```

Closure detail variants (for example completed, rejected, superseded,
reverted) should live in closeout metadata or decision notes rather
than expanding the top-level `status` vocabulary prematurely.

## 7) Recursive planning-tree semantics

First implementation should **not** expose an abstract `nodes/` UX.
However, the internal model should remain tree-ready.

Planning relationships are defined by metadata (`parent_id`,
`children`) rather than nested path structure.

Expected future validation includes:

- unique IDs
- valid parent references
- valid child references
- no cycles
- no orphaned active workstreams unless intentionally top-level
- warnings when parent/child declarations disagree

## 8) Relationship to work items and `lrh run`

Workstreams prepare the ground for future executable-leaf readiness
and `lrh run`, but this proposal does not implement either.

Future readiness concept (illustrative only):

```yaml
kind: work_item
id: WI-RUN-DRY-RUN
parent_id: WS-LRH-RUN-MVP
status: ready
autonomy_level: assisted
risk_level: low
acceptance_criteria:
  - ...
validation_commands:
  - scripts/test
allowed_paths:
  - src/lrh/
  - tests/
agent_policy:
  preferred_mode: dry_run
expected_outputs:
  - execution_record
  - validation_results
```

A future `lrh run --dry-run` should execute only validated executable
leaves.

## 9) Relationship to prompt IDs, execution records, evidence, and status

Workstreams do not replace prompt execution records.

```text
Workstream = planning / aggregation / intent
Work item = executable task
Execution record = what happened during a prompt/run
Evidence = concrete validation output
Status = interpreted project state
```

## 10) Validation expectations

Initial validation goals (design intent only):

Potential errors:

- invalid frontmatter
- missing required id
- duplicate workstream id
- invalid status
- invalid stage
- invalid kind
- invalid status/stage combination
- cycle in parent/child graph

Potential warnings:

- bucket/status mismatch
- missing title
- missing exit criteria
- unknown parent_id if parent is optional in MVP
- child references not found
- active workstream with no children or next action
- resolved workstream without closeout rationale

## 11) Snapshot expectations

Future snapshot behavior (illustrative):

```text
Workstreams:
  proposed: 2
  active: 1
  resolved: 7
  abandoned: 1

Active:
  WS-WORKSTREAMS-PLANNING-TREE
    stage: planned
    children: 3
    next: implement schema validation
```

## 12) Non-goals

This proposal PR must not:

- implement workstream parsing/loading
- implement validation
- implement snapshot changes
- add `lrh run`
- add agent adapters
- reorganize existing work items
- alter existing execution records unrelated to this prompt
- introduce broad process requirements for trivial fixes

## 13) Recommended follow-up sequence

1. Add the design proposal.
2. Update roadmap/current focus/work items.
3. Add `project/workstreams/` README and buckets.
4. Add minimal schema/model support.
5. Add validation.
6. Add internal tree index.
7. Add snapshot summary.
8. Add organize/tidy command.
9. Later add executable-leaf readiness and `lrh run --dry-run`.

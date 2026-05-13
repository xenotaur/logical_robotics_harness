# Bounded Execution Framework MVP

This document is LRH's canonical living design and context package for the bounded execution
framework MVP. It records the current architecture and staged implementation plan that future chats,
prompts, work items, and implementation PRs should use as their controlling context.

## Purpose

This document defines LRH's MVP execution framework: a staged path from execution-ready work items
to bounded, auditable runtime execution.

Core principle:

```text
LRH execution must not outpace the project control plane.
```

Before LRH automates work, the repository should represent:

- what is being done;
- why it exists;
- what authority is granted;
- what constraints apply;
- how success will be evidenced; and
- what remains human-gated.

The MVP therefore starts with contracts that can be inspected manually before LRH mutates branches,
opens pull requests, invokes agent backends, or runs stabilization loops.

## Document ownership and layering

LRH separates design rationale, living architecture, planning state, executable leaves, and execution
history:

```text
project/design/proposals/
  historical rationale and design-decision proposals

project/design/execution_framework_mvp.md
  canonical evolving design for bounded execution

project/workstreams/
  current workstream state and planning-node metadata

project/roadmap, project/focus, project/work_items
  current implementation plan and executable leaves

project/executions, project/evidence, run reports
  what happened during execution
```

Proposals explain why LRH chose this direction. `execution_framework_mvp.md` explains the current
MVP architecture and staged plan. The execution-framework workstream tracks current state and links
to this design.

## Scope and non-goals

In scope for the MVP design:

- execution readiness;
- run packet contract;
- run state;
- run report;
- ecosystem adapters;
- branch containment;
- bounded stabilization;
- manual-mode parity;
- evidence/provenance; and
- human gates.

Out of scope for the MVP or deferred to later phases:

- unbounded autonomous execution;
- automatic merge to main;
- release/publish automation;
- secret-bearing workflows;
- MCP bridges;
- telemetry systems beyond basic evidence;
- autonomy modes beyond the documented `autonomy_level` values; and
- full backend-specific automation before contracts stabilize.

## Architectural split: control plane vs runtime plane

The execution framework has two planes.

Control plane:

- project artifacts;
- workstreams;
- work items;
- policy;
- run packet spec;
- readiness validation;
- evidence requirements; and
- run reports.

Runtime plane:

- branch operations;
- PR operations;
- CI observation;
- review observation;
- agent backend calls; and
- bounded stabilization loop.

Phase 1 strengthens the control plane before Phase 3 mutates anything. This keeps command naming,
contracts, evidence expectations, and human gates reviewable before LRH adds runtime authority.

## Phase structure

### Phase 1: `lrh run` structural support

Goal:

```text
Create the infrastructure for something that could be run, without running agents or mutating branches.
```

Deliverables:

- execution readiness schema;
- run packet dry-run;
- run state model;
- run report MVP;
- readiness validation; and
- manual-mode run checklist.

Explicit non-goals:

- no branch mutation;
- no agent calls;
- no PR creation; and
- no runtime stabilization loop.

### Phase 2: ecosystem observation and containment adapters

Goal:

```text
Connect LRH to git/GitHub/CI/review ecosystem state safely before allowing mutation.
```

Deliverables:

- git branch policy model;
- agent branch namespace;
- repository cleanliness checks;
- GitHub PR/CI/review observation;
- protected-branch assumptions;
- backend-neutral adapter interfaces; and
- least-privilege credential assumptions.

Initial posture:

```text
observe first, mutate later
```

### Phase 3: bounded runtime execution

Goal:

```text
Actually execute bounded runs inside the policy and containment model.
```

Deliverables:

- dispatch backend prompt;
- wait/observe backend response;
- apply/update agent branch;
- observe CI/review;
- iterate within limits;
- stop on abort criteria; and
- emit final run report.

Human/policy gates remain for:

- merge to main;
- release/publish;
- work item closeout;
- workstream closeout;
- scope expansion; and
- destructive actions.

## Cross-cutting requirements

Every phase must preserve:

- **control-plane freshness** — substantial runs should update or produce project-control artifacts
  such as run packet, run state, execution record, run report, evidence, and work item/workstream
  closeout recommendation;
- **manual-mode parity** — a human following the packet should produce the same evidence and report
  shape as an automated backend;
- **human gates** — humans or explicit policy control merge, release, publish, closeout, scope
  expansion, and destructive actions;
- **least privilege** — each run gets only the authority needed for the selected target;
- **evidence/provenance** — reports cite validation, logs, commits, review, screenshots, metrics,
  or other evidence rather than unsupported model claims;
- **bounded loops** — backend calls, CI rounds, review rounds, time, and budget are capped;
- **abort criteria** — runs stop on policy violations, scope expansion, repeated failure, missing
  authority, or human rejection;
- **sandboxing/containment** — work is scoped to an allowed workspace and, in later phases, an
  agent-owned branch or stronger containment layer;
- **backend neutrality** — LRH owns packet, state, and report contracts while adapters provide
  capabilities; and
- **automation-laundering prevention** — final reports distinguish evidence, model claims, and
  human verification still required.

## Execution readiness contract

Execution readiness is candidate metadata on selected work items. It should evolve with the actual
work-item schema, so this section is a starting contract rather than a final validator commitment.

Candidate shape:

```yaml
execution:
  ready: true
  prompt_source: project/work_items/proposed/WI-EXAMPLE.md
  acceptance_criteria:
    - acceptance criterion copied or derived from the work item
  deliverables:
    - expected deliverable or artifact
  validation_commands:
    - scripts/test
  allowed_paths:
    - src/lrh/example/
    - tests/example/
  forbidden_paths:
    - .github/workflows/
    - secrets/
  autonomy_level: manual | human_gated | bounded_auto | sequential_bounded
  operation_risk: read_only | safe_local | branch_mutating | repo_mutating | external_side_effect | destructive
  containment: none | sacrificial_clone | sandboxed_filesystem | container | ephemeral_vm | monitored
  max_agent_calls: 1
  max_review_rounds: 3
  max_ci_rounds: 3
  requires_human_merge: true
  requires_human_closeout: true
  abort_criteria:
    - stop if requested changes expand scope beyond the selected work item
```

Key distinctions:

- `autonomy_level` is not `operation_risk`;
- `operation_risk` is not `containment`; and
- `containment` is not `evidence`.

Use `operation_risk` for the execution-readiness contract because it describes what kind of
operation the run may perform. Existing planning examples that use `risk_level` should be treated as
general planning-level risk summaries; implementation work should either migrate them to
`operation_risk` for execution metadata or explicitly derive `operation_risk` from `risk_level`
without losing review context.

A manual read-only investigation and a branch-mutating bounded-auto implementation can share a work
item type, but they require different authority, controls, and evidence.

## `lrh run` target model

Recommended target semantics:

```text
canonical target: work item
```

Recommended initial command shape:

```text
lrh run WI-... --dry-run
```

This document uses `lrh run` as provisional execution-framework shorthand. Any final command naming
must preserve the safe-default package boundary and should not imply autonomous capability in default
LRH before optional agentic capability is designed and accepted.

Later target compilation can be layered on top of the work-item target:

```text
prompt/ad-hoc task -> ad-hoc run packet
workstream -> sequence of selected work items
design -> generates work items, not directly executable
```

## Run packet contract

A run packet is the authorized plan for one bounded attempt.

```text
run packet = authorized plan
```

Candidate structure:

```yaml
run_packet:
  run_id: RUN-YYYYMMDD-HHMMSS-WI-EXAMPLE
  target:
    type: work_item
    id: WI-EXAMPLE
  workstream: WS-EXAMPLE
  prompt:
    source: project/work_items/proposed/WI-EXAMPLE.md
    rendered: project/runs/RUN-YYYYMMDD-HHMMSS-WI-EXAMPLE/prompt.md
  policy:
    autonomy_level: manual
    operation_risk: safe_local
    containment: sandboxed_filesystem
    max_agent_calls: 1
    max_review_rounds: 3
    max_ci_rounds: 3
    requires_human_merge: true
  workspace:
    branch: agents/manual/WI-EXAMPLE
    sandbox: local-working-tree
    allowed_paths:
      - project/design/
    forbidden_paths:
      - .github/workflows/
  validation:
    commands:
      - scripts/test
    required_checks:
      - markdown/control-plane review
  abort_criteria:
    - stop on scope expansion beyond WI-EXAMPLE
```

The run packet authorizes what may be attempted. It is not run state and it is not the final run
report. The packet answers "what is allowed?"; state answers "where are we now?"; the report answers
"what happened, what evidence exists, and what should happen next?"

## Run state contract

Run state is the current lifecycle position of one run.

```text
run state = where the run is now
```

Candidate states:

```text
created
packet_rendered
awaiting_human_approval
branch_prepared
pr_opened
agent_running
ci_waiting
review_waiting
stabilizing
blocked
aborted
completed
reported
```

Phase 1 may only use a small subset such as `created`, `packet_rendered`,
`awaiting_human_approval`, `blocked`, and `reported`. Later phases can activate branch, PR, agent,
CI, review, and stabilization states after adapters and policy gates exist.

## Run report contract

A run report is the final evidence and recommendation for one run.

```text
run report = final evidence and recommendation
```

Candidate result statuses:

```text
done
done_needs_human_verification
blocked
failed
rejected_or_infeasible
aborted_by_policy
```

Recommended contents:

- summary;
- target;
- branch/PR;
- prompts/responses or links to logs;
- commits;
- validation commands;
- CI checks;
- review comments addressed;
- remaining risks;
- human verification steps; and
- recommendation.

The report should distinguish between:

- evidence;
- model claims; and
- human verification still required.

A report can recommend work-item or workstream closeout, but closeout remains a separate human or
policy-gated decision.

## Branch containment model

Future branch namespace:

```text
agents/<backend>/<workstream-or-work-item>
```

Rules:

- agent can mutate agent-owned branch only;
- PR targets protected `main` or selected protected integration branch;
- CI runs on branch push and PR;
- human controls merge to main; and
- human/policy controls release, publish, and closeout.

Phase boundaries:

```text
Phase 1 does not create branches.
Phase 2 observes and models branches.
Phase 3 may mutate branches under policy.
```

Branch containment is a review boundary, not a complete sandbox. Stronger containment remains a
separate policy choice recorded in the run packet.

## Adapter architecture

Adapter categories:

- Git adapter;
- GitHub adapter;
- CI/review observation adapter;
- Agent backend adapter;
- Manual backend; and
- Fake backend.

Principle:

```text
LRH owns the contract; adapters provide capabilities.
```

Adapters should declare capabilities, required permissions, and unsupported operations. LRH should
not let an adapter's convenience API redefine packet, state, report, evidence, or policy semantics.

## Safety and risk model

Risks connect to controls as follows:

- excessive agency -> selected target, bounded loops, branch containment, human gates;
- prompt injection -> scoped context, no secrets by default, policy checks;
- insecure output handling -> validation and review before applying outputs;
- model denial of service/cost surprise -> max calls, max rounds, time/budget limits;
- supply-chain risk -> provenance, CI, protected branches, artifact evidence; and
- automation laundering -> final report distinguishes evidence from claims.

The MVP should make unsafe authority visible rather than hiding it behind a successful-looking run.

## Next implementation sequence

Next concrete implementation package:

1. Execution readiness schema MVP.
2. Run packet dry-run MVP.
3. Run report MVP.

Explicitly defer:

- GitHub mutation;
- branch creation;
- PR creation;
- agent calls;
- bounded stabilization loop; and
- backend-specific adapters.

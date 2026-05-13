# Bounded Execution Framework MVP

This document is LRH's canonical living design and context package for the bounded execution
framework MVP. It records the current architecture and staged implementation plan that future chats,
prompts, work items, and implementation PRs should use as their controlling context.

## Purpose

This document defines LRH's MVP execution framework: a staged path from execution-ready work items
to safe, auditable, human-assisted execution support first, and optional bounded automation later.

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

The MVP therefore starts with contracts and local assist surfaces that can be inspected and operated
manually before LRH mutates branches, opens pull requests, invokes agent backends, or runs
stabilization loops.

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

project/executions, project/runs, project/evidence, run reports
  what happened during execution
```

Proposals explain why LRH chose this direction. `execution_framework_mvp.md` explains the current
MVP architecture and staged plan. The execution-framework workstream tracks current state and links
to this design.

## Scope and non-goals

In scope for the MVP design:

- core state and interpretation APIs used by CLI and UI surfaces;
- safe-default `lrh serve` viewer and prompt workbench;
- execution readiness;
- run packet contract;
- durable run state;
- awaited-transition contracts;
- run report;
- ecosystem observation adapters;
- manual-mode parity;
- evidence/provenance; and
- human gates.

Out of scope for the default/safe layer, or deferred to optional agentic capability:

- autonomous agent dispatch;
- automatic branch mutation;
- automatic pull-request creation;
- automatic CI-fix or review-response loops;
- automatic merge to main;
- release/publish automation;
- destructive actions;
- secret-bearing workflows;
- MCP bridges;
- telemetry systems beyond basic evidence;
- autonomy modes beyond the documented `autonomy_level` values; and
- full backend-specific automation before contracts stabilize.

## Architectural split: safe control plane vs optional runtime authority

The execution framework has two broad authority zones.

Default / safe LRH:

- load, validate, and snapshot project state;
- generate requests and prompts;
- serve a local viewer and prompt workbench;
- show project, focus, workstream, work-item, and run state;
- render, edit, copy, and download prompts;
- support explicit-click writes to LRH control artifacts where appropriate; and
- support manual evidence and report recording.

Agentic / opt-in LRH:

- dispatch external agents;
- mutate branches;
- open pull requests automatically;
- run stabilization loops automatically;
- invoke CI-fix or review-fix loops automatically; and
- merge, publish, or release.

The boundary is a capability and governance boundary, not a formal security sandbox claim. It aligns
with the adopted safe-default agentic packaging proposal in
`project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md`: safe/default
LRH may include a human-assist `lrh serve` surface, while autonomous dispatch and mutation belong to
optional agentic packaging after contracts and policy gates are stable. Implementation should
initially preserve logical boundaries inside the existing `src/lrh/` package layout rather than force
premature package churn.


## Implementation package boundary

The execution-framework workstream is staged so future implementation prompts do not mix
prerequisite control-plane alignment, execution contracts, local workbench UI, observation, and
mutation-capable runtime authority.

The selected first implementation package is the smallest coherent **execution-contract package**:

1. `WI-EXECUTION-READINESS-SCHEMA`
2. `WI-RUN-PACKET-DRY-RUN`
3. `WI-RUN-REPORT-MVP`

This package defines the opt-in readiness metadata, dry-run/manual run packet artifact, and
evidence-backed run report shape needed for later execution work. It does not implement autonomous
execution, backend dispatch, branch mutation, PR creation, stabilization loops, merge/release
automation, or `lrh serve`.

Prerequisite control-plane alignment remains separate from the first execution-contract package:

- shared state/API interpretation for project-control artifacts;
- planning-tree relationship/index validation; and
- snapshot-visible planning summaries.

If any prerequisite is incomplete when a future implementation prompt is prepared, complete it in a
separate prerequisite prompt before starting the execution-contract package. The safe-default
`lrh serve` viewer and prompt workbench is a later read-only/local-assist package that should consume
the shared state and execution contracts; it is not part of the first execution-contract package.

## Staged layer model

### Layer 0: core state and interpretation APIs

Goal:

```text
Provide one shared interpretation of project state for CLI commands, the local viewer, and future dry-run packets.
```

Responsibilities:

- load project control artifacts;
- validate project state;
- snapshot project state;
- maintain a shared planning relationship/index model that resolves projects, workstreams, work
  items, parent/child relationships, active leaves, readiness/status summaries, and evidence/status
  links relevant to execution;
- preserve the user-facing planning vocabulary `Project -> Workstream -> Work Item` while allowing
  implementation internals to use a more general relationship/index model;
- resolve focus, workstreams, work items, active leaves, evidence, and status;
- expose prompt/request rendering inputs; and
- keep raw Markdown/frontmatter source separate from typed runtime objects.

Commands and surfaces such as `lrh validate`, `lrh snapshot`, `lrh request`, `lrh serve`, and later
`lrh run --dry-run` must consume these same core APIs rather than each inventing a workflow engine.
Request templates, UI projections, and run-oriented commands should not duplicate planning-tree
inference outside this shared layer.

Planning relationship validation is a prerequisite for trustworthy serve/run behavior. Layer 0 should
validate or warn about duplicate IDs, invalid planning record kinds, unknown parent or child
references, self-parenting, parent/child cycles, parent/children disagreement, unexpected orphaned
active records, and active workstreams that have no actionable leaf before higher layers treat that
state as execution context.

The preferred sequencing is:

```text
planning relationship/index model
-> planning relationship validation
-> snapshot planning summary
-> lrh serve renders the same summary
```

This keeps `lrh serve` a projection of the control plane. The viewer may add interaction and prompt
workbench affordances, but the first place planning-tree interpretation appears should be shared
snapshot-visible state rather than server-only logic.

### Layer 1: safe-default viewer and prompt workbench

Goal:

```text
Make the manual Huge Loop visible and easier to operate without making default LRH autonomous.
```

`lrh serve` is a local browser UI that projects existing/control-plane state. It is not a separate
workflow engine and must not become an autonomous runner in the default package. Its planning-tree
view should render the same snapshot planning summary produced by Layer 0, not reinterpret
workstream/work-item relationships independently.

It should eventually show:

- project identity and validation status;
- current focus;
- active workstreams;
- active work items;
- workstream tree / active leaf state;
- current manual Huge Loop state;
- available next human actions;
- generated prompts in editable form, including a safe-default "Generate run packet" action for
  selected work items before any autonomous run capability exists;
- copy-to-clipboard with a fallback download/copy path;
- evidence and report checklists; and
- later, observed PR/CI/review status after observation adapters exist.

### Layer 2: run packet, run state, awaited transitions, and run reports

Goal:

```text
Persist enough run context that manual and future automated runs share the same packet, state, event, evidence, and report shape.
```

Initial command shorthand remains:

```text
lrh run WI-... --dry-run
```

Layer 2 introduces `project/runs/<RUN-ID>/` contracts, manual-mode parity, awaited transitions, and
recovery/resume semantics without requiring autonomous dispatch.

### Layer 3: observation adapters

Goal:

```text
Connect LRH to ecosystem state safely before allowing mutation.
```

Responsibilities:

- git state observation;
- GitHub PR/CI/review observation;
- evidence extraction for run reports; and
- no mutation, comments, pushes, PR creation, merges, or workflow reruns.

Initial posture:

```text
observe first, mutate later
```

### Layer 4: optional agentic execution adapters

Goal:

```text
Allow explicitly installed/selected agentic capability to satisfy the same contracts programmatically.
```

Responsibilities, all outside the default safe layer:

- CLI agent dispatch;
- cloud task dispatch;
- branch mutation;
- PR creation where authorized;
- bounded stabilization; and
- backend-specific adapter behavior.

### Layer 5: optional daemon / webhook / dashboard mode

Goal:

```text
Support long-running orchestration only after durable run contracts and adapter boundaries are mature.
```

Possible future responsibilities:

- resume pending transitions;
- react to webhook or polling observations;
- monitor multiple projects; and
- coordinate long-running dashboards or daemon processes.

## Safe-default `lrh serve` write boundary

Default `lrh serve` may write LRH control artifacts only when the user explicitly initiates a write
action. Acceptable explicit-click writes include:

- saving a generated prompt packet under a run directory;
- creating a manual run state;
- recording a manually supplied PR URL;
- recording manually supplied review feedback;
- recording manually supplied validation evidence;
- rendering a final report draft; and
- creating an execution record through existing prompt-workflow conventions.

Default `lrh serve` must not:

- dispatch agents;
- mutate code branches;
- push commits;
- open PRs automatically;
- perform automated CI-fix loops;
- perform automated review-response loops;
- merge;
- publish or release; or
- perform destructive actions.

## Local server safety posture

`lrh serve` is a local assist UI, not a sandbox. Its default safety posture should be conservative:

- bind to `127.0.0.1` by default;
- do not bind to `0.0.0.0` unless explicitly requested;
- use a per-session random token for state-changing requests;
- avoid permissive CORS by default;
- do not display secrets by default;
- do not provide arbitrary filesystem browsing outside the project root;
- provide a read-only mode;
- require explicit confirmations/clicks for writes; and
- avoid claiming that local hosting alone provides isolation from malicious project content.

## Cross-cutting requirements

Every layer must preserve:

- **control-plane freshness** — substantial runs should update or produce project-control artifacts
  such as run packet, run state, execution record, run report, evidence, and work item/workstream
  closeout recommendation;
- **manual-mode parity** — a human following the packet should produce the same evidence and report
  shape as an automated backend;
- **explicit human gates** — humans or explicit policy control merge, release, publish, closeout,
  scope expansion, destructive actions, and default-layer writes;
- **least privilege** — each run gets only the authority needed for the selected target;
- **evidence/provenance** — reports cite validation, logs, commits, review, screenshots, metrics,
  or other evidence rather than unsupported model claims;
- **bounded loops** — backend calls, CI rounds, review rounds, time, and budget are capped when
  optional agentic adapters eventually exist;
- **abort criteria** — runs stop on policy violations, scope expansion, repeated failure, missing
  authority, or human rejection;
- **containment clarity** — branch containment is a review boundary, and stronger containment is a
  separate policy choice recorded in the run packet;
- **backend neutrality** — LRH owns packet, state, and report contracts while adapters provide
  capabilities; and
- **automation-laundering prevention** — final reports distinguish evidence, model claims, and
  human verification still required.

## Execution readiness contract

Execution readiness is candidate metadata on selected work items. It should evolve with the actual
work-item schema, so this section is a starting contract rather than a final validator commitment.

Strict execution-readiness validation remains opt-in. Existing work items should not be forced into
runner-ready metadata all at once. Strong readiness checks should apply to selected or explicitly
opted-in records, such as work items that declare execution/run metadata or that are passed to a run
packet or run command. This preserves compatibility for planning/control-plane records while allowing
strong validation where the execution framework is intentionally used.

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

## Prompt action selection

Planning stage chooses the next planning prompt; run state chooses the next execution-loop prompt.
This split prevents `lrh serve`, `lrh request`, and future run surfaces from treating planning
workflow state as if it were already execution-loop state.

Planning-stage prompt actions include:

- pro/con assessment;
- design assessment;
- implementation plan;
- prompt package;
- audit; and
- work items from audit.

Execution-loop prompt actions include:

- initial implementation prompt or run packet;
- review-response prompt;
- CI-response prompt;
- stabilization prompt; and
- evidence/report prompt.

## `lrh run` target model

Recommended target semantics:

```text
canonical target: work item
```

Desired long-term execution command family:

```text
lrh run WI-...
```

Potential preview/simulation form:

```text
lrh run WI-... --dry-run
```

Stable safe-default diagnostic/request command:

```text
lrh request run_packet_from_work_item <WORK_ITEM_ID>
```

This document uses `lrh run` as execution-framework shorthand for the future command family. Any
final command naming must preserve the safe-default package boundary and should not imply autonomous
capability in default LRH before optional agentic capability is designed and accepted.

`lrh request run_packet_from_work_item <WORK_ITEM_ID>` should remain narrowly constrained to
rendering the canonical run packet/request artifact for a work item. It must not imply execution,
simulation, dispatch, observation, mutation, or stabilization. `lrh run WI-... --dry-run` may
eventually preview or simulate a run using the current runner semantics. The two commands may
initially produce the same or nearly the same artifact, but they should not be documented as
permanently semantically identical.

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
    rendered: project/runs/RUN-YYYYMMDD-HHMMSS-WI-EXAMPLE/prompts/initial.md
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

## Durable run layout and awaited transitions

Planned run artifacts should be recoverable and inspectable:

```text
project/runs/
  RUN-YYYYMMDD-HHMMSS-WI-EXAMPLE/
    packet.yaml
    state.yaml
    events.jsonl
    prompts/
      initial.md
      review_response.md
      ci_response.md
    evidence/
      validation.md
      review.md
      ci.md
    report.md
```

`events.jsonl` is the append-only recovery and audit log. `state.yaml` is a materialized convenience
view derived from the latest known run position, not the sole source of history. A later runner or
server should be able to resume from these artifacts after interruption.

Awaited transitions represent pending work that may be satisfied manually or programmatically later.
Examples include `awaiting_human_approval`, `awaiting_manual_pr_url`, `awaiting_validation_evidence`,
`awaiting_ci_observation`, and `awaiting_review_feedback`. A human can satisfy an awaited transition
through explicit control-artifact updates or future explicit-click `lrh serve` actions. Optional
agentic adapters may later satisfy the same transition programmatically under the same packet, state,
event, evidence, and report contracts.

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
awaiting_manual_pr_url
awaiting_validation_evidence
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

The first safe-default implementation may only use a small subset such as `created`,
`packet_rendered`, `awaiting_human_approval`, `awaiting_validation_evidence`, `blocked`, and
`reported`. Later layers can activate branch, PR, agent, CI, review, and stabilization states after
adapters and policy gates exist.

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
- branch/PR when manually supplied or observed;
- prompts/responses or links to logs;
- commits when applicable;
- validation commands;
- CI checks when observed;
- review comments addressed when supplied or observed;
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

Rules for optional mutation-capable layers:

- agent can mutate agent-owned branch only;
- PR targets protected `main` or selected protected integration branch;
- CI runs on branch push and PR;
- human controls merge to main; and
- human/policy controls release, publish, and closeout.

Layer boundaries:

```text
Layer 1 does not create or mutate branches.
Layer 2 may describe branch policy in packets without mutating branches.
Layer 3 observes and models branches.
Layer 4 may mutate branches under optional agentic policy.
```

Branch containment is a review boundary, not a complete sandbox. Stronger containment remains a
separate policy choice recorded in the run packet.

## Adapter architecture

Adapter categories:

- Git observation adapter;
- GitHub observation adapter;
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
Observation adapters should arrive before mutation-capable adapters.

## Safety and risk model

Risks connect to controls as follows:

- excessive agency -> selected target, bounded loops, branch containment, human gates;
- prompt injection -> scoped context, no secrets by default, policy checks;
- insecure output handling -> validation and review before applying outputs;
- local UI confusion -> read-only mode, explicit-click writes, conservative bind/CORS/token defaults;
- model denial of service/cost surprise -> max calls, max rounds, time/budget limits;
- supply-chain risk -> provenance, CI, protected branches, artifact evidence; and
- automation laundering -> final report distinguishes evidence from claims.

The MVP should make unsafe authority visible rather than hiding it behind a successful-looking run.

## Recommended implementation sequence

Recommended design and implementation order:

1. Keep the prerequisite control-plane alignment separate from execution runtime work:
   `WI-LRH-CORE-STATE-APIS-MVP`, planning relationship validation, and
   `WI-WORKSTREAM-SNAPSHOT-MVP`.
2. Start the first execution-contract package only when those prerequisites are available enough for
   packet generation to use shared state instead of inventing its own planning interpretation.
3. Implement the first execution-contract package in this order:
   `WI-EXECUTION-READINESS-SCHEMA` -> `WI-RUN-PACKET-DRY-RUN` -> `WI-RUN-REPORT-MVP`.
4. Add the safe-default `lrh serve` viewer/prompt workbench afterward as a read-only/local-assist
   package that consumes shared state, readiness, packet, and report contracts.
5. Add run-state artifacts and manual run tracking under `project/runs/<RUN-ID>/` after the artifact
   contracts are reviewed.
6. Add observation adapters for git, PR, CI, and review status only after packets/reports can express
   the evidence they observe.
7. Add optional agentic dispatch adapters later, behind the adopted safe-default packaging boundary.

Explicitly defer from the default/safe layer:

- GitHub mutation;
- branch creation;
- PR creation;
- agent calls;
- automated CI-fix loops;
- automated review-response loops;
- bounded stabilization loop execution; and
- backend-specific autonomous adapters.

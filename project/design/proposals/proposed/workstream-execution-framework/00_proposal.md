---
id: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
title: Workstream Execution Framework
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-05-13
owner: anthony
related_focus:
  - FOCUS-BOOTSTRAP
related_roadmap:
  - ROADMAP-PHASE-02
supersedes: []
superseded_by: null
---

# Workstream Execution Framework — Top-Level Proposal

## Summary

This proposal describes a future **workstream execution framework** for
Logical Robotics Harness (LRH). As the Workstream Control Plane MVP
continues to mature through its active focus and reviewed implementation
slices, this proposal remains the deferred design home for the execution
concepts that should not be pulled into that MVP. It focuses on a later
conceptual boundary: bounded, auditable execution of already approved
executable leaves.

The design intentionally distinguishes **unbounded agent autonomy** from
**bounded, branch-contained, evidence-producing orchestration for
selected work items**. The target execution shape is:

```text
selected executable leaf
-> run packet
-> agent-owned branch
-> pull request
-> bounded review/CI stabilization loop
-> final run report
-> human/policy merge and closeout gate
```

The proposed containment model is repository-native. LRH selects a ready
work item or executable planning-tree leaf, packages the allowed goal,
paths, commands, budgets, and evidence expectations into a run packet,
and gives an execution backend only the authority needed to work in an
agent-owned branch such as `agents/<backend>/<workstream-or-work-item>`.
The pull request is the stabilization boundary: CI and review feedback
may be addressed inside explicit iteration limits, but merge, release,
publish, and workstream/work-item closeout remain human or policy gates.

This is a design proposal only. It does not assert that LRH already
supports autonomous execution, `lrh run`, GitHub API integration,
execution backends, orchestration loops, or privileged workflow
permissions. Those capabilities would need to be implemented later in
staged workstreams with their own review, validation, and evidence.

## Table of contents

1. [Motivation](#1-motivation)
2. [Scope and non-goals](#2-scope-and-non-goals)
3. [Where execution sits in the planning tree](#3-where-execution-sits-in-the-planning-tree)
4. [Bounded branch-level agency](#4-bounded-branch-level-agency)
5. [Run packets and run reports](#5-run-packets-and-run-reports)
6. [Backend-neutral execution contract](#6-backend-neutral-execution-contract)
7. [Evidence, observability, and lifecycle history](#7-evidence-observability-and-lifecycle-history)
8. [Human and policy gates](#8-human-and-policy-gates)
9. [Cross-cutting invariants](#9-cross-cutting-invariants)
10. [Build vs. buy positioning](#10-build-vs-buy-positioning)
11. [Risks and mitigations](#11-risks-and-mitigations)
12. [Adoption plan](#12-adoption-plan)
13. [Open questions](#13-open-questions)
14. [Reading order and document index](#14-reading-order-and-document-index)
15. [References](#15-references)

## 1. Motivation

LRH's control plane can now represent workstreams and planning-tree
relationships, but execution remains intentionally human-driven. The
next design question is how LRH should eventually help execute selected
leaves without turning the repository into an unbounded agent workspace.
The answer proposed here is not "let an agent do whatever is next." It
is a narrow workflow in which humans or policy select a specific leaf,
LRH emits a bounded run packet, an execution backend works in an
agent-owned branch, and the result is reviewed through a pull request
with explicit evidence and stop conditions.

This addresses several practical needs:

- work items should be executable without losing their workstream and
  planning-tree context;
- agent activity should leave durable repository evidence rather than
  disappearing into an external transcript;
- CI and review stabilization should be allowed, but only inside a
  bounded loop;
- merge-to-main, release, publish, and closeout should stay outside the
  agent's unilateral authority; and
- manual execution should remain a first-class equivalent path.

The proposal preserves LRH's repo-native thesis while making branch and
PR containment the primary safety boundary for future agentic work.

## 2. Scope and non-goals

### In scope

This proposal specifies the desired future architecture for:

- selecting an already-approved executable work item or planning-tree
  leaf;
- building a run packet that constrains goals, paths, commands,
  budgets, tokens, evidence, and stop conditions;
- assigning execution to an agent-owned branch namespace such as
  `agents/<backend>/<workstream-or-work-item>`;
- opening a pull request as the stabilization boundary;
- allowing a bounded CI/review loop with explicit maximum iteration
  counts;
- producing a final run report and evidence links;
- preserving manual-mode parity through the same packet and report
  shapes;
- retaining typed lifecycle transitions and append-only transition
  history where appropriate; and
- keeping merge, release, publish, and closeout behind human or policy
  gates.

### Non-goals for this design update

This proposal update does **not** implement or require:

- runtime code;
- CLI behavior changes;
- `lrh run`;
- GitHub API integration;
- agent backends;
- automation;
- schema validation behavior;
- execution backend selection;
- orchestration loops;
- privileged workflow permissions; or
- tests for runtime execution behavior.

The framework described here is proposed/future architecture. Any
implementation should arrive through smaller workstreams that first
codify packet/report schemas, manual operation, permission policy, and
validation behavior before enabling autonomous backends.

## 3. Where execution sits in the planning tree

Workstreams organize meaningful efforts. Work items remain the concrete
executable units. The recursive planning-tree model lets LRH identify
ready executable leaves, but readiness alone should not grant execution
authority.

Execution begins only after selection:

```text
Project / Workstream / Work Item planning tree
  -> selected executable leaf
  -> run packet
  -> bounded branch-level run
```

A selected leaf should carry enough context to define an execution
contract: parent workstream, acceptance criteria, allowed paths,
validation commands, risk level, expected evidence, and explicit
non-goals. LRH may derive defaults from workstream and work-item
metadata, but the run packet is the concrete boundary for one run.

The existing precedence principle still applies: repository control-plane
artifacts guide runtime behavior, and runtime observations may produce
evidence or reports but must not silently redefine project intent.

## 4. Bounded branch-level agency

### Branch containment

Future automated execution should be contained in an agent-owned branch.
The recommended namespace is:

```text
agents/<backend>/<workstream-or-work-item>
```

Examples:

```text
agents/codex/WI-WORKSTREAM-SNAPSHOT-MVP
agents/manual/WS-EXECUTION-FRAMEWORK-PILOT
agents/fake/WI-EXAMPLE-SMOKE
```

The exact slugging rules can be defined later, but the namespace should
make ownership and backend visible at a glance. Branch containment is not
a complete sandbox, but it gives LRH and repository maintainers a simple
reviewable boundary: proposed changes are isolated until a human or
policy-approved merge occurs.

### Pull request as stabilization boundary

The pull request is the unit where execution output becomes reviewable.
The branch may contain code, documentation, evidence stubs, run reports,
and execution records. CI results, review comments, and requested changes
attach to the PR rather than to an opaque agent session.

A backend may respond to CI and review feedback only inside a bounded
loop. A future run packet should specify limits such as:

```yaml
stabilization:
  max_ci_iterations: 3
  max_review_iterations: 2
  max_elapsed_minutes: 90
  stop_on_new_scope: true
```

When a limit is reached, the backend stops and the run report records the
remaining action items. The agent does not keep trying indefinitely, does
not expand scope to make the PR pass, and does not merge its own work.

### Least-privilege token model

Future execution backends should receive the least authority required for
the selected run. A default token posture should allow work on the
agent-owned branch and PR comment/status interaction, but should not allow
protected-branch writes, release publishing, secret mutation, or elevated
workflow dispatch unless a repository policy explicitly grants those
capabilities for the run.

Unsafe workflow permissions deserve special caution. By default, LRH
should avoid privileged PR workflows and any pattern where unreviewed
agent-authored code can obtain repository secrets. Elevated permissions
must be an explicit policy decision recorded in the run packet or its
controlling workstream, not an ambient backend default.

## 5. Run packets and run reports

### Run packet

A run packet is the proposed future artifact that turns a selected leaf
into an executable contract. It should be human-readable and suitable for
both manual and backend-driven execution.

A packet should include, at minimum:

- selected workstream/work-item IDs and source paths;
- goal and non-goals;
- allowed paths and forbidden paths;
- allowed commands and required validation commands;
- evidence expectations;
- branch namespace and PR target;
- backend mode (`manual`, `agent`, `fake`, or later adapters);
- token/permission posture;
- budget and elapsed-time caps;
- maximum CI/review iteration counts;
- stop conditions; and
- closeout questions the final report must answer.

Illustrative shape:

```yaml
run_packet:
  id: RUN-PACKET-EXAMPLE
  selected_leaf: WI-EXAMPLE
  parent_workstream: WS-EXAMPLE
  branch: agents/codex/WI-EXAMPLE
  target_branch: main
  mode: agent
  allowed_paths:
    - src/lrh/example/
    - tests/example/
  forbidden_paths:
    - .github/workflows/
  validation_commands:
    - scripts/test
  evidence_expected:
    - test output
    - final run report
  budget:
    max_elapsed_minutes: 90
    max_backend_spend_usd: 10
  stabilization:
    max_ci_iterations: 3
    max_review_iterations: 2
  gates:
    merge: human_or_policy
    release: human_or_policy
    publish: human_or_policy
    closeout: human_or_policy
```

### Run report

A run report is the durable summary of what happened during one run. It
should link to the run packet, branch, PR, commits, validation output,
CI results, review trace, evidence records, and final assessment.

The final assessment should use a constrained outcome vocabulary:

- `done_with_evidence` — the run satisfied acceptance criteria and cites
  independent evidence such as passing validation, review, screenshots,
  metrics, logs, or reports;
- `done_with_human_verification_steps` — the run completed its proposed
  changes but requires named human checks before merge or closeout;
- `not_done_with_action_items` — the run stopped with a clear remaining
  action list; or
- `infeasible_or_rejected_with_rationale` — the run could not or should
  not proceed, with rationale and any evidence gathered.

The report is not a marketing summary. It should make unfinished work,
failed validation, scope deviations, and human verification needs visible.

## 6. Backend-neutral execution contract

The execution framework should remain backend-neutral. A future adapter
contract should let LRH hand a run packet to different executors without
changing the control-plane model.

A backend adapter should be able to:

- declare capabilities and permission requirements;
- accept a run packet;
- prepare or reuse the agent-owned branch;
- perform bounded work under the packet constraints;
- surface CI/review feedback without hiding it;
- stop on budget, time, iteration, scope, or policy limits;
- return structured run status and transcript references; and
- produce or help populate the final run report.

Manual mode must use the same contract. A human executing a packet should
create the same branch/PR/report/evidence shape as an agent backend, even
if the human performs every step manually. This keeps manual-mode parity
from being a fallback story and makes it the baseline semantics for the
future runtime.

The historical layer documents in this proposal set use names such as
`RuntimeBackend`, `RuntimeRequest`, and `RuntimeResult`. Those remain
useful concepts, but later implementation should reconcile them with the
run packet / run report boundary before committing to public APIs.

## 7. Evidence, observability, and lifecycle history

Evidence and observability should remain separate.

Observability captures what happened during the run: transcripts, spans,
logs, costs, command outputs, CI attempts, and review-loop iterations.
These records may be verbose and operational.

Evidence is the durable project-control claim: tests passed, review was
performed, screenshots match expectations, a report was produced, a
metric threshold was met, or a human verification step remains. Evidence
should cite observability artifacts when useful, but it should not be
replaced by raw traces.

Typed lifecycle transitions remain valuable, especially for workstream
stage changes and run status changes. Where LRH records transitions, the
history should be append-only. A rerun or stabilization iteration should
append a new event rather than rewriting prior outcomes.

## 8. Human and policy gates

The branch-level execution model draws a hard line between stabilization
and authority.

Backends may be allowed, within a packet, to:

- edit allowed paths on an agent-owned branch;
- run allowed commands;
- push commits to the agent branch;
- open or update a PR;
- respond to CI failures within iteration limits; and
- respond to review feedback within iteration limits.

Backends should not be allowed by default to:

- merge into protected branches;
- tag releases;
- publish packages;
- mutate secrets;
- approve their own PRs;
- close workstreams or work items as completed; or
- reinterpret project goals beyond the selected packet.

Merge, release, publish, and workstream/work-item closeout require a
human or explicit policy gate. A policy gate may eventually automate a
decision, but it must be reviewable as policy, not hidden inside agent
prompting.

## 9. Cross-cutting invariants

### Manual-mode parity

For every workflow that an agent backend can perform, there must be a
documented manual workflow that a human can execute while producing
structurally equivalent artifacts: run packet, branch or documented patch
source, pull request or review bundle, validation output, evidence, and
run report.

Manual mode is not merely a hedge against agent failure. It is the design
pressure that keeps LRH from depending on a vendor-specific execution
system for its core semantics.

### Repository-as-control-plane

Authoritative state lives in committed Markdown and YAML in the
`project/` directory. Local runtime state, external dashboards, backend
session logs, and CI-provider records may provide supporting data, but
they must not silently override repository artifacts.

The repository should explain:

- which leaf was selected;
- what packet constrained the run;
- which branch and PR carried the work;
- what evidence was produced;
- what the final assessment was; and
- which human or policy gate made merge/closeout decisions.

### Anti-laundering posture

Automation must not launder uncertainty into completion claims. Passing
CI, an agent-authored summary, or multiple correlated model reviews are
not enough by themselves. LRH should require independent evidence,
review trace, and explicit final assessment language before status or
closeout claims are made.

## 10. Build vs. buy positioning

LRH's differentiators remain the control plane, planning-tree semantics,
evidence model, and repository-native audit trail. Runtime engines,
agent SDKs, CI providers, PR APIs, observability libraries, and MCP
bridges are substitutable infrastructure.

The framework should therefore build:

- run packet and run report semantics;
- lifecycle and gate vocabulary;
- evidence expectations;
- manual-mode equivalent workflows;
- backend adapter boundaries; and
- project-control integration.

It should borrow or wrap:

- agent runtimes;
- CI and source-hosting APIs;
- telemetry libraries;
- MCP servers and bridges; and
- review surfaces.

The earlier version of this proposal named Claude Agent SDK, MCP,
OpenTelemetry GenAI conventions, OpenLLMetry, Langfuse, spec-kit,
OpenSpec, LangGraph, and robotics bridge substrates. Those references
remain useful background, but this refined proposal does not require LRH
to bind its execution model to any one vendor, API, or agent framework.

## 11. Risks and mitigations

### Risk 1 — Excessive agency

An execution backend could expand scope, keep iterating, or make changes
outside the intended task. Mitigation: branch containment,
least-privilege tokens, explicit run packets, allowed paths/commands,
bounded CI/review loops, budget/time caps, stop conditions, and human or
policy gates for merge and closeout.

### Risk 2 — Automation laundering

Agent summaries, correlated model reviews, or green checks can create a
false impression of independent completion. Mitigation: require
independent evidence, CI results, review trace, and a final run report
with constrained outcome vocabulary and visible human verification steps.

### Risk 3 — Cost surprise

Agent execution and repeated stabilization attempts can cost real money.
Mitigation: per-run budgets, elapsed-time caps, explicit maximum
iteration counts, stop-on-new-scope behavior, and run reports that record
why a loop stopped.

### Risk 4 — Backend or vendor coupling

A design tied too closely to one SDK, provider, source host, or CI system
would make LRH brittle. Mitigation: a backend-neutral adapter contract,
manual-mode equivalent artifacts, capability declarations, and a
repository-control model that remains useful without any autonomous
backend.

### Risk 5 — Unsafe workflow permissions

Privileged PR workflows can expose secrets or let unreviewed code gain
more authority than intended. Mitigation: avoid privileged PR workflows
by default, deny protected-branch writes and secret mutation to execution
backends, and require explicit recorded policy for elevated permissions.

### Risk 6 — Scope creep

A selected task can become a broad refactor if the execution boundary is
unclear. Mitigation: the selected work item and run packet constrain
goals, non-goals, paths, commands, evidence, and closeout questions.
Stabilization loops stop rather than silently expanding the mission.

### Risk 7 — Agent behavior drift

Agent behavior may change across model versions, prompts, toolchains, or
execution backends. Mitigation: adapter capability declarations, packet
constraints, transcript/observability retention, structural validation of
reports and evidence, and manual-mode parity for comparison.

## 12. Adoption plan

This proposal should be implemented, if adopted, in narrow stages:

1. **Design/schema stage** — define run packet and run report schemas as
   project-control artifacts. Include manual examples first.
2. **Manual-mode stage** — document and support branch/PR/report flows
   that humans can execute from a packet without autonomous backends.
3. **Policy stage** — define token, branch, PR, permission, and gate
   policies. Keep elevated permissions opt-in.
4. **Adapter stage** — introduce a fake backend and one constrained real
   backend behind the same contract.
5. **Stabilization stage** — add bounded CI/review iteration handling
   with maximum counts and stop conditions.
6. **Evidence stage** — connect run reports, validation outputs, review
   traces, and evidence records to workstream/work-item status.
7. **Closeout stage** — define human/policy merge and closeout gates for
   resolved work items and workstreams.

A recommended next concrete workstream is an execution-framework
workstream artifact that plans the packet/report schema and manual-mode
pilot before any autonomous backend work.

## 13. Open questions

- What is the exact on-disk location for run packets and run reports:
  under `project/runs/`, under related workstreams, or both?
- Which fields are required in the first run packet schema, and which are
  advisory until validation matures?
- How should LRH represent a manual run that produces a patch without a
  source-hosted pull request?
- What branch slug rules avoid collisions while preserving readability?
- Which CI/review feedback is safe for a backend to address without
  re-approval, and which feedback requires a new packet?
- How should policy gates be represented so they are auditable but not
  over-engineered?
- How should existing prompt execution records relate to future run
  reports?

## 14. Reading order and document index

### Recommended reading order

For the updated branch-contained execution framing, read this umbrella
first. Then treat the older layer documents and appendix as retained
background that still contain useful concepts, but not final API
commitments.

1. This document (updated umbrella).
2. `03_layer3_workstream_orchestration.md` for lifecycle and transition
   background.
3. `04_layer4_agent_runtime.md` for runtime/backend abstraction
   background.
4. `05_layer5_observability_and_evidence.md` for the evidence and
   observability split.
5. `06_layer6_mcp_bridges.md` for bridge-adapter concerns.
6. `01_layer1_control_plane.md` and `02_layer2_templates.md` for the
   original workstream-control design context.
7. `appendix_b_lcats_corpora_analysis.md` as a historical worked
   example.

### Document index

```text
project/design/proposals/proposed/workstream-execution-framework/
  README.md                                  # set-level index
  00_proposal.md                             # updated umbrella proposal
  01_layer1_control_plane.md                 # original control-plane layer background
  02_layer2_templates.md                     # original template layer background
  03_layer3_workstream_orchestration.md      # original orchestration layer background
  04_layer4_agent_runtime.md                 # original runtime layer background
  05_layer5_observability_and_evidence.md    # original observability/evidence background
  06_layer6_mcp_bridges.md                   # original MCP bridge background
  appendix_b_lcats_corpora_analysis.md       # historical worked example
```

## 15. References

Citations inline in the older layer documents use the bracketed keys
below. URLs are included so a reader can verify the claim against an
authoritative source.

[cas]: https://github.com/anthropics/claude-agent-sdk-python
"Claude Agent SDK (Python) — anthropics/claude-agent-sdk-python"

[mcp]: https://modelcontextprotocol.io/
"Model Context Protocol — modelcontextprotocol.io"

[otel-genai]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
"OpenTelemetry — Semantic conventions for generative AI systems"

[openllmetry]: https://www.traceloop.com/docs/openllmetry
"OpenLLMetry by Traceloop — OpenTelemetry-based LLM instrumentation"

[langfuse]: https://langfuse.com/
"Langfuse — open-source LLM engineering platform"

[spec-kit]: https://github.com/github/spec-kit
"github/spec-kit — Spec-Driven Development toolkit"

[openspec]: https://github.com/Fission-AI/OpenSpec
"Fission-AI/OpenSpec — lightweight spec-driven framework"

[ros-mcp]: https://github.com/robotmcp/ros-mcp-server
"robotmcp/ros-mcp-server — ROS/ROS2 MCP server"

[arena-bench]: https://github.com/ignc-research/arena-bench
"ignc-research/arena-bench — benchmarking suite for navigation"

[arena-rosnav]: https://github.com/Arena-Rosnav
"Arena-Rosnav (Arena 3.0) — collaborative navigation platform"

[Claude Agent SDK (Python)][cas] · [Model Context Protocol][mcp] ·
[OpenTelemetry GenAI semantic conventions][otel-genai] ·
[OpenLLMetry][openllmetry] · [Langfuse][langfuse] ·
[github/spec-kit][spec-kit] · [Fission-AI/OpenSpec][openspec] ·
[robotmcp/ros-mcp-server][ros-mcp] · [arena-bench][arena-bench] ·
[Arena-Rosnav][arena-rosnav].

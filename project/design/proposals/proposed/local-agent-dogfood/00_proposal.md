---
id: PROP-LOCAL-AGENT-DOGFOOD
type: design_proposal
title: "Local Agent Dogfood and a Durable Session Boundary"
status: proposed
created_on: "2026-09-24"
updated_on: "2026-09-25"
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/execution_framework_mvp.md
  - project/design/proposals/proposed/workstream-execution-framework/04_layer4_agent_runtime.md
  - project/design/proposals/proposed/workstream-execution-framework/06_layer6_mcp_bridges.md
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
  - project/design/proposals/adopted/lrh-assistants/00_proposal.md
---

# Local Agent Dogfood and a Durable Session Boundary

## Summary

Build a local-first agent through a sequence of useful, measured prototypes.
Start with a work-item briefing assistant; then let it investigate a bounded
source corpus. Keep transcripts, provenance, budgets, and human evaluation from
the first prototype. Expand authority only when the preceding stage justifies it.

The long-term abstraction is an LRH-owned, durable session with a model-independent
semantic API. The native local runner and third-party agents use that same
authority boundary. MCP is the first agent-facing binding; vendor conversation
formats remain adapters. A separate reviewer contributes semantic judgment, while
deterministic policy and a constrained executor enforce permissions.

This is a **draft planning package for joint iteration**, not an adopted API or
authorization to run an agent. Only two initial implementation leaves are filed:
`WI-LOCAL-AGENT-001` and `WI-LOCAL-AGENT-002`, coordinated by
`WS-LOCAL-AGENT-DOGFOOD` under `WS-EXECUTION-FRAMEWORK`. The stage-0 lane was
later approved and `WI-LOCAL-AGENT-001` activated; see
[Stage-0 Lane Approval](#stage-0-lane-approval). `WI-LOCAL-AGENT-002` is not
active. No runtime code, dependencies, assistant scheduling, or serving
mutations are introduced by this package.

## Background / Motivation

Proprietary agent interfaces and export behavior change independently of LRH.
Cost and capacity limits also force work across several vendor sessions. LRH
should retain project context, policy, evidence, and continuity while allowing
the user to choose a local model or a third-party coding agent.

The Gemma coding-agent article is a starting experiment, not evidence that a
particular model or framework satisfies LRH's needs. A compact model may be useful
for briefing before it is reliable enough for tool use. The first question is
whether a local assistant saves human effort on actual LRH/LCATS work compared
with existing deterministic context tools and one model call.

The staged approach also limits speculative infrastructure: exportable logs do
not require a public protocol, and a useful briefing does not require autonomous
execution, a desktop application, or fine-tuning.

## Prior Art Check

Repository findings below are anchored to main commit
`8603b6514329ea242294da420aa448d2fc959fd1`. Paths and line numbers refer to that
snapshot. Recheck these contracts when activating a leaf.

| Existing source | Finding and consequence |
| --- | --- |
| `project/design/execution_framework_mvp.md:3-29,53-85` | Canonical architecture prioritizes manual contracts and safe-default surfaces. This proposal requests a separately approved experimental lane; it does not silently revise that priority. |
| `project/design/proposals/proposed/workstream-execution-framework/04_layer4_agent_runtime.md:15-34,77-85` | Existing proposed `RuntimeBackend` wraps Claude/manual/fake backends and explicitly excludes custom loops, a new permission system, and non-Claude backends. A local runner is a proposed extension; production adoption requires reconciling those non-goals. |
| `project/design/proposals/proposed/workstream-execution-framework/06_layer6_mcp_bridges.md:15-28` | Existing bridges expose external tools to LRH. The proposed agent-facing MCP adapter exposes LRH sessions to external agents: a complementary direction, with a separate trust boundary. |
| `project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md:127-184` | Layered constitutional review, capability policy, and sandboxing are already proposed. Extend that design before adding execution, rather than introducing a competing safety subsystem. |
| `src/lrh/assist/snapshot_cli.py:53-68`; `src/lrh/assist/run_packet.py:25-68` | Work-item snapshots and non-mutating, readiness-checked run packets already exist. Reuse their semantics and preserve their diagnostics; never manufacture readiness to get a packet. |
| `src/lrh/prompt_workflow_sessions.py:1-12,35-55` | Session identity and archive reconciliation exist. Host/child transcript identity is not an action-execution session contract. Link these identities later without replacing their meaning. |
| `project/workstreams/active/WS-LRH-ASSISTANTS.md:41-49,84-101` | Assistant roles have a staged plan and explicit archive/execution-tree gates. This experiment is a runner feasibility lane, not delivery of those assistant stages or permission to bypass their gates. |
| `experimental/README.md:3-17` | Temporary code belongs outside the package and default tests; private captures stay out of Git; promotion requires separate reviewed work. Follow this policy. |
| `project/design/backlog.md:1614-1659` | A separate `/lrh-assess` skill was judged unwarranted. Measure against deterministic readiness/context before inventing another assessment workflow. |

Also inspected the proposed parent workstream, the resolved
`WS-SESSION-ARCHIVE-SYNC`, and `WI-AGENT-BRANCH-CONTAINMENT`. Archive work has
advanced since some assistant blocker prose was written; this PR neither fixes
that prose nor unblocks assistant/runtime work. Branch containment remains a
separate dependency before mutation-capable work.

LCATS provides a useful organizational precedent:
[durable experiments](https://github.com/xenotaur/LCATS/tree/main/experiments)
and [temporary package experiments](https://github.com/xenotaur/LCATS/tree/main/lcats/experimental).
LRH currently has the temporary `experimental/` convention, but no tracked
`experiments/` tree at the inspected commit. The first implementation leaf must
document that new evidence convention explicitly. It must not import LCATS's
package placement into LRH's production package.

**Duplication decision:** keep this as a child of the existing execution
workstream. Its distinct deliverable is measured local-model usefulness and a
small experimental runner, not another production orchestrator, assistant role
model, session archive, or guardrail design.

## Design Decisions

### 1. Start with evidence, then increase authority

| Stage | Useful result | Added authority | Gate to the next stage |
| --- | --- | --- | --- |
| 0 — Brief | Explain one selected work item, constraints, evidence, and unresolved questions with source references. | One local inference over an explicitly approved static context packet; no agent tools. | Human assessment of usefulness, groundedness, latency, and export completeness. |
| 1 — Investigate | Answer questions requiring a few additional repository reads. | Bounded read/search of a preselected immutable corpus. | Demonstrable benefit over stage 0, with boundary and failure tests passing. |
| 2 — Draft | Produce a proposed patch and validation plan as artifacts. | Write only to the private artifact store; no repository apply or command execution. | Human patch review and evidence that proposals reduce work. |
| 3 — Execute under guardrails | Apply a reviewed patch and run bounded validation in an isolated workspace. | Explicit capabilities, independent action review, human escalation, sandboxed execution. | Durable action ledger, crash/retry reconciliation, containment and revocation demonstrated. |
| 4 — Resume and hand off | Resume work or attach a different agent through the same LRH session. | Authenticated session access and serialized action ownership; MCP adapter. | Two independent clients pass semantic conformance and interruption tests. |
| 5 — Local workbench | Inspect sessions, evidence, permissions, approvals, and model choices in a local UI. | Explicit user actions through the same API. | Preserve the read-only default and test the complete user workflow. |

Durability starts at stage 0. Stage 3 needs a transactional action ledger before
any side-effect dispatch; stage 4 adds production run integration and reliable
multi-client access. These are not permissions to postpone safety until stage 4.
Stages are capability gates, not calendar promises. A negative evaluation can
complete a leaf successfully while stopping expansion.

Only stages 0 and 1 are currently decomposed into work items. Later stages require
fresh design review and executable leaves. A local web workbench can precede a
Mac app wrapper; private remote access follows local validation. Public service,
multi-user tenancy, quotas, abuse handling, and operational support require a
separate design. Linux/Windows portability is an interface requirement, not a
claim that Mac testing validates those platforms.

### 2. One evolving prototype with small typed boundaries

Use `experimental/local_agent/` for one evolving Python prototype, with an
explicit CLI and opt-in tests outside normal package discovery. Do not maintain
six copied prototypes. Keep stage behavior selectable for fair comparisons.

Initial boundaries are small internal Protocols/dataclasses:

- **Context provider:** adapts existing LRH snapshots/readiness/packets for one
  explicitly selected project and work item. An unready item can be explained,
  with its diagnostics intact; it cannot be presented as execution-ready.
- **Model adapter:** local inference with a pinned model/quantization and
  recorded runtime version. Ollama is the initial candidate, not a required
  production dependency. Gemma is a candidate to measure, not the API's identity.
- **Runner:** one call at stage 0; a bounded explicit loop at stage 1. It never
  owns credentials or gets direct filesystem, shell, or network execution tools.
- **Dispatcher/policy:** validates typed requests and immutable budgets before
  any tool handler. Model output cannot rewrite policy or widen the source set.
- **Recorder:** trusted persistence of inputs, outputs, outcomes, and provenance
  to a private directory, separate from model-accessible repository sources.
- **Evaluator:** records human corrections and comparative usefulness; generation
  completion never constitutes human acceptance or project status evidence.

| Option | Advantage | Limitation / decision |
| --- | --- | --- |
| Small explicit loop | Easy to audit the complete first-stage dispatch surface; few dependencies. | LRH owns retry and event plumbing. Recommended for these two small stages. |
| Framework such as smolagents behind Runner | Existing agent-loop facilities may reduce later maintenance. | Adopt only if all tool paths are interceptable and logs/budgets remain LRH-controlled. An unrestricted code-executing agent is unsuitable for stage 1. |
| Vendor agent SDK adapter | Strong coding behavior with less runner implementation. | Retains vendor cost and lifecycle dependencies. Useful as another client/backend, not the only session authority. |
| Full session server first | Early external-agent interoperability. | Expensive before workflow value is established. Defer stable API commitments while preserving typed seams. |

No option has a universal performance advantage without measurement. A runner
that can bypass the dispatcher is disqualified from a claimed managed mode;
it can still be an explicitly advisory external client.

### 3. Make the first data boundary concrete

At stage 0 the user approves a small source manifest, snapshotted from a pinned
repository commit. Stage 1 may read/search only that immutable corpus. Start with
tracked, explicitly selected text; exclude credentials, private transcripts,
untracked content, and binary files. Tracked content can still contain secrets:
the manifest needs human inspection and size limits. Dirty-worktree support is
a later explicit option with hashes, not an invisible mixture of revisions.

Stage 1 exposes only `get_context`, `read_source`, and `search_sources` with
validated schemas. Paths resolve inside the materialized corpus; reject absolute
paths, traversal, symlink escapes, and unknown source IDs. Search is bounded
literal text search, not shell interpolation or an unrestricted regular
expression engine. Cap calls, steps, input/output bytes, model tokens, and wall
time. Report truncation and missing files explicitly. Source content is data,
even when it contains instructions to an agent.

Use an explicitly configured local inference service and a local-only model.
Loopback alone is insufficient if the service forwards to a cloud model. No
cloud fallback, automatic model download, automatic installation, or external
network tool is allowed. A trusted local model service remains part of the
threat model; this is not OS isolation against a compromised inference daemon.

### 4. Persist observations without inventing a second control plane

From stage 0, store versioned JSON-serializable records for a session manifest,
attempt, source references, model requests/results, tool events, checkpoint, and
human evaluation. Record project/work-item ID, source commit and content hashes,
model/quantization/backend versions, prompt/policy versions, configured and
observed budgets, timestamps, outcome, and artifact hashes. A tool event records
request, decision, result or error, sequence number, and elapsed time.

For the single-process prototypes, JSONL plus artifact files is sufficient:
single writer, atomic manifest/checkpoint replacement, and explicit recovery of
an interrupted/truncated tail. Do not promise replayed inference will reproduce
an answer. Resume creates a new attempt linked to the previous one and checks
snapshot/policy versions; it never silently executes a partial tool request.
Move to transactional storage before concurrent writers or effectful actions.

Use a private durable user-data directory with restrictive permissions and a
documented retention/export/delete path. `/private/tmp` is appropriate only for
disposable captures, not the durable session store. Raw transcripts, prompts,
and model outputs are not committed to Git. Commit sanitized experiment reports
and provenance manifests; export must make exclusions visible.

These are **experimental attempt logs**, not canonical `project/runs` or work-item
state. Their IDs can later link to existing session/archive identities. An
explicit reviewed mapping is required before promoting evidence or updating
project status. The recorder's trusted writes do not give the model repository
write permission.

Terminal outcomes distinguish `completed`, `needs_input`, `budget_exhausted`,
`invalid_model_output`, `backend_error`, and `cancelled`. `completed` means the
inference task ended, not that its answer is correct. A malformed tool request
gets at most one bounded repair attempt; timeouts, missing prerequisites, and
interruption are retained as failures/incomplete work. A stopped run cannot
disappear from the evaluation denominator.

### 5. Grow a native semantic Session API; bind it to MCP first

Do not freeze endpoint names in the prototypes. Preserve the conceptual
separation among an authenticated actor, durable LRH session, run/attempt,
vendor conversation, and transport connection. The session survives connections
and model changes; a vendor transcript is an attachment, not authoritative state.

A later versioned API should cover capabilities, session creation/attachment,
context inspection, proposed actions, action decisions, execution status,
event cursors, artifacts, cancellation, and evidence submission. The local CLI,
UI, native runner, and MCP server call the same service layer. A separate REST
server is optional, not a prerequisite for a native API.

The public contract must specify typed schemas, errors, authorization scopes,
session/action state machines, idempotency keys, optimistic revisions,
capability negotiation, event ordering/retention, and compatibility policy.
Provide conformance tests and a second independently written client before
claiming anyone can implement it. MCP handles connection/tool exposure; it does
not itself define LRH durability, execution authority, or workflow semantics.

| Connection mode | LRH guarantee |
| --- | --- |
| Advisory external agent | LRH protects its own tools; it cannot govern actions the agent performs elsewhere. |
| Managed native agent | All model-requested actions pass through LRH policy and executor boundaries. |
| Brokered external agent | Equivalent mediation only if its workspace/tools/credentials prevent bypass and that containment is tested. |

Skills/plugins teach an agent how to attach and use the tools. They improve
usability; they are not an enforcement mechanism. The external agent may retain
its own reasoning/session language, but must use LRH references, decisions, and
capabilities for actions inside an LRH-managed runtime.

### 6. Put constitutional judgment inside an enforceable safety design

The early prototypes approve a restricted read corpus and enforce each read
deterministically. They do not claim to implement the full second-agent review
design. Before stage 3, reconcile and adopt the existing constitutional sandbox
envelope with an explicit action contract:

1. An agent proposes a normalized action with resources and expected effects.
2. Hard policy validates scope/budgets; a separate reviewer assesses intent,
   instruction conflicts, disclosure, and semantic risk from bounded context.
3. Required human decisions are collected. A reviewer may deny/escalate and may
   not grant authority forbidden by policy; reviewer failure denies or pauses.
4. The executor validates a short-lived decision bound to the exact action digest,
   actor, workspace revision, policy version, and capability before dispatch.
5. Persist the decision before dispatch and record results and verification after.

Every externally effectful operation must use this path, including writes,
commands, network access, publication, and robot actions. Define read/disclosure
classes explicitly; a read that exposes private data outside its authorized
boundary is not exempt simply because it does not modify a file. The trusted
recorder is a narrow platform capability, not a generic write tool.

The reviewer has no execution capability and cannot modify its own constitution.
Different context and, where feasible, a different model reduce shared failure
modes but do not prove independence or safety. Log decisions and concise reasons,
not hidden chain-of-thought. Human escalation and sandbox enforcement remain
necessary; a second model does not guarantee alignment.

Before effects, specify stale-grant rejection, revocation, cancellation races,
crash recovery, and reconciliation of unknown outcomes. Idempotency is not an
exactly-once guarantee for arbitrary external effects. Physical robotics needs
additional hardware/interlock and domain-specific safety work; this coding pilot
does not authorize robot control.

### 7. Evaluate on work the user actually wants done

Prepare approximately 12 small tasks across LRH and LCATS, including readiness
explanations, evidence gaps, finding relevant code, and explaining a narrow
implementation change. Pin inputs; separate tuning tasks from held-out tasks.
Compare deterministic LRH output/manual completion, a single local model call,
and (stage 1) bounded tool use with the same task and source access. Counterbalance
task order to reduce human learning effects and record unequal context budgets.

Before live runs, record hardware/RAM, model and quantization, context limits,
latency/resource ceilings, and a scoring rubric. Measure useful answers without
material correction, unsupported assertions, whether citations actually support
claims, correction/review time, end-to-end human effort, latency, retries,
resource use, and failures. Report raw per-task scores and all stopped attempts.

Proposed advancement rule: useful results on a clear majority of pilot tasks,
acceptable held-out quality, lower median human effort than the chosen baseline,
acceptable latency on the target Mac, no accepted critical fabricated project
status, and no boundary escapes in the adversarial suite. The owner must set the
numeric usefulness and latency thresholds before running the evaluation; do not
tune them after seeing results. A small pilot is evidence for a next experiment,
not statistical assurance of safety. Stage 1 must justify its extra complexity
over the single-call baseline. Failure is a valid result and may lead to a better
model, narrower task, or stopping this workstream.

## Non-Goals

- A production agent runtime, public protocol, stable SDK, or immediate MCP server.
- Automatic work-item transitions, evidence acceptance, merge, release, or publish.
- Changing the default `lrh serve` permission surface or enabling assistant stages.
- Shell execution, patch application, arbitrary tools, or network access in the
  first two prototypes.
- Autonomous multi-agent scheduling or physical robot control.
- A model leaderboard, commercial service, or guaranteed local-model equivalence
  to Claude, Codex, or Antigravity.
- Fine-tuning before a usable baseline and a curated, permissioned evaluation set.

## Implementation Plan

1. Iterate on this draft, resolve the initial scope/privacy/hardware questions,
   and explicitly approve the experimental lane. Adoption must reconcile its
   relationship to the canonical execution design; this PR does not rewrite it.
2. Select and activate `WI-LOCAL-AGENT-001`: static-context briefing CLI,
   durable export, deterministic fake-backend checks, and a reproducible pilot.
3. Review the findings. Activate `WI-LOCAL-AGENT-002` only after an explicit
   decision that read/search access is worth testing; completion of 001 alone
   is not automatic authorization.
4. Decide stop/revise/promote. Promotion into `src/lrh/`, a new production extra,
   and future stages require separately scoped work and reviewed contracts.

Temporary code lives in `experimental/local_agent/`. Stage 0 introduces a
documented `experiments/` convention and the next available numbered experiment
directory (for example `experiments/01_local_agent_briefing/` if still available).
Each durable experiment includes purpose, task corpus or reproducible references,
code commit, setup, manifest, commands, sanitized results, limitations, and a
human decision. Stage 1 adds its own comparable results without overwriting stage
0. Full raw logs stay in the private store. Avoid adding `prototypes/` or
`examples/` as competing homes for the same code.

Later: native Session API and MCP conformance; local web UI and optional desktop
packaging; private remote access; separately designed multi-user service. Build
an opt-in dataset from reviewed runs with provenance, permissions, redaction,
quality labels, and train/evaluation separation. Fine-tune only if measured error
patterns warrant it, and compare against prompt/context/model changes first.
Pin and version model artifacts and retain rollback. MIT licensing for harness
code does not relicense model weights, datasets, or third-party dependencies;
check their terms before distribution.

## Stage-0 Lane Approval

Recorded 2026-09-25 by the owner after a read-only readiness review. This
section approves a narrow slice of the proposal; the proposal as a whole remains
`proposed`.

**Approved:**

- The isolated experimental lane for stage 0 only: tool-less, single-call local
  briefing under `experimental/local_agent/`, outside the package and default
  test discovery, with no project-state writes.
- Activation of `WI-LOCAL-AGENT-001` and `WS-LOCAL-AGENT-DOGFOOD`.
- Pre-registration of hardware, model digest, budgets, storage, task corpus, and
  criteria in `experiments/01_local_agent_briefing/` before any live run.

**Not approved:** stage 1 (`WI-LOCAL-AGENT-002`), later stages, the native
Session API and MCP binding (Decision 5), the constitutional execution contract
(Decision 6), and any production runtime or backend adoption. Each needs its own
decision.

**Evidence rule (refines Decision 4):** raw transcripts, context packets, exact
prompts, and raw model responses stay in the private store. Parsed briefing
records that a human has scored may be committed as experiment evidence. Each
one carries its scores and claim annotations, passes a sensitivity scan and PR
review, and is labelled as a model output record rather than project state.
Committed records live under `experiments/`, outside `project/`.

**Decision rule (refines Decision 7):** the owner pre-declares both a binding
floor and advisory targets before live runs. Failing the floor means stop or
revise. Targets are reported as met or unmet and inform, but do not decide, the
owner's stop/revise/proceed choice. Each miss is classified as context-limited,
model-limited, or task-limited. Context-limited misses are evidence for
evaluating stage 1, consistent with `WI-LOCAL-AGENT-002`'s activation condition.

**Local-only inference:** the model adapter requires a loopback endpoint and the
pinned local model digest, rejects remote or cloud-tagged models, and records
these checks per run. Disabling the inference service's cloud features is
optional defense in depth.

## Open Questions for Joint Review

For stage 0, the lane, static-context briefing, and assistant-gate questions
below are answered by the [Stage-0 Lane Approval](#stage-0-lane-approval). The
hardware, model, corpus, storage, and target choices will be pre-registered in
`experiments/01_local_agent_briefing/` before live runs. The questions stay
open for later stages.

- Which Mac/RAM configuration and locally installed model should define the first
  pilot? What are the predeclared latency and human-effort targets?
- Which LRH/LCATS work items are useful, safe to include, and suitable for held-out
  comparison? Is commit-only context adequate for the initial briefing?
- Approve static-context briefing first, or require a different narrow daily task?
- Where should private logs live, how long should they be retained, and which
  fields are excluded from shareable exports?
- Does adoption explicitly allow this isolated research lane ahead of production
  runtime readiness, while preserving the existing assistant-stage gates?
- Which existing run/session types should be reused when promoting the prototype,
  and which policy changes must accompany the non-Claude runtime extension?

## References

- [CODE Magazine: Local Vibe Coding with Gemma 4 12B](https://www.codemag.com/Article/2610021/Local-Vibe-Coding-with-Gemma-4-12B)
  — motivating example, not a dependency or validated LRH result.
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
  — candidate model integration surface.
- [smolagents documentation](https://huggingface.co/docs/smolagents/index)
  — alternative runner implementation to evaluate only if needed.
- [MCP architecture](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
  — transport/client/server context for a later agent-facing binding.
- [Robot Constitutions](https://arxiv.org/abs/2503.08663)
  — motivation for separate semantic review; reported experimental alignment is
  not a guarantee for LRH coding or robotics actions.
- [CODE Magazine: Fine-Tuning Large Language Models, Part 1](https://www.codemag.com/Article/2610031/Fine-Tuning-Large-Language-Models-Part-1)
  — deferred learning pathway after useful, permissioned run data exists.

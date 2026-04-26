---
id: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
title: Workstream Execution Framework
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
owner: anthony
related_focus:
  - FOCUS-BOOTSTRAP
related_roadmap:
  - ROADMAP-PHASE-02
supersedes: []
superseded_by: []
---

# Workstream Execution Framework — Top-Level Proposal

## Summary

This proposal introduces a **workstream** as a new typed artifact in the
Logical Robotics Harness (LRH) control plane and lays out a six-layer
execution framework that lets workstreams progress, mostly automatically,
from conception through closure while staying entirely auditable from a
Git checkout. A workstream is a coherent thread of work that sits between
`focus` and `work_items`, advances through eight explicit lifecycle stages
(`conceived → assessed → designed → planned → executing → reviewing →
closed`, with `abandoned` as an off-ramp), and accretes Markdown+YAML
artifacts under `project/workstreams/{bucket}/WS-{SLUG}/` as it moves.
Around that artifact, the proposal stacks six layers — control plane
extensions, first-party templates, the workstream orchestrator itself, an
agent runtime adapter, an observability + evidence split, and MCP backend
bridges — that together turn an LRH repository into something a Claude
Agent SDK runtime can drive while a human reviews the diff.

The proposal is structured deliberately so that each layer is small,
substitutable, and exercised by a worked example. Two non-negotiable
constraints run through every layer: **manual-mode parity** (every
workflow that an agent can perform must have a documented manual
equivalent that produces structurally identical artifacts) and
**repository-as-control-plane** (state lives in committed Markdown and
YAML — never in a side database, never in an external service that the
repo can't be reconstructed from).

This document is the umbrella; one detailed sub-proposal per layer
(`01_layer1_*.md` through `06_layer6_*.md`) defines the schemas, APIs,
modules, tests, and worked examples for that layer, and a Pass-B appendix
(`appendix_b_lcats_corpora_analysis.md`) walks a single workstream end to
end across all six layers.

## Table of contents

1. [Motivation](#1-motivation)
2. [Scope and non-goals](#2-scope-and-non-goals)
3. [Where workstreams sit in the existing model](#3-where-workstreams-sit-in-the-existing-model)
4. [The six-layer stack](#4-the-six-layer-stack)
5. [Cross-cutting invariants](#5-cross-cutting-invariants)
6. [Build vs. buy positioning](#6-build-vs-buy-positioning)
7. [Risks and mitigations](#7-risks-and-mitigations)
8. [Adoption plan](#8-adoption-plan)
9. [Open questions](#9-open-questions)
10. [Reading order and document index](#10-reading-order-and-document-index)
11. [References](#11-references)

## 1. Motivation

### Summary

LRH today has the bones of a control plane — typed models, frontmatter
validation, a precedence resolver, evidence and execution records — but
it has no first-class concept for "a piece of work that needs to advance
through stages over time, possibly with help from an agent." We've been
modeling that implicitly with `focus` plus a hand-curated cluster of
related work items, which works for one or two threads but breaks down
once a project has multiple parallel investigations, design efforts, or
deliverables in flight. The workstream concept fills that gap.

### Why now

Three forces make this the right time to introduce the abstraction:

The Claude Agent SDK has matured enough that wrapping it as a runtime
substrate is a reasonable bet rather than a research project — the SDK
exposes typed `query()` and `ClaudeSDKClient` interfaces, hooks for
PreToolUse/PostToolUse/Stop, structured outputs, and W3C trace-context
propagation that we'd otherwise have to build ourselves
([anthropics/claude-agent-sdk-python][cas]).

The Model Context Protocol has stabilized enough to be the bridge
substrate: MCP servers exist for ROS, browsers, filesystems, databases,
and dozens of other backends, and the MCP specification is now hosted
under the Linux Foundation as an open standard
([modelcontextprotocol.io][mcp]).

OpenTelemetry's GenAI semantic conventions have stabilized to the point
where instrumenting agent runs against a known schema is a defensible
default rather than a homegrown invention
([OpenTelemetry GenAI semconv][otel-genai]).

Borrowing these three substrates while keeping the *control plane* in
LRH — repo-native, Git-tracked, human-readable — is the strategic bet
this proposal locks in.

### Concrete pain we're solving

In the current LRH model, when a contributor wants to start a piece of
work that has a non-trivial lifecycle — e.g. "build a corpus-analysis
capability for LCATS" — they have to either jam everything into a single
work item (which loses staged structure) or scatter the work across
several work items connected only by `related_focus` (which loses the
"this is one coherent thread" framing). Neither captures stages,
gating, evidence-at-close, or the progression from a vague conception
to a finished review. Worse, when an agent helps, there's no place to
hang the agent's deliberation, the runtime trace, the cost budget, or
the structured findings. Workstreams give us all of that in one
artifact.

## 2. Scope and non-goals

### Summary

The proposal is intentionally larger than a single PR's worth of code,
but each layer ships independently. This section nails down what we
*are* committing to and what we are explicitly deferring.

### In scope

The proposal commits to:

A typed `Workstream` model in the control plane, mirrored by a directory
schema under `project/workstreams/`, with frontmatter as the
authoritative source of truth and bucket directories as a derived view —
matching the conventions LRH already uses for work items
(`project/design/repository_spec.md`, `project/work_items/README.md`).

A small in-house orchestrator that advances a workstream through its
stages, gated by mode and explicit `--confirm` flags, with an
append-only `transitions[]` audit trail in frontmatter.

A `RuntimeBackend` Protocol with three implementations — `claude` (wraps
the Claude Agent SDK), `manual` (records human work as if it were a
backend), and `fake` (for tests) — so the orchestrator can't tell who
actually did the work.

A telemetry layer that emits OTel-aligned spans on disk and an evidence
layer that produces durable Markdown records under `project/evidence/`,
with explicit extractors that turn traces into evidence.

A bridge layer that lets workstreams open MCP-backed sessions to
external systems (ROS, simulators, browsers) and record what those
sessions did as evidence.

CLI surface across all of the above (`lrh workstream`,
`lrh observability`, `lrh evidence`, `lrh bridge`).

### Out of scope (for this proposal)

Intentionally deferred: a hosted UI, a multi-tenant evidence service,
parallel orchestration of multiple workstreams in a single run, an
`OpenTelemetry`-collector-backed default (we'll start with JSON files on
disk and design the OTel backend but ship the file backend first),
distributed agent execution across machines, automated prompt
optimization, and any feature that requires synchronizing state between
LRH and an external server-of-record. The design preserves the doors
for these but does not walk through them.

## 3. Where workstreams sit in the existing model

### Summary

Workstreams are a new layer between **current focus** and **work
items**, refining a focus into one or more coherent threads of work
without replacing either concept. Existing LRH artifacts — focus,
work items, evidence, executions, contributors, principles, guardrails —
keep their current meanings; workstreams reference them.

### Precedence position

The proposal adds workstreams to the canonical precedence chain. Today
the chain is `principles → goal → roadmap → focus → work items →
guardrails → runtime` (see
`project/memory/decisions/precedence_semantics.md`). After this
proposal lands, the chain is:

```text
1. principles
2. goal
3. roadmap
4. focus
5. workstreams        # NEW
6. work_items
7. guardrails
8. runtime
```

This reflects the operational truth that a workstream narrows a focus
and groups work items, but is itself narrower than the focus that
spawned it. Layer 1 sub-proposal
(`01_layer1_control_plane.md`) specifies the precedence-resolver
changes; the precedence-semantics decision record is updated in
lockstep per the AGENTS.md "precedence maintenance note."

### Relationship to existing artifacts

A workstream **refines a focus** by carving out a coherent slice of it.
A focus may have zero, one, or many active workstreams — most early
focuses will have one. A workstream **groups work items**: each
work item becomes a step in a workstream's `plan.md` (Layer 2) or a
prompt in `prompts/` (Layer 3). Existing work items don't lose their
identity; they gain a `related_workstream` field analogous to today's
`related_focus`. A workstream **owns** an `executions/` directory of
prompt-execution records (existing PROMPTS.md schema, see Layer 3) and
**points at** evidence records under the project-level
`project/evidence/` (so evidence remains globally discoverable, not
buried inside workstreams).

### Worked example (one paragraph)

The LCATS project has `FOCUS-LCATS-CORPORA` covering "make the corpora
processing reliable." Today that focus might have a half-dozen related
work items pulling in different directions. After this proposal,
`FOCUS-LCATS-CORPORA` has two workstreams: `WS-LCATS-CORPORA-UPDATE`
(produce the next clean snapshot of the corpus) and
`WS-LCATS-CORPORA-ANALYSIS` (analyze the corpus for issues so the
update workstream knows what to fix). Each workstream walks the eight
stages independently, references its own work items, and produces its
own evidence — and the cross-workstream relationship is captured by a
`sibling_workstreams` field. The Pass-B appendix walks
`WS-LCATS-CORPORA-ANALYSIS` end-to-end as the canonical worked example
for this whole proposal.

## 4. The six-layer stack

### Summary

The execution framework is a stack of six layers, each with its own
sub-proposal and its own deliverable boundary. Layers communicate
through narrow Protocols so each layer can be substituted independently
and tested in isolation. The numbering matches the sub-proposal files.

### Layer 1 — Control plane extensions (existing code, mostly)

The control plane already loads, validates, and resolves projects;
Layer 1 adds workstream-aware loading, validation, snapshotting, and
precedence resolution. New module: `src/lrh/control/workstream.py` (and
schema entries under `project/design/schemas/`). New CLI: `lrh
workstream new|list|show|advance|resume|abandon|gates|tidy|validate`.
This is the smallest layer — most of it is incremental on existing
code. See `01_layer1_control_plane.md` for the schema and CLI.

### Layer 2 — Templates

LRH grows first-party Markdown templates for the per-stage artifacts a
workstream emits (`workstream.md`, `conception.md`, `assessment.md`,
`design.md`, `plan.md`, `prompts/`, `decisions/`). This is deliberately
**not** spec-kit's templates — see [build vs. buy](#6-build-vs-buy-positioning).
The templates live under `src/lrh/assist/templates/workstream/` and are
loaded as package resources, matching the package-owned template
direction documented in the repo-root README. See
`02_layer2_templates.md` for the template inventory.

### Layer 3 — Workstream orchestration (the new core)

A small in-house state machine that advances a workstream through its
stages. Modules under `src/lrh/workstream/`: `models.py`, `schema.py`,
`state_machine.py`, `loader.py`, `writer.py`, `orchestrator.py`,
`precedence.py`. The single load-bearing API is
`advance_workstream(project, ws_id, *, runtime, observer, mode,
rerun) -> AdvanceResult`. We **explicitly reject** LangGraph here:
once LRH owns all state in the repo, LangGraph's value evaporates. See
`03_layer3_workstream_orchestration.md` for the state machine, the
`AdvanceResult` taxonomy, the two-step manual-advance pattern, and the
parity tests.

### Layer 4 — Agent runtime

A `RuntimeBackend` Protocol with three implementations. Modules under
`src/lrh/runtime/`: `api.py`, `models.py`, `claude_backend.py`,
`manual_backend.py`, `fake_backend.py`, `hooks.py`, `permissions.py`,
`budget.py`, `transcript.py`. The Claude backend wraps
`anthropics/claude-agent-sdk-python` ([cas][cas]); the manual backend
lets a human do the work and reports the same `RuntimeResult` shape;
the fake backend is for tests. See `04_layer4_agent_runtime.md` for
the Protocol, the `Outcome` enum, and the hook wiring.

### Layer 5 — Observability and evidence (split into 5a and 5b)

Two top-level packages with a unidirectional dependency: 5a
`src/lrh/observability/` produces ephemeral spans and traces,
JSON-on-disk by default with an OTel backend designed but not first;
5b `src/lrh/evidence/` produces durable Markdown records under
`project/evidence/` via extractors that read traces. This split
matches OTel's "GenAI" semantic conventions ([otel-genai][otel-genai])
plus LRH's own evidence model. See
`05_layer5_observability_and_evidence.md` for the dataclasses, the
extractor protocol, and the staging-and-promotion pattern for manual
evidence.

### Layer 6 — MCP backend bridges

Adapters that connect external systems via MCP. Modules under
`src/lrh/bridges/`: `api.py`, `models.py`, `registry.py`, `config.py`,
`lifecycle.py`, plus an `adapters/` subpackage (`mcp_adapter`,
`ros_adapter`, `arena_bench_adapter`, `fake_adapter`). The Arena-Bench
adapter ([ignc-research/arena-bench][arena-bench]) launches a roslaunch
subprocess, waits for the ROS master plus a `scenario_loaded` flag, and
runs both the upstream `robotmcp/ros-mcp-server` ([ros-mcp][ros-mcp])
and a custom Arena-Bench scenario-control MCP server. See
`06_layer6_mcp_bridges.md` for the Protocols, the lifecycle handling,
and the NARROW DOORWAY worked example.

## 5. Cross-cutting invariants

### Summary

Two invariants apply to every layer and are enforced in the test suite,
not just in prose. Each layer's sub-proposal explains how it satisfies
them.

### Invariant A: manual-mode parity

For every workflow that an agent backend can perform, there must exist
a documented manual workflow that a human can execute, producing
**structurally identical** artifacts (same frontmatter schema, same
file layout, same evidence-record shape, same transition-record shape).
The manual backend in Layer 4 reports the same `RuntimeResult` shape
that the Claude backend does. The evidence model in Layer 5b treats
`source: human` and `source: agent_trace` as peers, validated against
the same per-kind schemas. Layer 3 ships a `manual_parity_test.py`
under `tests/workstream_tests/` that fails the build whenever the
agent path produces an artifact that the manual path can't.

This is **not** a hedge against agent failure — it's the structural
property that lets LRH be useful in the LCATS-style "human collaborator
reviews a sample of agent output" workflow at all. Pass B in the
appendix demonstrates manual-mode parity in action by having a human
collaborator produce evidence records in the same shape as the agent's
records and comparing them in a cross-review run.

### Invariant B: repository-as-control-plane

Authoritative state lives in committed Markdown and YAML in the
`project/` directory. Local runtime state (caches, logs, transient
sessions, secrets) may exist but is non-authoritative and must not
silently override repository artifacts — this is already an LRH
principle (`project/design/design.md` §9). The proposal extends it:

Telemetry spans live on disk under `project/runs/RUN-{ulid}/spans.jsonl`
in the default backend; an OTel-collector backend may stream
**copies** of those spans elsewhere but the on-disk JSONL is the
source of truth.

Evidence records under `project/evidence/` are the durable record of
what happened; transcripts under `project/runs/RUN-{ulid}/` are the
source for the body of evidence records but are themselves
non-authoritative once an evidence record cites them.

A workstream's `transitions[]` array in frontmatter is append-only and
is the audit trail for stage progression. Re-running an `advance` does
not modify history; it appends new entries.

This invariant is what makes LRH reproducible from a `git clone`. If
the runtime substrate or the observability backend changes tomorrow,
the repo still tells the full story.

## 6. Build vs. buy positioning

### Summary

The proposal does real legwork comparing against the rest of the field
and lands on a **hybrid**: build the differentiators, borrow the
commodities. This section names what we build, what we borrow, and why
each call lands where it does. The reasoning is summarized here; each
layer's sub-proposal contains the layer-specific build/buy detail.

### What we build (LRH differentiators)

The control plane (existing), the workstream lifecycle (Layer 3), the
evidence system (Layer 5b), and the MCP-to-evidence bridge wiring
(Layer 6 plus extractor registration in Layer 5b). These are LRH's
identity. There is no upstream substitute that owns repo-native typed
artifacts with frontmatter as authoritative truth and structured
evidence per workstream stage.

### What we borrow (commodities)

The Claude Agent SDK is the runtime substrate
([anthropics/claude-agent-sdk-python][cas]). It already does tool
allowlisting, hooks, permission modes, and W3C trace context — there's
no reason to rebuild any of that. We wrap it behind a `RuntimeBackend`
Protocol so we can swap it later if we need to.

OpenTelemetry GenAI semantic conventions are the schema for spans
([OpenTelemetry GenAI semconv][otel-genai]). We align where the
conventions are stable and use the `lrh.*` namespace for LRH-specific
attributes that aren't covered. This is closer to a "schema we adopt"
than a "library we depend on" — there's no GenAI semconv runtime, just
a vocabulary.

OpenLLMetry by Traceloop ([traceloop OpenLLMetry][openllmetry]) is the
likely instrumentation library when we eventually wire an OTel-collector
backend; Langfuse ([langfuse.com][langfuse]) is the likely
self-hosted UI. Both are deferred — the JSON-on-disk backend is what
ships first.

The Model Context Protocol is the bridge substrate
([modelcontextprotocol.io][mcp]). MCP servers for ROS, browsers,
filesystems, databases, and dozens of others already exist; we
front-load on `robotmcp/ros-mcp-server` ([ros-mcp][ros-mcp]) for the
Arena-Bench adapter rather than writing our own ROS bridge.

### What we deliberately don't borrow

**spec-kit** ([github/spec-kit][spec-kit]) is positioned as adjacent,
not upstream. It's a high-quality spec-driven-development toolkit, and
LRH's templates speak LRH's frontmatter dialect — adopting spec-kit's
templates would force a translation layer for marginal benefit. Layer 2
documents this trade-off explicitly. spec-kit's "constitution" concept
maps onto LRH's existing `principles/` directory, so the *idea* is
embraced even though the artifacts aren't.

**OpenSpec** ([Fission-AI/OpenSpec][openspec]) is a lighter-weight
alternative to spec-kit aimed at AI coding assistants. It overlaps with
LRH's spec layer but, like spec-kit, doesn't model the broader
control plane (focus, work items, evidence, status). It's a useful
reference for keeping LRH's spec layer lean.

**LangGraph** is rejected at Layer 3. Once LRH owns all state in the
repo, LangGraph is duplicating that state in an in-process graph. The
Layer 3 sub-proposal walks through this trade-off carefully — there's
~200 lines of in-house state machine that does what we need without
the dependency.

**CrewAI / AutoGen / BMAD-METHOD** are agent-orchestration frameworks
that target a different problem (multi-agent collaboration patterns).
They're not bad, just not what we're building — LRH's "agency" is at
the workstream level, not at the inter-agent-message level.

### Why this lands here

The high-leverage decision is that **LRH's value is the control plane
and the evidence model**, not the runtime, the telemetry, the bridge
plumbing, or the templates. Those are all things that mature externally
faster than a small project could match. Wrapping each one behind a
narrow Protocol means we can keep our own API stable while the
substrates evolve.

## 7. Risks and mitigations

### Summary

Four risks dominate. Each is named explicitly so we can track whether
we're addressing it.

### Risk 1 — Automation laundering

Multiple agent reviews of the same artifact look like independent
confirmation but share a model and a prompt context, producing
correlated false confidence. Mitigation: the cross-review pattern in
the Pass-B appendix has a *human collaborator* produce evidence in the
same shape and compares the two. Layer 5b's `cross_review_comparison`
evidence kind exists specifically to record agreement rates and flag
patterns of agent-only or human-only findings.

### Risk 2 — Soft idempotence

Execution records (the existing PROMPTS.md pattern) are LRH's
idempotence mechanism, but they're advisory, not enforced. An agent
can re-run a side-effecting tool and produce duplicate evidence.
Mitigation: Layer 4 budget enforcement plus Layer 3's `rerun=False`
default plus the `NOOP_IDEMPOTENT` `AdvanceResult` outcome. Critical
side effects (writes to `project/`, MCP tool calls with persistence
semantics) get pre-tool-use hook checks per Layer 4.

### Risk 3 — Agent behavior drift

Agents don't reliably follow prompts. The Pass-B example surfaced an
agent that ignored a "do not summarize" instruction. Mitigation: Layer
4 hooks (PostToolUse + Stop) can enforce structural constraints on
written artifacts; Layer 5b evidence-record validation can reject
records with extraneous content; production prompts in
`prompts/PROMPT-XXX.md` get a `forbidden_actions` block analogous to
the existing work-item field
(`project/design/repository_spec.md` §"Work Items"). This won't
eliminate drift; it does make drift visible.

### Risk 4 — ROS process-lifecycle fragility

Layer 6's Arena-Bench adapter launches roslaunch as a subprocess.
Gazebo and friends don't always die on `SIGTERM`. Mitigation: Layer 6
specifies process-group handling (`os.setsid`, `killpg(SIGTERM)`,
escalating to `SIGKILL` after a timeout) and a `lrh bridge cleanup`
command for orphaned processes. The risk is real — robotics code is
where this whole proposal will encounter the most operational reality
— and we're being explicit about it.

### Risk 5 — Cost surprise

Agent runs cost real money. The Pass-B example's pilot is $10; a
production-scale run is $50+. Mitigation: Layer 4's two-level budget
(per-call and per-workstream cumulative), plus Layer 5b cost-attribution
extraction, plus the `expected_evidence_at_close` closure check that
makes "did we even get our money's worth" a structural question.

## 8. Adoption plan

### Summary

The framework ships in dependency order. Each phase is gated on
manual-mode parity passing, evidence emission working, and existing
LRH validation continuing to succeed.

### Phase 1 — Layer 1 + Layer 2 (small)

Add workstream schema, loader, validator, and the precedence position
update; ship the package-owned templates. Outcome: `lrh workstream
new` and `lrh workstream validate` work. No orchestration yet. Tests:
schema validation, bucket-status consistency, parity with the work-item
loader. This phase is mostly typing and copying patterns from
`src/lrh/control/`.

### Phase 2 — Layer 3 (the new core)

Ship the orchestrator, the state machine, the two-step manual-advance
pattern, and `manual_parity_test.py`. Outcome: `lrh workstream
advance --mode manual` walks a workstream end to end without ever
loading an agent backend. Tests: parity tests, transition-record
invariants, gate logic, idempotence behavior on rerun.

### Phase 3 — Layer 4 (agent runtime, behind a Protocol)

Ship the `RuntimeBackend` Protocol, the manual + fake backends, and
then the Claude backend. Outcome: `lrh workstream advance --mode
agent` runs the Claude SDK against a sample workstream and writes a
transcript. Tests: `Outcome` taxonomy coverage, hook enforcement,
budget enforcement, transcript persistence.

### Phase 4 — Layer 5 (observability + evidence)

Ship Layer 5a (telemetry) first with the JSON-on-disk backend, then
Layer 5b (evidence) with the built-in extractor set. Outcome: a
workstream advance produces a `RUN-{ulid}/` directory and `lrh
evidence extract` produces evidence records under
`project/evidence/`. Tests: extractor coverage, schema-registry
validation, manual stub-and-fill flow.

### Phase 5 — Layer 6 (bridges)

Ship the `BridgeAdapter` Protocol, the `fake_adapter`, and then the
`arena_bench_adapter` in that order. Outcome: a workstream can open
an Arena-Bench session, run NARROW DOORWAY, and emit metrics as
evidence. Tests: lifecycle teardown under failure, MCP-server health
checks, evidence extraction from bridge output.

### Phase 6 — Pass-B realization in LCATS

Move from worked-example doc to actual workstream:
`WS-LCATS-CORPORA-ANALYSIS` ships against the LCATS repo with five
real Poe stories from a small Gutenberg sample, runs in hybrid mode,
and produces real evidence records. This is the integration test for
the whole proposal.

## 9. Open questions

These are tracked here so they don't get lost; each layer's
sub-proposal owns the resolution of the relevant ones.

How rich should `expected_evidence_at_close` get? Pass B made it
load-bearing for closure gating; it's currently per-evidence-kind
counts. We may want per-kind structural assertions ("at least one
`cross_review_comparison` record with `agreement_rate >= 0.7`"). Layer 3
owns this.

Should evidence records be allowed to *replace* prior records (versus
strictly append)? Pass B assumed append-only. Some workstream stages
(re-runs after prompt revision) might want supersedes/superseded_by
semantics analogous to work items. Layer 5b owns this.

Does the orchestrator emit operational telemetry for itself? Workstream
cost is tracked; orchestrator overhead (loading, validating,
idempotence checks) isn't. Layer 5a owns this; the answer is "probably
yes, eventually."

Do we need a workstream `parent` relationship in addition to
`sibling_workstreams`? Pass B found siblings; longer LCATS work might
have parent/child (a meta-workstream that spawns sub-workstreams).
Layer 1 owns this.

How do we handle the agent running corpora-update tooling itself
(Pass B deferred this as out-of-pilot)? This affects the bridge
layer's bound on what tools the agent can call. Layer 6 owns this.

## 10. Reading order and document index

### Recommended reading order

For someone who wants the full picture:

1. This document (umbrella).
2. `appendix_b_lcats_corpora_analysis.md` (the worked example — read it
   *before* the layer sub-proposals; it makes the abstractions concrete).
3. `03_layer3_workstream_orchestration.md` (the new core — the most
   load-bearing layer).
4. `04_layer4_agent_runtime.md` (because the runtime Protocol is what
   makes manual-mode parity testable).
5. `05_layer5_observability_and_evidence.md` (because evidence is what
   makes a workstream auditable).
6. `06_layer6_mcp_bridges.md` (because bridges are how this connects to
   the world).
7. `01_layer1_control_plane.md` and `02_layer2_templates.md` (the
   smallest, mostly boilerplate-ish layers).

For someone who just wants to know whether to merge: read this document
and §"Adoption plan" (§8). Each phase is gated independently.

### Document index

```text
project/design/proposals/workstream-execution-framework/
  README.md                                  # set-level index (what each file is)
  00_proposal.md                             # this document — umbrella
  01_layer1_control_plane.md                 # workstream-aware loader/validator/precedence
  02_layer2_templates.md                     # first-party templates
  03_layer3_workstream_orchestration.md      # state machine + orchestrator + parity tests
  04_layer4_agent_runtime.md                 # RuntimeBackend Protocol + Claude/manual/fake
  05_layer5_observability_and_evidence.md    # 5a telemetry + 5b evidence
  06_layer6_mcp_bridges.md                   # BridgeAdapter Protocol + Arena-Bench
  appendix_b_lcats_corpora_analysis.md       # WS-LCATS-CORPORA-ANALYSIS end-to-end
```

## 11. References

Citations inline in the text use the bracketed keys below. URLs are
included so a reader can verify the claim against an authoritative
source.

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

# Workstream Execution Framework — Proposal Set

This proposal set now frames LRH's future execution framework as
bounded, branch-contained orchestration for already-approved executable
leaves. The intended path is: selected executable leaf -> run packet ->
agent-owned branch -> pull request -> bounded CI/review stabilization ->
final run report -> human/policy merge and closeout gate.

The set is structured as one updated umbrella proposal, six older
layer-specific sub-proposals (retained as background design material),
and a Pass-B worked-example appendix. The umbrella document is the
current entry point for branch containment, pull-request stabilization,
least-privilege token posture, manual-mode equivalence, and final run
report outcomes.

## Status

`proposed` (deferred) — this proposal set is retained as LRH's
long-term execution architecture and is not rejected. The Workstream
Control Plane MVP has landed; the next proposed design step is an
execution-framework workstream that defines run packet/report schemas
and a manual branch/PR pilot before any autonomous backend work.

## Reading order

Read the umbrella document ([`00_proposal.md`](00_proposal.md)) first.
It supersedes the older layer documents for the current bounded
branch-level execution framing. The layer sub-proposals remain useful
background for lifecycle, runtime, evidence, observability, and bridge
concepts, and the appendix grounds the original framework in a real
case.

1. [`00_proposal.md`](00_proposal.md) — Updated umbrella proposal:
   bounded branch-level agency, run packets, run reports, pull requests
   as stabilization boundaries, least-privilege token posture,
   manual-mode equivalence, human/policy gates, risks, and adoption
   plan.

2. [`01_layer1_control_plane.md`](01_layer1_control_plane.md) —
   Layer 1: extending the loader/validator/snapshot/precedence
   resolver to recognize workstreams as a typed artifact, with a
   bucketed on-disk layout (`proposed/`, `active/`, `resolved/`,
   `abandoned/`), a stage state machine encoded in frontmatter,
   and a transitions audit trail.

3. [`02_layer2_templates.md`](02_layer2_templates.md) — Layer 2:
   first-party templates for the eight artifact kinds workstreams
   produce (workstream, conception, assessment, design, plan,
   prompt, decision, evidence stub), distributed via package
   resources, instantiated through `{{PLACEHOLDER}}` substitution.

4. [`03_layer3_workstream_orchestration.md`](03_layer3_workstream_orchestration.md)
   — Layer 3: the in-house state machine and the
   `advance_workstream()` API, with idempotent re-runs, gates per
   mode (`agent` / `manual` / `hybrid`), a two-step manual-advance
   pattern, failure semantics, and a `can_close()` predicate that
   reads `expected_evidence_at_close`.

5. [`04_layer4_agent_runtime.md`](04_layer4_agent_runtime.md) —
   Layer 4: the `RuntimeBackend` Protocol, frozen
   `RuntimeRequest` / `RuntimeResult` dataclasses, three backends
   (Claude SDK, manual, fake), per-call and per-workstream cost
   caps, hook chains (`PreToolUse` / `PostToolUse` /
   `PostToolUseFailure` / `Stop`), three permission modes (`ask` /
   `accept_edits` / `strict`).

6. [`05_layer5_observability_and_evidence.md`](05_layer5_observability_and_evidence.md)
   — Layer 5: split into 5a (telemetry, OTel-aligned spans,
   transcripts) and 5b (durable evidence records under
   `project/evidence/` produced by extractors that read traces),
   with a per-evidence-kind schema registry and a stub-and-fill
   flow for manual evidence.

7. [`06_layer6_mcp_bridges.md`](06_layer6_mcp_bridges.md) —
   Layer 6: `BridgeAdapter` / `BridgeSession` Protocols, four
   built-in adapters (`mcp`, `ros`, `arena_bench`, `fake`),
   process-group teardown discipline, bridge-specific evidence
   extractors, manual-mode parity through per-adapter manual
   prompts.

8. [`appendix_b_lcats_corpora_analysis.md`](appendix_b_lcats_corpora_analysis.md)
   — Pass-B worked example: `WS-LCATS-CORPORA-ANALYSIS` walked
   end-to-end across all six layers, with on-disk artifacts,
   stage transitions, sample `RuntimeRequest`/`RuntimeResult`,
   span samples, evidence records, and the closure check in action.
   Surfaces Pass-B findings B1–B5 in situ.

## Frontmatter IDs

Each document carries a stable `id:` in frontmatter that does not
change across revisions. Cross-references use these IDs.

| File | ID |
|------|-----|
| `00_proposal.md` | `PROP-WORKSTREAM-EXECUTION-FRAMEWORK` |
| `01_layer1_control_plane.md` | `PROP-WORKSTREAM-LAYER1-CONTROL-PLANE` |
| `02_layer2_templates.md` | `PROP-WORKSTREAM-LAYER2-TEMPLATES` |
| `03_layer3_workstream_orchestration.md` | `PROP-WORKSTREAM-LAYER3-ORCHESTRATION` |
| `04_layer4_agent_runtime.md` | `PROP-WORKSTREAM-LAYER4-RUNTIME` |
| `05_layer5_observability_and_evidence.md` | `PROP-WORKSTREAM-LAYER5-OBSERVABILITY-EVIDENCE` |
| `06_layer6_mcp_bridges.md` | `PROP-WORKSTREAM-LAYER6-MCP-BRIDGES` |
| `appendix_b_lcats_corpora_analysis.md` | `PROP-WORKSTREAM-APPENDIX-B-LCATS-CORPORA` |

## Canonical documents this proposal touches

Adoption of this proposal set will require coordinated edits to the
following canonical documents under `project/design/`:

`project/design/design.md` — adds a "Workstreams" section between
"Focus" and "Work Items"; updates the precedence chain; adds the
six-layer stack to the architecture summary.

`project/design/architecture.md` — adds module entries for
`src/lrh/workstream/`, `src/lrh/runtime/`, `src/lrh/observability/`,
`src/lrh/evidence/`, and `src/lrh/bridges/`.

`project/design/repository_spec.md` — adds top-level entries for
`project/workstreams/`, `project/runs/`, and `project/evidence/`.

`project/memory/decisions/precedence_semantics.md` — adds
workstreams at position 5 in the canonical precedence chain (per
the AGENTS.md "precedence maintenance note").

`project/work_items/README.md` — minor cross-reference to
`project/workstreams/README.md` once the latter exists.

`AGENTS.md` and `STYLE.md` — no edits required; this proposal
conforms to both.

The canonical edits are a separate changeset, gated on the proposal
set transitioning from `proposed` to `accepted`.

## Pass-B findings catalogued

The five findings from the manual Pass-B run that motivated this
proposal set, with the layer that operationalizes each:

`B1` — per-evidence-kind schemas — Layer 5b §5.

`B2` — `data:` field on evidence records — Layer 5b §3.

`B3` — `no_issues_found: true` — Layer 5b §5 (schema registry).

`B4` — sibling workstreams in frontmatter — Layer 1
§"Frontmatter schema."

`B5` — explicit `expected_evidence_at_close` — Layer 1
frontmatter; Layer 3 `can_close()` consumes it.

The appendix walks each finding through its post-formalization
shape on the `WS-LCATS-CORPORA-ANALYSIS` case.

## External references used

The references list spans the proposal documents; key sources cited
across the set:

- [Model Context Protocol spec](https://modelcontextprotocol.io/)
- [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Traceloop OpenLLMetry](https://www.traceloop.com/docs/openllmetry)
- [Langfuse](https://langfuse.com/)
- [github/spec-kit](https://github.com/github/spec-kit)
- [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)
- [robotmcp/ros-mcp-server](https://github.com/robotmcp/ros-mcp-server)
- [ignc-research/arena-bench](https://github.com/ignc-research/arena-bench)
- [Arena-Rosnav](https://github.com/Arena-Rosnav/arena-rosnav)

Each reference appears in its motivating sub-proposal's References
section with a quote where the source is treated as authoritative
for a specific design choice.

## Style and convention conformance

Markdown body text wraps at a stable line width to keep diffs
small. Code samples use module imports (per `STYLE.md` §"Imports"),
built-in generics (`list[str]`, not `typing.List[str]`), and frozen
dataclasses for public records. Test layout examples mirror the
source-tree layout (per `STYLE.md` §"Tests"). All CLI commands
proposed here ship with `--dry-run` and `--check` flags where they
mutate state. Encoding is UTF-8 throughout.


## Reconciliation position

This set remains a source of retained long-term concepts, including:
repository-as-control-plane, manual-mode parity, typed lifecycle
transitions, auditable transition history, backend/runtime abstraction,
evidence-versus-observability separation, explicit human approval and
closeout gates, and caution around automation laundering, excessive
agency, cost surprise, unsafe workflow permissions, scope creep,
agent behavior drift, and backend/vendor coupling.

Deferred concepts from this set include agent runtime execution, a
workstream orchestrator, automated stage advancement, MCP bridges,
telemetry systems, `lrh run` / autonomous run command naming, concrete
execution backends, GitHub/API automation, privileged workflow
permissions, and CI/review stabilization loops. Future autonomous
command names remain undecided and should respect the safe-default
agentic packaging boundary.

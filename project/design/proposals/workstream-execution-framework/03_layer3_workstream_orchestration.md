---
id: PROP-WORKSTREAM-LAYER3-ORCHESTRATION
title: Layer 3 — Workstream Orchestration
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 3 — Workstream Orchestration

## Summary

This sub-proposal specifies the **workstream orchestrator** — the
small, in-house state machine that advances a workstream through its
eight-stage lifecycle, gates transitions per mode, runs prompts via
the runtime layer, and writes the resulting artifacts back to disk.
The orchestrator is intentionally thin (~200 lines of state-machine
logic plus dataclass plumbing) and Protocol-driven, so that Layer 4
(runtime), Layer 5 (observability + evidence), and Layer 6 (bridges)
can each evolve independently. The single load-bearing API is
`advance_workstream(project, ws_id, *, runtime, observer, mode,
rerun) -> AdvanceResult`, returning a typed outcome that the CLI and
tests can pattern-match on.

The deliverable boundary for Layer 3 is: after this layer ships, a
contributor can take a workstream from `conceived` all the way to
`closed` using `lrh workstream advance`, with every stage either
auto-advancing or pausing for `--confirm` per the workstream's gate
configuration. **Crucially, manual mode works end-to-end** — the
same orchestrator advances a workstream whose every stage is human-
authored, just by selecting the manual backend in Layer 4. That
manual-mode parity is enforced by a load-bearing test
(`manual_parity_test.py`) that fails the build whenever an agent
path can produce an artifact a manual path can't. We also explicitly
**reject LangGraph** at this layer — once LRH owns all state in the
repo, the only thing LangGraph would add is a duplicate state store.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [Why an in-house state machine](#2-why-an-in-house-state-machine)
3. [The eight stages and the legal-transition graph](#3-the-eight-stages-and-the-legal-transition-graph)
4. [Module layout](#4-module-layout)
5. [The advance API](#5-the-advance-api)
6. [The two-step manual-advance pattern](#6-the-two-step-manual-advance-pattern)
7. [Gates and modes](#7-gates-and-modes)
8. [Failure semantics and idempotence](#8-failure-semantics-and-idempotence)
9. [Closure and `expected_evidence_at_close`](#9-closure-and-expected_evidence_at_close)
10. [CLI surface](#10-cli-surface)
11. [Worked examples](#11-worked-examples)
12. [Tests](#12-tests)
13. [Risks](#13-risks)
14. [References](#14-references)

## 1. Goals and non-goals

### Summary

Layer 3 is the new core of the framework. It reads a typed
`Workstream` from Layer 1, calls into Layer 4's runtime to do the
actual work, hands the resulting trace to Layer 5 for evidence
extraction, and writes the updated workstream back to disk —
producing a transition record on every successful advance. It does
**not** know how the runtime is implemented (Layer 4's job), how
spans become evidence (Layer 5's job), or how external systems
connect (Layer 6's job).

### Goals

The eight-stage lifecycle is a typed state machine, not free-form
prose. The legal-transition graph is enforced at advance time and
also at validation time. Gates are per-mode default with per-
workstream override, encoded in frontmatter. Every advance emits
exactly one new entry in the workstream's `transitions[]` list (an
append-only audit trail, separate from execution records and
evidence). Manual mode and agent mode both produce the same shape of
artifacts — verified by a parity test. Idempotence on rerun is
correct: re-running the same advance command on a workstream that
has already advanced is a `NOOP_IDEMPOTENT`, not a duplicate.

### Non-goals

The orchestrator does not run agents itself — it calls into a
`RuntimeBackend` (Layer 4). It does not parse traces — it hands them
to extractors (Layer 5b). It does not open MCP sessions — it requests
them from the bridge layer (Layer 6) when a workstream's prompt
specifies them. It does not parallelize across workstreams; serial
advance per workstream is the v1 contract.

## 2. Why an in-house state machine

### Summary

The choice between borrowing an orchestration framework (LangGraph,
CrewAI, AutoGen) and building a small state machine in LRH is the
single biggest architectural call in this layer. We pick build, on
the merits of LRH's specific situation. This section walks the
trade-offs.

### What LangGraph offers

LangGraph is a graph-based orchestration framework for LLM agents,
with state, edges, and persistence built in. It's good at modeling
agent loops where the next step depends on the previous step's
output, and it has a checkpointer system for durability.

### Why LangGraph isn't a fit

LRH already has the durable store: the Git-tracked `project/`
directory. Once frontmatter `transitions[]` is the audit trail and
`workstream.md` is the manifest, a LangGraph state object would be a
**second** state store, inconsistent in form and reconciliation
semantics with the first. Reconciling them would dominate the
implementation effort.

LRH's state machine is small. Eight stages, a fixed transition
graph, mode-driven gating, simple failure semantics. A handwritten
`state_machine.py` is roughly 200 lines including comments and the
legal-transition table. LangGraph is a few thousand lines of
framework for a problem that doesn't need framework.

LRH's manual-mode parity invariant is awkward to satisfy in
LangGraph. LangGraph models agent runs as graphs with conditional
edges; "a human did this manually and we recorded the same shape of
artifact" doesn't have a clean primitive. In our model, the manual
backend is just another `RuntimeBackend` and the orchestrator can't
tell.

LRH's debugging story is "read the Markdown." LangGraph adds another
debugging surface (graph state, checkpointer state) that we'd then
have to keep consistent with the Markdown. That's a reproducibility
loss.

### What about CrewAI / AutoGen / BMAD-METHOD

These are agent-orchestration frameworks aimed at multi-agent
collaboration patterns (a "researcher" agent talks to a "writer"
agent talks to a "reviewer" agent). LRH's "agency" is at the
workstream level, not at the inter-agent-message level. There's no
inter-agent collaboration to orchestrate at v1; we have one agent
per prompt and the workstream is what coordinates them.

### What we keep open

The `RuntimeBackend` Protocol (Layer 4) is narrow enough that a
LangGraph-backed runtime is a straightforward future addition for
contributors who want it for sub-tasks within a single prompt
execution. We're not closing that door — we're saying it's not v1.

## 3. The eight stages and the legal-transition graph

### Summary

The lifecycle has eight stages and a small, fixed transition graph.
Every transition is either auto-advanced (no `--confirm` needed) or
gated (`--confirm` required) per the workstream's mode-derived
defaults.

### The stages

```text
proposed bucket           active bucket          terminal buckets
+-----------+   +-----------+   +-----------+   +-----------+
| conceived | → | assessed  | → | designed  | → | planned   |
+-----------+   +-----------+   +-----------+   +-----------+
                                                       |
                                                       v
                                                +-----------+
                                                | executing |
                                                +-----------+
                                                       |
                                                       v
                                                +-----------+
                                                | reviewing |
                                                +-----------+
                                                  |        |
                                          +-------+        +-------+
                                          v                        v
                                     +----------+            +-----------+
                                     |  closed  |            | abandoned |
                                     +----------+            +-----------+
```

### The legal-transition table

```python
LEGAL_TRANSITIONS: dict[Stage, set[Stage]] = {
    Stage.CONCEIVED: {Stage.ASSESSED, Stage.ABANDONED},
    Stage.ASSESSED:  {Stage.DESIGNED, Stage.ABANDONED},
    Stage.DESIGNED:  {Stage.PLANNED, Stage.ABANDONED},
    Stage.PLANNED:   {Stage.EXECUTING, Stage.ABANDONED},
    Stage.EXECUTING: {Stage.REVIEWING, Stage.ABANDONED},
    Stage.REVIEWING: {Stage.CLOSED, Stage.ABANDONED, Stage.EXECUTING},
    Stage.CLOSED:    set(),
    Stage.ABANDONED: set(),
}
```

Notes: `reviewing → executing` is legal, to support the case where
review surfaces issues the executing stage needs to fix. `closed`
and `abandoned` are terminal; reopening requires creating a new
workstream with `supersedes:`.

### Authorial guidance per stage

Each stage has a single primary artifact:

```text
conceived  → conception.md       (rough sketch)
assessed   → assessment.md       (scope, constraints, risks, mode)
designed   → design.md           (technical design)
planned    → plan.md + prompts/  (decomposition into prompts)
executing  → evidence under project/evidence/ via prompts (multi-file)
reviewing  → cross_review_comparison evidence + closure decision
closed     → closure block in workstream.md frontmatter
abandoned  → closure block with reason: abandoned
```

The orchestrator's job at each non-terminal stage is to drive the
production of that stage's primary artifact via the runtime, then
record the transition once the artifact passes validation.

## 4. Module layout

### Summary

All Layer 3 code lives under `src/lrh/workstream/`. Each module has
a single concern.

### Modules

```text
src/lrh/workstream/
  __init__.py
  models.py           # Workstream, Stage, Mode, Gate, Transition,
                      # AdvanceResult, AdvanceOutcome
  schema.py           # frontmatter validation (or import from Layer 1)
  state_machine.py    # legal-transition table, gate logic
  loader.py           # disk -> typed model (or import from Layer 1)
  writer.py           # typed model -> disk; appends transitions
  orchestrator.py     # advance_workstream() and friends
  precedence.py       # adapter into the precedence resolver
```

Tests:

```text
tests/workstream_tests/
  __init__.py
  models_test.py
  schema_test.py
  state_machine_test.py
  loader_test.py
  writer_test.py
  orchestrator_test.py
  manual_parity_test.py     # load-bearing
  workstream_smoke_test.py  # integration
```

## 5. The advance API

### Summary

The single load-bearing entry point is `advance_workstream`. It
returns an `AdvanceResult` carrying a typed `AdvanceOutcome` so
callers can pattern-match without inspecting strings.

### The function signature

```python
# src/lrh/workstream/orchestrator.py
from typing import Protocol

from lrh.workstream import models
from lrh.runtime import api as runtime_api
from lrh.observability import api as observer_api


def advance_workstream(
    project: models.Project,
    ws_id: str,
    *,
    runtime: runtime_api.RuntimeBackend,
    observer: observer_api.Observer,
    mode: models.Mode | None = None,
    rerun: bool = False,
    confirm: bool = False,
) -> models.AdvanceResult:
    """Advance a workstream by one stage.

    The orchestrator reads the workstream from disk, determines the
    next legal stage, checks the gate for the current mode, runs the
    appropriate runtime prompt(s) if needed, validates the produced
    artifact, appends a Transition entry to frontmatter, and writes
    the workstream back. Idempotent: re-running on an already-advanced
    workstream returns NOOP_IDEMPOTENT.

    Args:
        project: Loaded Project model from Layer 1.
        ws_id: Workstream identifier.
        runtime: Runtime backend (Layer 4); selects manual/agent/fake.
        observer: Observability sink (Layer 5a).
        mode: Override the workstream's mode_default for this advance.
        rerun: If True, allow re-running an already-completed stage.
        confirm: If True, satisfy a confirm-gated transition.

    Returns:
        An AdvanceResult whose outcome is one of AdvanceOutcome.
    """
```

### `AdvanceResult` and `AdvanceOutcome`

```python
import enum
from dataclasses import dataclass


class AdvanceOutcome(enum.Enum):
    ADVANCED            = "advanced"
    GATE_REACHED        = "gate_reached"
    MANUAL_PROMPT_READY = "manual_prompt_ready"
    NOOP_IDEMPOTENT     = "noop_idempotent"
    FAILED              = "failed"


@dataclass(frozen=True)
class AdvanceResult:
    outcome: AdvanceOutcome
    workstream_id: str
    from_stage: models.Stage
    to_stage: models.Stage | None     # None on GATE_REACHED, NOOP, FAILED
    runtime_result: runtime_api.RuntimeResult | None
    transition: models.Transition | None
    prompt_path: str | None           # set on MANUAL_PROMPT_READY
    failure_reason: str | None        # set on FAILED
```

### Outcome semantics

`ADVANCED` — the orchestrator successfully ran the stage's runtime
call (or human equivalent), validated the produced artifact, and
appended a transition. The new stage is in `to_stage`.

`GATE_REACHED` — the next transition requires `--confirm` per the
gate configuration. No runtime call was made; no transition was
appended. Caller can re-invoke with `confirm=True`.

`MANUAL_PROMPT_READY` — the stage is a manual stage; the orchestrator
has materialized a prompt file under
`project/workstreams/{bucket}/WS-{SLUG}/prompts/PROMPT-XXX-MANUAL.md`
and is waiting for the human to write the artifact, then re-run with
`--confirm-manual`. See §6.

`NOOP_IDEMPOTENT` — the workstream is already at or past the stage
the caller asked for. No transition was appended. Re-running is
safe.

`FAILED` — the runtime call failed, the produced artifact failed
validation, or some other recoverable error occurred. The stage
**does not advance**; a transition entry is appended with
`failure_reason` set. Re-running is allowed (with `rerun=True`).

## 6. The two-step manual-advance pattern

### Summary

Manual stages are not a degenerate case — they're a first-class
runtime mode. The orchestrator handles manual advance in two steps so
that the human work is auditable and re-entry is clean.

### Step 1: prepare

```bash
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --mode manual
MANUAL_PROMPT_READY
  stage: conceived -> assessed
  prompt written to:
    project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/
      prompts/PROMPT-002-MANUAL-ASSESSMENT.md
  Next: write project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/
    assessment.md
  Then re-run:
    lrh workstream advance WS-LCATS-CORPORA-ANALYSIS \
      --confirm-manual --transition-note "..."
```

The orchestrator stamps a manual prompt file (using
`prompt.md.tmpl` with `{{MODE}} = manual`), writes it to disk, and
returns `MANUAL_PROMPT_READY`. **No transition entry is appended
yet** — the workstream's frontmatter is unchanged.

### Step 2: confirm

The human writes `assessment.md`, then:

```bash
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS \
    --confirm-manual --transition-note "Assessed in 30 minutes; \
mode_default=hybrid; budget OK"
ADVANCED
  stage: conceived -> assessed
  transition appended at 2026-04-25T18:33:00-04:00
```

The orchestrator checks that the expected stage artifact exists and
validates against schema, then appends the transition entry with
`mode: manual` and the human-supplied `note`. The manual-mode prompt
file remains under `prompts/` as a record of what was asked.

### Why two steps

A single command would force the orchestrator to either block on
human input (bad CLI ergonomics) or silently accept whatever the
human did and assume it was the work (bad auditing). Two steps makes
the contract explicit: the prompt is a request, the artifact is the
work, the confirmation closes the loop with a note.

### Symmetric with agent mode

Agent mode goes through the same orchestrator, just without the
intermediate human step:

```text
prepare     → runtime.execute(prompt)
            → validate produced artifact
            → append transition (mode: agent)
            → write back
            → return ADVANCED
```

The orchestrator does not branch on `mode` for the success path —
it branches on whether the runtime backend's `execute()` call
returned synchronously (agent/fake) or asynchronously requested human
input (manual). This is the manual-mode parity invariant in code
form.

## 7. Gates and modes

### Summary

Each transition is either auto-advanced or gated. Gates are
configured per-mode by default; per-workstream overrides live in
frontmatter.

### Default gate configuration per mode

```python
DEFAULT_GATES: dict[Mode, dict[tuple[Stage, Stage], Gate]] = {
    Mode.MANUAL: {
        # Every transition is auto in manual mode — the human is
        # already in the loop.
        (Stage.CONCEIVED, Stage.ASSESSED):  Gate.AUTO,
        (Stage.ASSESSED, Stage.DESIGNED):   Gate.AUTO,
        (Stage.DESIGNED, Stage.PLANNED):    Gate.AUTO,
        (Stage.PLANNED, Stage.EXECUTING):   Gate.AUTO,
        (Stage.EXECUTING, Stage.REVIEWING): Gate.AUTO,
        (Stage.REVIEWING, Stage.CLOSED):    Gate.AUTO,
    },
    Mode.AGENT: {
        # Conservative defaults: gate at executing-entry and at
        # closure to keep agent runs auditable.
        (Stage.CONCEIVED, Stage.ASSESSED):  Gate.AUTO,
        (Stage.ASSESSED, Stage.DESIGNED):   Gate.AUTO,
        (Stage.DESIGNED, Stage.PLANNED):    Gate.AUTO,
        (Stage.PLANNED, Stage.EXECUTING):   Gate.CONFIRM,
        (Stage.EXECUTING, Stage.REVIEWING): Gate.AUTO,
        (Stage.REVIEWING, Stage.CLOSED):    Gate.CONFIRM,
    },
    Mode.HYBRID: {
        # Most permissive on early stages; gate at executing-entry,
        # at reviewing-exit, and on closure.
        (Stage.CONCEIVED, Stage.ASSESSED):  Gate.AUTO,
        (Stage.ASSESSED, Stage.DESIGNED):   Gate.AUTO,
        (Stage.DESIGNED, Stage.PLANNED):    Gate.AUTO,
        (Stage.PLANNED, Stage.EXECUTING):   Gate.CONFIRM,
        (Stage.EXECUTING, Stage.REVIEWING): Gate.AUTO,
        (Stage.REVIEWING, Stage.CLOSED):    Gate.CONFIRM,
    },
}
```

### Per-workstream override

A workstream can override gates in its `gates:` frontmatter:

```yaml
gates:
  designed_to_planned: confirm    # override hybrid default of auto
  reviewing_to_closed: auto       # override hybrid default of confirm
```

The orchestrator merges defaults with overrides at runtime.

### Per-stage mode override

A workstream can also declare per-stage mode overrides:

```yaml
mode_default: hybrid
stage_modes:
  designed: manual
  executing: agent
  reviewing: manual
```

This is how the LCATS analysis workstream in Pass B gets its
"design manual, execute agent, review manual" behavior.

## 8. Failure semantics and idempotence

### Summary

Failure is uniform and recoverable. The stage doesn't advance, a
failure transition entry is appended, and the workstream is in a
state where re-running is safe.

### Failure path

```text
1. orchestrator calls runtime.execute(prompt)
2. runtime returns RuntimeResult with outcome != SUCCESS
3. orchestrator does NOT advance the stage
4. orchestrator appends a transition entry:
     from: <current_stage>
     to:   <current_stage>      # same stage
     at:   <now>
     by:   <invoker>
     mode: <runtime mode>
     failure_reason: <RuntimeResult.outcome.value> + detail
5. orchestrator returns AdvanceResult(outcome=FAILED, ...)
6. user can re-run with --rerun once the cause is addressed
```

A failure transition entry's `from == to` is the on-disk signal that
this transition recorded a failure. Validators flag this consistently.

### Idempotence on rerun

Re-running `lrh workstream advance WS-X` on a workstream that has
already advanced past the requested stage returns
`NOOP_IDEMPOTENT`. No new transition is appended.

Re-running with `--rerun` on a stage that previously failed runs the
runtime again. The orchestrator detects "we previously emitted
artifact X for this stage" via existence-check and refuses to
overwrite unless `--rerun` is also paired with a fresh prompt-id (or
the agent's permission_mode allows overwrites — Layer 4 owns this).

For agent runs, idempotence has a soft component (the existing
PROMPTS.md execution-record idempotence pattern) and a hard component
(file-existence checks at the orchestrator level). The combination
gives us "don't double-spend money" and "don't double-write
artifacts" without requiring a database.

## 9. Closure and `expected_evidence_at_close`

### Summary

Closing a workstream is gated structurally: the orchestrator refuses
to advance `reviewing → closed` unless the workstream's evidence
ledger meets the `expected_evidence_at_close` counts.

### The closure check

```python
def can_close(
    workstream: models.Workstream,
    project: models.Project,
) -> tuple[bool, list[str]]:
    """Return (ok, reasons) where reasons explains any block."""
    expected = workstream.expected_evidence_at_close
    actual = collections.Counter(
        ev.kind for ev in project.evidence_for_workstream(workstream.id)
    )
    reasons: list[str] = []
    for kind, required_count in expected.items():
        if actual[kind] < required_count:
            reasons.append(
                f"need {required_count} of kind {kind}; have {actual[kind]}"
            )
    return (not reasons, reasons)
```

The orchestrator calls this before `reviewing → closed`; if the
check fails, it returns `FAILED` with `failure_reason` listing what's
missing. Closure transitions are also `CONFIRM`-gated by default, so
the human reviewer signs off explicitly.

### Closure types

```yaml
closure:
  reason: completed       # all expected_evidence_at_close met
  evidence_supporting:
    - ev-...
    - ev-...
  closed_at: ...
  closed_by: ...
```

```yaml
closure:
  reason: abandoned       # workstream is being shut down without completion
  abandonment_reason: "blocked by ROS lifecycle issues; superseded by WS-..."
  closed_at: ...
  closed_by: ...
```

```yaml
closure:
  reason: superseded
  superseded_by: WS-LCATS-CORPORA-ANALYSIS-V2
  closed_at: ...
  closed_by: ...
```

The validator enforces that `closure.reason: completed` requires the
evidence checks to pass, while `abandoned` and `superseded` skip
them.

## 10. CLI surface

### Summary

Six new subcommands beyond Layer 1's `new | list | show | validate`.

### Commands

```bash
# Advance one stage.
lrh workstream advance <WS-ID> \
    [--mode manual|agent|hybrid] \
    [--confirm] \
    [--confirm-manual] \
    [--transition-note "..."] \
    [--rerun] \
    [--dry-run]

# Resume a workstream that was interrupted (re-runs the current
# stage's prompt without advancing).
lrh workstream resume <WS-ID> [--rerun]

# Mark a workstream abandoned with a reason.
lrh workstream abandon <WS-ID> --reason "..."

# Show or override gates for a workstream.
lrh workstream gates <WS-ID> [--show | --set <transition>=<auto|confirm>]

# Move workstreams between buckets to match metadata (analogous to
# `lrh validate --fix` for work items).
lrh workstream tidy [--fix]

# Print the next legal stage and what's required to advance.
lrh workstream next <WS-ID>
```

`--dry-run` on `advance` reports what would happen without writing
anything (per STYLE.md §"Scripts" requirement that scripts/CLI
support `--dry-run`).

## 11. Worked examples

### Summary

Three short examples covering the most common paths.

### Example A — Hybrid workstream walks the lifecycle

```bash
# Start
$ lrh workstream new --id WS-LCATS-CORPORA-ANALYSIS \
                     --title "Analyze the LCATS corpora" \
                     --focus FOCUS-LCATS-CORPORA \
                     --mode-default hybrid

# Conceived → assessed (auto in hybrid; assessment.md is manual stage)
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
MANUAL_PROMPT_READY
  prompt written to .../prompts/PROMPT-002-MANUAL-ASSESSMENT.md
  next: write assessment.md, then --confirm-manual

# Human writes assessment.md, confirms.
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS \
    --confirm-manual --transition-note "Mode hybrid; budget $10"
ADVANCED  conceived -> assessed

# Designed (manual again per stage_modes), planned (manual)…
# Then planned → executing (CONFIRM gate in hybrid).
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
GATE_REACHED  planned -> executing requires --confirm

$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --confirm
ADVANCED  planned -> executing
# orchestrator runs PROMPT-001..PROMPT-005 via runtime.execute(),
# emits 5 corpus_issue_report evidence records per Layer 5b.

# Executing → reviewing (auto in hybrid).
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
ADVANCED  executing -> reviewing

# Reviewing produces cross_review_comparison evidence (manual stage).
# … then reviewing → closed (CONFIRM in hybrid).
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --confirm \
    --transition-note "Pilot succeeded; agreement rate 0.73 above \
0.70 threshold."
ADVANCED  reviewing -> closed
```

### Example B — Failure and rerun

```bash
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --confirm
FAILED  planned -> executing
  failure_reason: budget_exhausted (per_call_usd cap of $2.00 hit)
  transition appended

# raise budget, then rerun
$ vim project/workstreams/active/WS-LCATS-CORPORA-ANALYSIS/workstream.md
# (set per_call_usd: 4.00)
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --rerun
ADVANCED  planned -> executing
```

### Example C — Idempotent re-run is a noop

```bash
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
NOOP_IDEMPOTENT  workstream already at stage closed
```

## 12. Tests

### Summary

Tests are layered: pure state-machine tests, single-advance tests
with a fake runtime, the parity test, and an end-to-end smoke test.

### Test plan

`state_machine_test.py` — exhaustive coverage of legal and illegal
transitions; gate evaluation across modes; per-workstream override
merging; closure invariants (`expected_evidence_at_close`).

`writer_test.py` — round-trip a `Workstream` through the writer and
back through Layer 1's loader; assert frontmatter ordering is
deterministic (per STYLE.md §"Determinism") and `transitions[]` is
strictly append-only.

`orchestrator_test.py` — drive `advance_workstream()` with a
`fake_runtime` (Layer 4) and a `fake_observer` (Layer 5a); cover all
five `AdvanceOutcome` values; verify failure transitions are
recorded; verify `--rerun` and `--dry-run` paths.

**`manual_parity_test.py` (load-bearing)** — for each of the eight
stages, run the same workstream through the agent path and the
manual path. Assert that the produced artifacts are byte-identical
modulo: timestamps, contributor IDs, and the `mode` field on the
transition entry. This is the test that codifies Invariant A from
the umbrella proposal. It must pass on every PR.

`workstream_smoke_test.py` — full lifecycle smoke test on a fixture
project containing a single hybrid workstream. Asserts the final
on-disk state matches a golden snapshot under
`tests/workstream_tests/fixtures/expected/`.

### Determinism

All tests seed any randomness (per STYLE.md §"Determinism"). All
timestamps in fixtures are baked. The fake runtime returns canned
results keyed by prompt-id.

### Manual parity test details

```python
# tests/workstream_tests/manual_parity_test.py
import unittest
from lrh.workstream import orchestrator
from lrh.runtime import api, manual_backend, fake_backend


class ManualParityTest(unittest.TestCase):
    """For each stage, agent and manual backends must produce the same
    artifact shape.
    """

    def test_assessed_stage_parity(self):
        agent_workstream = self._advance_with(
            stage_under_test="assessed",
            backend=fake_backend.FakeAgentBackend(canned="<assessment>"),
        )
        manual_workstream = self._advance_with(
            stage_under_test="assessed",
            backend=manual_backend.ManualBackend(
                canned_human_input="<assessment>",
            ),
        )
        agent_artifact = agent_workstream.read_artifact("assessment.md")
        manual_artifact = manual_workstream.read_artifact("assessment.md")
        self.assertEqual(
            self._normalize(agent_artifact),
            self._normalize(manual_artifact),
        )

    # ... one per stage ...

    def _normalize(self, artifact: str) -> str:
        # Strip timestamps, contributor IDs, mode field.
        ...
```

## 13. Risks

### Summary

The risks for Layer 3 are operational, not structural.

The state machine is small but it's load-bearing. A bug in the
legal-transition table or in gate evaluation produces
hard-to-diagnose lifecycle confusion. Mitigation: high test coverage,
a strict invariant check in the validator (`transitions[]` reflects a
valid path through the graph), and the parity test catching whole
classes of bugs.

Closure-check correctness depends on Layer 5b's evidence loader.
Mitigation: closure tests use a real (small) Layer 5b fixture rather
than mocking. If Layer 5b breaks, closure tests break — that's the
right coupling.

`transitions[]` is append-only by convention; nothing prevents a
contributor from rewriting it manually. Mitigation: validator
enforcement against the prior commit's frontmatter; CI check; clear
documentation that hand-editing transitions is a last-resort
recovery action.

The two-step manual-advance pattern can leave a workstream in a
half-advanced state if the human walks away. Mitigation: `lrh
workstream show` prominently displays "manual prompt waiting" with
the prompt path; `lrh workstream tidy --fix` can clean up stale
manual prompts that no longer point to a real artifact (with
`--confirm` to actually delete).

## 14. References

`PROMPTS.md` — existing prompt-record and execution-record schema.
The `prompts/PROMPT-XXX.md` files written by the workstream lifecycle
are an extension of this schema (with `workstream:` field added).

`project/executions/README.md` — existing execution-record store. The
runtime layer (Layer 4) writes execution records per the existing
PROMPTS.md schema; Layer 3's orchestrator triggers those writes.

`project/design/design.md` — existing LRH design document. §"Workflow
Model" enumerates the iterative project stages; the workstream
lifecycle is a typed instantiation of that pattern at the workstream
grain rather than the project grain.

`project/memory/decisions/precedence_semantics.md` — precedence
chain. Layer 1 (control plane) updates this; Layer 3 inherits the
new ordering.

[anthropics/claude-agent-sdk-python][cas] — runtime substrate (Layer
4 wraps it). Important for understanding why we don't need LangGraph:
the SDK already provides the per-prompt agent loop with hooks,
permission modes, and structured outputs.

[modelcontextprotocol.io][mcp] — bridge substrate (Layer 6).
Workstream prompts may reference MCP servers; Layer 3 plumbs the
references but doesn't open the sessions itself.

[OpenTelemetry GenAI semconv][otel-genai] — span vocabulary used by
Layer 5a. Workstream advance emits a `lrh.run` span with workstream
context that downstream observability tools can read.

[github/spec-kit][spec-kit] — alternative SDD framework. The
workstream lifecycle's "spec drives implementation" framing is
spec-kit-compatible at the conceptual level even though the
templates are LRH-native.

[Fission-AI/OpenSpec][openspec] — lighter-weight per-change folder
pattern that LRH's workstream directory mirrors.

[cas]: https://github.com/anthropics/claude-agent-sdk-python
[mcp]: https://modelcontextprotocol.io/
[otel-genai]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
[spec-kit]: https://github.com/github/spec-kit
[openspec]: https://github.com/Fission-AI/OpenSpec

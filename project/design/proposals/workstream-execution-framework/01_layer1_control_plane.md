---
id: PROP-WORKSTREAM-LAYER1-CONTROL-PLANE
title: Layer 1 — Control Plane Extensions for Workstreams
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 1 — Control Plane Extensions for Workstreams

## Summary

This sub-proposal adds **workstream-aware loading, validation,
snapshotting, and precedence resolution** to LRH's existing control
plane. The new artifact is small but load-bearing: a `Workstream`
typed model, a directory schema under `project/workstreams/`, a
validator that enforces the schema and bucket-status consistency, a
snapshotter that surfaces workstreams in `lrh snapshot` output, and an
update to the precedence resolver placing workstreams between focus
and work items in the canonical chain. Most of this layer is
incremental on existing patterns — work items already model status
buckets with frontmatter as authoritative source of truth, and the
loader, validator, and resolver all extend cleanly.

The deliverable boundary for Layer 1 is: after this layer ships, a
workstream Markdown directory parses, validates, and shows up in
snapshots, but **nothing advances yet**. Advance is Layer 3's job.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [Workstream as a typed model](#2-workstream-as-a-typed-model)
3. [Directory schema](#3-directory-schema)
4. [Frontmatter schema](#4-frontmatter-schema)
5. [Loader changes](#5-loader-changes)
6. [Validator changes](#6-validator-changes)
7. [Snapshot and survey changes](#7-snapshot-and-survey-changes)
8. [Precedence resolver changes](#8-precedence-resolver-changes)
9. [CLI surface](#9-cli-surface)
10. [Worked examples](#10-worked-examples)
11. [Tests](#11-tests)
12. [Risks](#12-risks)
13. [References](#13-references)

## 1. Goals and non-goals

### Summary

Layer 1 buys us one thing: a workstream artifact that LRH can read,
validate, and locate in the precedence chain. It does **not** buy us
state advance, agent execution, telemetry, or evidence — those belong
to later layers.

### Goals

The layer commits to a `Workstream` typed model that mirrors the
on-disk Markdown+YAML shape and exposes typed fields rather than raw
dictionaries (per AGENTS.md "Source vs runtime model"). It commits to
schema validation with the same severity model the existing validator
uses (`error | warning | info`, see
`project/design/design.md` §15.5). It commits to bucket-status
consistency checks analogous to the work-item rule that filename stem
equals `id` and bucket directory equals metadata `status`. It commits
to a precedence-resolver update that adds workstreams to the chain in
position 5, with the precedence-semantics decision record updated in
the same change set per AGENTS.md.

### Non-goals

The layer does not advance workstream stages, run agents, emit
telemetry, write evidence, or open bridges. Those are Layers 3, 4, 5,
and 6 respectively. The CLI in this layer is intentionally minimal:
`new`, `list`, `show`, `validate` only. `advance | resume | abandon |
gates | tidy` are introduced by Layer 3.

## 2. Workstream as a typed model

### Summary

Following the established LRH pattern, the control plane exposes a
typed `Workstream` dataclass loaded from disk by a parser and
validated by a validator. The typed model is the long-term internal
API; raw dictionaries are not.

### Module layout

```text
src/lrh/control/workstream/
  __init__.py
  models.py          # Workstream, Stage, Mode, Gate, Transition dataclasses
  schema.py          # frontmatter validation
  loader.py          # disk -> typed model
  paths.py           # bucket directory layout helpers
```

This sits next to the existing `src/lrh/control/` package and follows
the same module-per-concern style. New tests live under
`tests/control_tests/workstream/`.

### Dataclass sketch

The skeleton (full Python is in Layer 3's sub-proposal; this is the
shape of the typed model used for loading and validation):

```python
import enum
from dataclasses import dataclass, field
from typing import Any


class Stage(enum.Enum):
    CONCEIVED = "conceived"
    ASSESSED = "assessed"
    DESIGNED = "designed"
    PLANNED = "planned"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


class Mode(enum.Enum):
    MANUAL = "manual"
    AGENT = "agent"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class Transition:
    from_stage: Stage
    to_stage: Stage
    at: str            # ISO-8601 timestamp
    by: str            # contributor id
    mode: Mode
    note: str
    failure_reason: str | None = None
    closure_reason: str | None = None


@dataclass(frozen=True)
class Workstream:
    id: str
    title: str
    stage: Stage
    bucket: str        # proposed | active | resolved | abandoned
    mode_default: Mode
    related_focus: list[str]
    related_work_items: list[str]
    sibling_workstreams: list[str]
    expected_evidence_at_close: dict[str, int]
    transitions: list[Transition] = field(default_factory=list)
    body: str = ""
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)
```

The `frozen=True` choice is deliberate: workstream advance produces a
**new** workstream value with an extended `transitions` list and an
updated `stage`, then writes it back to disk. The orchestrator in
Layer 3 owns the write path; the loader is read-only.

## 3. Directory schema

### Summary

Workstreams live under `project/workstreams/{bucket}/WS-{SLUG}/`. The
bucket directory is a derived view; frontmatter `stage` (mapped to a
bucket via a fixed mapping) is authoritative — exactly the work-item
pattern.

### On-disk layout

```text
project/
  workstreams/
    proposed/
      WS-LCATS-CORPORA-ANALYSIS/
        workstream.md             # the manifest (frontmatter + body)
        conception.md             # written at conceived stage
        assessment.md             # written at assessed stage
        design.md                 # written at designed stage
        plan.md                   # written at planned stage
        prompts/
          PROMPT-001.md
          PROMPT-002.md
        decisions/
          DEC-001-mode-choice.md
    active/
    resolved/
    abandoned/
```

### Bucket mapping

```text
stage          -> bucket
-----------------------------
conceived       proposed
assessed        proposed
designed        proposed
planned         proposed
executing       active
reviewing       active
closed          resolved
abandoned       abandoned
```

The bucket is derived from `stage`. `lrh workstream validate`
enforces consistency: a workstream with `stage: executing` under
`proposed/` is an error.

### Why this layout

The directory layout matches the existing work-item bucket pattern
(`project/design/repository_spec.md` §"Work Items"), so contributors
already know how to read and edit it. Per-stage artifacts live in
sibling files inside the workstream directory rather than in
subdirectories, because they're written at most once and accumulate
linearly. `prompts/` and `decisions/` are subdirectories because they
accumulate many entries.

## 4. Frontmatter schema

### Summary

The `workstream.md` manifest carries a YAML frontmatter block with
fields covering identity, stage, mode, relations, gates, evidence
expectations, and the `transitions[]` audit trail. The Markdown body
is the human-readable description.

### Required fields

```yaml
id: str                      # WS-{SLUG}, slug uppercase + hyphens
title: str                   # human-readable
stage: str                   # one of Stage values
mode_default: str            # one of Mode values
created_on: date             # ISO-8601 date
updated_on: date             # ISO-8601 date
```

### Recommended fields

```yaml
related_focus: [str]         # focus IDs this workstream refines
related_work_items: [str]    # work item IDs
sibling_workstreams: [str]   # peer workstream IDs (Pass-B finding)
gates:                       # stage -> required confirmation policy
  designed_to_planned: auto
  planned_to_executing: confirm
  executing_to_reviewing: auto
  reviewing_to_closed: confirm
expected_evidence_at_close:  # closure criteria; Pass-B finding
  corpus_issue_report: 5
  analysis_summary: 1
  cross_review_comparison: 1
budget:
  per_workstream_usd: 10.00
  per_call_usd: 2.00
owner: str                   # contributor id
contributors: [str]
assigned_agents: [str]
```

### Append-only audit trail

```yaml
transitions:
  - from: conceived
    to: assessed
    at: 2026-04-25T18:33:00-04:00
    by: anthony
    mode: manual
    note: "Initial assessment after constraints conversation"
  - from: assessed
    to: designed
    at: 2026-04-25T19:10:00-04:00
    by: anthony
    mode: manual
    note: "Wrote design.md"
```

### Closure fields

When the workstream reaches `closed` or `abandoned`:

```yaml
closure:
  reason: completed       # completed | superseded | abandoned
  evidence_supporting:
    - ev-WS-LCATS-CORPORA-ANALYSIS-P006
    - ev-WS-LCATS-CORPORA-ANALYSIS-P007
  closed_at: 2026-04-26T16:00:00-04:00
  closed_by: anthony
```

### A complete minimal example

```yaml
---
id: WS-LCATS-CORPORA-ANALYSIS
title: Analyze the LCATS corpora for transcription issues
stage: conceived
mode_default: hybrid
created_on: 2026-04-25
updated_on: 2026-04-25
related_focus:
  - FOCUS-LCATS-CORPORA
sibling_workstreams:
  - WS-LCATS-CORPORA-UPDATE
gates:
  designed_to_planned: auto
  planned_to_executing: confirm
  executing_to_reviewing: auto
  reviewing_to_closed: confirm
expected_evidence_at_close:
  corpus_issue_report: 5
  analysis_summary: 1
  cross_review_comparison: 1
budget:
  per_workstream_usd: 10.00
  per_call_usd: 2.00
owner: anthony
contributors:
  - anthony
  - claude-sonnet-agent
assigned_agents:
  - claude-sonnet-agent
transitions: []
---

# WS-LCATS-CORPORA-ANALYSIS

Analyze five Edgar Allan Poe stories from the LCATS corpora and
report transcription/encoding issues per the assessment.
```

## 5. Loader changes

### Summary

The existing `src/lrh/control/loader.py` learns to discover, parse,
and load workstreams alongside focus and work items. Loader changes
are mechanical: copy the work-item bucket-walking pattern, parse the
new frontmatter shape into the new `Workstream` dataclass, and expose
a `Project.workstreams: list[Workstream]` field on the existing
`Project` model.

### New behaviors

`lrh.control.loader.load_project(path)` discovers
`project/workstreams/{proposed,active,resolved,abandoned}/`,
recursively reads each `WS-*/workstream.md`, parses frontmatter, and
constructs `Workstream` instances. Parsing failures produce
`error`-severity validation findings without aborting the whole load
(matching the existing per-file-error policy). The `Project` model
gains `workstreams: list[Workstream]` and `workstreams_by_id:
dict[str, Workstream]`.

The loader does **not** read sibling files (`conception.md`,
`design.md`, etc.) — those are loaded on demand by Layer 3 when an
advance reads a stage's artifact. This keeps the load cost bounded
even on projects with many workstreams.

### Why this scopes cleanly

The work-item loader already handles the bucket+frontmatter pattern;
the workstream loader is structurally identical with a different
schema. Existing tests under `tests/control_tests/loader_test.py`
serve as the reference harness; the new tests live under
`tests/control_tests/workstream/loader_test.py` per STYLE.md §"Test
Tree Layout."

## 6. Validator changes

### Summary

The existing validator gains workstream-aware checks. Most of the
new checks are mechanical translations of the work-item validation
pattern; a few are workstream-specific.

### New checks

Per-file schema checks: required fields present, enum values valid,
list fields well-typed, dates in ISO-8601, IDs unique within the
project. These follow the parsing → schema → cross-reference →
semantic-policy layered pattern documented in design.md §15.5.

Bucket-stage consistency: the on-disk bucket directory must match the
mapping derived from `stage`. Mismatches are `error`. This is the
same invariant work items have ("directory bucket equals metadata
status").

Filename rule: the workstream directory name must equal frontmatter
`id`. Mismatches are `error`.

Cross-reference checks: `related_focus` IDs must reference real focus
documents; `related_work_items` IDs must reference real work items;
`sibling_workstreams` IDs must reference real workstreams (and a
sibling's `sibling_workstreams` should symmetrically reference the
current workstream — a `warning` if asymmetric).

Transitions invariants: `transitions[]` must be append-only relative
to whatever was on disk before this run, must form a legal sequence
under the state machine (Layer 3 owns the legality table; Layer 1
just calls into it), and must have monotonic timestamps. Violations
are `error`. The validator reads the prior commit's frontmatter
(when present) to enforce append-only semantics, falling back to
"can't verify" with a `warning` when not in a git checkout.

Closure invariants: `stage in {closed, abandoned}` requires a
`closure` block with `reason`, and `reason: completed` requires
`evidence_supporting` non-empty. This mirrors the work-item terminal
rule.

`expected_evidence_at_close` invariant at closure: closure with
`reason: completed` requires that the count of evidence records of
each named kind referencing this workstream is at least the listed
number. (The validator may need to call into Layer 5b's evidence
loader to count; the dependency direction is fine because Layer 5b
loads from disk and doesn't depend on the validator.)

### Severity guidance

Errors block validation: bad enum, missing required field, bucket
mismatch, broken cross-reference, illegal transition.

Warnings are loadable but suspicious: asymmetric sibling, unmet
`expected_evidence_at_close` for a non-closed workstream that's been
in `reviewing` for >7 days, mode mismatch (workstream's
`mode_default: agent` but no `assigned_agents` listed).

Info: things worth noting but acceptable, e.g. workstream older than
30 days still in `proposed/`.

## 7. Snapshot and survey changes

### Summary

The existing `lrh snapshot` and `lrh survey` commands learn to
include workstreams in their output. This is small — they iterate
the typed model — but it's the user-visible payoff of Layer 1.

### Snapshot

`lrh snapshot` produces a compact JSON description of the project's
state. After Layer 1, snapshot output gains a `workstreams` array
parallel to `work_items`:

```json
{
  "schema_version": "1.1",
  "project": "logical_robotics_harness",
  "focus": [...],
  "workstreams": [
    {
      "id": "WS-LCATS-CORPORA-ANALYSIS",
      "title": "Analyze the LCATS corpora for transcription issues",
      "stage": "executing",
      "bucket": "active",
      "mode_default": "hybrid",
      "related_focus": ["FOCUS-LCATS-CORPORA"],
      "sibling_workstreams": ["WS-LCATS-CORPORA-UPDATE"],
      "transitions_count": 4,
      "open_for_days": 1
    }
  ],
  "work_items": [...]
}
```

The schema version bumps from `1.0` to `1.1`. Existing consumers that
ignore unknown fields keep working; new consumers can read the
workstreams array.

### Survey

`lrh survey` produces a human-readable Markdown overview. After
Layer 1, surveys include a "Workstreams" section listing each
workstream with its stage, mode, and last transition. The format is
deterministic and matches the existing work-item section style.

## 8. Precedence resolver changes

### Summary

Workstreams enter the precedence chain in position 5, between focus
and work items, narrowing focus and grouping work items. The
precedence-semantics decision record is updated in the same change
set per AGENTS.md.

### New chain

```text
1. principles
2. goal
3. roadmap
4. focus
5. workstreams           # NEW
6. work_items
7. guardrails
8. runtime
```

### Operational meaning

Workstreams refine focus the way work items refine focus today, but
at a coarser grain — a workstream is "a thread of work" while a work
item is "an executable unit." When the resolver builds the operational
context for a runtime invocation, it includes the active workstream(s)
under the active focus, then the work items under those workstreams.

When a runtime invocation references a work item (`--work-item
WI-0042`), the resolver walks up: which workstream owns this work
item? Is that workstream's `stage` compatible with executing this work
item? (E.g., a workstream in `reviewing` shouldn't be executing new
work items.) Mismatches are warnings; guardrails can promote them to
errors.

### Files updated together

Per AGENTS.md "precedence maintenance note," any precedence change
must keep the following synchronized in one change set:

```text
project/memory/decisions/precedence_semantics.md
src/lrh/control_plane/precedence.py
tests/control_plane/test_precedence.py
project/design/architecture.md (§"Four-plane model" / precedence subsection)
project/design/repository_spec.md (§"Precedence")
project/design/design.md (§"Precedence Model")
```

This is non-negotiable; the workstream precedence change is a single
PR that touches all of them.

## 9. CLI surface

### Summary

Layer 1 ships four `lrh workstream` subcommands. Advance, resume,
abandon, gates, and tidy ship in Layer 3.

### Commands

```bash
# Create a new workstream skeleton in proposed/.
lrh workstream new --id WS-LCATS-CORPORA-ANALYSIS \
                   --title "Analyze the LCATS corpora" \
                   --focus FOCUS-LCATS-CORPORA \
                   [--mode-default hybrid]

# List workstreams, optionally filtered by bucket or stage.
lrh workstream list [--bucket active] [--stage executing]

# Show a workstream's full state.
lrh workstream show WS-LCATS-CORPORA-ANALYSIS

# Validate workstream consistency (called by `lrh validate` too).
lrh workstream validate [--fix]
```

`--fix` on `validate` is intentionally limited: it can move a
mis-bucketed workstream to its correct bucket (analogous to the
work-item fixer), but it cannot edit frontmatter — that requires a
human decision.

## 10. Worked examples

### Summary

Two examples, both small. The first creates a workstream skeleton;
the second walks a validation failure to its fix.

### Example A — Creating a workstream

```bash
$ lrh workstream new --id WS-LCATS-CORPORA-ANALYSIS \
                     --title "Analyze the LCATS corpora" \
                     --focus FOCUS-LCATS-CORPORA \
                     --mode-default hybrid
Created project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/
  workstream.md
$ cat project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/workstream.md
---
id: WS-LCATS-CORPORA-ANALYSIS
title: Analyze the LCATS corpora
stage: conceived
mode_default: hybrid
created_on: 2026-04-26
updated_on: 2026-04-26
related_focus:
  - FOCUS-LCATS-CORPORA
gates:
  designed_to_planned: auto
  planned_to_executing: confirm
  executing_to_reviewing: auto
  reviewing_to_closed: confirm
transitions: []
---

# WS-LCATS-CORPORA-ANALYSIS

(Add a description here — what is this workstream for?)
```

### Example B — Validation catches a bucket mismatch

A contributor manually edits `stage: planned` to `stage: executing`
without moving the directory:

```bash
$ lrh workstream validate
ERROR: WS-LCATS-CORPORA-ANALYSIS — bucket-stage mismatch:
  on-disk bucket: proposed/
  metadata stage: executing
  expected bucket: active/
  fix: mv project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS \
          project/workstreams/active/WS-LCATS-CORPORA-ANALYSIS

$ lrh workstream validate --fix
moved project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS
   -> project/workstreams/active/WS-LCATS-CORPORA-ANALYSIS
$ lrh workstream validate
OK
```

## 11. Tests

### Summary

Tests live under `tests/control_tests/workstream/` and follow the
existing module-mirroring layout per STYLE.md.

### Test plan

`models_test.py` — round-trip a `Workstream` dataclass through a
realistic frontmatter dict; confirm enum coercion, defaults, and
required-field handling.

`schema_test.py` — exhaustive coverage of the validator: missing
required fields, bad enums, malformed dates, illegal transitions,
unmet closure invariants. Per STYLE.md, prefer real fixture files
under `tests/control_tests/workstream/fixtures/` over heavy mocking.

`loader_test.py` — load a fixture `project/` containing several
workstreams across all four buckets; confirm the typed model is
populated correctly and that bad workstreams produce findings without
aborting the load.

`paths_test.py` — bucket mapping, slug-to-directory naming, the
`--fix` move logic.

Integration test: `workstream_validation_smoke_test.py` — run `lrh
validate` against a fixture project that contains workstreams in
every stage, in every legal and a few illegal configurations. Assert
exit code, finding count, and structured-output schema.

Determinism: all fixture timestamps are baked in; no `datetime.now()`
in tests (per STYLE.md §"Determinism"). UTF-8 encoding is explicit
(per STYLE.md §"Encoding").

## 12. Risks

### Summary

The risks for Layer 1 are small and known. Most of them are about
keeping documentation in sync.

The precedence-semantics decision record drift is the dominant risk.
Mitigation: a single PR updates all six files listed in §8 in
lockstep. CI gets a small docs-sync check that compares the
ordering across files.

Backwards compatibility for existing snapshot consumers is mostly a
non-issue (we add a field; snapshot consumers that care about schema
versioning bump from 1.0 to 1.1), but it's worth flagging in the PR
description.

`Workstream` ID conflicts with `WS-*` strings used elsewhere in the
project (none today, but worth a project-wide grep before landing).

## 13. References

`project/design/design.md` — current LRH design document, especially
§"Precedence Model," §15 ("Structured Metadata Model"), and §15.5
("Validation Expectations").

`project/design/repository_spec.md` — current repository specification,
especially §"Work Items" (the bucket pattern this layer mirrors) and
§"Precedence."

`project/memory/decisions/precedence_semantics.md` — the canonical
precedence-semantics decision record. Workstream addition is a
required co-edit.

`project/work_items/README.md` — current work-item bucket conventions.
This proposal preserves them and adds a parallel structure for
workstreams.

`AGENTS.md` — the precedence-maintenance note in particular.

`STYLE.md` — test layout, determinism, encoding, type-annotation, and
import conventions for the new modules.

[github/spec-kit](https://github.com/github/spec-kit) — for the
"constitution" concept that maps onto LRH's `principles/`. We do not
adopt their templates.

[Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) — for the
lighter-weight spec-driven framing. Useful as a reference for keeping
LRH's spec layer (Layer 2) lean.

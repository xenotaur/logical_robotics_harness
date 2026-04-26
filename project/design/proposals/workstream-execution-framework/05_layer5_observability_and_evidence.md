---
id: PROP-WORKSTREAM-LAYER5-OBSERVABILITY-EVIDENCE
title: Layer 5 — Observability and Evidence
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 5 — Observability and Evidence

## Summary

This sub-proposal specifies **two top-level packages with a
unidirectional dependency**: Layer 5a (`src/lrh/observability/`)
emits ephemeral spans and traces, JSON-on-disk by default, OTel-
collector-backed eventually; Layer 5b (`src/lrh/evidence/`)
produces durable Markdown records under `project/evidence/` via
extractors that read traces. The split matches OTel's "GenAI"
semantic conventions on the telemetry side
([OpenTelemetry GenAI semconv][otel-genai]) and LRH's existing
evidence philosophy on the durability side: **status grounded in
evidence, evidence grounded in artifacts** (per AGENTS.md
§"Evidence"). Layer 5b imports Layer 5a but never the reverse —
that's the unidirectional dependency.

The deliverable boundary is: after this layer ships, every workstream
advance produces a `project/runs/RUN-{ulid}/` directory containing
spans and transcripts (Layer 5a), and an `lrh evidence extract` pass
(triggered automatically at runtime stop, manually re-runnable)
produces typed evidence records under `project/evidence/` (Layer 5b).
Manual evidence flows through a staging-and-promotion pattern that
preserves manual-mode parity. Per-evidence-kind schemas live in a
project-local registry under `project/evidence/schemas/` —
Pass B's discovery surfaced this need explicitly.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [The 5a / 5b split](#2-the-5a--5b-split)
3. [Layer 5a — Observability](#3-layer-5a--observability)
4. [Layer 5b — Evidence](#4-layer-5b--evidence)
5. [Per-evidence-kind schema registry](#5-per-evidence-kind-schema-registry)
6. [Manual evidence: stub-and-fill](#6-manual-evidence-stub-and-fill)
7. [CLI surface](#7-cli-surface)
8. [Worked examples](#8-worked-examples)
9. [Tests](#9-tests)
10. [Risks](#10-risks)
11. [References](#11-references)

## 1. Goals and non-goals

### Summary

Layer 5 makes a workstream auditable. Telemetry is the running
record; evidence is the durable record. Both have to exist; neither
substitutes for the other.

### Goals

A typed `Span` and `Trace` model that aligns with OTel GenAI
semantic conventions where stable. A JSON-on-disk default backend
that produces `project/runs/RUN-{ulid}/spans.jsonl` and
`transcript.jsonl`. An OTel-collector backend designed but deferred
(documented but not first-shipping). A typed `EvidenceRecord`
dataclass with `source: human | agent_trace | tool_output |
external`. A pluggable `EvidenceExtractor` Protocol with a
registry. A built-in extractor set covering test runs, file
modifications, commits, tool errors, manual reviews, and MCP
results. Per-evidence-kind schema registration under
`project/evidence/schemas/`. A staging-and-promotion flow for manual
evidence. CLI for both layers (`lrh observability` and `lrh
evidence`).

### Non-goals

We do not implement an OTel collector (we instrument; the user can
run their own collector). We do not ship Langfuse-specific
integration (it's the natural target for the OTel backend, but
that's deferred). We do not implement an evidence query language
beyond simple filters (a structured query CLI is future work and
is named in §10). We do not version evidence records (no
supersedes/superseded_by); evidence is append-only by design.

## 2. The 5a / 5b split

### Summary

Two packages, one direction of dependency. This section nails down
why the split and what each side owns.

### Why two packages

Telemetry and evidence have different lifetimes. Spans are useful
for the next 24-48 hours of debugging; evidence is useful for the
next 24-48 months of reading project history. Conflating them
forces tradeoffs that don't fit either need.

Telemetry is high-volume; evidence is low-volume. A single agent
prompt produces dozens of span events; an evidence record is a
once-per-prompt artifact. Storing them the same way is wrong.

Telemetry is machine-first; evidence is human-first. Spans are
attribute bags optimized for query and analysis; evidence records
are Markdown documents optimized for reading.

OTel has a vocabulary for telemetry ([otel-genai][otel-genai]) but
no vocabulary for project-level evidence. Different schemas, different
governance, different lifecycle.

### The dependency direction

```text
src/lrh/evidence/    --imports-->    src/lrh/observability/
                                                 |
                                                 +-- never imports evidence
```

Layer 5a doesn't know what evidence is. It emits spans, writes
transcripts, exposes a backend interface. Layer 5b imports Layer
5a's typed models to read traces and produces evidence records from
them. This direction matches data flow (spans → evidence) and keeps
each layer testable in isolation.

### What each side owns

Layer 5a owns: span emission, trace identifiers, span exporters
(JSON-file default; OTel-collector deferred), transcript persistence,
the `Observer` Protocol that runtime backends call into, run
directories under `project/runs/`, run garbage collection.

Layer 5b owns: evidence-record schema, evidence on-disk layout under
`project/evidence/`, the `EvidenceExtractor` Protocol, the extractor
registry, per-evidence-kind schema registration, manual stub-and-fill
flow, evidence-record validation.

## 3. Layer 5a — Observability

### Summary

Layer 5a is "structured logs + spans on disk by default." The model
aligns with OTel GenAI conventions; the backend is JSON files; the
Observer interface is what Layer 4's runtimes call into.

### Module layout

```text
src/lrh/observability/
  __init__.py
  api.py                # Observer Protocol; SpanContext
  models.py             # Span, Trace, RunDirectory
  attributes.py         # OTel-aligned attribute name constants
  backends/
    __init__.py
    file_backend.py     # default; writes spans.jsonl + transcript.jsonl
    otel_backend.py     # designed; not first-shipping
  run_directory.py      # project/runs/RUN-{ulid}/ helpers
  gc.py                 # `lrh observability gc` implementation
```

Tests:

```text
tests/observability_tests/
  __init__.py
  api_test.py
  models_test.py
  file_backend_test.py
  run_directory_test.py
  gc_test.py
  observer_smoke_test.py
```

### The `Observer` Protocol

```python
# src/lrh/observability/api.py
from typing import Protocol
from lrh.observability import models


class Observer(Protocol):
    """Sink for spans and transcript events.

    Layer 4's runtime backends call into this Protocol to record what
    they did. The default implementation writes JSON files under
    project/runs/RUN-{ulid}/.
    """

    def start_run(
        self,
        workstream_id: str,
        prompt_id: str,
        invoker: str,
    ) -> models.RunContext:
        """Begin a run and return a context object."""

    def start_span(
        self,
        ctx: models.RunContext,
        name: str,
        attributes: dict,
    ) -> models.SpanContext:
        ...

    def add_event(
        self,
        span: models.SpanContext,
        name: str,
        attributes: dict,
    ) -> None:
        ...

    def end_span(
        self,
        span: models.SpanContext,
        attributes: dict | None = None,
        status: str = "ok",
    ) -> None:
        ...

    def end_run(
        self,
        ctx: models.RunContext,
        outcome: str,
    ) -> None:
        ...

    def transcript_append(
        self,
        ctx: models.RunContext,
        record: dict,
    ) -> None:
        """Append a structured transcript record (JSONL)."""
```

### Span attributes

Where OTel GenAI conventions are stable, we use them; where they're
not, we use `lrh.*`. Examples:

```text
# OTel GenAI (per opentelemetry.io/docs/specs/semconv/gen-ai/)
gen_ai.provider.name             = "anthropic"
gen_ai.request.model             = "claude-sonnet-4-7"
gen_ai.request.max_tokens        = 8192
gen_ai.usage.input_tokens        = 8231
gen_ai.usage.output_tokens       = 1842

# LRH-specific
lrh.workstream.id                = "WS-LCATS-CORPORA-ANALYSIS"
lrh.workstream.stage             = "executing"
lrh.prompt.id                    = "PROMPT(WS-...:P_001)[...]"
lrh.backend.name                 = "claude_agent_sdk"
lrh.runtime.permission_mode      = "accept_edits"
lrh.runtime.allowed_tools        = ["Read", "Write"]
lrh.cost.usd                     = 0.31
```

The OTel-aligned attribute names live in
`src/lrh/observability/attributes.py` as constants so the Python
code never spells them inline. This makes future schema-version
bumps a one-file change.

### Span structure

```python
@dataclass(frozen=True)
class Span:
    span_id: str             # ULID
    parent_span_id: str | None
    trace_id: str            # ULID
    name: str                # e.g. "lrh.run", "lrh.runtime.execute"
    started_at: str          # ISO-8601
    ended_at: str | None
    attributes: dict
    events: tuple[SpanEvent, ...] = ()
    status: str = "ok"       # "ok" | "error"


@dataclass(frozen=True)
class SpanEvent:
    name: str                # "tool.preuse", "tool.postuse", "agent.completion"
    at: str                  # ISO-8601
    attributes: dict
```

### Run directory layout

```text
project/runs/
  RUN-01J3K9ABCXYZ.../
    metadata.json           # workstream_id, prompt_id, invoker, started_at, etc.
    spans.jsonl             # one Span per line
    transcript.jsonl        # one tool-call/response record per line
    final_message.txt       # agent's final assistant message
```

The run directory is on disk and committed to Git when meaningful
(e.g., the run that produced an evidence record); transient runs
that don't produce evidence are eligible for garbage collection via
`lrh observability gc`.

### Content capture pattern

Per OTel guidance ([otel-genai][otel-genai]), large content (full
prompts, large tool inputs, long completions) belongs in transcripts
on disk; spans carry references rather than full content. Our
transcript records use `transcript_record_id` references that span
events point at. This keeps spans cheap to query while preserving
the full content auditing trail.

### File backend (default, first-shipping)

`backends/file_backend.py` implements the Observer Protocol against
the on-disk run directory. JSONL writes are append-only (one
`fcntl.flock`-bracketed `os.write` per record) so that even
crashing runs leave readable spans. UTF-8 is explicit per
STYLE.md §"Encoding."

### OTel backend (designed, deferred)

`backends/otel_backend.py` is sketched in this proposal but not
shipped first. It would forward the same Spans through an
OpenTelemetry SDK exporter (`opentelemetry-sdk` plus an OTLP gRPC
exporter pointed at a user-provided collector). The likely
production target is OpenLLMetry-instrumented Langfuse
([traceloop OpenLLMetry][openllmetry], [langfuse.com][langfuse]),
which natively supports the GenAI semantic conventions. Shipping the
file backend first means we can prove the model end-to-end without
a collector dependency; switching to OTel later is a backend swap,
not an API change.

## 4. Layer 5b — Evidence

### Summary

Layer 5b turns runtime traces and human contributions into durable
Markdown records under `project/evidence/`. The dataclass shape, the
extractor Protocol, the registry, and the staging-and-promotion flow
all live here.

### Module layout

```text
src/lrh/evidence/
  __init__.py
  api.py               # EvidenceExtractor Protocol; ExtractorRegistry
  models.py            # EvidenceRecord, Provenance, EvidenceReference
  schema.py            # frontmatter + body validation
  loader.py            # disk -> typed model
  writer.py            # typed model -> disk
  extractors/
    __init__.py
    test_run.py        # TestRunExtractor
    file_modification.py  # FileModificationExtractor
    commit.py          # CommitExtractor
    tool_error.py      # ToolErrorExtractor
    manual_review.py   # ManualReviewExtractor
    mcp_result.py      # McpResultExtractor
  staging.py           # stub-and-fill flow for manual evidence
  registry.py          # per-evidence-kind schema loader
```

Tests:

```text
tests/evidence_tests/
  __init__.py
  api_test.py
  models_test.py
  schema_test.py
  loader_test.py
  writer_test.py
  extractors/
    test_run_test.py
    file_modification_test.py
    commit_test.py
    tool_error_test.py
    manual_review_test.py
    mcp_result_test.py
  staging_test.py
  registry_test.py
  evidence_smoke_test.py
```

### The `EvidenceRecord` dataclass

```python
# src/lrh/evidence/models.py
import enum
from dataclasses import dataclass, field
from pathlib import Path


class Provenance(enum.Enum):
    AGENT_TRACE = "agent_trace"
    HUMAN       = "human"
    TOOL_OUTPUT = "tool_output"
    EXTERNAL    = "external"


@dataclass(frozen=True)
class EvidenceReference:
    kind: str            # "file", "trace", "url", "evidence" (back-reference)
    path: str | None     # file path (for kind=file)
    trace_id: str | None # trace id (for kind=trace)
    url: str | None      # url (for kind=url)
    evidence_id: str | None  # evidence id (for kind=evidence)


@dataclass(frozen=True)
class EvidenceRecord:
    id: str                          # "ev-..."
    kind: str                        # registered evidence kind
    workstream_id: str
    work_item_id: str | None
    stage: str                       # workstream stage at capture
    source: Provenance
    title: str
    summary: str
    references: tuple[EvidenceReference, ...]
    captured_at: str                 # ISO-8601
    captured_by: str                 # contributor id
    data: dict                       # structured findings (Pass-B finding)
    body: str = ""                   # the Markdown narrative
```

### The `data:` field (Pass-B finding)

`data` is a structured dict whose schema is registered per evidence
kind. This was a key Pass-B discovery — without `data`, evidence is
unstructured prose that downstream tools (the orchestrator's closure
check; cross-workstream queries; the validator) can't read. With
`data`, an evidence record can express:

```yaml
data:
  story_id: gutenberg-2148
  story_title: "The Tell-Tale Heart"
  author: "Edgar Allan Poe"
  issues:
    - category: encoding_glitch
      severity: medium
      span: { start_line: 12, end_line: 12 }
      excerpt: "â€¦"
      reasoning: "Mojibake at em-dash"
  no_issues_found: false
```

The `no_issues_found` field is also a Pass-B finding: without an
explicit boolean, "no issues" and "agent didn't analyze" are
indistinguishable. The registered schema for `corpus_issue_report`
makes `no_issues_found` required.

### On-disk layout

```text
project/evidence/
  ev-WS-LCATS-CORPORA-ANALYSIS-P001.md
  ev-WS-LCATS-CORPORA-ANALYSIS-P002.md
  ev-WS-LCATS-CORPORA-ANALYSIS-P006.md   # summary
  ev-WS-LCATS-CORPORA-ANALYSIS-P007.md   # cross-review
  ev-HUMAN-CORPORA-ANALYSIS-001.md       # human-produced
  schemas/
    corpus_issue_report.schema.json
    analysis_summary.schema.json
    cross_review_comparison.schema.json
  staging/                                # manual stub-and-fill
    ev-HUMAN-CORPORA-ANALYSIS-002.md
```

The flat layout (no subdirectories under `evidence/`) is deliberate:
evidence records are globally discoverable by id; the workstream
membership is in frontmatter. This matches how work items are
organized today.

### The `EvidenceExtractor` Protocol

```python
# src/lrh/evidence/api.py
from typing import Protocol
from lrh.evidence import models
from lrh.observability import models as obs_models


class EvidenceExtractor(Protocol):
    """Reads runtime traces (and optionally other inputs) to produce
    evidence records.

    Multiple extractors run on the same trace; their outputs are
    merged into the per-run evidence ledger. Extractors are pure:
    they read inputs and return a list of EvidenceRecord; they do
    not write to disk themselves.
    """

    def name(self) -> str:
        ...

    def applies_to(
        self,
        run: obs_models.RunContext,
        spans: tuple[obs_models.Span, ...],
        transcript: tuple[dict, ...],
    ) -> bool:
        """Return True if this extractor has anything to extract from
        this run."""

    def extract(
        self,
        run: obs_models.RunContext,
        spans: tuple[obs_models.Span, ...],
        transcript: tuple[dict, ...],
    ) -> tuple[models.EvidenceRecord, ...]:
        """Produce evidence records. Pure; no I/O."""
```

Extractors are registered with `ExtractorRegistry` and run in
deterministic order at runtime stop (and on `lrh evidence extract`).

### Built-in extractors

`TestRunExtractor` — looks for `pytest`/`unittest` invocations in
the trace; produces a `test_run` evidence record summarizing
pass/fail counts.

`FileModificationExtractor` — looks for Write tool calls; produces
a `file_modification` evidence record listing modified paths.

`CommitExtractor` — looks for git-commit tool calls (or shell
commands invoking git); produces a `commit` evidence record with
SHA and message.

`ToolErrorExtractor` — looks for tool failures; produces a
`tool_error` evidence record describing what failed.

`ManualReviewExtractor` — handles the manual-review case: the
contributor wrote a record under `staging/` with frontmatter
metadata; the extractor verifies and promotes it.

`McpResultExtractor` — looks for MCP tool calls (Layer 6); produces
`mcp_result` evidence with the tool, args, and result. Often gets
specialized per-bridge under `bridges/extractors/` (Layer 6).

### Two evidence-production patterns (Pass-B finding)

Pass B surfaced two patterns the Layer 5b design must name explicitly:

Pattern A: **Agent writes evidence directly via Write tool;
extractor verifies and promotes.** The agent's prompt instructs it
to write a `staging/ev-WS-...-PNNN.md` file in the right shape; the
extractor reads the staging file, validates against the registered
schema, and promotes to `project/evidence/`. This is what
`corpus_issue_report` evidence does in the Pass B example. It's
appropriate when the agent is the right party to produce structured
findings.

Pattern B: **Extractor reads structured trace data and produces
evidence.** The agent operates normally (no special evidence-write
prompt); the extractor reads spans/transcript and synthesizes the
evidence. This is what `test_run`, `commit`, and `tool_error`
evidence does. It's appropriate when the trace data already contains
the evidence and we just need to lift it.

The proposal supports both. Per-prompt frontmatter declares which
pattern applies via `evidence_pattern: agent_writes | extractor_synthesizes`.

## 5. Per-evidence-kind schema registry

### Summary

Pass B revealed that without per-kind schemas, evidence records are
too unstructured to drive validation. The registry lives in the
project — not in LRH itself — because evidence kinds are
project-specific.

### Registry layout

```text
project/evidence/schemas/
  corpus_issue_report.schema.json
  analysis_summary.schema.json
  cross_review_comparison.schema.json
  test_run.schema.json              # built-in kinds also registered here
  file_modification.schema.json
  commit.schema.json
  tool_error.schema.json
```

Each schema is a JSON Schema document validating the `data:` block
of an evidence record of that kind. LRH ships built-in schemas for
the built-in extractor kinds (under `src/lrh/evidence/schemas/`,
copied to project on `lrh evidence init`); projects add their own
under `project/evidence/schemas/`.

### Registry API

```python
# src/lrh/evidence/registry.py
from pathlib import Path


class SchemaRegistry:
    """Loads and validates per-evidence-kind schemas."""

    def __init__(self, project_path: Path) -> None:
        self._builtin = self._load_builtin()
        self._project = self._load_project(project_path)

    def get(self, kind: str) -> dict | None:
        """Return JSON Schema for a kind, or None if unregistered."""
        return self._project.get(kind) or self._builtin.get(kind)

    def validate(
        self,
        kind: str,
        data: dict,
    ) -> list[str]:
        """Return validation errors for this data dict against the
        registered schema."""
        ...
```

The validator from Layer 1 calls `SchemaRegistry.validate` when
loading evidence records. Errors are surfaced through the same
severity model.

### Worked schema example

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "corpus_issue_report",
  "type": "object",
  "required": ["story_id", "story_title", "issues", "no_issues_found"],
  "properties": {
    "story_id": {"type": "string"},
    "story_title": {"type": "string"},
    "author": {"type": "string"},
    "no_issues_found": {"type": "boolean"},
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["category", "severity", "reasoning"],
        "properties": {
          "category": {
            "type": "string",
            "enum": [
              "encoding_glitch",
              "missing_ending",
              "transcriber_note_residue",
              "other"
            ]
          },
          "severity": {
            "type": "string",
            "enum": ["low", "medium", "high"]
          },
          "span": {
            "type": "object",
            "properties": {
              "start_line": {"type": "integer"},
              "end_line": {"type": "integer"}
            }
          },
          "excerpt": {"type": "string"},
          "reasoning": {"type": "string"}
        }
      }
    }
  }
}
```

The validator enforces the schema on every evidence record of kind
`corpus_issue_report` whether agent- or human-produced. This is how
Layer 5b enforces Invariant A (manual-mode parity) at the record
level.

## 6. Manual evidence: stub-and-fill

### Summary

Manual evidence flows through `project/evidence/staging/` so that
the human's record looks structurally identical to the agent's. The
extractor for manual evidence is the same code path as for agent
evidence — just `source: human` instead of `source: agent_trace`.

### The flow

Step 1: a manual-mode prompt is stamped (`PROMPT-XXX-MANUAL.md`) by
Layer 3's orchestrator. The prompt instructs the human to write an
evidence stub in `staging/`.

Step 2: the human writes
`project/evidence/staging/ev-HUMAN-WS-X-001.md` using the
`evidence_stub.md.tmpl` template (Layer 2). They fill in the `data:`
block according to the registered schema.

Step 3: the human runs `lrh evidence promote
ev-HUMAN-WS-X-001`. The CLI runs `ManualReviewExtractor`, which
validates the staging file against the registered schema and (if
valid) moves it to `project/evidence/`.

Step 4: the workstream's transition (executing → reviewing or
similar) references the promoted evidence record.

### Why staging

The staging directory is a buffer that lets a human edit iteratively
without committing partial records to the durable evidence store.
It also gives the validator a clear place to enforce schema before
promotion, preventing malformed evidence from contaminating
`project/evidence/`.

### Symmetric for agent-written evidence

Pattern A (agent writes evidence directly) also writes to
`staging/` first, then `lrh evidence extract` promotes after
schema validation. So both pattern A and the manual flow use the
same staging convention — that's manual-mode parity in action.

## 7. CLI surface

### Summary

`lrh observability` for telemetry; `lrh evidence` for evidence.

### Observability commands

```bash
# List runs.
lrh observability list-runs [--workstream WS-...] [--limit N]

# Show a run's spans and transcript summary.
lrh observability show-run RUN-...

# Garbage-collect runs that didn't produce evidence and are older
# than --age (default 30 days).
lrh observability gc [--age 30] [--dry-run]

# Export a run as a single bundle (tar.gz of run-dir + referenced
# evidence) for sharing.
lrh observability export RUN-... --out runfile.tar.gz
```

### Evidence commands

```bash
# Initialize a project's evidence directory + schemas.
lrh evidence init

# List evidence records, optionally filtered.
lrh evidence list [--workstream WS-...] [--kind KIND] [--source human]

# Show one record.
lrh evidence show ev-...

# Re-extract evidence from a stored run.
lrh evidence extract RUN-... [--dry-run]

# Promote a staging record to project/evidence/.
lrh evidence promote ev-...

# Validate evidence records against registered schemas.
lrh evidence verify [ev-...]

# (Future) Query evidence by kind/data fields.
lrh evidence query --kind corpus_issue_report --severity high
```

`--dry-run` is supported on `extract` and `gc` per STYLE.md §"Scripts."

## 8. Worked examples

### Summary

Three examples covering the dominant paths.

### Example A — Agent writes evidence; extractor promotes

Agent runs `PROMPT-001` with prompt body asking it to write
`staging/ev-WS-...-P001.md`. The agent uses Write to create the
file. At stop, `EvidenceExtractionStopHook` (Layer 4) calls Layer
5b's extractor registry. `ManualReviewExtractor.applies_to(...)`
returns True (a staging file exists for this run). `extract(...)`
validates the file against `corpus_issue_report.schema.json` and
returns the parsed `EvidenceRecord`. The orchestrator's writer
moves it from `staging/` to `project/evidence/`. The transition
referencing this evidence is appended to the workstream.

### Example B — Manual evidence by a human collaborator

The human runs `lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
--mode manual` at the reviewing stage. Layer 3 stamps
`PROMPT-008-MANUAL-REVIEW.md`. The human reads the agent's evidence
records, opens five Poe stories themselves, and writes
`staging/ev-HUMAN-CORPORA-ANALYSIS-001.md` through
`-005.md` using the `evidence_stub.md.tmpl` template. They run
`lrh evidence promote ev-HUMAN-CORPORA-ANALYSIS-001` for each. Then:

```bash
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --confirm-manual \
    --transition-note "Human review complete; 5 records produced."
ADVANCED  reviewing -> closed (CONFIRM gate satisfied)
```

The cross-review-comparison evidence (`P-007`) reads both the
agent's and the human's records and produces a `cross_review_comparison`
record with `agreement_rate: 0.73`. The closure check passes
because `expected_evidence_at_close` requires
`cross_review_comparison: 1` and we have one.

### Example C — Re-extracting evidence from a stored run

A schema bug is found in `corpus_issue_report`: the original schema
allowed `severity: critical` but the spec says only
`low | medium | high`. The schema is fixed. To re-validate prior
runs:

```bash
$ lrh evidence verify
ERROR: ev-WS-LCATS-CORPORA-ANALYSIS-P002 — data.issues[0].severity:
       'critical' is not one of ['low', 'medium', 'high']

$ lrh evidence extract RUN-01J3K9... --dry-run
would re-emit ev-WS-LCATS-CORPORA-ANALYSIS-P001..P005 from spans
diff:
  -severity: critical
  +severity: high
```

The contributor inspects the dry-run, confirms the rewrite is
safe, and runs without `--dry-run`. The re-extraction is recorded
in the run's `metadata.json` so the audit trail is preserved.

## 9. Tests

### Summary

Tests follow the established LRH module-mirroring layout. Determinism
is critical because evidence records contain timestamps that humans
read.

### Test plan

`api_test.py` (observability) — Protocol shape; observer-context
lifecycle.

`models_test.py` — span and trace round-trip; ULID generation
determinism (seeded).

`file_backend_test.py` — append-only writes; crash safety (writes
that fail mid-record leave the prior record intact).

`run_directory_test.py` — directory creation; metadata.json shape;
filename slug rules.

`gc_test.py` — gc preserves runs that produced evidence; respects
`--age`; `--dry-run` produces a plan.

`api_test.py` (evidence) — extractor Protocol shape; registry merging
order (project overrides built-ins for the same kind).

`models_test.py` (evidence) — evidence-record round-trip;
EvidenceReference variants.

`schema_test.py` — every built-in schema parses as JSON Schema;
schemas reject malformed data dicts.

`writer_test.py` — round-trip evidence record; deterministic
frontmatter ordering.

Per-extractor tests under `tests/evidence_tests/extractors/` —
each extractor gets a fixture run and asserts the produced
records match a golden snapshot.

`staging_test.py` — staging file lifecycle; promote moves the file;
malformed staging is rejected.

`registry_test.py` — built-in schema loading; project overrides;
unknown kind returns None.

`evidence_smoke_test.py` — full flow: a fake run produces a
staging file, an extractor promotes it, the validator verifies it.

### Manual-mode parity test for evidence

A test in `tests/evidence_tests/manual_parity_test.py` asserts that
an agent-produced and a human-produced record for the same evidence
kind are byte-identical modulo `source`, `captured_by`,
`captured_at`. This is the Layer 5b counterpart to Layer 3's
`manual_parity_test.py`.

## 10. Risks

### Summary

Two structural risks plus two operational ones.

### Risk: schema-registry drift

Per-evidence-kind schemas can drift between projects, and what's
"the same kind" can become ambiguous. Mitigation: built-in kinds
have schemas in LRH; project-specific kinds must be declared in
`project/evidence/schemas/`; the validator complains about
unregistered kinds.

### Risk: extractor false positives

`ManualReviewExtractor.applies_to` uses heuristics (does a staging
file with a matching workstream id exist?) that can produce
unintended promotions. Mitigation: schema validation is mandatory
before promotion; promotions are recorded in the run's metadata
and reversible by deleting from `project/evidence/` and re-running
extraction.

### Risk: orphaned spans / runs

A workstream advance that crashes mid-run leaves a partial
RUN-{ulid} directory. Mitigation: `lrh observability gc` cleans
up partial runs older than `--age`; the file backend's
append-only writes mean even partial runs are inspectable.

### Risk: evidence query gap

We don't ship a real query CLI. `lrh evidence list --kind X` is
filtering, not querying. For Pass-B's "show me all high-severity
findings across analyzed stories," users currently grep. Future
work: a `lrh evidence query` with structured filters over `data:`
fields. Out of scope for v1.

### Risk: cost-attribution holes

We attribute cost per prompt and sum per workstream, but the
orchestrator's overhead (validation, idempotence checks, evidence
extraction) isn't tracked. Pass B flagged this. Mitigation:
operational telemetry on the meta-layer is on the future-work
list (umbrella §9 open question).

## 11. References

[OpenTelemetry GenAI semconv][otel-genai] — span attribute
vocabulary. We align where stable; per the spec, "as of March
2026, most GenAI semantic conventions are in experimental status,"
which is why we name OTel-aligned attributes through a constants
module that can absorb churn.

[OpenTelemetry GenAI agent spans][otel-agent-spans] — specifically
covers agent and framework spans, which is the shape Layer 5a
emits. Useful reference for span hierarchy decisions.

[traceloop OpenLLMetry][openllmetry] — likely instrumentation
library for the OTel-collector backend. Already implements the
GenAI semconv.

[langfuse.com][langfuse] — likely self-hosted UI for the OTel
backend. Natively supports GenAI semconv per their docs.

[anthropics/claude-agent-sdk-python][cas] — for the W3C trace
context propagation that our spans tie into when the SDK is the
runtime.

`project/design/design.md` §"Evidence" and §"Status" — existing LRH
evidence philosophy. This proposal extends rather than replaces.

`AGENTS.md` §"Evidence" — "Status should be grounded in evidence.
Do not generate optimistic summaries that are detached from tests,
logs, metrics, screenshots, reports, or review notes." Layer 5b
operationalizes this.

`STYLE.md` §"Encoding," §"Determinism" — UTF-8, seeded randomness,
stable ordering — all enforced in this layer's tests.

[otel-genai]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
[otel-agent-spans]: https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
[openllmetry]: https://www.traceloop.com/docs/openllmetry
[langfuse]: https://langfuse.com/
[cas]: https://github.com/anthropics/claude-agent-sdk-python

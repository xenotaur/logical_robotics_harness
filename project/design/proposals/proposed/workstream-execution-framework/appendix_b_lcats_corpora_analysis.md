---
id: PROP-WORKSTREAM-APPENDIX-B-LCATS-CORPORA
title: Appendix B — Worked Example, WS-LCATS-CORPORA-ANALYSIS
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Appendix B — Pass-B Worked Example: WS-LCATS-CORPORA-ANALYSIS

## Summary

This appendix walks one workstream — `WS-LCATS-CORPORA-ANALYSIS`,
the LCATS literary-corpus analysis task surfaced by Pass B — end-
to-end across all six layers of the execution framework. The
purpose is twofold: (1) to demonstrate that the framework actually
holds up under a non-trivial real workload, and (2) to surface the
implementation findings Pass B produced (per-evidence-kind schemas,
the `data:` field on evidence records, `no_issues_found: true`,
sibling workstreams, and `expected_evidence_at_close`) inside the
context that motivated them.

The corpus is five Edgar Allan Poe stories pulled from Project
Gutenberg into `project/workstreams/active/WS-LCATS-CORPORA-\
ANALYSIS/corpus/`. The task is: classify each story for three
kinds of textual issues — `encoding_glitch`, `missing_ending`,
`transcriber_note_residue` — under a $10 cost budget, with a 70%
agreement threshold against a human collaborator, in `mode: hybrid`
(agent does first-pass, human reviews on `executing → reviewing`).

The walkthrough is sectioned by layer (Layer 1 first, Layer 6 last,
mirroring the proposal sequence). Each section shows the on-disk
artifacts the layer produces or consumes, the relevant frontmatter
or code, and what Pass B specifically discovered when we ran this
case manually.

## Table of contents

1. [The workstream at a glance](#1-the-workstream-at-a-glance)
2. [Pass-B findings recap](#2-pass-b-findings-recap)
3. [Layer 1 — Control-plane on-disk artifacts](#3-layer-1--control-plane-on-disk-artifacts)
4. [Layer 2 — Templates instantiated](#4-layer-2--templates-instantiated)
5. [Layer 3 — Stage transitions and prompts](#5-layer-3--stage-transitions-and-prompts)
6. [Layer 4 — Agent runtime calls](#6-layer-4--agent-runtime-calls)
7. [Layer 5a — Telemetry](#7-layer-5a--telemetry)
8. [Layer 5b — Evidence records](#8-layer-5b--evidence-records)
9. [Layer 6 — Bridge attachment (none here)](#9-layer-6--bridge-attachment-none-here)
10. [Closure check and the `expected_evidence_at_close` machinery](#10-closure-check-and-the-expected_evidence_at_close-machinery)
11. [Sibling workstreams and the post-Pass-B observation](#11-sibling-workstreams-and-the-post-pass-b-observation)
12. [What this case demonstrates about the framework](#12-what-this-case-demonstrates-about-the-framework)
13. [References](#13-references)

## 1. The workstream at a glance

### Summary

`WS-LCATS-CORPORA-ANALYSIS` analyzes five public-domain literary
texts for three issue types, in a hybrid (agent + human-review)
mode, under a $10 cost cap, with cross-review against a human
collaborator.

### The corpus

Five Poe stories, public domain via Project Gutenberg:

```text
project/workstreams/active/WS-LCATS-CORPORA-ANALYSIS/corpus/
├── pit_and_the_pendulum.txt
├── the_raven.txt
├── the_telltale_heart.txt
├── the_masque_of_the_red_death.txt
└── the_fall_of_the_house_of_usher.txt
```

These are pinned to a specific Project Gutenberg snapshot (URL +
SHA256 in `corpus/SOURCES.md`) so the analysis is reproducible.

### The three issue types

`encoding_glitch` — mojibake or mis-decoded characters (e.g.,
`â€™` where `'` belonged), typical of Latin-1 → UTF-8 conversion
errors.

`missing_ending` — narrative truncation, often from Project
Gutenberg headers/footers being mis-stripped.

`transcriber_note_residue` — `[Transcriber's Note: ...]` blocks
left in the body of the text rather than collected at the end.

These are the same three issues Pass B used because they are
easy to generate ground-truth labels for and they exercise three
different reasoning shapes (regex / structural / contextual).

### Configuration

```yaml
mode: hybrid
budget:
  per_call_max_usd: 0.50
  per_workstream_max_usd: 10.00
agreement_threshold: 0.70    # 70% against human reviewer
human_reviewer: anthony.g.francis@gmail.com
```

## 2. Pass-B findings recap

### Summary

Five concrete findings that came out of running this case by hand
before we had Layers 3–6 implemented. Each is incorporated into the
corresponding layer's proposal; this appendix shows them in situ.

### Finding B1 — Per-evidence-kind schemas are required

We initially intended one schema for all evidence records. Pass B
showed that `corpus_issue_report`, `agreement_score`, and
`reviewer_signoff` have radically different shapes — collapsing
them lost information. Layer 5b §5 is the response: a registry
under `project/evidence/schemas/` keyed by `kind`.

### Finding B2 — Evidence records need a `data:` field

A purely-prose evidence record is unparseable for closure checks.
Pass B made us add a structured `data:` block alongside the
Markdown body. Layer 5b §3 specifies it.

### Finding B3 — `no_issues_found: true` matters

A story with zero issues should still produce a
`corpus_issue_report` evidence record — not silence. Otherwise the
closure check can't distinguish "we analyzed it and found nothing"
from "we forgot to analyze it." Layer 5b §5 makes this explicit in
the schema.

### Finding B4 — Sibling workstreams reduce duplication

Three issue types could each be a child workstream, but Pass B
showed they share enough infrastructure (corpus ingestion, model
config, reviewer pool) that one workstream with three evidence
kinds is the right shape. The `siblings:` frontmatter field
captures cross-references when the relationship is symmetric (no
parent). Layer 1 §"Frontmatter schema" picks this up.

### Finding B5 — `expected_evidence_at_close` must be explicit

Closure inferred from the absence of TODOs is unreliable. Pass B
showed we need an explicit per-workstream contract: at close, the
following evidence kinds and counts must exist. Layer 1 frontmatter
adds `expected_evidence_at_close`; Layer 3 `can_close()` consumes
it.

## 3. Layer 1 — Control-plane on-disk artifacts

### Summary

A complete on-disk listing of the workstream directory after the
case has reached `closed`, with annotations on which Pass-B
findings touched which files.

### Directory layout

```text
project/workstreams/resolved/WS-LCATS-CORPORA-ANALYSIS/
├── workstream.md              # frontmatter + body (Layer 1)
├── conception.md              # Layer 2 template instance
├── assessment.md              # Layer 2 template instance
├── design.md                  # Layer 2 template instance
├── plan.md                    # Layer 2 template instance
├── prompts/                   # Layer 2 prompt instances
│   ├── P-001-orchestrator.md
│   ├── P-002-encoding-classifier.md
│   ├── P-003-ending-classifier.md
│   ├── P-004-residue-classifier.md
│   ├── P-005-cross-reviewer.md
│   ├── P-006-disagreement-resolver.md
│   ├── P-007-summarizer.md
│   └── P-008-final-report.md
├── decisions/                 # Layer 2 decision records
│   ├── D-001-use-three-classifier-prompts.md
│   ├── D-002-agreement-threshold-70pct.md
│   └── D-003-resolve-tied-disagreements-via-human.md
├── corpus/                    # input data, pinned
│   ├── SOURCES.md
│   ├── pit_and_the_pendulum.txt
│   ├── the_raven.txt
│   ├── the_telltale_heart.txt
│   ├── the_masque_of_the_red_death.txt
│   └── the_fall_of_the_house_of_usher.txt
└── README.md                  # auto-generated index
```

### `workstream.md` frontmatter (post-close)

```yaml
---
id: WS-LCATS-CORPORA-ANALYSIS
title: LCATS literary-corpus analysis (Poe set, three issue kinds)
status: closed
mode: hybrid
created_on: 2026-04-22
updated_on: 2026-04-26

# B4 — siblings (cross-reference)
siblings:
  - WS-LCATS-CORPORA-LOVECRAFT       # active, parallel run on different corpus
  - WS-LCATS-CORPORA-HAWTHORNE       # planned

# B5 — expected evidence contract
expected_evidence_at_close:
  - kind: corpus_issue_report
    count: 5                  # one per story
  - kind: agreement_score
    count: 5
  - kind: reviewer_signoff
    count: 1

# Bridges section absent — this is a pure-text workstream

prompts:
  - id: P-001
    template: prompt
    role: orchestrator
  - id: P-002
    template: prompt
    role: encoding_classifier
  # ... P-003 through P-008 ...

budget:
  per_call_max_usd: 0.50
  per_workstream_max_usd: 10.00

agreement_threshold: 0.70
human_reviewer: anthony.g.francis@gmail.com

# Layer 1 transitions audit trail (B1, B5 inform validation)
transitions:
  - from: null
    to: conceived
    at: 2026-04-22T09:00:00Z
    actor: anthony
  - from: conceived
    to: assessed
    at: 2026-04-22T11:30:00Z
    actor: anthony
  - from: assessed
    to: designed
    at: 2026-04-22T15:15:00Z
    actor: anthony
  - from: designed
    to: planned
    at: 2026-04-23T10:00:00Z
    actor: anthony
  - from: planned
    to: executing
    at: 2026-04-23T11:00:00Z
    actor: anthony
  - from: executing
    to: reviewing
    at: 2026-04-25T14:30:00Z
    actor: lrh.workstream.advance
  - from: reviewing
    to: closed
    at: 2026-04-26T16:00:00Z
    actor: anthony
---
```

### Layer 1 validator output (sample)

```text
$ lrh workstream validate WS-LCATS-CORPORA-ANALYSIS
✓ Frontmatter schema (workstream.md)
✓ Cross-reference: 3 siblings exist or are flagged 'planned'
✓ Cross-reference: 8 prompts referenced, 8 found
✓ Transition history: 7 transitions, all legal per Stage table
✓ expected_evidence_at_close: 11 expected, 11 present
✓ Bucket placement: status=closed → resolved/  ✓
✓ ID uniqueness: WS-LCATS-CORPORA-ANALYSIS  unique in workstreams index
PASS
```

## 4. Layer 2 — Templates instantiated

### Summary

Eight prompts and three decisions plus the four lifecycle docs
(conception / assessment / design / plan), all from Layer 2
templates. Showing one prompt and one decision in full.

### `prompts/P-002-encoding-classifier.md`

```markdown
---
id: P-002
workstream: WS-LCATS-CORPORA-ANALYSIS
template: prompt
role: encoding_classifier
created_on: 2026-04-23
---

# Prompt: encoding-glitch classifier

## Role

You are a careful textual analyst.

## Task

Read the attached short story. Identify any character sequences
that look like encoding glitches — mojibake from a Latin-1 → UTF-8
mis-decode, smart-quote fallbacks (`â€™`, `â€œ`, `â€`), or
double-encoded HTML entities (`&amp;amp;`).

## Output

A JSON object with this shape:
{
  "no_issues_found": <bool>,
  "issues": [
    {"line": <int>, "snippet": <str>, "category": "smart_quote" | "double_encode" | "other", "confidence": "high" | "medium" | "low"}
  ]
}

Set `no_issues_found: true` if and only if `issues` is empty.
This is required (Pass-B finding B3) — silence is ambiguous.

## Constraints

Do not modify the source text. Do not classify content meaning,
only encoding hygiene. If unsure, mark `confidence: low` rather
than guessing.

## Cost ceiling

This prompt may consume at most $0.30 per story.
```

### `decisions/D-002-agreement-threshold-70pct.md`

```markdown
---
id: D-002
workstream: WS-LCATS-CORPORA-ANALYSIS
template: decision
created_on: 2026-04-23
status: accepted
---

# Decision: 70% agreement threshold against human reviewer

## Context

We need a numeric threshold above which the agent's classification
is accepted without resolution, and below which the human reviewer
arbitrates. The classification is per-issue-type per-story.

## Considered alternatives

- 50% — too permissive; equivalent to a coin flip
- 70% — common practice in inter-annotator agreement literature
  for short-document classification tasks
- 90% — too restrictive given the model's known calibration on
  rare-class identification

## Decision

70%, computed as `1 - (disagreements / total_classifications)`.
Below 70% on any issue type for any story → human reviewer
arbitrates.

## Consequences

- Resolution prompts (P-006) only fire when threshold is missed.
- Closure cannot proceed until all sub-threshold cases are resolved.
```

### Note

These were generated from `src/lrh/templates/prompt.md` and
`src/lrh/templates/decision.md`. The italicized inline guidance
from the templates (per Layer 2 §"Template skeletons") was deleted
in the instances; the headings and required sections remain.

## 5. Layer 3 — Stage transitions and prompts

### Summary

Eight stage transitions (one per legal hop) drove the workstream
from `conceived` to `closed`. Each transition either fired a
runtime call (Layer 4) or an editorial step (manual / hybrid). The
sequence below is annotated with the prompts and budget consumed.

### Stage trace

| # | From → To | Driver | Prompt | Cost |
|---|-----------|--------|--------|------|
| 1 | (none) → `conceived` | manual | n/a | $0 |
| 2 | `conceived` → `assessed` | runtime | P-001 (orchestrator) | $0.18 |
| 3 | `assessed` → `designed` | runtime | P-001 (orchestrator) | $0.22 |
| 4 | `designed` → `planned` | manual | n/a | $0 |
| 5 | `planned` → `executing` | runtime | P-001 (orchestrator) | $0.05 |
| 6 | `executing` → `executing` (loop) | runtime | P-002 × 5, P-003 × 5, P-004 × 5, P-005 × 5, P-006 × 2 | $5.84 |
| 7 | `executing` → `reviewing` | runtime | P-007 (summarizer) | $0.31 |
| 8 | `reviewing` → `closed` | manual | n/a (human reviewer) | $0 |

Total cost: **$6.60** of the $10.00 cap.

### `LEGAL_TRANSITIONS` enforcement at work

Transition 6 is a self-loop on `executing` — the orchestrator
calls the runtime repeatedly while remaining in stage `executing`.
This is a deliberate Layer 3 affordance: the stage doesn't change
on every prompt, only on stage boundaries. Idempotent re-runs of
the same prompt produce the same evidence ID; Layer 3 §"Idempotence"
specifies this.

### Two-step manual-advance check at transition 8

The reviewer ran `lrh workstream advance WS-LCATS-CORPORA-ANALYSIS
--to closed` on the workstream after manually inspecting evidence
in `project/evidence/`. The CLI returned:

```text
Manual advance prepared:
  - WS-LCATS-CORPORA-ANALYSIS: reviewing → closed
  - 11 expected evidence records present
  - All sub-threshold cases resolved (D-002 satisfied)
  - Reviewer signoff record: EV-WS-LCATS-CORPORA-ANALYSIS-SIGNOFF-001

Confirm with: lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --confirm
```

The reviewer ran the confirm command, which appended the
transition to `transitions[]` and moved the directory `active/ →
resolved/`.

## 6. Layer 4 — Agent runtime calls

### Summary

Twenty-two runtime calls (one per row of the inner loop), all
through `ClaudeBackend`. Showing one `RuntimeRequest` /
`RuntimeResult` pair in full.

### Sample call: P-002 against `the_raven.txt`

```python
# Constructed by Layer 3, handed to Layer 4
request = runtime_models_mod.RuntimeRequest(
    prompt_id="P-002",
    workstream_id="WS-LCATS-CORPORA-ANALYSIS",
    prompt=PROMPT_BODY_RENDERED_WITH_STORY_ATTACHED,  # see below
    cwd=pathlib.Path("project/workstreams/active/WS-LCATS-CORPORA-ANALYSIS"),
    allowed_tools=["read_file"],
    permission_mode="strict",
    mcp_servers=[],                # no bridges this workstream
    max_turns=4,
    max_budget_usd=0.30,
    timeout_seconds=180,
    transcript_path=pathlib.Path(
        "project/runs/RUN-01HZJ.../transcripts/P-002-raven.jsonl"
    ),
    structured_output_schema=ENCODING_CLASSIFIER_SCHEMA,
    trace_parent="00-...-...-01",
)
```

### Sample result

```python
result = runtime_models_mod.RuntimeResult(
    completed=True,
    outcome=runtime_models_mod.Outcome.SUCCESS,
    backend_name="claude",
    tool_calls=2,                       # two read_file calls
    cost_usd=0.21,
    tokens={"input": 18402, "output": 384},
    turns_used=2,
    duration=datetime.timedelta(seconds=12.4),
    transcript_path=pathlib.Path(
        "project/runs/RUN-01HZJ.../transcripts/P-002-raven.jsonl"
    ),
    structured_output={
        "no_issues_found": True,        # B3 — explicit
        "issues": [],
    },
    final_message="No encoding glitches detected.",
    trace_id="01HZJ...",
    failure_detail=None,
)
```

### Permission mode in action

`permission_mode="strict"` (Layer 4 §"Permission modes") meant
every `read_file` call required the runtime to allow it explicitly.
The hook chain (`PreToolUse`) verified the path was inside the
workstream's `corpus/` directory; a hypothetical attempt to read
`project/memory/` would have been denied with `Outcome.TOOL_DENIED`.

### Cost cap in action

The per-call budget was $0.30, set by the prompt's "cost ceiling"
line in `P-002`'s body — Layer 3 reads that line out of the
template and pins it onto `max_budget_usd`. The actual call
cost $0.21, well under cap. If the call had hit cap, the result
would have set `outcome=BUDGET_EXHAUSTED` and the orchestrator
would have logged an evidence record of kind `budget_exhausted`
without retrying (per Layer 3 §"Failure semantics").

## 7. Layer 5a — Telemetry

### Summary

`project/runs/RUN-01HZJ...` ended up with 24 spans (one per
runtime call plus orchestrator-bracketing spans), one transcript
per call, total ~2.4 MB on disk.

### Run directory

```text
project/runs/RUN-01HZJ23...JK4/
├── run.json                  # run metadata, span/transcript index
├── spans.jsonl               # 24 OTel-aligned spans
└── transcripts/
    ├── P-001-orchestrator-1.jsonl
    ├── P-002-raven.jsonl
    ├── P-002-pit.jsonl
    ├── ...
    └── P-007-summarizer.jsonl
```

### One span (P-002 against `the_raven.txt`)

```json
{
  "trace_id": "01HZJ23BWZ3X7Q9R7P2K4Y9N",
  "span_id": "1f4c6a9d2e7a8b0d",
  "parent_span_id": "0a5e4b1c8f3e2d1c",
  "name": "lrh.runtime.execute",
  "start_time_ns": 1745601234000000000,
  "end_time_ns": 1745601246400000000,
  "attributes": {
    "gen_ai.system": "anthropic",
    "gen_ai.request.model": "claude-sonnet-4-6",
    "gen_ai.usage.input_tokens": 18402,
    "gen_ai.usage.output_tokens": 384,
    "gen_ai.response.finish_reasons": ["stop"],
    "lrh.workstream_id": "WS-LCATS-CORPORA-ANALYSIS",
    "lrh.prompt_id": "P-002",
    "lrh.story": "the_raven",
    "lrh.cost_usd": 0.21,
    "lrh.outcome": "success",
    "lrh.runtime.backend": "claude",
    "lrh.transcript.ref": "transcripts/P-002-raven.jsonl"
  },
  "events": [
    {
      "name": "tool_call",
      "time_ns": 1745601238500000000,
      "attributes": {
        "tool.name": "read_file",
        "tool.args.path": "corpus/the_raven.txt"
      }
    }
  ]
}
```

### Why both spans and transcripts

Pass B confirmed the split was right: spans give us aggregate
queries ("total cost on this workstream"); transcripts give us
narrative replay ("show me what the agent saw and said for
P-002 on `the_raven`"). Layer 5a §3 specifies the rule —
content refs in spans, full content in transcripts.

### OTel attribute alignment

`gen_ai.system`, `gen_ai.request.model`,
`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, and
`gen_ai.response.finish_reasons` are all from the OpenTelemetry
GenAI semantic conventions ([otel-genai]). The `lrh.*` namespace
holds LRH-specific attributes that aren't in upstream semconv.

## 8. Layer 5b — Evidence records

### Summary

Eleven evidence records produced, matching the
`expected_evidence_at_close` contract: 5 `corpus_issue_report` + 5
`agreement_score` + 1 `reviewer_signoff`. Showing one of each in
full.

### `corpus_issue_report` (one of five)

```yaml
---
id: EV-WS-LCATS-CORPORA-ANALYSIS-RAVEN-001
workstream: WS-LCATS-CORPORA-ANALYSIS
kind: corpus_issue_report
provenance: agent_trace
extractor: ManualReviewExtractor
extracted_at: 2026-04-25T12:14:09Z
schema: corpus_issue_report.v1
data:
  story: the_raven
  source_sha256: 7d3f8a9b2c4e1f6a0d8b3e7c5a9f2b4d1c6e8a0f3b5d7e9a1c3f5b7d9e1a3c
  no_issues_found: true        # B3
  issue_breakdown:
    encoding_glitch:
      no_issues_found: true
      issues: []
    missing_ending:
      no_issues_found: true
      issues: []
    transcriber_note_residue:
      no_issues_found: true
      issues: []
  total_issues: 0
  classifier_runs:
    - prompt_id: P-002
      cost_usd: 0.21
    - prompt_id: P-003
      cost_usd: 0.18
    - prompt_id: P-004
      cost_usd: 0.19
---

# Corpus issue report: the_raven

The agent ran three classifiers (encoding glitches, missing ending,
transcriber-note residue) over the_raven.txt and found no issues
in any category. The cross-reviewer (P-005) agreed.

## Per-classifier notes

- encoding_glitch: clean UTF-8 throughout; no smart-quote fallbacks
  or double-encoded entities found.
- missing_ending: the text closes with the canonical "Quoth the
  Raven 'Nevermore.'" stanza; no truncation observed.
- transcriber_note_residue: no `[Transcriber's Note: ...]` blocks
  in the body. (Project Gutenberg footer was stripped before
  ingestion.)
```

### `agreement_score` (one of five)

```yaml
---
id: EV-WS-LCATS-CORPORA-ANALYSIS-RAVEN-AGREEMENT-001
workstream: WS-LCATS-CORPORA-ANALYSIS
kind: agreement_score
provenance: agent_trace
extractor: AgreementScoreExtractor   # bridge-specific to this workstream
extracted_at: 2026-04-25T12:14:11Z
schema: agreement_score.v1
data:
  story: the_raven
  agent_classifications: 0     # zero issues × three categories
  human_classifications: 0
  agreements: 0
  disagreements: 0
  agreement_rate: 1.0          # vacuously perfect
  threshold: 0.70
  threshold_met: true
---

# Agreement score: the_raven

Agent and human reviewer agreed perfectly: both reported zero
issues across all three categories. Vacuous case — the agreement
rate is computed as 1.0 by convention when total classifications
are zero on both sides.
```

### `reviewer_signoff` (the one)

```yaml
---
id: EV-WS-LCATS-CORPORA-ANALYSIS-SIGNOFF-001
workstream: WS-LCATS-CORPORA-ANALYSIS
kind: reviewer_signoff
provenance: human
extractor: null                # written directly by reviewer
extracted_at: 2026-04-26T15:58:12Z
schema: reviewer_signoff.v1
data:
  reviewer: anthony.g.francis@gmail.com
  reviewed_at: 2026-04-26T15:58:00Z
  approved_to_close: true
  notes: "All five corpus reports reviewed. Two threshold misses
    (pit_and_the_pendulum encoding, masque transcriber-note) were
    correctly resolved via P-006. Closing."
---

# Reviewer signoff: WS-LCATS-CORPORA-ANALYSIS

I reviewed all 11 evidence records and confirm closure. Two
sub-threshold cases (pit_and_the_pendulum on encoding_glitch at
0.60; masque on transcriber_note_residue at 0.50) went through
the disagreement-resolver prompt (P-006) and produced acceptable
joint classifications.
```

### Per-evidence-kind schemas in use

`project/evidence/schemas/corpus_issue_report.v1.json` was the
biggest schema (B1) — its `data:` block has nested per-classifier
objects, each with `no_issues_found` and `issues[]`. Without the
per-kind schema, the validator would have collapsed these into
one of three rigid shapes that fit none of them well. Pass B's
finding B1 is concretely visible here: schema-per-kind, registered
under `project/evidence/schemas/`.

## 9. Layer 6 — Bridge attachment (none here)

### Summary

This workstream has no bridges. The frontmatter `bridges:` field
is absent. Layer 6 is exercised by *not* being invoked.

### Why this is worth noting

A reasonable failure mode for a six-layer architecture is forcing
all six layers to participate in every workstream. The framework
explicitly does not require that. Layer 6 is pay-for-what-you-use:
no `bridges:`, no MCP servers attached, no process-group cleanup,
zero overhead. The runtime's `mcp_servers=[]` shortcut path skips
the bridge registry entirely.

### Counter-example pointer

The PROSOC mapping in `06_layer6_mcp_bridges.md` §10 is the
analogue case where the same workstream pattern *does* attach a
bridge. Consult that section for the with-bridges shape; this
appendix is the without-bridges shape.

## 10. Closure check and the `expected_evidence_at_close` machinery

### Summary

Layer 3's `can_close()` consumed the
`expected_evidence_at_close` contract from frontmatter, queried
Layer 5b's record store, and returned True. The full algorithm
in this case.

### The contract

```yaml
expected_evidence_at_close:
  - kind: corpus_issue_report
    count: 5
  - kind: agreement_score
    count: 5
  - kind: reviewer_signoff
    count: 1
```

### `can_close()` execution trace

```text
$ lrh workstream advance WS-LCATS-CORPORA-ANALYSIS --to closed --dry-run
[layer-3] reading expected_evidence_at_close
[layer-3] resolved 3 expected kinds: corpus_issue_report (5),
          agreement_score (5), reviewer_signoff (1)
[layer-5b] querying evidence index for workstream=WS-LCATS-CORPORA-ANALYSIS
[layer-5b]   - corpus_issue_report: 5 records found ✓
[layer-5b]   - agreement_score: 5 records found ✓
[layer-5b]   - reviewer_signoff: 1 record found ✓
[layer-3] all expected evidence present
[layer-3] checking sub-threshold resolution (D-002, 70% threshold)
[layer-5b]   - 2 sub-threshold cases found
[layer-5b]   - 2 P-006 disagreement-resolver records found ✓
[layer-3] checking transitions[] legal sequence
[layer-3]   reviewing → closed: legal ✓
[layer-3] can_close: TRUE
```

### B5 in context

Without `expected_evidence_at_close`, this check would have to
infer "doneness" from heuristics. With it, the check is a join
between two declared sets — straightforward, deterministic, easy
to audit. The reviewer didn't have to guess what counted as
complete; the workstream told them.

## 11. Sibling workstreams and the post-Pass-B observation

### Summary

`WS-LCATS-CORPORA-ANALYSIS` has two siblings declared in
frontmatter — one active, one planned. The siblings list is
symmetric (no parent), captures the cross-corpus relationship, and
is enforced by the Layer 1 validator.

### The siblings

```yaml
siblings:
  - WS-LCATS-CORPORA-LOVECRAFT       # active in parallel
  - WS-LCATS-CORPORA-HAWTHORNE       # planned, not started
```

The validator (Layer 1) checks each sibling reference against the
workstreams index. Per Pass B's finding B4, planned siblings are
permitted (otherwise we couldn't declare future related work);
abandoned siblings are warned but not errored.

### Why not parent/child

The natural temptation was to make `WS-LCATS-CORPORA-ANALYSIS` a
parent and the per-corpus runs children. Pass B argued against
this on two grounds:

The corpora don't depend on each other — they're parallel,
independent runs of the same shape. A parent workstream implies
"this orchestrates that," which would be a lie.

Closure semantics. A parent that depends on a slow-moving sibling
(the Hawthorne corpus is gated on copyright clearance) would
itself never close. Sibling relationships preserve closure
independence.

### Post-Pass-B observation

We initially modeled cross-corpus relationships through link
text in the body. Pass B made it explicit by promoting the
relationship to frontmatter. This is the same shape as
`expected_evidence_at_close` — making implicit relationships
machine-readable.

## 12. What this case demonstrates about the framework

### Summary

Five concrete take-aways from running this case end-to-end.

### Take-away 1 — Hybrid mode is the natural default

`mode: hybrid` showed up as the right balance: agent does the
mechanical pass-through, human reviews the boundaries (sub-
threshold disagreements, final closure). The framework supports
all three modes (`agent`, `manual`, `hybrid`); this case argued
that hybrid is the right pick for almost any quality-graded
workload.

### Take-away 2 — Cost caps need to be both per-call and per-workstream

The per-call $0.50 ceiling caught one P-006 invocation that would
otherwise have run away ($0.83 estimated under no cap). The
per-workstream $10.00 ceiling was nowhere near binding ($6.60
total). Both were necessary; either alone would have been a
gap. Layer 4 §"Budget" specifies the dual cap.

### Take-away 3 — Evidence records carry their own typing

Pass B's findings B1–B3 (per-kind schemas, `data:` field,
`no_issues_found: true`) all converged on the same observation:
evidence records that don't carry typing degrade to prose, and
prose can't be queried. The pattern that fell out — frontmatter
contract + Markdown body + structured `data:` block + per-kind
schema — survives this case intact.

### Take-away 4 — Manual-mode parity isn't theoretical

Reviewer signoff at transition 8 was a manual artifact written
directly by a human. The framework treated it identically to
agent-produced evidence: same schema (`reviewer_signoff.v1`),
same closure check, same path through Layer 5b. The
`provenance: human` field is the only difference. Layer 5b §6's
stub-and-fill pattern wasn't even used here because the reviewer
wrote the record directly — but it would have been used had the
reviewer wanted to dictate notes through an MCP transcription
tool first.

### Take-away 5 — Bridges should be optional

Section 9 above is a non-event for this case. That is the right
shape: Layer 6 was designed and proposed but it didn't appear
on disk for this workstream because nothing here needed it. The
six-layer stack is a buffet, not a tasting menu.

## 13. References

### Source artifacts

`AGENTS.md` — mission, evidence philosophy, manual-mode parity.

`STYLE.md` — encoding, determinism, frozen dataclasses.

`project/design/design.md` §"Evidence" and §"Status".

`00_proposal.md` (umbrella, this proposal set) — the umbrella
proposal this appendix supports.

`01_layer1_control_plane.md` through `06_layer6_mcp_bridges.md`
(sibling proposals) — the six sub-proposals walked through above.

### External references

[Project Gutenberg][gutenberg] — corpus source. Snapshot SHAs
pinned in `corpus/SOURCES.md` per text.

[OpenTelemetry GenAI semantic conventions][otel-genai] — span
attribute vocabulary used in the trace samples in §7.

[anthropics/claude-agent-sdk-python][cas] — runtime backend (the
sample `RuntimeRequest`/`RuntimeResult` in §6 maps to the SDK's
session shape).

[modelcontextprotocol.io][mcp] — protocol spec; this workstream
attaches no MCP servers but the framework would route them
through Layer 6 if it did.

### Pass-B notes

The Pass-B run that produced findings B1–B5 was conducted between
2026-03-30 and 2026-04-11 by hand; the artifacts above are the
post-formalization reconstruction in the framework's intended
shape. The original Pass-B run's notes live in
`project/memory/decisions/pass_b_findings.md` (to be created as
part of this proposal's adoption — see umbrella §"Adoption plan").

[gutenberg]: https://www.gutenberg.org/
[otel-genai]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
[cas]: https://github.com/anthropics/claude-agent-sdk-python
[mcp]: https://modelcontextprotocol.io/

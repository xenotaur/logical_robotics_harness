---
id: PROP-PROMPT-EXECUTION-SEARCH-AND-MATCH
type: design_proposal
title: Prompt execution search and match infrastructure
status: adopted
created_on: 2026-05-06
updated_on: 2026-05-10
implementation_status: implemented
evidence:
  - EV-0006
---

## 1) Purpose

Define an implementation-oriented design for prompt execution-record
lookup, prompt-file matching, and exploratory execution search in LRH.

The design preserves the existing exact prompt-ID lookup command as the
authoritative primitive for soft-idempotence decisions:

```bash
lrh prompt check-execution --prompt-id ...
```

It then layers two human-friendly workflows on the same package-owned
record parsing and query infrastructure:

```bash
lrh match executions ...
lrh search executions ...
```

This proposal was originally introduced as design-only. Follow-up PRs have
implemented the package-owned record parsing, exact prompt-file matching,
and exploratory execution search command surface while preserving the
execution-record schema and rerun policy.

## 2) Motivation and problem statement

LRH already supports lightweight prompt traceability through prompt IDs
and execution records. That is enough for a direct structured question:

```text
Has this exact prompt ID already been executed?
```

Prompt-heavy workflows still leave three related but distinct questions
awkward to answer:

1. **Exact lookup:** whether a specific prompt ID has a prior execution
   record.
2. **File-to-record matching:** whether a prompt file appears to have
   been executed, especially when an operator has a prompt Markdown file
   rather than a copied prompt ID.
3. **Exploratory search:** which execution records mention a workstream,
   command, slug, topic, PR, validation result, or follow-up concern.

Those questions need a coherent architecture so future implementation
PRs do not duplicate Markdown/frontmatter parsing, path traversal,
prompt-ID extraction, filtering, or output formatting.

The central design requirement is that exact prompt-ID lookup remains
authoritative for soft idempotence. Matching and search are useful for
human discovery, review, and triage, but they should not drive automatic
rerun decisions unless they resolve to the same exact structured prompt
ID evidence used by `check-execution`.

## 3) Relationship to existing prompt workflow tooling

The current prompt workflow is intentionally lightweight:

- prompt IDs are stable textual identifiers;
- execution records live under `project/executions/`;
- execution records use Markdown with frontmatter;
- `AD_HOC` is valid when no work item applies;
- reruns, reverts, and supersession preserve history rather than
  deleting records;
- meaningful prompt-driven work should check prior execution records
  before proceeding.

The installed CLI already provides package-owned prompt commands that
accept explicit project roots. The repository-local helper scripts
remain useful for maintainers, but durable behavior should move toward
package-owned modules and CLI commands so client repositories can use
LRH without depending on this checkout's `scripts/` directory.

This proposal keeps that direction:

- `lrh prompt check-execution` stays under the prompt workflow command
  surface because it answers an exact prompt-ID workflow question.
- `lrh match executions` belongs under a broader matching command
  surface because the input is a prompt file or other source artifact,
  not necessarily a raw prompt ID.
- `lrh search executions` belongs under a search command surface because
  it is explicitly exploratory text/query discovery over execution
  records.

## 4) Existing `check-execution` behavior remains authoritative

`lrh prompt check-execution --prompt-id ...` should remain the core
exact-match primitive because it has the strongest evidence semantics:

- the caller supplies one complete prompt ID;
- records are parsed as structured execution records;
- matching is against the structured `prompt_id` field, not arbitrary
  body text;
- status values retain the existing soft-idempotence meaning;
- output can be made deterministic and machine-readable;
- exit codes can represent exact lookup outcomes without ranking or
  ambiguity.

The command should answer only the exact question:

```text
Which execution records have frontmatter prompt_id exactly equal to X?
```

It should not be broadened into fuzzy matching, substring search, or
semantic retrieval. Keeping this command narrow protects the prompt
workflow's soft-idempotence rule: prior `landed` or `in_progress`
records for the same exact prompt ID are enough to stop ordinary rerun
work unless the prompt explicitly requests a rerun.

## 5) Conceptual separation

LRH should model three related operations separately.

### 5.1 Exact structured lookup

Exact lookup operates on structured metadata:

- input: one prompt ID string;
- primary field: `ExecutionRecord.prompt_id`;
- matching rule: exact string equality after ordinary CLI argument
  parsing, with no fuzzy normalization;
- primary consumer: soft idempotence and automation-safe checks;
- canonical command: `lrh prompt check-execution`.

Exact lookup is authoritative because it asks a precise question against
the canonical record field.

### 5.2 File-to-record matching

File-to-record matching starts from a source artifact, usually a prompt
file. It extracts candidate identifiers and then delegates exact checks
to shared query infrastructure.

- input: prompt file path, optional project root, optional work-item
  filter;
- extraction: prompt IDs found in the file, and later possibly prompt
  slug/work-item hints;
- primary matching rule for the first implementation: exact prompt-ID
  matching for every prompt ID found in the file;
- primary consumer: humans deciding whether an existing prompt file has
  already been executed;
- canonical command: `lrh match executions`.

Matching may eventually include heuristics, but heuristic matches should
be clearly labeled as non-authoritative.

### 5.3 Exploratory text search

Search answers broad discovery questions:

- input: free-text query and optional filters;
- fields: selected structured fields and Markdown body text;
- matching rule: deterministic text containment or simple token matching
  in the first implementation;
- primary consumer: humans navigating prior work;
- canonical command: `lrh search executions`.

Search is useful for finding related records, but it is not sufficient
for soft-idempotence decisions because body text may mention a prompt ID,
work item, or topic without representing an actual execution of that
prompt.

## 6) Proposed CLI design

### 6.1 `lrh prompt check-execution`

Retain the existing command shape:

```bash
lrh prompt check-execution \
  --prompt-id "PROMPT(AD_HOC:EXAMPLE)[2026-05-06T12:00:00-04:00]" \
  --project-root /path/to/project
```

Recommended options:

- `--prompt-id TEXT` required;
- `--project-root PATH` optional, defaulting through the existing LRH
  project-root conventions;
- `--json` for stable machine-readable output;
- `--include-body` omitted by default and only considered later if
  users need record snippets.

Human output should be concise:

```text
found: 1 execution record for exact prompt ID
- project/executions/AD_HOC/2026_05_06_120000_EXAMPLE.md
  status: landed
  work_item: AD_HOC
```

JSON output should expose the same result without relying on formatted
text:

```json
{
  "prompt_id": "PROMPT(AD_HOC:EXAMPLE)[2026-05-06T12:00:00-04:00]",
  "match_count": 1,
  "records": [
    {
      "path": "project/executions/AD_HOC/2026_05_06_120000_EXAMPLE.md",
      "execution_id": "2026_05_06_120000_EXAMPLE",
      "work_item": "AD_HOC",
      "status": "landed"
    }
  ]
}
```

### 6.2 `lrh match executions`

Introduce a human-friendly command for matching source artifacts to
execution records:

```bash
lrh match executions --prompt-file prompts/example.md
lrh match executions --prompt-file prompts/example.md --json
```

Recommended first-slice options:

- `--prompt-file PATH` required initially;
- `--project-root PATH` optional;
- `--work-item ID` optional filter;
- `--json` optional;
- `--show-unmatched` optional for files containing multiple prompt IDs.

First implementation semantics:

1. read the prompt file;
2. extract complete `PROMPT(...)[...]` identifiers;
3. load execution records once;
4. run exact prompt-ID checks for each extracted ID;
5. report exact matches and unmatched prompt IDs.

Example human output:

```text
prompt file: prompts/example.md
prompt IDs found: 2

exact matches:
- PROMPT(WI-EXAMPLE:IMPLEMENT)[2026-05-06T12:00:00-04:00]
  - project/executions/WI-EXAMPLE/2026_05_06_120000_IMPLEMENT.md
    status: landed

unmatched prompt IDs:
- PROMPT(WI-EXAMPLE:FOLLOW_UP)[2026-05-06T12:30:00-04:00]
```

If no prompt IDs are found, the first implementation should report that
clearly and avoid pretending that filename or body-text heuristics are
authoritative.

### 6.3 `lrh search executions`

Introduce exploratory search over execution records:

```bash
lrh search executions "release smoke"
lrh search executions "PROMPT(WI-EXAMPLE" --field prompt_id --json
lrh search executions "scripts/test" --status landed --work-item AD_HOC
```

Recommended first-slice options:

- positional `QUERY` required;
- `--project-root PATH` optional;
- `--work-item ID` optional filter;
- `--status VALUE` repeatable optional filter;
- `--field FIELD` repeatable optional scope, with allowed values such as
  `prompt_id`, `execution_id`, `work_item`, `status`, `summary`,
  `result`, `validation`, `follow_up`, and `body`;
- `--limit N` optional;
- `--json` optional.

The first implementation should use deterministic local scanning and
simple text matching. It should not introduce indexing, semantic search,
embeddings, external services, or heavyweight query languages.

## 7) Proposed module/package structure

Because `src/lrh/prompt_workflow.py` already exists, use a low-churn
module extraction rather than immediately converting it into a package
directory.

Recommended near-term structure:

```text
src/lrh/
  prompt_workflow.py          # CLI-facing prompt workflow glue and legacy helpers
  prompt_workflow_records.py  # execution-record dataclasses, parsing, loading
  prompt_workflow_queries.py  # check, match, and search query functions
```

Rationale:

- minimizes import churn;
- keeps existing command integration stable;
- creates clear ownership for reusable parsing/query logic;
- avoids a premature package-directory migration;
- leaves room for a later `src/lrh/prompt_workflow/` package if the
  surface grows substantially.

Command wiring can remain in the existing CLI modules, but command
handlers should call package-owned query APIs rather than reimplementing
record traversal or parsing.

## 8) Shared execution-record parsing and query infrastructure

The first implementation should centralize these responsibilities:

- locating `project/executions/` from an explicit project root;
- walking execution-record Markdown files in deterministic order;
- parsing frontmatter once;
- preserving record body text for search;
- validating or at least normalizing expected fields;
- exposing typed dataclasses to command handlers and tests;
- providing reusable exact-check, match, and search functions.

The loader should be tolerant enough for historical records, but query
results should expose missing or malformed fields explicitly where they
affect behavior. For example, an execution record with no `prompt_id`
should not match an exact prompt-ID check, but a diagnostic warning can
be included in human output or a JSON `warnings` field.

The loader should not import from `scripts/`. Repository-local scripts
may become thin wrappers around package-owned functionality later, but
package code must remain reusable for client repositories.

## 9) Proposed data structures and APIs

Illustrative dataclasses:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionRecord:
    path: Path
    execution_id: str | None
    prompt_id: str | None
    work_item: str | None
    status: str | None
    created_at: str | None
    frontmatter: dict[str, object]
    body: str


@dataclass(frozen=True)
class ExecutionCheckResult:
    prompt_id: str
    records: tuple[ExecutionRecord, ...]
    warnings: tuple[str, ...] = ()

    @property
    def found(self) -> bool:
        return bool(self.records)


@dataclass(frozen=True)
class ExecutionSearchHit:
    record: ExecutionRecord
    matched_fields: tuple[str, ...]
    snippet: str | None = None
```

Illustrative query APIs:

```python
def load_execution_records(project_root: Path) -> tuple[ExecutionRecord, ...]:
    """Load execution records under project/executions in stable order."""


def check_execution(
    records: tuple[ExecutionRecord, ...],
    prompt_id: str,
) -> ExecutionCheckResult:
    """Return records whose structured prompt_id exactly equals prompt_id."""


def match_prompt_file_to_executions(
    prompt_file: Path,
    records: tuple[ExecutionRecord, ...],
) -> tuple[ExecutionCheckResult, ...]:
    """Extract prompt IDs from prompt_file and run exact checks for each."""


def search_execution_records(
    records: tuple[ExecutionRecord, ...],
    query: str,
    *,
    fields: tuple[str, ...] = (),
    statuses: tuple[str, ...] = (),
    work_item: str | None = None,
    limit: int | None = None,
) -> tuple[ExecutionSearchHit, ...]:
    """Search execution records using deterministic local text matching."""
```

The concrete implementation can add small helper types if needed, such
as `ExecutionRecordLoadResult` for warnings. The first slice should keep
the model small and avoid abstractions that only serve future indexing or
semantic retrieval.

## 10) Matching semantics

### 10.1 Exact prompt-ID matching

The first `match executions` implementation should be exact-only:

- extract all full prompt IDs from the source prompt file;
- preserve source order while de-duplicating repeated IDs;
- run `check_execution` for each ID;
- label the result as `exact`;
- report unmatched IDs clearly;
- use structured execution-record `prompt_id` fields only.

This keeps `match executions` aligned with soft idempotence while making
it easier for users who have a prompt file rather than a copied ID.

### 10.2 Future heuristic matching considerations

Future matching may help when prompt files lack prompt IDs or when users
want related-record hints. Possible heuristics include:

- matching work-item ID and prompt slug;
- matching normalized prompt title headings;
- matching generated execution-record slug;
- matching a stable hash of prompt body text if such a hash is added to
  future records;
- matching nearby timestamps only as supporting context, never as proof.

Guardrails for any heuristic phase:

- heuristic matches must be explicitly labeled as heuristic;
- they must not be returned as authoritative exact matches;
- they should include reason codes and matched fields;
- they should not change `check-execution` behavior;
- they should not be used by default to decide whether a prompt rerun is
  blocked.

## 11) Search semantics and filtering

Search should be deterministic and local in the first implementation.
Recommended semantics:

- case-insensitive containment by default;
- optional field scoping through `--field`;
- filtering by `work_item` and `status` before text matching;
- stable ordering by record path or created timestamp plus path;
- optional snippets for human output;
- no scoring beyond simple field match ordering in the first slice.

Searchable field groups can map to structured values and Markdown
sections:

- structured: `execution_id`, `prompt_id`, `work_item`, `status`, `pr`,
  `commit`, `created_at`;
- body sections: `summary`, `result`, `validation`, `follow_up`;
- fallback: `body` for the full Markdown body.

Search should be explicit about its limits. A record found by searching
for a prompt ID in body text may be related, but it is not equivalent to
a structured prompt-ID execution match.

## 12) Exit-code behavior

Recommended exit codes for first-slice commands:

| Command | Condition | Exit code |
| --- | --- | --- |
| `lrh prompt check-execution` | exactly one exact record found | `0` |
| `lrh prompt check-execution` | no exact records found | `1` |
| `lrh prompt check-execution` | multiple exact records found; ambiguous human review required | `2` |
| `lrh prompt check-execution` | invalid input or unreadable project | `2` |
| `lrh match executions` | prompt IDs found and all have exact matches | `0` |
| `lrh match executions` | prompt IDs found but at least one is unmatched | `1` |
| `lrh match executions` | no prompt IDs found | `1` |
| `lrh match executions` | invalid input or unreadable file/project | `2` |
| `lrh search executions` | one or more hits found | `0` |
| `lrh search executions` | no hits found | `1` |
| `lrh search executions` | invalid query/filter/project | `2` |

The important distinction is that exit code `1` represents a valid query
with no complete success, while exit code `2` represents command usage,
environment failure, or an authoritative exact-lookup ambiguity requiring
human review. This preserves the current `check-execution` behavior where
multiple structured records for the same prompt ID are not treated as an
automation-safe success.

## 13) JSON and human-readable output

Human-readable output should optimize for review:

- concise summaries;
- relative paths from project root;
- statuses and work-item IDs near each record;
- clear labels for `exact`, `unmatched`, and future `heuristic` results;
- warnings at the end.

JSON output should optimize for scripts:

- stable field names;
- no dependence on text formatting;
- paths represented relative to project root unless an absolute path is
  explicitly requested later;
- result kind fields such as `exact`, `unmatched`, or `search_hit`;
- warnings as structured arrays;
- no ANSI styling.

The JSON shape should be covered by tests before being advertised as
stable in user documentation.

## 14) Testing strategy

Testing should be fast, deterministic, and hermetic.

Recommended unit tests:

- loading execution records from temporary project directories;
- parsing frontmatter and body text;
- exact prompt-ID checks against structured `prompt_id` fields;
- duplicate prompt IDs in a prompt file;
- prompt files with no prompt IDs;
- unmatched prompt IDs;
- search over structured fields;
- search over body sections;
- status and work-item filtering;
- stable ordering;
- malformed execution records with warnings.

Recommended CLI tests:

- `lrh prompt check-execution` returns expected exit codes;
- `lrh match executions` reports exact matches and unmatched IDs;
- `lrh search executions` returns hits and no-hit exit codes;
- `--json` output parses and contains expected fields.

Avoid network access, package installs, Git remotes, and heavyweight
subprocesses in the normal unit suite. If later packaging or installed
CLI smoke checks are needed, keep them in smoke tests rather than unit
tests.

## 15) Migration and refactor strategy

Use a low-churn extraction sequence:

1. Add `prompt_workflow_records.py` with dataclasses, prompt-ID regex
   helpers, frontmatter parsing reuse, and record loading.
2. Add `prompt_workflow_queries.py` with exact check, prompt-file match,
   and search functions.
3. Refactor the existing `lrh prompt check-execution` command to call
   `check_execution` without changing user-visible behavior.
4. Add focused tests proving the refactor preserves exact lookup
   semantics.
5. Add `lrh match executions` using the same loader and exact query API.
6. Add `lrh search executions` using the same loader and search API.
7. Consider script wrappers or documentation updates only after package
   commands are stable.

This avoids a large all-at-once rewrite and creates reviewable PRs where
each behavior change has direct tests.

## 16) Staged implementation plan / PR sequencing

Recommended PR sequence:

1. **Shared record model and loader.** Introduce `ExecutionRecord`,
   loading, and parsing tests. No CLI behavior change.
2. **Exact query extraction.** Introduce `ExecutionCheckResult` and
   `check_execution`, then refactor `lrh prompt check-execution` to use
   them. Preserve existing output and exit behavior unless tests expose a
   bug that is intentionally fixed.
3. **Prompt-file matching command.** Add `match_prompt_file_to_executions`
   and `lrh match executions` with exact-only semantics.
4. **Exploratory search command.** Add `ExecutionSearchHit`,
   `search_execution_records`, and `lrh search executions` with simple
   deterministic text matching and filters.
5. **Documentation hardening.** Update prompt workflow documentation and
   command help examples after the command surface is tested.
6. **Optional heuristics proposal.** If users need non-exact matching,
   write a follow-up proposal or focused design note before implementing
   heuristic match behavior.

## 17) Risks, tradeoffs, and mitigations

| Risk or tradeoff | Mitigation |
| --- | --- |
| Users may treat search hits as proof of prior execution. | Keep `check-execution` documentation explicit; label search as exploratory. |
| Matching may grow into fuzzy search too early. | First implementation extracts prompt IDs and delegates exact checks only. |
| Parsing logic may be duplicated across commands. | Centralize record loading and query APIs in package-owned modules. |
| A package-directory migration could create noisy imports. | Use low-churn sibling modules first. |
| Malformed historical records may cause brittle failures. | Load records with warnings; fail only when required command inputs are invalid. |
| Search may become slow with many records. | Use deterministic scanning first; revisit indexing only with measured need. |
| JSON output could become unstable accidentally. | Add tests for JSON shapes before documenting stability. |

## 18) Best-practice rationale

Separating exact structured lookup from exploratory search follows a
simple evidence hierarchy:

1. A structured `prompt_id` field exactly equal to the requested prompt
   ID is direct evidence that the prompt was recorded as executed.
2. A prompt file containing that prompt ID can be matched to execution
   records by delegating to the same exact lookup.
3. A search hit is contextual evidence that may help a human find related
   work, but it may be a mention, note, follow-up, or review reference
   rather than an execution record for the prompt.

That hierarchy keeps automation conservative and reviewable. Exact
checks can safely support soft idempotence; matching can make exact
checks easier to use; search can support discovery without weakening the
meaning of an authoritative prompt execution record.

## 19) Non-goals for the first implementation slice

The first implementation should not include:

- embeddings or semantic search;
- persistent indexes;
- external search services;
- fuzzy rerun-blocking decisions;
- automatic prompt execution state mutation;
- broad CLI restructuring unrelated to these commands;
- migration from `src/lrh/prompt_workflow.py` to a package directory.

These capabilities can be reconsidered after the exact lookup, match,
and local search workflows are implemented and tested.

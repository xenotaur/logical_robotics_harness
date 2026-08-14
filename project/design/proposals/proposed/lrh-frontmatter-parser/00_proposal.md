---
id: PROP-LRH-FRONTMATTER-PARSER
type: design_proposal
title: Frontmatter YAML Parser Consolidation and Content Safety
status: proposed
created_on: 2026-08-08
updated_on: 2026-08-08
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - src/lrh/control/parser.py
  - src/lrh/control/validator.py
  - project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md
---

## Summary

LRH's two hand-rolled frontmatter parsers (`src/lrh/control/parser.py`,
`src/lrh/control/validator.py`) disagree on what valid frontmatter is, causing a
comment line inside a YAML list to crash one code path silently while
passing the other. This proposal consolidates both onto a single
PyYAML-based parser, and — because existing content across the repo (and,
by inheritance, every downstream repo using LRH's frontmatter conventions)
was authored assuming a more permissive grammar than real YAML actually
has — pairs that consolidation with a one-time content-safety migration, a
permanent lint guard, and updated authoring guidance, so the fix is
durable rather than trading one silent-failure class for another.

## Background / Motivation

A `#` comment line interleaved between items of a YAML list in frontmatter
(e.g. `artifacts_expected:\n  # note\n  - path/one`) is valid YAML — PyYAML
parses it fine — but raises `ValueError: unsupported nested mapping` in
`src/lrh/control/parser.py`'s `_parse_frontmatter_mapping`
(`src/lrh/control/parser.py:65-123`), because its block-list scanner only
recognizes `- item`, blank lines, or "indented → illegal nested mapping."
This exact pattern was independently introduced and independently
rediscovered by two different concurrent sessions on the same day, which
is itself evidence it's an easy, recurring mistake, not a one-off.

Worse, `lrh validate` (the validator everyone runs by default) does not
catch it, because it uses a second, independent hand-rolled parser —
`src/lrh/control/validator.py`'s `_parse_simple_yaml` (`src/lrh/control/validator.py:568-639`,
prior to this proposal's changes) — which happens to skip `#`-prefixed
lines unconditionally, everywhere, and so never trips on this shape. Only
`lrh work-items validate` and `lrh work-items readiness` (which route
through `src/lrh/control/parser.py`) surface the bug, and `readiness` surfaces it
as a misleading "work item not found" rather than a parse error, since
`_parse_work_item_lenient` in `src/lrh/work_items/readiness.py:165` catches
the `ValueError` and returns `None`.

`WI-VALIDATOR-YAML-PARSER` already recorded the demand to replace
`_parse_simple_yaml` with "a production-grade parser," anticipating almost
exactly this. What that WI didn't (and couldn't) anticipate: a full audit
of `project/`'s actual content against real PyYAML surfaced three further
compatibility classes that a naive swap would silently mishandle:

1. **List items with an unquoted `key: value` shape** (e.g. `- Some
   sentence: with a colon`) parse as a one-entry mapping, not a string —
   confirmed in 9 real files.
2. **Plain scalars starting with a reserved indicator (backtick, etc.) or
   containing a second unescaped colon** are hard YAML syntax errors —
   confirmed in 18 more real files.
3. **A space followed by `#` anywhere inside a plain scalar starts a YAML
   comment**, silently truncating the rest of the value with no parse
   error at all — confirmed in 45 files / 50 fields, mostly
   `instruction_source` values referencing "PR #NNN," a field the project
   already treats as provenance-critical.

A fourth issue — PyYAML's default resolver auto-converting unquoted
ISO-8601-shaped scalars (`created_at`, etc.) into `datetime` objects —
hits 723 of 972 files, but was traced to only 3 real downstream consumers
(`prompt_workflow_records.py:129`, `prompt_workflow_slug.py:685`,
`prompt_workflow_search.py:250`), all fixable by handling `datetime`/`date`
explicitly rather than falling through to `str()`/dropping the value.

Verified directly (not inferred): all three lexical-grammar issues (1-3)
are properties of YAML's *plain scalar* style specifically, not of
PyYAML's implementation — quoted (`"..."`) and block-scalar (`>`) forms of
the identical content parse correctly and losslessly under
`yaml.safe_load`. This holds for any spec-compliant YAML parser (PyYAML,
ruamel.yaml, strictyaml all tokenize plain scalars the same way), so no
drop-in parser substitution fixes already-existing content — the fix has
to include a content-encoding change, not just an engine change.

## Prior Art Check

### Duplication search
- In-repo: Related — `project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md`
  already proposes replacing `src/lrh/control/validator.py`'s `_parse_simple_yaml` with
  PyYAML/ruamel.yaml, for the same "bootstrap avoided dependencies, no
  longer justified" reason. It is scoped only to `src/lrh/control/validator.py`, not
  `src/lrh/control/parser.py` (where the actually-reported bug lives), and has no
  awareness of the content-compatibility findings below, since none of
  that was known when it was filed.
- Sibling repos: None identified — LCATS, Taurcode, Taurworks, prosoc,
  Velumin, and Replication Vector all consume LRH's frontmatter
  conventions but were not checked individually for local parser forks;
  this proposal assumes they inherit LRH's parser as-is.
- External libraries: PyYAML (already a declared dependency,
  `pyproject.toml`), ruamel.yaml (ruled out — its `TimeStamp` type is
  still `isinstance(datetime.datetime)`, so it doesn't solve the
  date-coercion problem either, and its round-trip-fidelity value
  proposition is irrelevant since LRH's frontmatter writer,
  `conversations/frontmatter.py`, is already a separate hand-written
  serializer, not a read-modify-write loop through this parser),
  strictyaml (ruled out for this scope — returns a wrapper object
  requiring all ~15 `src/lrh/control/parser.py` consumers to change, and still
  inherits the same plain-scalar lexical grammar since it "parses a
  restricted subset of the YAML specification").
- Recommendation: Proceed — extend/supersede `WI-VALIDATOR-YAML-PARSER`
  rather than duplicate it.

### Demand search
- Work items: Found — `WI-VALIDATOR-YAML-PARSER` — "Replace bootstrap YAML
  parser with production-grade parser" (satisfied and substantially
  extended by this proposal).
- Proposals: None found.
- Backlog: No matching entries in `project/design/backlog.md` or
  `decision_log.md`.
- Recommendation: Offer to close/supersede `WI-VALIDATOR-YAML-PARSER` —
  actioned in this same PR; see `project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md`.

## Design Decisions

### Decision 1: Parser engine

Options considered: keep two hand-rolled parsers (status quo — rejected,
it's the root cause); PyYAML `yaml.safe_load`; ruamel.yaml; strictyaml.

**Chosen: PyYAML `yaml.safe_load`**, already a declared dependency and
matching `WI-VALIDATOR-YAML-PARSER`'s own shortlist. ruamel.yaml and
strictyaml are both ruled out per the Prior Art Check above — neither
solves problems PyYAML doesn't, and both add dependency/migration cost
disproportionate to the benefit.

### Decision 2: Handling implicit date-typing

Options considered: disable PyYAML's implicit timestamp resolver (zero
downstream changes, but an unofficial pattern hooking
`yaml_implicit_resolvers` directly — no `remove_implicit_resolver` ships
in PyYAML itself, confirmed against the installed package's
`resolver.py`); accept real `datetime`/`date` objects and patch the 3
actual consumers.

**Chosen: accept real datetime objects, patch the 3 consumers**
(`_frontmatter_string`, `_string_frontmatter_fields`, `_stringify` each
gain an explicit `isinstance(value, (date, datetime))` branch calling
`.isoformat()`), matching PyYAML's genuine default behavior — the same
default `python-frontmatter`, the most widely used Python frontmatter
library, uses. This keeps LRH's parser layer free of non-standard
configuration, at the cost of touching `prompt_workflow_slug.py`'s
cross-PR freshness-matching logic.

### Decision 3: Detecting the colon-collapse case

**Chosen:** extend `lrh validate`'s existing list-field schema checks
(`WORK_ITEM_LIST_FIELDS`, `WORKSTREAM_LIST_FIELDS`,
`DESIGN_PROPOSAL_LIST_FIELDS`) with a shared
`_check_list_field_items_are_strings()` helper flagging any non-string
list item as a validation error — surfaces the problem rather than
silently coercing it, since a silent auto-fix at parse time would mask
future authoring mistakes the same way the original bug did.

### Decision 4: Migrating existing unsafe content

Options considered: leave existing files broken until someone hits them
(rejected — that's the status quo failure mode); hand-edit every affected
file (works for the ~72 files found in LRH itself, but not reusable by
downstream repos); a diff-based tool comparing the old lenient parser's
output against `yaml.safe_load`'s output and rewriting every divergence;
a raw-text lexical scanner restricted to the proven-unsafe patterns.

**Rejected: blanket diff-based rewriting.** An earlier draft of this
decision proposed comparing LRH's existing lenient parser's reading
against `yaml.safe_load`'s reading and rewriting any line where they
diverge. Verified directly that this is unsound: the old parser retains
literal quote characters on already-correctly-quoted list items (e.g.
`- "some text"` reads back as the string `'"some text"'`, quotes
included) while `yaml.safe_load` correctly strips them — a bare diff
would treat *already-safe, correctly-quoted* content as a divergence and
re-encode the old parser's quote-containing reading as new literal data,
corrupting it. The same blanket-diff approach would also flag every
`created_at`-shaped field as a divergence (string vs. `datetime`), which
Decision 2 already resolved as an accepted, correct behavior — rewriting
those would contradict Decision 2's own resolution rather than implement
it.

**Chosen:** the migration tool shares its detection logic with Decision
5's lint guard — the same raw-text, pre-YAML-parse checks (unescaped
`: `, unescaped ` #`, a scalar starting with a reserved indicator, a
plain scalar that fails to parse at all, or a scalar in a string field
that would implicit-resolve to a non-string type) — run in "fix" mode
instead of "detect" mode. A line is only a rewrite candidate when its *raw
text* matches one of these proven-unsafe patterns; a bare difference in what
the two parsers *return* is never itself a rewrite trigger, so already-safe
quoted content and the accepted date/datetime divergence are never
touched. Once a line is flagged this way, the value to re-encode is that
line's literal text as the historical lenient parser would have read it
(ground truth for author intent for a *confirmed-unsafe* line only, not a
detection signal) — rewritten as a properly quoted (or block-scalar, for
multi-line) scalar. Self-verifying (re-parse after rewrite, assert intent
preserved), minimal-diff (never a full-file re-dump). Exposed via the
existing `lrh project doctor` surface (`src/lrh/cli/main.py:267`, already
generic and `--project-root`-driven) as a new `--fix-frontmatter` flag,
dry-run by default. Sharing the detector with Decision 5 also means the
migration tool and the lint guard can never disagree about what counts as
unsafe — a lint pass after migration is a hard guarantee of a clean
result, not just an expectation.

For repos without LRH's lenient-parser lineage, the same raw-text
detector still applies unchanged (it never depended on the old parser for
*detection*, only for the replacement text of an already-flagged line);
those repos' replacement text is instead derived directly from the raw
line (stripped of the specific unsafe construct) rather than from the old
parser's reading.

**Rollout for this repository specifically:** run dry-run first against
LRH's own `project/` tree and manually review the diff before applying —
given 45+27 files already found by manual audit, more may surface once
the tool runs exhaustively, and this is new logic that will rewrite
committed files.

### Decision 5: Preventing recurrence

**Chosen:** a raw-text, pre-YAML-parse lexical scanner added to `lrh
validate` — detector only, never a rewriter — flagging unescaped `: `,
unescaped ` #`, scalars starting with a reserved indicator, or
whole-scalar values that would implicit-resolve to any non-string type
(bool, null, int, float, or date/timestamp) in a string field — not a
fixed bool/null/date/int enumeration, since that list was itself found
missing `float` during review (a bare unquoted `1.5` implicit-resolves the
same way `1` does) and a closed list invites the same class of gap again.
Paired with a single blanket rule added to the
frontmatter-authoring skills (`lrh-work-item`, `lrh-workstream`,
`lrh-proposal`, `lrh-closeout`/`lrh-execute`'s record-writing steps): quote
every free-text scalar value; never write bare prose after `key:` or
`- `. A blanket rule is chosen over an enumerated character checklist
because a checklist is exactly the kind of thing this investigation showed
gets satisfied 95% of the way and still misses a landmine.

## Non-Goals

- Does not change LRH's frontmatter *writer* (`conversations/frontmatter.py`)
  — that module already deterministically quotes/escapes and is unaffected
  by this proposal.
- Does not adopt ruamel.yaml or strictyaml — both evaluated and ruled out
  per Decision 1.
- Does not attempt to enumerate every possible YAML landmine — the lint
  guard and migration tool (Decision 4, revised) share one detector
  covering the four lexical-grammar classes already confirmed; a landmine
  outside those classes would need a new pattern added to the shared
  detector, not a separate mechanism.
- Does not run the migration tool against any repo other than LRH itself
  as part of this proposal's implementation — downstream repos adopt it
  via their own LRH dependency upgrade, on their own timeline.
- Does not change `lrh work-items readiness`'s "work item not found"
  wording for other malformed-frontmatter cases beyond what the parser
  consolidation fixes.

## Implementation Plan

Large scope, multi-stage — governed by a companion workstream
(`WS-LRH-FRONTMATTER-PARSER`, filed alongside this proposal). Work items
to be filed under it:

1. Parser consolidation: `src/lrh/control/parser.py` → `parse_frontmatter_mapping()`
   on `yaml.safe_load`; `src/lrh/control/validator.py` drops `_parse_simple_yaml`, imports
   the shared function; `_check_list_field_items_are_strings()` added to
   the three schema checks. Unit + integration tests (including the
   real-`project/`-tree loader test as regression guard).
2. Datetime consumer patches (3 files) + tests.
3. Manual content fixes for the 27 files already found by audit (9
   colon-collapse + 18 syntax-error), landed alongside step 1 so `lrh
   validate`/`loader_test` pass cleanly again.
4. Migration tool (`lrh project doctor --fix-frontmatter`) — dry-run mode
   first, reviewed manually against LRH's own `project/` tree, `--apply`
   only after review; covers the 45-file truncation class and any further
   findings the exhaustive tool run surfaces beyond the manual audit.
5. Lint guard in `lrh validate` (raw-text scanner) + skill guidance
   updates.
6. Close `WI-VALIDATOR-YAML-PARSER` as superseded by this proposal
   (actioned in this same PR).

## Cross-References

- Superseded work item: `project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md`
- Bug site: `src/lrh/control/parser.py:65-123`
- Duplicate parser: `src/lrh/control/validator.py:568-639`
- Companion workstream: `project/workstreams/proposed/WS-LRH-FRONTMATTER-PARSER.md`

## Open Questions

- Should the migration tool's allow-list fallback mode (for repos without
  LRH's lenient-parser lineage) be built now or deferred until a
  downstream repo actually needs it? Deferred to the governing work item's
  scoping.
- Should the lint guard's four risk patterns live in `src/lrh/control/validator.py`
  directly or a new `control/frontmatter_lint.py` module? Deferred to
  implementation.

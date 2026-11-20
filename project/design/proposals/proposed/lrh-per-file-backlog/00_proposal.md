---
id: PROP-LRH-PER-FILE-BACKLOG
type: design_proposal
title: "Per-File Backlog Entries — One Markdown File per Entry with Minimal Frontmatter"
status: proposed
created_on: 2026-11-12
updated_on: 2026-11-12
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/backlog.md
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/backlog.md
  - project/design/proposals/adopted/lrh-skills-target-aware-install/backlog.md
  - project/memory/decision_log.md
  - src/lrh/skills/_shared/prior-art-check.md
---

# Per-File Backlog Entries — One Markdown File per Entry with Minimal Frontmatter

## Summary

Replace hand-maintained single-file backlogs (`project/design/backlog.md` and
its equivalents) with one Markdown file per backlog entry under
`project/backlog/{open,closed}/`, each carrying a small YAML frontmatter
block (slug `id`, `title`, `status`, `noted`, and a few optional fields) and a
free-prose body. LRH validates only the frontmatter and provides read-only
`lrh backlog list|search` views first; write-side commands follow once a
skill needs to write entries automatically. The format is designed so every
existing backlog in the LRH project family — LRH, Taurworks, LCATS, and
prosoc — can be hand-migrated to it.

## Background / Motivation

Backlogs across the LRH project family are hand-edited Markdown files in at
least three different shapes, none of which tooling can edit safely:

- **LRH** `project/design/backlog.md` — 2,488 lines, 46 `## ` entries, zero
  table rows, fields `**Noted:**` (45×) / `**Status:**` (41×) /
  `**Related:**` (40×) / `**Idea:**` (36×) separated by `---`
  (`project/design/backlog.md:3-6`). `**Status:**` is free prose ("Not yet
  a…", "Tracked as…", "Resolved — 2026-07-30…"), so open entries cannot be
  listed mechanically. 83 commits have touched it; one required a merge
  resolution (`ce231039`, "resolve backlog.md conflict").
- **Taurworks** `project/design/backlog.md` — 2 entries, a verbatim copy of
  LRH's template, both derived by hand from an audit's follow-up
  recommendations (`project/audits/side_effects.md` #1 and #7).
- **LCATS** `lcats/project/design/backlog.md` — 1,297 lines, about 35
  `### ` entries grouped under source-named `## ` sections, with status and
  P0–P3 priority encoded in the heading suffix (LCATS `backlog.md:16-23`,
  `:178`). The same incident is recorded twice as separate entries
  (`:178` and `:845`, both the 2026-08-07 `*-0051` WI-numbering collision) —
  a dedupe failure. The header says promoted items are removed
  (`:7-9`), but resolved entries are retained in practice (`:40`, `:88`,
  `:262`, `:502`, struck through at `:704`, `:731`).
- **prosoc** `project/design/backlog.md` — 257 lines whose main content is
  four Markdown tables of one-line items (§§ at `:9`, `:82`, `:123`,
  `:159`). Its own `## Tooling` note (`:185-193`) asks for the card-audit
  skills to append rows automatically, which the in-flight prosoc work item
  `WI-CARD-AUDIT-BACKLOG-SYNC` addresses with a project-local helper (not on
  prosoc `main` as of 2026-11-11).

The common difficulty is that adding, updating, closing, or deduping an entry
means a precise range edit inside a large shared file: the edit must not
spill into neighbouring prose, a re-run must not duplicate an existing entry,
and concurrent branches that each append an entry conflict. Audit-producing
skills (`/lrh-doc-audit`, prosoc's card audits, ad-hoc audits under
`project/audits/`) generate exactly the kind of findings that should be
collated into a backlog, so the pressure to write entries by tool will grow.

A session assessment (2026-11-11) compared five candidate formats and found
that per-file entries are the only option that removes the precision-edit and
append-conflict problems by construction, and that they match patterns LRH
already uses: per-file work items (274 files bucketed by lifecycle under
`project/work_items/`), per-file decisions (`project/memory/decisions/`,
coexisting with the single-file `project/memory/decision_log.md`), and the
validated-writer approach of `PROP-LRH-MEMORY-COMMAND`.

## Prior Art Check

### Duplication search
- In-repo: No existing backlog tooling found (`src/lrh/` has no backlog
  module; `lrh search` covers only `executions`). Related precedents:
  `project/work_items/` lifecycle buckets and `lrh work-items organize`;
  `project/memory/decisions/`; `PROP-LRH-MEMORY-COMMAND`
  (`lrh memory write|list|search|validate`); the frontmatter reader
  `read_frontmatter_and_body` (`src/lrh/prompt_workflow_memory.py:187`).
  Two proposal-local backlogs exist
  (`project/design/proposals/adopted/lrh-skills-target-aware-install/backlog.md`,
  `type: design_backlog`; and
  `project/design/proposals/adopted/lrh-codex-conversation-exporter/backlog.md`,
  a pointer kept deliberately thin because planning skills only search the
  canonical backlog).
- Sibling repos: prosoc `WI-CARD-AUDIT-BACKLOG-SYNC` (project-local table
  append helper, in flight); LCATS and Taurworks have no backlog tooling.
- External libraries: Considered Backlog.md (`MrLesk/Backlog.md`, an npm CLI
  that stores each task as a Markdown file with YAML frontmatter). Not
  adopted: it models executable tasks (acceptance criteria, kanban status,
  assignees) rather than deferred ideas, uses sequential `TASK-N` IDs that
  required cross-branch ID tracking to avoid collisions, and would add a
  Node toolchain dependency. Its one-file-per-entry layout is borrowed.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: No matching LRH entry. Related: prosoc `backlog.md` § "Tooling"
  (`:185-193`) requests automatic backlog appends; LRH § "Programmatic
  planning-state transitions" requests lifecycle commands for other
  planning artifacts (adjacent, not satisfied by this proposal).
- Recommendation: Link prosoc `WI-CARD-AUDIT-BACKLOG-SYNC` once it lands, so
  its helper can target this format during prosoc's migration.

## Design Decisions

### Decision 1: Storage model

Options considered:
- **Single file, strict heading entries** (LRH's current template with an
  enumerated status and explicit slug). Cheapest migration for LRH and
  Taurworks, but concurrent appends still conflict, and deduping or updating
  still requires parsing and range-editing a large file.
- **Single file with a metadata block per entry** (fenced YAML or HTML
  comments). Inherits both the conflict problem and visual noise.
- **One file per entry** with YAML frontmatter and a Markdown body.
- **Structured data file** (YAML or JSONL) rendered to Markdown. Easy to
  edit by machine, but LRH entries are 20–100 lines of cited prose, which is
  impractical inside YAML or JSON strings, and it conflicts with the lesson
  that "the project schema needs to be readable without the harness"
  (`project/memory/lessons_learned.md:3`).
- **GitHub Issues.** Built-in dedupe and status, but takes the backlog out of
  version control and makes prior-art checks depend on the network.

**Chosen: one file per entry.** Writes are scoped to a single file, dedupe is
an existence check on the ID, new entries never conflict because they are new
files, and the layout matches LRH's existing per-file planning artifacts.

### Decision 2: Location and lifecycle buckets

Options considered:
- `project/design/backlog/` — keeps proximity to today's file.
- `project/backlog/` — a peer of `project/work_items/`, reflecting that
  backlog entries are not all design matters.
- A status field only, with no directory buckets.

**Chosen: `project/backlog/open/` and `project/backlog/closed/`.** Entries with
`status: open` live in `open/`; all other statuses live in `closed/`. A plain
`ls project/backlog/open/` is a usable index without any tooling, mirroring
work-item buckets. Closed entries are retained rather than deleted, which
resolves LCATS's remove-versus-retain drift in favour of the observed
practice in both LCATS and LRH.

### Decision 3: Identity

Options considered:
- Sequential numbers (`BL-0001`).
- Slugs.

**Chosen: lowercase-kebab slugs, equal to the filename stem and never
renumbered.** Sequential numbering computed as "global max + 1" has already
collided across concurrent sessions in LCATS (`backlog.md:178`), and
Backlog.md needed cross-branch ID tracking for the same reason. LRH work
items already use slug IDs.

### Decision 4: Frontmatter schema

**Chosen: four required fields and seven optional ones; no required body
sections.**

```yaml
---
id: lrh-memory-command            # required; slug; equals filename stem
title: "lrh memory command for well-formed cross-agent writes"   # required
status: open                      # required; open | promoted | resolved | dropped
noted: 2026-08-17                 # required; ISO date first recorded
source: "rescue_claude_sessions memory audit"   # optional; session, PR, audit, or WI
priority: P2                      # optional; P0-P3 (LCATS convention)
kind: idea                        # optional; grouping, e.g. missing-forward-ref
subject: null                     # optional; what the entry is about
revisit_when: []                  # optional; trigger conditions for reopening
promoted_to: null                 # optional; WI/WS/PROP ID when status is promoted
related: []                       # optional; IDs or paths
---

Free prose: what was noticed, why it was deferred, the first concrete step.
```

The field set is the intersection of what the four existing backlogs already
record, plus `revisit_when` (written as prose "Revisit if…" in LRH and
Taurworks) and `promoted_to` (which makes promotion explicit). The schema is
deliberately small so a backlog entry does not become a lightweight work item:
there are no owners, dependencies, acceptance criteria, or required sections.

### Decision 5: One-line items (prosoc's tables)

Options considered:
- Keep tables inside a single entry file (reintroduces range edits).
- One file per table row.

**Chosen: one file per row, frontmatter-only bodies allowed.** A prosoc row
becomes, for example, `kind: missing-forward-ref`,
`subject: environment.dense_crowd`. Among open entries, `(kind, subject)` is
unique when both are set, which gives prosoc's audit skills the dedupe key
they need. `lrh backlog list --kind missing-forward-ref --format table`
regenerates today's table as a view.

### Decision 6: Views and indexing

Options considered:
- A committed, generated `INDEX.md`.
- On-demand views only.

**Chosen: on-demand views; no committed index.** A committed generated index
would reintroduce the merge conflicts this design removes. `lrh backlog list`
(filters: `--status`, `--kind`, `--priority`; formats: text, table, JSON) and
`lrh backlog search` (deterministic substring search over frontmatter and
body, matching `lrh memory search`) provide the views.

### Decision 7: Validation

**Chosen: `lrh validate` checks backlog frontmatter only, and only when
`project/backlog/` exists.** Checks: `id` present, lowercase-kebab (the
Decision 3 slug syntax), and equal to the filename stem; `id` unique across
both `open/` and `closed/`, so an entry's identity stays unambiguous when it
moves between buckets; `title` present and non-empty; `status` in the
enumerated set; `status`/bucket agreement (warning, as for proposals);
`noted` parses as a date; `promoted_to` set when `status` is `promoted`;
`(kind, subject)` unique among open entries. These checks apply from the
first phase, because agents create entry files directly until the write
side exists (Decision 8). Bodies are not validated. This makes backlog
entries a lightly formal LRH artifact, a change from today's explicitly
informal `backlog.md`.

### Decision 8: Read side before write side

**Chosen: ship `list`/`search` and validation first; add `lrh backlog add`
(with ID and `(kind, subject)` dedupe), `close`, and `organize` when a skill
needs to write entries automatically.** Read-only views cannot damage any
repository's content, and they address the observed dedupe failure by making
search-before-add cheap. Until the write side exists, agents create entry
files directly and `lrh validate` catches schema errors.

### Decision 9: Migration and legacy files

**Chosen: hand-migrate each repository separately; replace each legacy file
with a short pointer stub.** The stub follows the existing precedent of
`project/design/proposals/adopted/lrh-codex-conversation-exporter/backlog.md`,
which keeps a thin pointer to the canonical location. LRH's two
proposal-local backlogs fold into `project/backlog/` with `related:` pointing
at their proposals. Skill references that name backlog sections by heading
text (for example `src/lrh/skills/_shared/prior-art-check.md:6` and `:99`,
`src/lrh/skills/_shared/chain-defaults.md:7`,
`src/lrh/skills/_shared/lifecycle-chain.md:6`) are repointed to entry file
paths, which are more stable than heading text.

## Non-Goals

- Does not replace work items, workstreams, or proposals — backlog entries
  remain pre-planning notes, and promotion to a work item is unchanged.
- Does not define required body sections or validate entry prose.
- Does not add ranking, scheduling, a board view, or any GitHub Issues sync.
- Does not migrate the LCATS Gettenberg post-adoption register
  (`lcats/project/development/gettenberg-post-adoption-backlog.md`) entry by
  entry; it is a single-topic dossier with pinned evidence and is expected to
  become one backlog entry that links to it.
- Does not set timing for downstream migrations (Taurworks, LCATS, prosoc);
  each repository schedules its own.
- Does not supersede prosoc's `WI-CARD-AUDIT-BACKLOG-SYNC`; that helper can
  be retargeted during prosoc's migration.

## Open Questions

- Is `project/backlog/` the right location, or should entries stay under
  `project/design/backlog/` to minimise churn in existing references?
- Is a separate `deferred` status needed, or does `open` plus `revisit_when`
  cover it?
- During the transition, should the prior-art check (and `lrh backlog
  search`) also read a legacy `project/design/backlog.md` when present, so
  downstream repositories on the old format keep working?
- Should already-resolved or obsolete LRH entries migrate to `closed/`, or be
  dropped with a pointer to their git history?
- Is a committed index ever worth its conflict cost (for example, generated
  only at closeout)?

## Implementation Plan

Medium scope (multiple PRs), best tracked by a workstream:

1. **Schema, validation, and read-only views** — define the frontmatter
   schema, add backlog checks to `lrh validate`, implement
   `lrh backlog list|search`.
2. **Migrate LRH** — convert the 46 entries in `project/design/backlog.md`
   and the two proposal-local backlogs; replace `backlog.md` with a pointer
   stub; repoint skill references and the prior-art check's backlog step.
3. **Write side** — `lrh backlog add` (ID and `(kind, subject)` dedupe),
   `close`, and `organize`, once an automated writer exists (for example,
   audit-skill collation).
4. **Downstream migrations** — Taurworks (2 entries), LCATS (about 35
   entries plus one register pointer), and prosoc (about 43 table rows plus
   prose sections), each as a work item in its own repository.

## Cross-References

- Current LRH backlog: `project/design/backlog.md`
- Validated-writer precedent: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
- Single-file log with per-file promotion precedent: `project/memory/decision_log.md`, `project/memory/decisions/`
- Proposal-local backlogs: `project/design/proposals/adopted/lrh-skills-target-aware-install/backlog.md`, `project/design/proposals/adopted/lrh-codex-conversation-exporter/backlog.md`
- Prior-art check backlog step: `src/lrh/skills/_shared/prior-art-check.md:99`
- Sibling backlogs: Taurworks `project/design/backlog.md`; LCATS `lcats/project/design/backlog.md`; prosoc `project/design/backlog.md`
- External prior art: Backlog.md (`MrLesk/Backlog.md`)

---
id: AUDIT-DOCS-2026-08-21
audit_type: docs
schema_version: 1
status: proposed
repo_root: .
project_root: project
docs_root: docs
control_root: project
package_roots:
  - src/lrh
framework: diataxis
recommended_next_prompt: organize_docs
recommended_phase: scaffold
---

# Documentation Audit — lrh memory CLI coverage

## Summary

`lrh memory` (10 subcommands: `write`, `list`, `validate`, `repair`,
`sync`, `read`, `search`, `export`, `import`, `transfer`) has zero
presence anywhere in `docs/` — no reference page, no how-to guide, no
mention in either README index. This is a genuine gap, not a planned
item awaiting a scheduled doc pass: neither `PROP-LRH-MEMORY-COMMAND`
nor `WS-LRH-MEMORY-COMMAND` names a docs deliverable anywhere in their
text. `lrh sessions` (the CLI's other undocumented command family) has
the identical gap, confirming this isn't unique to memory but is the
established baseline for any command family that hasn't yet gone
through a `/lrh-doc-audit` → `/lrh-doc-organize` pass.

This audit is deliberately scoped to the `lrh memory` gap specifically,
at the user's request — it is not a full-repository documentation
audit. `docs_root` above covers the full `docs/` tree for discovery
purposes, but findings and recommendations below are scoped to the
`memory` (and, where directly comparable, `sessions`) command family.

## Scope and roots inspected

- `docs_root`: `docs/` (full tree walked for the CLI reference and
  how-to indexes; other quadrants — `tutorials/`, `explanations/`,
  `conversations/` — inspected only for cross-references to `memory`
  or `sessions`, not exhaustively re-audited).
- `control_root`: `project/` — inspected `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`,
  `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`, and the four
  `WI-LRH-MEMORY-*` work items for any stated docs intent.
- `package_roots`: `src/lrh/prompt_workflow_memory.py`,
  `src/lrh/memory_workflow.py` — the implementation the docs gap is
  measured against.
- Explicitly **not** re-audited: the rest of `docs/` (already has an
  established structure and its own recent content — see `docs/README.md`
  current-how-to-guides and current-CLI-reference lists, both current as
  of this scan).

## Current documentation inventory

`docs/reference/cli/` (10 files, all Diataxis **Reference**):
`README.md`, `conversation.md`, `meta.md`, `request.md`, `secrets.md`,
`serve.md`, `skills.md`, `snapshot.md`, `survey.md`, `validate.md`,
`work-items.md`. **No `memory.md`. No `sessions.md`.**

`docs/reference/cli/README.md`'s own "Currently relevant docs" list
(lines ~24-34) enumerates exactly those 10 — `memory` and `sessions`
are absent from the index itself, not merely missing a target file.

`docs/README.md`'s top-level "Current CLI reference" list (same
structure) independently omits both `memory` and `sessions`.

`docs/how-to/README.md` (14 guides) has no memory- or sessions-specific
entry. The closest existing precedent for a multi-subcommand CLI family
getting full Diataxis coverage is `lrh secrets`: a 169-line
`docs/reference/cli/secrets.md`, a 185-line
`docs/how-to/scan-and-purge-secrets.md`, and a linked
`docs/explanations/secrets-hygiene-safety-model.md` — three quadrants,
one command family.

`lrh search` (the design precedent `lrh memory search` was explicitly
modeled on, per `PROP-LRH-MEMORY-COMMAND`'s own Decision 7) is itself
only partially documented: `docs/README.md`'s CLI-reference section
notes "Prompt workflow commands (`lrh prompt`, `lrh match`, `lrh
search`) are currently documented in
[Prompt workflow](tutorials/first-prompt-driven-change.md) and
[PROMPTS.md](../PROMPTS.md)" rather than a dedicated reference page —
worth naming as a related, pre-existing gap, not one this audit's
recommendations need to fix.

## Current project and package layout

Implementation: `src/lrh/prompt_workflow_memory.py` (core logic: `write_memory`,
`list_memories`, `validate_corpus`, `repair_memory`, `sync_memory`,
`read_memory`, `search_memories`, `export_memories`, `import_memories`,
`transfer_memories`), `src/lrh/memory_workflow.py` (CLI wiring,
`run_memory_cli`). Dispatched from `src/lrh/cli/main.py`.

Governing design: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
(`status: adopted`, `implementation_status: implemented`). Four
implementing work items, all `resolved`: `WI-LRH-MEMORY-WRITE-SIDE`,
`WI-LRH-MEMORY-ARCHIVE-SIDE`, `WI-LRH-MEMORY-READ-SIDE`,
`WI-LRH-MEMORY-PORTABILITY`. A fifth, `WI-LRH-MEMORY-TRANSFER-SAFETY`,
is open (PR #597) fixing two `transfer`/`import` correctness bugs — its
fix will change `transfer`'s exact `--from`/`--to` resolution behavior,
which is directly relevant to how precisely a reference page can
describe that flag before the fix lands (see Risks and cautions).

## Diataxis classification

| Content needed | Quadrant | Exists? |
|---|---|---|
| Exact `lrh memory <subcommand>` flags, arguments, exit behavior | Reference | No |
| "How to move memories between two projects" (export/import/transfer) | How-to | No |
| "How to keep a project's memory corpus backed up" (sync) | How-to | No |
| Why `authored_by`/cross-agent overwrite guards exist; snapshot-before-overwrite rationale | Explanation | No (partially inferable from `PROP-LRH-MEMORY-COMMAND`'s Design Decisions, which is a `project/` control-plane artifact, not human-facing docs) |
| Guided "first memory write" walkthrough | Tutorial | No — not recommended as a gap to fill; `lrh secrets` and `lrh work-items` (comparable multi-subcommand families) have no tutorial either, only reference + how-to. Flagging a tutorial gap here would be recommending a convention this repo doesn't actually follow for peer command families (guardrail: base gaps on current reality, not templates). |

## Navigation findings

- `docs/reference/cli/README.md`'s own index and `docs/README.md`'s
  top-level index would both need a new line each — they are the only
  two navigation entry points a reader would use to discover a new
  `memory.md` page; both currently work correctly for the 10 documented
  families (no broken cross-links found in either).
- No how-to guide currently references `lrh memory` in passing (checked
  via `grep -rn "lrh memory" docs/how-to/`bin — zero matches), so there
  is no existing "guide that assumes a concept with no reference to link
  to" gap of the kind Step 5's navigation-gap check looks for — the
  command family is simply absent, not half-referenced.

## Accuracy findings

Not applicable — there is no existing `memory`-related content in
`docs/` to check for accuracy drift.

## Stale or ambiguous links

Scanned `docs/README.md`, `docs/reference/README.md`,
`docs/reference/cli/README.md`, and `docs/how-to/README.md` (the four
files whose content this audit directly cites) for internal links per
the normalization rules (skip pure fragments, strip `#section` before
checking, resolve relative to the containing file). **No stale links
found** in these four files. A full-tree stale-link sweep was not run —
out of this audit's explicit lrh-memory scope; note as a candidate for
a future, separately-scoped full audit if desired.

## Project-control-plane vs human-docs boundary

`PROP-LRH-MEMORY-COMMAND`'s "Design Decisions" section (Decisions 1-9)
already contains real explanatory rationale — why `authored_by` exists,
why snapshot-before-overwrite over never-shrink, why substring-only
search — but it lives in `project/design/proposals/`, which is
control-plane state per this project's own convention (`docs/README.md`:
*"The authoritative LRH project control plane remains in
[`../project/`](../project/)... When project state, active plans,
design authority, or evidence matters, link to the relevant artifact
under `project/` instead of duplicating it here."*). A future
`docs/explanations/` page for memory should **link to** these Decisions
rather than re-narrate them, matching how
`docs/explanations/secrets-hygiene-safety-model.md` is written as new
prose that references — not duplicates — its own governing design
artifacts.

## Recommended target documentation structure

Modeled directly on the `lrh secrets` precedent (closest existing
multi-subcommand CLI family with full coverage):

- `docs/reference/cli/memory.md` — one reference page covering all 10
  subcommands, organized by the same four implementation stages the
  proposal itself uses (write-side: `write`/`list`/`validate`/`repair`;
  archive-side: `sync`; read-side: `read`/`search`; portability:
  `export`/`import`/`transfer`), each subcommand's exact flags and exit
  behavior.
- `docs/how-to/back-up-and-restore-project-memory.md` — the `sync`
  workflow (why/when to run it, what `--dry-run` shows, where the
  archive root resolves to).
- `docs/how-to/move-memories-between-projects.md` — the
  `export`/`import`/`transfer` workflow, including the explicit-filter
  requirement (`export`/`transfer` refuse to run unfiltered) and the
  known safety gap `WI-LRH-MEMORY-TRANSFER-SAFETY` is fixing.
- Two-line additions to `docs/reference/cli/README.md`'s and
  `docs/README.md`'s existing indexes.
- Optional, not blocking: a short `docs/explanations/` page on the
  validated-write invariants, linking to `PROP-LRH-MEMORY-COMMAND`
  rather than restating it.

## Recommended phased PRs

1. **PR 1 (reference page + index entries).** Add
   `docs/reference/cli/memory.md` and the two index-line additions.
   Self-contained, no dependency on the how-to guides.
2. **PR 2 (how-to guides).** Add the two how-to guides above, each
   linking back to PR 1's reference page. Sequenced after PR 1 so the
   how-to guides have a real reference target to link to rather than a
   forward-reference.
3. **PR 3, deferred/optional.** The explanations page, once someone
   decides it's worth the duplication-vs-linking tradeoff against
   `PROP-LRH-MEMORY-COMMAND`'s existing Design Decisions section.

## Proposed first PR scope

- Create `docs/reference/cli/memory.md` documenting all 10 `lrh memory`
  subcommands (flags, arguments, exit behavior), organized by the four
  implementation stages.
- Add one line to `docs/reference/cli/README.md`'s "Currently relevant
  docs" list: `` - [`memory`](memory.md) — validate, sync, search, and
  transfer Claude Code's per-project memory corpus. ``
- Add one line to `docs/README.md`'s "Current CLI reference" list:
  `` - [`lrh memory`](reference/cli/memory.md) ``
- Do not create the how-to guides in this PR — sequenced as PR 2 per
  the phased plan above, so this first PR stays reviewable and
  single-purpose.
- Do not touch `lrh sessions`'s identical gap in this PR — same
  pattern, different command family, own separate audit/PR if wanted.

## Risks and cautions

- `WI-LRH-MEMORY-TRANSFER-SAFETY` (PR #597, open) will change
  `transfer`'s exact `--from`/`--to` path-vs-slug resolution behavior.
  Writing `memory.md`'s `transfer` section before that fix lands risks
  documenting behavior that changes underneath the page within days.
  Recommend either sequencing the reference-page PR after
  `WI-LRH-MEMORY-TRANSFER-SAFETY` merges, or writing the `transfer`
  section narrowly (documented flags and purpose only, deferring the
  exact resolution-order prose) and following up via `/lrh-doc-work`
  once that WI lands.
- `lrh search`'s own pre-existing, narrower doc gap (no dedicated
  reference page; only a tutorial mention) is out of this audit's
  scope but is directly relevant precedent to `lrh memory search` —
  worth a cross-reference note in the eventual `memory.md`, not a
  reason to block this audit's own recommendations.

## Validation commands for follow-up PRs

- `lrh validate`
- Manual link-check: verify every new link in `docs/reference/cli/memory.md`,
  `docs/reference/cli/README.md`, and `docs/README.md` resolves, using the
  same normalization rules as this audit's Step 5 (skip pure fragments,
  strip `#section` before checking, resolve relative to the containing file).

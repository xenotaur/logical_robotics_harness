---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-SESSION-ID-DOCS
title: "Document the /lrh-export and /lrh-session-id skill families and fix the stale export docs"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
depends_on:
  - WI-LRH-EXPORT-DISPATCHER
  - WI-LRH-SESSION-ID-DISPATCHER
  - WI-ANTIGRAVITY-SESSION-ID-RESOLVER
  - WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT
blocked_by: []
expected_actions:
  - run_tests
  - create_file
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - rewrite_adopted_or_resolved_documents
  - print_transcript_text
acceptance:
  - "docs/conversations/ has a how-to for exporting and identifying Claude Code, Codex and Antigravity sessions, each starting from the dispatcher and naming the per-vendor skill; the existing codex_export.md is updated rather than duplicated"
  - "A reference page lists every skill in both families (dispatchers, variants and deprecated stubs), with what each wraps, its invocation rule, its archive default and its session_transcript pointer format, and is linked from docs/reference/README.md and docs/conversations/README.md"
  - "The backlog entry 'Generalize conversation export manifests beyond Codex before /lrh-export' is marked resolved and links PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES; project/design/proposals/README.md lists the Codex app-server export proposal under adopted/ and lists this proposal"
  - "lrh conversation inspect-export --help no longer describes itself as Codex-only"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - docs/conversations/README.md
  - docs/conversations/codex_export.md
  - docs/conversations/claude_export.md
  - docs/conversations/antigravity_export.md
  - docs/conversations/conversation-capture-options.md
  - docs/reference/export-and-session-id-skills.md
  - docs/reference/README.md
  - project/design/backlog.md
  - project/design/proposals/README.md
  - src/lrh/cli/main.py
---

# WI-EXPORT-SESSION-ID-DOCS: Document the export and session-ID skill families

## Summary

Write user-facing docs for both skill families once the dispatchers exist:

- a how-to per vendor under `docs/conversations/`;
- one reference page listing every export and session-ID skill.

In the same change, fix the stale planning docs and help text found in the
2026-09-24 audit behind `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`.

## Problem / Context

Findings from the 2026-09-24 audit:

- **Codex-only how-to.** `docs/conversations/` has a how-to only for Codex
  (`codex_export.md`). It never mentions the Claude or Antigravity export
  skills.
- **No skill list.** No page anywhere under `docs/` lists the LRH skills;
  `CLAUDE.md`'s `## Skills` index is the only one.
- **Stale backlog status.** The backlog entry "Generalize conversation export
  manifests beyond Codex before `/lrh-export`" still says "Tracked, not yet
  designed". Its manifest precondition is already met: `SUPPORTED_SOURCE_TOOLS`
  in `src/lrh/conversations/export_manifest.py` covers all three vendors.
- **Stale proposals README.** `project/design/proposals/README.md` lists the
  Codex app-server export proposal under `proposed/` with status `proposed`,
  but it was adopted.
- **Stale help text.** `lrh conversation inspect-export`'s help text says
  "Inspect a Codex conversation export Markdown artifact", but it inspects all
  three vendors' exports.

### Duplication search
- In-repo: Related: `docs/conversations/codex_export.md`, to extend rather
  than duplicate, and `docs/reference/cli/conversation.md`, which is CLI
  reference, not skill reference. No skill reference page exists.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found. `WI-SKILLS-TUTORIAL` (open PR #558) proposes a
  general skills tutorial. Link to it, but do not overlap with it.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`.
- Backlog: "Generalize conversation export manifests beyond Codex before
  `/lrh-export`". This item marks it resolved.
- Recommendation: Resolve the backlog entry as part of this item.

This item also depends on two others, so it documents settled behavior
instead of inventing it:

- `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`. It may end as implemented or as
  abandoned; either way, its result decides whether the Antigravity how-to
  documents a session-ID skill and pointer format, or states they are
  deferred.
- `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`. Its outcome decides the
  confirm-gate column for Antigravity in the reference page.

## Scope

- Add Claude and Antigravity how-tos, and update the Codex how-to to lead with
  `/lrh-export` and `/lrh-session-id`.
- Add one reference page covering both skill families.
- Fix the backlog, the proposals README and the `inspect-export` help text.

## Required Changes

1. **How-tos.** Add `docs/conversations/claude_export.md` and
   `docs/conversations/antigravity_export.md`, matching the structure of
   `codex_export.md`. Each should:
   - start from `/lrh-export` and `/lrh-session-id`;
   - name the per-vendor skills;
   - explain the archive default, the confirm gate and pointer reporting.

   Update `codex_export.md` to the new names and to lead with the
   dispatchers.
2. **Conversations index.** Update `docs/conversations/README.md`'s
   "Implemented capture support" and "Currently relevant docs" to cover all
   three vendors, and update `conversation-capture-options.md` to match.
3. **Reference page.** Add `docs/reference/export-and-session-id-skills.md`
   with a table covering every dispatcher, variant and deprecated stub. For
   each, give:
   - the CLI command it wraps;
   - its invocation rule;
   - its archive default;
   - its pointer format.

   Link it from `docs/reference/README.md` and
   `docs/conversations/README.md`.
4. **Backlog.** Mark the "Generalize conversation export manifests beyond
   Codex before `/lrh-export`" entry in `project/design/backlog.md` resolved,
   with a link to the proposal.
5. **Proposals README.** In `project/design/proposals/README.md`, correct the
   Codex app-server export entry's bucket and status, and add this proposal.
6. **Help text.** Change the `inspect-export` help string in
   `src/lrh/cli/main.py` to be vendor-neutral.

## Non-Goals

- Does not write a general skills tutorial. That is `WI-SKILLS-TUTORIAL`.
- Does not change skill behavior.
- Does not rewrite adopted or resolved documents.

## Acceptance Criteria

- Per-vendor how-tos exist and lead with the dispatchers.
- A reference page covers every skill in both families and is linked from both
  indexes.
- The backlog entry and the proposals README are corrected.
- `inspect-export --help` is vendor-neutral.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh conversation inspect-export --help`

---
resolution: null
blocked_reason: null
blocked: false
id: WI-FRONTMATTER-MIGRATION-LINT-GUARD
title: Add frontmatter migration tool and lint guard
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-FRONTMATTER-PARSER
related_design:
  - project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
depends_on:
  - WI-FRONTMATTER-PARSER-CONSOLIDATION
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - apply_fix_frontmatter_without_manual_review
acceptance:
  - A shared raw-text lexical detector implements the four confirmed unsafe-plain-scalar patterns (unescaped ': ', unescaped ' #', a scalar starting with a reserved indicator, and a scalar in a string field that would implicit-resolve to a non-string type)
  - lrh validate uses the shared detector to flag unsafe patterns as a new lint category, report-only
  - lrh project doctor gains a --fix-frontmatter flag using the same shared detector, dry-run by default, requiring explicit --apply to write; for a repo with LRH's lenient-parser lineage, the replacement value comes from the historical lenient parser's reading, never from stripping the raw line
  - The migration tool's dry-run has been run and manually reviewed against LRH's own project/ tree, and either applied to this repo's own project/ tree after that review or followed by a concrete, blocking follow-up work item that applies it -- this item is not complete on dry-run-and-review alone
  - Frontmatter-authoring skills (lrh-work-item, lrh-workstream, lrh-proposal, lrh-closeout, lrh-execute) are updated with the "always quote free text" guidance in both their src/lrh/skills/ source and their .claude/skills/ and .agents/skills/ rendered mirrors
required_evidence:
  - lrh_validate
  - test_output
  - manual_review
artifacts_expected:
  - src/lrh/control/validator.py
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/
  - .agents/skills/
---

## Summary

Add a shared raw-text unsafe-scalar detector used by both a new `lrh
validate` lint category and a new `lrh project doctor --fix-frontmatter`
one-time content migration tool, plus authoring guidance to prevent
recurrence — implementing Decisions 4-5 of `PROP-LRH-FRONTMATTER-PARSER`.

## Problem / Context

`PROP-LRH-FRONTMATTER-PARSER` (adopted via PR #531) Decision 4 and
Decision 5 specify a shared detector approach after an earlier draft
(diff old-parser-output-vs-`yaml.safe_load`-output) was found, in review,
to risk corrupting already-correctly-quoted content and contradicting
Decision 2's accepted date/datetime divergence. See the proposal's Design
Decisions section for the full rationale and the two P2 findings (float
coverage, detector-list parity between the migration tool and lint guard)
a later review round on that same PR fixed.

### Duplication search
- In-repo: None found — no existing `lrh project doctor --fix-frontmatter`
  flag or frontmatter lint category exists.
- Sibling repos: None identified.
- External libraries: None applicable — this is repo-specific lexical
  detection logic, not a general YAML-tooling gap.
- Recommendation: Proceed.

### Demand search
- Work items: None found beyond `WI-FRONTMATTER-PARSER-CONSOLIDATION`
  (this WI's dependency, not a duplicate).
- Proposals: `PROP-LRH-FRONTMATTER-PARSER` (adopted) — this WI is its
  implementation.
- Backlog: No matching entries.
- Recommendation: No further action.

## Scope

- Implement the shared raw-text unsafe-scalar detector.
- Wire it into `lrh validate` as a new lint category (report-only).
- Wire it into a new `lrh project doctor --fix-frontmatter` flag (dry-run
  default, explicit `--apply`).
- Update frontmatter-authoring skill guidance.

## Required Changes

1. Implement the shared detector (a raw-text, pre-YAML-parse regex-based
   function, in `src/lrh/control/validator.py` or a new
   `src/lrh/control/frontmatter_lint.py` module — decide during
   implementation per the proposal's own Open Questions) covering: unescaped
   `: ` inside a plain scalar/list item, unescaped ` #`, a scalar starting
   with a reserved YAML indicator character, and a scalar in a string-typed
   field that would implicit-resolve to a non-string type (bool, null, int,
   float, or date/timestamp) — not a closed enumeration, per the proposal's
   round-2 review fix.
2. Add a new lint category to `lrh validate` using this detector,
   report-only, never rewriting.
3. Add a `--fix-frontmatter` flag to `lrh project doctor`
   (`src/lrh/cli/main.py`), dry-run by default, requiring explicit `--apply`
   to write. **On a flagged line, derive the replacement value per the
   proposal's Decision 4, not by stripping the raw line:** for a repo with
   LRH's lenient-parser lineage (this repo included), re-encode the line's
   literal text *as the historical lenient parser would have read it*
   (ground truth for author intent) as a properly quoted or block-scalar
   value — stripping the unsafe construct from the raw line directly is
   reserved for repos *without* that lineage only, per the proposal's own
   text. Getting this backwards corrupts real content: e.g.
   `instruction_source: ... discovered verifying PR #531` would lose
   ` #531` if the raw line were naively stripped at the unsafe construct,
   when the correct behavior is to preserve the full intended sentence and
   change only its YAML encoding. Minimal-diff (never a full-file re-dump).
   Self-verify by re-parsing after rewrite.
4. Run `lrh project doctor --fix-frontmatter` (dry-run) against this repo's
   own `project/` tree and manually review the diff. **This work item is
   not complete on dry-run-and-review alone:** either apply the reviewed
   fix to this repo's own `project/` tree (`--apply`) as part of this work
   item, or file a concrete, blocking follow-up work item that applies it —
   WS-LRH-FRONTMATTER-PARSER's exit criteria must not be satisfiable while
   the 45 files/50 fields with silently-truncated provenance-critical
   content (the proposal's most dangerous finding) remain unfixed with no
   tracked path to actually fixing them.
5. Update `src/lrh/skills/lrh-work-item/SKILL.md`,
   `lrh-workstream/SKILL.md`, `lrh-proposal/SKILL.md`,
   `lrh-closeout/SKILL.md`, and `lrh-execute/SKILL.md` (and both their
   rendered `.claude/skills/` and `.agents/skills/` mirrors — per
   `project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md`,
   `.agents/skills/` is Codex's own first-class local install target,
   parallel to `.claude/skills/`, not an optional extra) with the blanket
   rule: quote every free-text scalar value; never write bare prose after
   `key:` or `- `.

## Non-Goals

- Does not build the allow-list fallback mode for repos without LRH's
  lenient-parser lineage — deferred per the proposal's Open Questions;
  file a follow-up WI if a downstream repo needs it.
- Does not run the migration tool against any repo other than LRH itself.
- Does not attempt to enumerate every possible YAML landmine beyond the
  four confirmed classes.

## Acceptance Criteria

- `lrh validate` flags the four confirmed unsafe-plain-scalar patterns as a
  distinct lint category, without rewriting anything.
- `lrh project doctor --fix-frontmatter` exists, is dry-run by default, and
  only writes with explicit `--apply`.
- The migration tool and lint guard share one detector implementation —
  verified by a test asserting they agree on the same fixture inputs.
- The dry-run has been run and manually reviewed against this repo's
  `project/` tree.
- The five named skills' guidance is updated and their rendered mirrors are
  in sync.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh project doctor --fix-frontmatter` (dry-run, manual review of output)

## Dependencies / Order

Depends on `WI-FRONTMATTER-PARSER-CONSOLIDATION` landing first — the shared
detector's "reserved-suffix" and "implicit-resolution" checks are meaningful
only once the parser layer they're guarding is the consolidated
`yaml.safe_load`-based one, and running the migration tool against content
the consolidation WI already fixed avoids duplicate/conflicting rewrites.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-FRONTMATTER-PARSER.md`
- Design: `project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md`

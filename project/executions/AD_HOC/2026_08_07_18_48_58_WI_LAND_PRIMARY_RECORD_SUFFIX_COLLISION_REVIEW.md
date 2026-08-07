---
execution_id: 2026_08_07_18_48_58_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_REVIEW)[2026-08-07T18:48:20+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_07_16_34_03_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/508
commit: 38cbe83
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/508
session_transcript: pending
created_at: 2026-08-07T18:48:58+00:00
---

# Summary

Round 2 of review-response on PR #508. After merging `origin/main` into
the branch to resolve a `CONFLICTING` mergeable state (which had silently
blocked CI from ever triggering — matches the project's own known
`mergeable:CONFLICTING` CI-silence pattern), two new Codex findings landed
on the resulting merge commit.

# Result

**Fixed (2):**

1. (P1, Codex) "Restrict base-slug proof to the candidate's lineage": the
   provenance check's base-slug existence test was scoped repo-wide (a
   `grep` across every `execution_id` under `project/executions/`), which
   is its own false-positive risk in the opposite direction from the
   original bug — two unrelated primaries named e.g. `FOO` and
   `FOO_REVIEW` would make the repo-wide lookup falsely "prove"
   `FOO_REVIEW` is a side record of `FOO`. Fixed by scoping the base-slug
   lookup to `$candidate_slugs` (this search's own gathered candidates)
   instead of the whole repository — a genuine side record's base is
   always among its own siblings, so this closes the cross-project
   false-positive with no loss of correctness on any previously-verified
   case.
2. (P2, Codex) "Synchronize the authoritative primary-selection rule": the
   Five Glue-Logic Rules summary table (`land-workflow.md` line 16) still
   stated the old bare-suffix exclusion rule, contradicting the corrected
   algorithm documented further down the same file. Updated the table row
   to point at the provenance check instead of restating the old rule.

# Validation

- Re-verified all four previously-tested cases (PR #464 real collision,
  PR #347 real orphan, doubled-suffix `ADOPT_PROP` case, isolated-`FOO`
  hypothetical simulating an unrelated repo-wide match) against the
  corrected, `$candidate_slugs`-scoped algorithm — all resolve correctly
- `diff -r` on the `lrh-land` mirror pair → zero output
- `scripts/format --check --diff`, `scripts/lint` → clean
- `lrh validate` → 0 errors, 1 pre-existing unrelated warning
  (`WS-SESSION-ARCHIVE-SYNC`)
- PR mergeable state confirmed `MERGEABLE` after the `origin/main` merge
  (was `CONFLICTING`); all 5 CI checks green on the merge commit

# Follow-up

Suggest re-running `/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/508`
before merge to verify these fixes against the current diff and resolve
the review threads.

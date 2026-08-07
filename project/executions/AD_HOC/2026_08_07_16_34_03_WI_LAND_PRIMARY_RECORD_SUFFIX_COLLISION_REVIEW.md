---
execution_id: 2026_08_07_16_34_03_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_REVIEW)[2026-08-07T16:33:27+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_07_16_17_43_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION
pr: https://github.com/xenotaur/logical_robotics_harness/pull/508
commit: ee64b2b
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/508
session_transcript: pending
created_at: 2026-08-07T16:34:03+00:00
---

# Summary

Address 1 Codex P1 review comment on PR #508 (primary-record
provenance-check fix). Comment identified a real regression risk in the
landed algorithm and was fixed, not skipped.

# Result

**Fixed (1):**

1. `r3737192840` (Codex, P1) — "Keep orphaned side records out of the
   primary set": the algorithm's "no matching base slug found → primary"
   rule silently misclassified an orphaned side record (a `_REVIEW`/
   `_CONFIRM` record for a PR with no `/lrh-implement` primary at all,
   per those skills' own `rerun_of`-empty convention for that case) as
   primary — indistinguishable, by naming alone, from the bug's real
   motivating scenario (a primary record whose own slug coincidentally
   ends in a reserved word).

   Fix: three-state classification (primary / ambiguous / not-found) with
   sibling elimination. A "no base" reserved-suffix candidate is promoted
   to primary only when another candidate for the same PR is
   unambiguously a genuine side record — proving a primary must exist.
   Otherwise it is `ambiguous`, not primary: `/lrh-land` Step 1 stops and
   asks the human rather than silently guessing; the lower-stakes
   `rerun_of` sites in `/lrh-confirm-fixes` and `/lrh-review-response`
   leave `rerun_of` empty and note the ambiguity instead of guessing.

   The remaining irreducible case (a PR with exactly one orphaned side
   record and no primary or siblings at all — genuinely undecidable from
   `execution_id` naming alone, requiring a schema change to fully
   resolve) is logged to `project/design/backlog.md`, not silently
   ignored.

# Validation

- Re-verified against this repo's real collision case (PR #464,
  `WI-SKILLS-LRH-SELF-REVIEW`): sibling elimination correctly resolves it
  to primary (its `_CONFIRM` sibling proves a primary exists)
- Simulated a lone orphan (same file, no siblings): correctly falls to
  `ambiguous` instead of being silently misclassified as primary — the
  exact regression Codex identified
- Re-verified the doubled-suffix case (`ADOPT_PROP_LRH_SELF_REVIEW_REVIEW`)
  still resolves correctly under the new three-state algorithm
- `diff -r` on all three mirror pairs → zero output
- `scripts/format --check --diff`, `scripts/lint` → clean (after
  correcting a mid-session Black version drift by prefixing the LRH conda
  env's `bin/` to `PATH`)
- `scripts/test` → 1004 tests passed
- `lrh validate` → 0 errors, 0 warnings

# Follow-up

Suggest running `/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/508`
before merge to verify the fix against the current diff and resolve the
review thread.

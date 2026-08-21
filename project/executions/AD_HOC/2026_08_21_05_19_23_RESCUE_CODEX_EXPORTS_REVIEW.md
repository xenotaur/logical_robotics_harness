---
execution_id: 2026_08_21_05_19_23_RESCUE_CODEX_EXPORTS_REVIEW
prompt_id: PROMPT(AD_HOC:RESCUE_CODEX_EXPORTS_REVIEW)[2026-08-21T05:12:55+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/582
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/582
session_transcript: claude-app:dcf660e9-d89f-41e7-a220-edcede420919
created_at: 2026-08-21T05:19:23+00:00
---

# Summary

Address five open review comments on PR #582 (`experimental/rescue_codex_exports`):
two `chatgpt-codex-connector` P2 findings and three from
`copilot-pull-request-reviewer`. All five passed the presence / validity /
feasibility triage; none conflicted with a design decision — each is a
genuine robustness gap in first-draft tooling that hadn't been reviewed
yet.

`rerun_of` is empty: Step 3's slug-based check found no prior `_REVIEW`
record for this branch, and no primary record with slug
`RESCUE_CODEX_EXPORTS` exists — PR #582 was opened by hand rather than
through `/lrh-implement`, so there is no primary implementation record to
link (same shape as PR #561's own `_REVIEW` record).

# Result

**Codex — duplicate destination names across source depths (fixed).**
`plan_move` only checked each candidate against the pre-run destination,
not against sibling candidates in the same batch. Two candidates at
different nesting depths sharing a basename (the skill mints
`lrh-codex-export-<id>` independent of depth) both appeared absent from
the destination during planning and both were queued into `to_move`; the
second `shutil.copytree` during `--apply` then collided with the first's
freshly-written directory and crashed mid-run, after the first source had
already been deleted. `plan_move` now groups `to_move` by basename after
classification and routes any name with more than one candidate into the
`divergent` bucket (refused, reported, nothing written) — reconciling
which one is authoritative is a judgement call, not a mechanical one, the
same rationale already used for content divergence.

**Codex — provenance recorded after deletion, not before (fixed).**
`append_manifest` ran once, after the whole batch loop finished deleting
originals. A manifest-write failure (unwritable log, full disk) would
therefore occur only after every source in the batch was already gone,
leaving destination arrivals with no recoverable provenance despite the
tool's own documented invariant. Replaced with `append_manifest_entry`,
called once per directory immediately after that directory's copy is
verified and *before* its original is deleted; if it raises, the loop
reports a per-item failure, removes the unlogged copy, and leaves that one
original in place rather than aborting the whole run or losing
provenance for directories already processed.

**Copilot — inconsistent skip exit code (fixed).** `find_exports.py`
returned 1 for a missing `--source` directory while `move_exports.py`
returned 0 for the identical condition, despite both printing "skip."
Aligned `find_exports.py` to return 0, matching the "skip" language both
scripts already use — a missing scan root (e.g. `${TMPDIR:-/tmp}` absent
in a constrained environment) is a no-op to report, not a tool error.

**Copilot — unescaped `|` in Markdown manifest cells (fixed).** Added
`_escape_table_cell`, replacing `|` with `\|` before writing the source
and dest path cells, so a path containing a pipe character can't corrupt
`MIGRATION_LOG.md`'s table structure.

**Copilot — uncaught `shutil.copytree` failure (fixed).** `copy_and_verify`
now catches `OSError` around `copytree` (permissions, ENOSPC, a source
file vanishing mid-copy), removes any partial destination directory it
left behind, and returns a failure description through the existing
mismatch-reporting path instead of crashing the run and leaving a partial
copy that would block a re-run's own "target already exists" check.

Nothing skipped.

# Validation

Run inside the `LRH` conda environment (`conda activate LRH`):

    scripts/version tools          — Python 3.11.15, Ruff 0.15.12, Black 26.3.1,
                                      lrh 0.2.5.dev1727+g8b897fe4c
    scripts/format --check --diff  — 208 files unchanged (exit 0)
    scripts/lint                   — all checks passed (exit 0)
    scripts/test                   — Ran 1174 tests, OK (exit 0)
    lrh validate                   — 0 errors, 0 warnings

`black`/`ruff` run directly against the new files (not covered by
`scripts/format`/`scripts/lint`, which target `src/lrh tests` only): clean.

Each fix verified against a synthetic fixture reproducing the exact
failure mode the comment described:

- Duplicate-basename collision at different depths: refused, nonzero
  exit, nothing written to the destination.
- `find_exports.py` and `move_exports.py` both exit 0 against a
  nonexistent `--source`.
- A `|` in a source path: `--apply` succeeds, `MIGRATION_LOG.md` shows the
  escaped `\|` and remains a valid table.
- Permission-denied destination (chmod 500) simulating a `copytree`
  failure: reported as a per-item failure, partial copy removed, original
  source directory confirmed still present afterward.

# Follow-up

- `session_transcript` resolved directly (same Claude host session that
  opened PR #582, no `pending` needed).
- Suggest `/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/582`
  before merge to verify these fixes against the current diff and resolve
  the review threads.

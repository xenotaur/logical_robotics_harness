---
execution_id: 2026_07_29_21_06_52_LRH_CLOSEOUT_AND_PLANNING_SKILL_BUGS
prompt_id: PROMPT(AD_HOC:LRH_CLOSEOUT_AND_PLANNING_SKILL_BUGS)[2026-07-29T21:06:44-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/438
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/Taurcode/pull/70 (review comments on the resynced skill copies)
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-29T21:06:52-04:00
---

# Summary

Fix eight bugs in lrh-closeout, lrh-proposal, lrh-work-item, lrh-workstream,
and lrh-land surfaced by automated review (Copilot + Codex) on Taurcode PR
#70, which resynced these skills downstream: a per-PR (rather than
per-execution-record) session-transcript resolution bug in lrh-closeout, an
idempotence-check-ordering bug in the three planning skills, four instances
of stale `claude-app:<session-id>` placeholder wording, and a missing
`disable-model-invocation: true` on lrh-land.

# Result

Landed all 8 fixes in commit `125ee23` (PR #438): per-record session-transcript
resolution in `lrh-closeout`, disk-search-by-slug-before-minting in
`lrh-proposal`/`lrh-work-item`/`lrh-workstream`, `claude-app:<host-uuid-stem>`
placeholder wording in 4 files, and `disable-model-invocation: true` on
`lrh-land`. Automated review (Copilot + Codex) on that commit surfaced 7
further comments — all tracing to one gap in the disk-search fix itself:
`<SLUG_UPPER_UNDERSCORE>` was used without ever being defined, and the
`find -name "*<SLUG>*.md"` glob matched the slug as a substring anywhere in
the filename (Codex: could false-positive-block on an unrelated longer
slug, e.g. a `_REVIEW.md` record). Addressed in commit `95ee0a1`: added a
one-line derivation note before each `find` command, and anchored the glob
to the trailing filename segment (`*_<SLUG_UPPER_UNDERSCORE>.md`) in all 6
locations (SKILL.md + references/execution-record.md across the 3 planning
skills).

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf) after both commits
- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`,
  `scripts/test` (808 tests, OK) — all passed after the review-response fix
- `diff -r` clean between `src/lrh/skills/<skill>` and `.claude/skills/<skill>`
  for all 5 skills touched, both commits

# Follow-up

- Once this PR merges, re-sync Taurcode PR #70 from a clean `main` checkout
  (not a feature-branch checkout) so it only carries stable, merged content.
- The same stale `claude-app:<session-id>` placeholder wording exists in
  5 more files not touched here (`lrh-confirm-fixes`, `lrh-doc-organize`,
  `lrh-implement` x2, `lrh-review-response`) — out of scope for this PR
  since review didn't flag them, but worth a follow-up sweep.

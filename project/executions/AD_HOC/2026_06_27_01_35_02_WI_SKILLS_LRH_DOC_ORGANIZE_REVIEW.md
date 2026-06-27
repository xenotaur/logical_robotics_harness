---
execution_id: 2026_06_27_01_35_02_WI_SKILLS_LRH_DOC_ORGANIZE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_DOC_ORGANIZE_REVIEW)[2026-06-27T01:31:51-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_06_27_01_26_52_WI_SKILLS_LRH_DOC_ORGANIZE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/337
commit: dda610e
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/337
session_transcript: claude-app:local_1137bbd3-29eb-4c2e-be43-11a4f4c79216
---

# Summary

Address review comments on PR #337 (lrh-doc-organize skill). Three distinct
issues: missing prompt-ID mint step, diataxis-criteria.md wrong skill context,
and "Step 3b" reference that doesn't exist.

# Result

**Fixed — Issue A (missing prompt-ID mint, P2):** Added new Step 3 — "Mint
prompt ID + idempotence check" — between "Load references" and "Read audit or
discovery pass". Uses slug `doc-organize-phase-<N>-<YYYY-MM-DD>`. Steps 3–10
renumbered to 4–11; confirm gate updated from "Step 5" to "Step 6"; quality
checklist updated with new prompt-ID bullet at top.

**Fixed — Issue B (diataxis-criteria.md skill context, 2 comments):** Updated
the intro paragraph of `lrh-doc-organize/references/diataxis-criteria.md` to
say "Apply at Step 5 of `/lrh-doc-organize`" (scope one phase) and updated the
template counterpart comment from `audit_docs.md` to `organize_docs.md`.

**Fixed — Issue C ("Step 3b" reference, 2 comments):** Changed "proceed to
discovery mode (Step 3b)" in Step 1 to "proceed to discovery mode in Step 4"
(reflecting the renumbering from Issue A).

Both `src/lrh/skills/lrh-doc-organize/` and `.claude/skills/lrh-doc-organize/`
updated; `diff -r` confirms identical.

# Validation

- `scripts/version tools` — Python 3.11.15, Black 26.3.1, Ruff 0.15.12 (env path issue; not a regression)
- `scripts/format --check --diff` — skipped; environment issue (no Python code changed)
- `scripts/lint` — skipped; environment issue (no Python code changed)
- `scripts/test` — skipped; environment issue (no Python code changed)
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-doc-organize/ .claude/skills/lrh-doc-organize/` — identical

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after session ends
- Merge PR #337

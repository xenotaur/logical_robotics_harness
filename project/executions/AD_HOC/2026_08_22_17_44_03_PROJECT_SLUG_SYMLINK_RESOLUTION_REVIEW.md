---
execution_id: 2026_08_22_17_44_03_PROJECT_SLUG_SYMLINK_RESOLUTION_REVIEW
prompt_id: PROMPT(AD_HOC:PROJECT_SLUG_SYMLINK_RESOLUTION_REVIEW)[2026-08-22T17:43:47+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_22_05_28_12_PROJECT_SLUG_SYMLINK_RESOLUTION
pr: https://github.com/xenotaur/logical_robotics_harness/pull/603
commit: 9a7f49c6283cae918a632e18be32f7583400d7f6
created_at: 2026-08-22T17:44:03+00:00
agent: claude_code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/603
session_transcript: claude-app:local_02330303-d423-49f8-9864-aeac6023c0b9
---

# Summary

Addressed two review findings on PR #603 (`WI-PROJECT-SLUG-SYMLINK-RESOLUTION`):
Copilot's `grep -r` vs. `git grep` convention finding, and Codex's P1 finding
that the Demand search was scoped too narrowly and missed a real prior-art
match in an adopted design proposal.

# Result

1. **Copilot finding (presence: yes; validity: yes; feasibility: yes) —
   fixed.** The WI's Demand search and a Risk Notes audit suggestion both
   used `grep -r`/`grep -rn` instead of `git grep`, against AGENTS.md's
   documented convention for repository-wide surveys written into tracked
   artifacts. Replaced both with `git grep` equivalents.
2. **Codex finding (presence: yes; validity: yes; feasibility: yes) —
   fixed.** The original Demand search checked only
   `project/work_items/` and claimed no proposal existed. Re-ran with
   `git grep -n project_slug_for_path` across `project/work_items/`,
   `project/design/proposals/`, and `project/design/backlog.md`. Found
   `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
   Decision 8 (line 120), which independently documents
   `project_slug_for_path()`'s `.resolve()`/symlink-following behavior as
   context for disqualifying a symlink-based design option — real prior
   art, but it does not request or implement a fix, so it corroborates
   rather than duplicates this WI. Added it to `related_design` and cited
   it in Problem/Context and the Demand search section, with an explicit
   note that it does not satisfy this WI's scope.

Both fixes pushed directly to PR #603 (commits `f782854f`, on top of the
prior `e01d660f`).

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `scripts/format --check --diff` — 213 files unchanged.
- `scripts/lint` — all checks passed.
- Markdown-only change; `scripts/test` not run (no Python code touched).

# Follow-up

- None outstanding from this review round.

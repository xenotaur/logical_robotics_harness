---
execution_id: 2026_06_27_00_50_50_WI_SKILLS_DOC_WORK_ITEMS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_DOC_WORK_ITEMS_REVIEW)[2026-06-27T00:42:17-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/335
commit: 8830474
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/335
session_transcript: pending
---

# Summary

Address review comments on PR #335 (WS-SKILLS-DOC workstream + three
WI-SKILLS-LRH-DOC-* work items). Two distinct issues: inverted copy direction
in all three work items, and a non-design artifact in `related_design`.

# Result

**Fixed — Issue A (copy direction):** All three work items (WI-SKILLS-LRH-DOC-AUDIT,
WI-SKILLS-LRH-DOC-ORGANIZE, WI-SKILLS-LRH-DOC-WORK) had Required Changes steps
and acceptance criteria that said "create `.claude/skills/` first, copy to `src/`".
CONTRIBUTING.md defines `src/lrh/skills/<name>/` as canonical. Inverted direction
in all Required Changes steps (steps now read "create `src/`, copy to `.claude/`")
and all acceptance criteria ("`.claude/` is an exact copy of `src/`").

**Fixed — Issue B (`related_design`):** WS-SKILLS-DOC.md had
`project/workstreams/resolved/WS-SKILLS.md` in its `related_design` frontmatter
field. That field is for design/proposal artifacts; the workstream reference was
already present in the body prose. Removed from `related_design`.

No primary execution record found to populate `rerun_of` (PR #335 was created
directly, not via `/lrh-implement`).

# Validation

- `scripts/version tools` — Python 3.11.15, Black 26.3.1, Ruff 0.15.12 (via conda env; bare `python` not in PATH — environment issue, not regression)
- `scripts/format --check --diff` — skipped; environment issue (no Python code changed)
- `scripts/lint` — skipped; environment issue (no Python code changed)
- `scripts/test` — skipped; environment issue (no Python code changed)
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after session ends
- Close PR #334 (superseded by #335)
- Merge PR #335

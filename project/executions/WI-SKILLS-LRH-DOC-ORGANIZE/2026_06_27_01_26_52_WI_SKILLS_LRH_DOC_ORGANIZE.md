---
execution_id: 2026_06_27_01_26_52_WI_SKILLS_LRH_DOC_ORGANIZE
prompt_id: PROMPT(WI-SKILLS-LRH-DOC-ORGANIZE:WI_SKILLS_LRH_DOC_ORGANIZE)[2026-06-27T01:22:10-04:00]
work_item: WI-SKILLS-LRH-DOC-ORGANIZE
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/337
commit: dda610e
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-DOC-ORGANIZE.md
session_transcript: claude-app:local_1137bbd3-29eb-4c2e-be43-11a4f4c79216
---

# Summary

Implement the `/lrh-doc-organize` Claude Code skill: `SKILL.md` (10-step
execution flow), per-skill `references/diataxis-criteria.md` copy,
`references/organize-constraints.md` (scope source rules, path-preservation,
README update rules, Diataxis boundary rules, one-phase-per-PR rule),
`references/organize-workflow.md` (lifecycle placement, execution record
convention). Package copy at `src/lrh/skills/lrh-doc-organize/` (canonical)
mirrored to `.claude/skills/lrh-doc-organize/`. Cross-reference comment added
to `organize_docs.md`. `CLAUDE.md ## Skills` updated.

# Result

All eight skill files created (4 in `src/`, 4 mirrored to `.claude/`).
`organize_docs.md` cross-reference comment added. `CLAUDE.md` entry added.

Key design choices:
- Argument: optional `[audit-path] [--phase N]`; defaults to most recent
  audit artifact in `project/audits/docs/`, falls back to discovery mode
- Confirm gate at Step 5 before branch creation or any file changes
- Branch naming: `<username>/chore/doc-organize-phase-<N>-<YYYY-MM-DD>`
- Execution record slug: `doc-organize-phase-<N>-<YYYY-MM-DD>` (AD_HOC bucket)
- `organize-constraints.md` encodes all six constraint categories from
  `organize_docs.md`, independently reframed for skill context
- `organize-workflow.md` describes the full three-skill pipeline and
  audit-archive convention after all phases complete

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
- Move `WI-SKILLS-LRH-DOC-ORGANIZE` to `project/work_items/resolved/`
- Implement `WI-SKILLS-LRH-DOC-WORK` next

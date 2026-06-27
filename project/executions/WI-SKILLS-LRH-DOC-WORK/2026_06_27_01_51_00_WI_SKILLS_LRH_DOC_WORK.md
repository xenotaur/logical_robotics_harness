---
execution_id: 2026_06_27_01_51_00_WI_SKILLS_LRH_DOC_WORK
prompt_id: PROMPT(WI-SKILLS-LRH-DOC-WORK:WI_SKILLS_LRH_DOC_WORK)[2026-06-27T01:44:21-04:00]
work_item: WI-SKILLS-LRH-DOC-WORK
status: in_progress
rerun_of: 
pr: 
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-DOC-WORK.md
session_transcript: pending
created_at: 2026-06-27T01:51:00-04:00
---

# Summary

Implement the `/lrh-doc-work` Claude Code skill: `SKILL.md` (12-step
execution flow with prompt-ID mint at Step 3), per-skill
`references/diataxis-criteria.md` copy, and `references/doc-work-scope.md`
(scope identification from PR diff / WI acceptance criteria / WS summary,
update-only rule, PR vs. direct-commit guidance, doc-type mapping table).
Package copy at `src/lrh/skills/lrh-doc-work/` (canonical) mirrored to
`.claude/skills/lrh-doc-work/`. No template cross-reference (no `lrh request`
analog exists). `CLAUDE.md ## Skills` updated.

# Result

All six skill files created (3 in `src/`, 3 mirrored to `.claude/`).
`CLAUDE.md` entry added.

Key design choices:
- Argument: optional `[pr-url | WI-ID | WS-ID]`; auto-detects from current
  branch and recent git history if omitted
- Three-tier argument disambiguation: `https://` → PR URL, `WI-` → work item,
  `WS-` → workstream
- Prompt ID minted at Step 3 (before any file reads or changes), using slug
  derived from the work reference type: `pr-<number>`, `wi-<kebab>`, `ws-<kebab>`
- Confirm gate at Step 7 before branch creation or any file changes
- Branch naming: `<username>/chore/doc-work-<work-reference-slug>`
- Execution record slug: `doc-work-<work-reference-slug>` (AD_HOC bucket)
- No template cross-reference: no `lrh request` analog exists for this skill
- `doc-work-scope.md` covers all three reference types (PR, WI, WS), auto-detect
  mode, scope rules (update-only, no audit/reorganize), stale-doc handling, PR
  vs. direct-commit guidance, and a mapping table of change types to doc types
- Proactively included prompt-ID mint at Step 3 to match the pattern fixed in
  the PR #337 review of `/lrh-doc-organize`

# Validation

- `scripts/version tools` — environment issue; not a regression (no Python code changed)
- `scripts/format --check --diff` — skipped; environment issue (no Python code changed)
- `scripts/lint` — skipped; environment issue (no Python code changed)
- `scripts/test` — skipped; environment issue (no Python code changed)
- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-doc-work/ .claude/skills/lrh-doc-work/` — identical

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after session ends
- Update `pr:` and `commit:` after PR opens and merges
- Merge PR
- Move `WI-SKILLS-LRH-DOC-WORK` to `project/work_items/resolved/`

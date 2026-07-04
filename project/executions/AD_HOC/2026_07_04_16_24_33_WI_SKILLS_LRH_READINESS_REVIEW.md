---
execution_id: 2026_07_04_16_24_33_WI_SKILLS_LRH_READINESS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_READINESS_REVIEW)[2026-07-04T16:16:44-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/369
commit: cebb61a026cac22319ded0701466b9ba1d55c90a
created_at: 2026-07-04T16:24:33-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/369
session_transcript: claude-app:5d2f21ba-4fa7-44f2-b4f1-69a8becf1b97
---

# Summary

Addressed two review comments on PR #369 (WI-SKILLS-LRH-READINESS): an
`unresolved-metadata-reference` warning from pointing `related_design` at
`.claude/skills/...` paths, and a missing patch-drafting step in the
`ready-work-item` acceptance criteria.

# Result

- `copilot-pull-request-reviewer`: confirmed via `lrh work-items validate`
  that `related_design` entries under `.claude/skills/` produced
  `unresolved-metadata-reference` warnings (`_REFERENCE_FIELDS_TO_DIRS` in
  `src/lrh/work_items/validate.py:19` only resolves `related_design` against
  `project/design/`). Fixed by setting `related_design: []` and keeping the
  `.claude/skills/...` links only in the body's "Related Workstream and
  Designs" section.
- `chatgpt-codex-connector`: confirmed via `src/lrh/assist/README.md:125-137`
  and `src/lrh/assist/templates/request/ready_work_item.md:37-62` that
  `ready-work-item` renders a non-mutating request and expects a
  `## Proposed Work-Item Patch` to be drafted from it, not applied directly.
  Fixed by updating the Summary, Required Changes, and Acceptance Criteria
  body sections plus the `acceptance:` frontmatter list to require drafting
  that patch before the confirm gate.

# Validation

- `lrh validate` — 0 errors, 0 warnings
- `lrh work-items validate` — no diagnostics remaining for
  `WI-SKILLS-LRH-READINESS.md`
- `scripts/format --check --diff` — clean, 175 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 694 tests, OK

# Follow-up

None — both review comments fully addressed; no skipped items.

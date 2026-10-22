---
execution_id: 2026_10_06_03_50_00_WI_SKILLS_CHATGPT_EXPORT_HARDENING
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING)[2026-09-30T01:28:03+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/775
commit: b559d3622b34f54dc35083babe1d8365fe68f763
created_at: 2026-10-06T03:50:00+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CHATGPT-EXPORT-HARDENING.md
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Created the planning work item `WI-SKILLS-CHATGPT-EXPORT-HARDENING` via
`/lrh-work-item`. It tracks the non-blocking P3 findings deferred from PR
#747's review rounds (`WI-SKILLS-CHATGPT-EXPORT`), as recorded in
`2026_09_28_16_05_19_WI_SKILLS_CHATGPT_EXPORT_IMPL_CLOSEOUT_NOTE`.

# Result

Added `project/work_items/proposed/WI-SKILLS-CHATGPT-EXPORT-HARDENING.md` on
branch `xenotaur/feat/wi-skills-chatgpt-export-hardening` and opened PR #775.

User decisions at the confirm gate:

- **`merge_pr` dropped from `forbidden_actions`.** It forced an override
  question on PR #747.
- **Option A for the hidden-directory finding.** The fix goes in the shared
  `SkillSource.skill_names()`, so `install`, `status`, `check`, and `export`
  are all covered, rather than an export-only filter or a split work item.

The hidden-directory scope was grounded by a probe against `main`
(`ae123356`, unchanged in the relevant files since `da995eca`). A source with
`demo-skill/` and `.git/` gave:

- `skill_names() == ['.git', 'demo-skill']`;
- `install` installed `.git`;
- `status` reported `.git: up_to_date`;
- `export` failed the whole batch.

Prior-art check: no duplicate. The other `when_to_use` mentions
(`WI-LRH-EXPORT-DISPATCHER`, `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`)
concern individual skills' invocation text. Demand comes from PR #747's
closeout note and self-review records.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-CHATGPT-EXPORT-HARDENING`:
  prompt-ready, no warnings.

# Follow-up

- No workstream to update (`related_workstreams: []`).
- After this PR merges, implement via `/lrh-implement` or `/lrh-execute`.
  Use a branch slug distinct from this planning branch (for example an
  `-impl` suffix) to avoid side-record slug collisions.

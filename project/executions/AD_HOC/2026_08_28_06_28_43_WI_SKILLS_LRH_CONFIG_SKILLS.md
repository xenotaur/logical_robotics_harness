---
execution_id: 2026_08_28_06_28_43_WI_SKILLS_LRH_CONFIG_SKILLS
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_CONFIG_SKILLS)[2026-08-28T06:27:07+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/638
commit: bca085b20e4ee721765e893add83137b35f3bfae
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-CONFIG-SKILLS.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-28T06:28:43+00:00
---

# Summary

Filed `WI-SKILLS-LRH-CONFIG-SKILLS`: a `/lrh-config-skills` skill to
inspect and set `project/agent_skills.yaml` install policy, same Option C
architecture as `/lrh-config-gates` applied to the config mechanism
`WI-SKILLS-REPO-CONFIG` already built but never exposed a human-facing
status/confirm layer for.

# Result

- `project/work_items/proposed/WI-SKILLS-LRH-CONFIG-SKILLS.md` created:
  scoped a new `lrh agent-skills status` CLI subcommand (reusing
  `installer.py`'s existing `load_agent_skills_config`/
  `resolve_agent_skills_install_plan` precedence functions, not
  reimplementing them) plus the skill itself. Explicitly scoped: the
  skill may create `project/agent_skills.yaml` from scratch (unlike
  `/lrh-config-gates`, since no other mechanism ever creates this file),
  and must never offer `install.overwrite` as a destructive-capable
  toggle (`docs/reference/schemas/agent-skills-config.md`'s Precedence
  section documents it as CLI-`--force`-only).
- PR #638 opened.

# Validation

- Prior-art check: `git grep -liE "config-skills|agent_skills.yaml|lrh-config-skills"`
  over `project/work_items`, `project/design/backlog.md`,
  `project/design/proposals` -- found `WI-SKILLS-REPO-CONFIG` (resolved,
  built the underlying mechanism only), `WI-SKILLS-SOURCE-ABSTRACTION`,
  `WI-SKILLS-STATUS-CHECK` (unrelated resolved prerequisites), and the
  adopted `lrh-skills-target-aware-install` proposal -- no duplicate of
  this human-facing skill layer exists.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Implementation not yet started -- `/lrh-implement` or `/lrh-execute
WI-SKILLS-LRH-CONFIG-SKILLS` is the natural next step once this filing PR
lands.

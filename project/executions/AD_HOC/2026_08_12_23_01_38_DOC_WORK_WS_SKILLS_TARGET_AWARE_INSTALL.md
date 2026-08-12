---
execution_id: 2026_08_12_23_01_38_DOC_WORK_WS_SKILLS_TARGET_AWARE_INSTALL
prompt_id: PROMPT(AD_HOC:DOC_WORK_WS_SKILLS_TARGET_AWARE_INSTALL)[2026-08-12T21:29:04+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/546
commit: c1075a51
created_at: 2026-08-12T23:01:38+00:00
agent: codex_app
instruction_source: WS-SKILLS-TARGET-AWARE-INSTALL
session_transcript: codex-app:019fe4b6-c537-7c10-8f09-3c2d7e132816
---

# Summary

Updated LRH user documentation after closing
`WS-SKILLS-TARGET-AWARE-INSTALL`, the target-aware skills install workstream.

# Result

- Created `docs/reference/cli/skills.md`, a dedicated reference for
  `lrh skills install`, `lrh skills status`, and `lrh skills check`.
- Linked the new CLI reference from `docs/reference/cli/README.md`.
- Updated `docs/how-to/keep-skills-up-to-date.md` to document that
  Antigravity `plugin.json` participates in status/check/diff/force safety
  behavior.
- Updated `docs/how-to/use-lrh-with-agent-assistants.md` to clarify global vs
  project-scope installs, including why global Antigravity installs make LRH
  skills available across worktrees.
- Opened PR: https://github.com/xenotaur/logical_robotics_harness/pull/546

# Validation

- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools`
  - Reconciled local setup to required Black 26.3.1 and Ruff 0.15.12 before
    validation.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint`
- `git diff --check`
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src python -m lrh.cli.main validate`
  - Passed with 0 errors and 1 pre-existing warning:
    `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` for
    `WS-SESSION-ARCHIVE-SYNC`.
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src scripts/test`
  - Passed: 1086 tests.

# Follow-up

None.

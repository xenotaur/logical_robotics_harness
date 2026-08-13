---
execution_id: 2026_08_13_06_30_16_DOC_WORK_WS_SKILLS_TARGET_AWARE_INSTALL_REVIEW
prompt_id: PROMPT(AD_HOC:DOC_WORK_WS_SKILLS_TARGET_AWARE_INSTALL_REVIEW)[2026-08-13T06:26:02+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_12_23_01_38_DOC_WORK_WS_SKILLS_TARGET_AWARE_INSTALL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/546
commit: 047819398ce899570f8440c211c35d21fbb83c85
created_at: 2026-08-13T06:30:16+00:00
agent: codex_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/546
session_transcript: codex-app:019fe4b6-c537-7c10-8f09-3c2d7e132816
---

# Summary

Addressed review feedback on PR #546 about project-scope skill installation
documentation implying that `--local` automatically uses the current checkout
as the skill source.

# Result

- Triaged two reviewer comments from `chatgpt-codex-connector` and
  `copilot-pull-request-reviewer`; both were present, valid, and feasible.
- Updated `docs/how-to/use-lrh-with-agent-assistants.md` to clarify that
  project scope selects the install destination only, and that checkout-source
  installs require `--source current-repo` or equivalent
  `project/agent_skills.yaml` configuration.
- Updated `docs/how-to/keep-skills-up-to-date.md` with the same source-vs-scope
  clarification.
- Committed the documentation fix as `c8a38cf1`.

# Validation

- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools`
  - Reconciled local setup from Black 25.11.0 / Ruff 0.15.0 to required
    Black 26.3.1 / Ruff 0.15.12 before validation.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
  - Passed after rerunning outside the sandbox; the sandboxed attempt failed
    with a multiprocessing socket permission error.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint`
  - Passed after rerunning outside the sandbox; the sandboxed attempt failed
    during Black's multiprocessing socket setup.
- `git diff --check`
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src scripts/test`
  - Passed after rerunning outside the sandbox: 1086 tests OK.
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src python -m lrh.cli.main validate`
  - Passed with 0 errors and 1 pre-existing warning:
    `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` for
    `WS-SESSION-ARCHIVE-SYNC`.

# Follow-up

Continue the `/lrh-land` chain with `/lrh-confirm-fixes` to verify and resolve
the review threads before merge.

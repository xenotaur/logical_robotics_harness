---
execution_id: 2026_08_02_21_08_02_WS_SKILLS_TARGET_AWARE_INSTALL
prompt_id: PROMPT(AD_HOC:WS_SKILLS_TARGET_AWARE_INSTALL)[2026-08-02T20:57:48+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/468
commit: 59af4a0
agent: codex_app
instruction_source: project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
session_transcript: codex-app:current-task
created_at: 2026-08-02T21:08:02+00:00
---

# Summary

Apply the LRH `/lrh-workstream` workflow to
`PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`, creating a governed workstream and
implementation work items for making LRH skills installable for Codex. Add the
proposal-local Codex compatibility backlog requested during the session.

# Result

Created `WS-SKILLS-TARGET-AWARE-INSTALL` and six proposed work items covering
target-aware install, source abstraction, repo config, render adapters,
status/check commands, and body-prose neutralization. Added
`project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md`
to track Claude-authored skill assumptions that create Codex friction.

# Validation

- `scripts/version tools` passed, but reported `pyright` missing.
- `lrh validate` passed with 0 errors and 0 warnings after adding required
  backlog frontmatter and concrete work item planning nodes.
- `scripts/format --check --diff` did not run because the local environment has
  Black 25.11.0 while the repository requires 26.3.1.

# Follow-up

- Implement `WI-SKILLS-TARGET-AWARE-INSTALL` as the first delivery slice.
- Use the proposal-local backlog as burn-down input for Codex skill compatibility
  work, especially execution-record provenance and manual-only invocation
  metadata translation.
- Research ChatGPT Skills export separately before scheduling implementation.

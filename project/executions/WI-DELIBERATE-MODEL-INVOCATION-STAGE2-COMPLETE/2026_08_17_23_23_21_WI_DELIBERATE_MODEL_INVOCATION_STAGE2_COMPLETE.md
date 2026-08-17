---
execution_id: 2026_08_17_23_23_21_WI_DELIBERATE_MODEL_INVOCATION_STAGE2_COMPLETE
prompt_id: PROMPT(WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE:WI_DELIBERATE_MODEL_INVOCATION_STAGE2_COMPLETE)[2026-08-17T22:45:23+00:00]
work_item: WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/560
commit: 753c133e
created_at: 2026-08-17T23:23:21+00:00
---

# Summary

Implemented `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` on branch
`xenotaur/feat/wi-deliberate-model-invocation-stage2-complete` and opened PR
#560.

# Result

- Removed the retained Stage 2 `disable-model-invocation` frontmatter from
  `/lrh-self-review`, `/lrh-confirm-fixes`, `/lrh-land`, and `/lrh-execute`.
- Added narrow `when_to_use` guidance for the affected Claude/source skills and
  authored Codex `agents/openai.yaml` policy with
  `allow_implicit_invocation: false`.
- Made `/lrh-self-review` diff-mode report-only by default, with `--apply` as
  the explicit opt-in for working-tree edits.
- Documented the recursion-guard posture consistently: Codex implicit invocation
  is mechanically disabled; the unresolved Claude subagent-preload hard guard is
  explicitly reassigned to Stage 3 gate-policy audit scope rather than treated as
  solved by advisory text.
- Added the `/lrh-confirm-fixes` empty-thread gate and updated the stale sibling
  workflow reference.
- Updated `WI-DELIBERATE-MODEL-INVOCATION` and
  `DEC-DELIBERATE-CHAIN-INITIATION` to record the Stage 2 supersession and
  reassignment.
- Regenerated repo-local Claude and Codex skill mirrors and refreshed the
  user-scope installs under `~/.claude/skills/` and `~/.agents/skills/`.
- Re-stamped `project/config/chain-defaults.yaml` after touching files on the
  current staleness watch list.

# Validation

- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH scripts/version tools`
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH scripts/format --check --diff`
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH scripts/lint`
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH PYTHONPATH=src scripts/test`
  — 1089 tests passed when run outside the sandbox; sandbox-only socket binding
  failures were reproduced by an accidental local rerun and are not code
  regressions.
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH PYTHONPATH=src python -m lrh.cli.main validate`
  — 0 errors, 0 warnings.
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH PYTHONPATH=src python -m lrh.cli.main skills check --target claude --local`
- `PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH PYTHONPATH=src python -m lrh.cli.main skills status --target codex --local`
- Direct user-scope checks verified no `^disable-model-invocation:` frontmatter
  remains in affected `~/.claude/skills/` or `~/.agents/skills/` installs, and
  Codex installs carry `policy.allow_implicit_invocation: false`.
- Substitute self-review pass recorded in
  `project/executions/AD_HOC/2026_08_17_23_20_39_WI_DELIBERATE_MODEL_INVOCATION_STAGE2_COMPLETE_SELFREVIEW.md`.

# Follow-up

Await automatic PR review and CI. Do not manually retrigger hosted GitHub review
agents; use substitute self-review if a fresh review signal is needed. Other
live Claude Code or Codex sessions may keep the skill copies loaded at their own
startup and should be restarted to observe the refreshed installed corpora.

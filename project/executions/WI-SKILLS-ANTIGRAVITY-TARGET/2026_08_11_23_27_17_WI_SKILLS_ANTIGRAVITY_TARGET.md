---
execution_id: 2026_08_11_23_27_17_WI_SKILLS_ANTIGRAVITY_TARGET
prompt_id: PROMPT(WI-SKILLS-ANTIGRAVITY-TARGET:WI_SKILLS_ANTIGRAVITY_TARGET)[2026-08-11T23:03:29+00:00]
work_item: WI-SKILLS-ANTIGRAVITY-TARGET
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/544
commit: 6c0b7c2f
created_at: 2026-08-11T23:27:17+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-ANTIGRAVITY-TARGET.md
session_transcript: codex-app:019fe4b6-c537-7c10-8f09-3c2d7e132816
---

# Summary

Implemented Antigravity as a first-class LRH skill install target while keeping
the canonical source under `src/lrh/skills/`.

# Result

- Added `antigravity` to the skills CLI target choices and installer target
  model.
- Added Antigravity user and project destinations:
  `~/.gemini/config/plugins/lrh/skills/` and
  `./.gemini/plugins/lrh/skills/`.
- Added an Antigravity renderer that strips Claude-only frontmatter keys
  (`disable-model-invocation`, `argument-hint`) and preserves the remaining
  skill metadata/body.
- Added deterministic `plugin.json` generation at the LRH Antigravity plugin
  root.
- Preserved explicit two-target config behavior for `claude` + `codex` while
  making `all` include Claude, Codex, and Antigravity.
- Updated installer, CLI, config-schema, and how-to documentation.
- Added unit and CLI coverage for Antigravity target resolution, dry-run
  behavior, user-modified skill preservation/diffing, local plugin-tree writes,
  `all` selection, and config-driven target selection.
- Opened PR: https://github.com/xenotaur/logical_robotics_harness/pull/544

# Validation

- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/version tools`
  - Black 26.3.1 and Ruff 0.15.12 matched repository expectations.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff`
- `git diff --check`
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint`
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src scripts/test`
  - Passed: 1079 tests.
- `PATH=/Users/centaur/anaconda3/bin:$PATH lrh validate`
  - Passed with 0 errors and 1 pre-existing warning:
    `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` for
    `WS-SESSION-ARCHIVE-SYNC`.
- `PATH=/Users/centaur/anaconda3/bin:$PATH PYTHONPATH=/Users/centaur/Workspace/LogicalRoboticsHarness/Workstreams/Codex/SkillsUpgrade/logical_robotics_harness/src python -m unittest tests.skills_installer_test tests.cli_tests.skills_test`
  - Passed: 113 focused installer/CLI tests.
- `python -m lrh.cli.main skills check --target claude --local`
  - Passed; all local Claude skills up to date.
- `python -m lrh.cli.main skills status --target codex --local`
  - Completed successfully; existing local Codex generated copies report
    modified status relative to the selected source.
- `python -m lrh.cli.main skills status --target antigravity --local`
  - Completed successfully; project-local Antigravity skills were missing before
    install, as expected.
- `python -m lrh.cli.main skills install --target antigravity --dry-run`
  - Completed successfully; reported the expected would-install set.
- Isolated temp project Antigravity install from `src/lrh/skills`
  - Installed all LRH skills under `.gemini/plugins/lrh/skills/`.
  - Wrote `.gemini/plugins/lrh/plugin.json`.
  - Post-install `skills status --local --target antigravity` reported all
    skills up to date.
- Fresh independent local self-review was performed without intentionally
  triggering GitHub review agents. The reviewer found a CLI subprocess harness
  issue where tests could import a stale sibling checkout; the tests were
  updated to pin subprocess `PYTHONPATH` to this checkout, and focused/full
  tests passed afterward.

Environment note: a first full-suite run without `PYTHONPATH` imported `lrh`
from a sibling checkout at
`/Users/centaur/Workspace/LogicalRoboticsHarness/logical_robotics_harness/src`
and failed against stale code. The corrected full-suite command above pinned
this checkout's `src` path and passed.

# Follow-up

None.

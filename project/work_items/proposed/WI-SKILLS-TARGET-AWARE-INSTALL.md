---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-TARGET-AWARE-INSTALL
title: Add target-aware Claude and Codex installs to lrh skills install
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-TARGET-AWARE-INSTALL
related_design:
  - project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_chatgpt_export
acceptance:
  - `lrh skills install` accepts `--target claude|codex|all`
  - Existing no-target behavior remains Claude-compatible
  - User-scope Codex installs write to `~/.agents/skills/`
  - Project-scope Codex installs with `--local` write to `./.agents/skills/`
  - Dry-run, force, diff, local-modification, and symlink-safety behavior is covered for both Claude and Codex targets
  - Documentation describes Claude and Codex install targets and the interim Codex body-prose caveat
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - src/lrh/cli/main.py
  - tests/skills_installer_test.py
  - tests/cli_tests/skills_test.py
  - docs/how-to/keep-skills-up-to-date.md
---

# Add target-aware Claude and Codex installs to `lrh skills install`

## Summary

Implement the first slice of target-aware skill installation: add
`--target claude|codex|all`, preserve current Claude defaults, and make Codex's
`.agents/skills/` directories first-class local install targets.

## Problem / Context

`lrh skills install` currently installs only to Claude skill directories. Codex
has a parallel local skill discovery path, but LRH cannot install canonical
skills there. This work item implements the proposal's recommended first work
item without attempting full render-adapter or ChatGPT export support.

## Scope

- Add target selection to the CLI.
- Resolve Claude and Codex user/project target roots.
- Preserve existing install safety behavior for all targets.
- Keep Codex output as direct copies with a documented body-prose caveat.
- Add focused installer and CLI tests.

## Required Changes

- Update `src/lrh/skills/installer.py` so skill installation can plan and
  apply installs for both Claude and Codex targets while preserving the
  existing Claude default behavior when no target is specified.

- Add target resolution for all selected scope/target combinations:
  `claude` user scope maps to `~/.claude/skills/`; `claude` project scope with
  `--local` maps to `./.claude/skills/`; `codex` user scope maps to
  `~/.agents/skills/`; `codex` project scope with `--local` maps to
  `./.agents/skills/`; `all` maps to both Claude and Codex targets for the
  selected scope.

- Update `src/lrh/cli/main.py` so `lrh skills install` accepts
  `--target claude|codex|all`. The default must remain equivalent to the
  current Claude-only behavior.

- Preserve existing install safety behavior for every target: `--dry-run`
  reports intended actions without writing files; `--force` is required to
  overwrite user-modified target copies; `--diff` keeps the existing CLI
  behavior of printing diffs after the normal install action, so users who want
  no writes must combine `--dry-run --diff`; symlinked skill roots are not
  dereferenced; bundled scripts are not executed during install.

- Keep Codex output as direct copies for this first slice. Do not implement
  Codex render adapters or `agents/openai.yaml` generation in this work item;
  document the known interim caveat that copied skill bodies may still contain
  Claude-specific prose pending later neutralization work.

- Extend `tests/skills_installer_test.py` with temporary-directory coverage
  for Claude and Codex user/project targets, `all` target behavior, dry-run,
  force, diff, local-modification detection, and symlink safety.

- Extend `tests/cli_tests/skills_test.py` with CLI coverage for the new
  `--target` option, including valid target values and invalid-target
  rejection.

- Update `docs/how-to/keep-skills-up-to-date.md` to describe Claude and Codex
  install targets, the default Claude-compatible behavior, project-local Codex
  installs with `--local --target codex`, and the direct-copy caveat for Codex.

## Non-Goals

- Does not implement source abstraction, repo config, render adapters, status
  commands, or ChatGPT export.
- Does not rewrite all skill bodies to be agent-neutral.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

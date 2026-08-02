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

---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-STATUS-CHECK
title: Add skill install status and check commands
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
depends_on:
  - WI-SKILLS-TARGET-AWARE-INSTALL
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - `lrh skills status` reports installed, missing, modified, and target-specific skill states
  - `lrh skills check` reports unsupported metadata and target drift without writing files
  - Commands support Claude and Codex targets
  - Human-readable output is covered by focused tests
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/cli/main.py
  - src/lrh/skills/installer.py
  - tests/cli_tests/skills_test.py
  - tests/skills_installer_test.py
---

# Add skill install status and check commands

## Summary

Add read-only commands for inspecting skill install state, target drift, and
compatibility issues before writing any target files.

## Problem / Context

Target-aware installs make it more important to see what would change across
Claude and Codex directories. Status and check commands give maintainers a
safe, reviewable way to inspect drift and unsupported metadata.

## Scope

- Add `lrh skills status`.
- Add `lrh skills check`.
- Report installed/missing/modified states per target.
- Report unsupported or untranslated metadata.

## Required Changes

- Extend `src/lrh/cli/main.py` so `lrh skills` accepts read-only `status` and
  `check` subcommands alongside the existing `install` subcommand.

- Add installer-layer read-only inspection support in `src/lrh/skills/installer.py`
  that reuses the existing target, source, repo-config, renderer, and diff
  resolution paths instead of duplicating install planning logic.

- Implement `lrh skills status` so it reports per-target skill state for the
  resolved source/scope/target selection, including installed, missing,
  up-to-date, locally modified, and target-specific rendered-output states.

- Implement `lrh skills check` so it exits non-zero when unsupported metadata,
  untranslated metadata, target drift, invalid Codex metadata, or locally
  modified target copies are detected, while never writing to `.claude/skills/`,
  `.agents/skills/`, user skill directories, or canonical source directories.

- Preserve install safety expectations for read-only commands: do not execute
  bundled skill scripts, do not dereference symlinked skill roots or symlinked
  installed entries, and do not overwrite or repair target copies.

- Ensure both commands support Claude and Codex targets, user and project
  scopes, `all` target selection, package/current-repo/explicit-path sources,
  and repo-config defaults from `project/agent_skills.yaml`.

- Define human-readable output that distinguishes status-oriented information
  from check failures, so maintainers can inspect drift before running
  `lrh skills install --force`.

- Extend `tests/skills_installer_test.py` with focused coverage for status/check
  planning and detection behavior across missing, up-to-date, modified, drifted,
  symlinked, Claude, Codex, and `all` target cases.

- Extend `tests/cli_tests/skills_test.py` with CLI coverage for `lrh skills
  status` and `lrh skills check`, including help text, valid/invalid target
  handling, read-only behavior, human-readable output, and non-zero check
  failures.

- Keep ChatGPT export, body-prose neutralization, and any write/repair behavior
  out of this work item.

## Non-Goals

- Does not write skill files.
- Does not implement ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

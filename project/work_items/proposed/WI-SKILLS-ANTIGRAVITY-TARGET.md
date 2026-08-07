---
id: WI-SKILLS-ANTIGRAVITY-TARGET
title: Add Antigravity target and plugin exporter support to lrh skills install
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
  - project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md
depends_on:
  - WI-SKILLS-TARGET-AWARE-INSTALL
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - "`lrh skills install` accepts `antigravity` target (`--target claude|codex|antigravity|all`)"
  - "User-scope Antigravity installs write to `~/.gemini/config/plugins/lrh/skills/` and generate `plugin.json`"
  - "Project-scope Antigravity installs with `--local` write to `./.gemini/plugins/lrh/skills/` and generate `plugin.json`"
  - "`AntigravitySkillRenderer` strips Claude-specific frontmatter (`disable-model-invocation`, `argument-hint`)"
  - "Dry-run, force, diff, and local-modification behavior holds for `antigravity` target"
  - "`lrh validate` reports 0 errors"
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - src/lrh/cli/main.py
  - tests/skills_installer_test.py
  - tests/cli_tests/skills_test.py
  - docs/how-to/use-lrh-with-agent-assistants.md
---

# Add Antigravity target and plugin exporter support to `lrh skills install`

## Summary

Extend the target-aware installer (`src/lrh/skills/installer.py`) to support `antigravity` as an explicit install target alongside `claude` and `codex`. When selected, `lrh skills install --target antigravity` renders canonical skills into Antigravity plugin structures (`skills/<name>/SKILL.md`) and generates a root `plugin.json` manifest.

## Problem / Context

Antigravity uses native plugin manifests (`plugin.json`) and skill folders (`skills/<name>/SKILL.md`) housed under `~/.gemini/config/plugins/<plugin>/` for ambient system-prompt indexing. Decision record `DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY` established a dual-tier strategy: direct in-repo discovery via `AGENTS.md`/`GEMINI.md` rules (Tier 1, documented) and target exporter support in `lrh skills install` (Tier 2, this work item).

### Prior Art Check
- **Duplication search**: Evaluated `src/lrh/skills/installer.py` and `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`. Found existing target infrastructure for `claude` and `codex` (`SkillTarget` enum, `SkillRenderer` protocol). Verdict: no duplication; this extends the existing target-aware architecture.
- **Demand search**: Documented in `DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY` and `docs/how-to/use-lrh-with-agent-assistants.md`. Verdict: direct demand established in design/docs.

## Scope

- Add `ANTIGRAVITY = "antigravity"` to `SkillTarget` enum and `--target` CLI options.
- Define `AntigravitySkillRenderer` implementing `SkillRenderer` protocol to strip Claude-specific frontmatter (`disable-model-invocation`, `argument-hint`) and generate root `plugin.json`.
- Support user scope (`~/.gemini/config/plugins/lrh/`) and project scope (`./.gemini/plugins/lrh/` via `--local`).
- Preserve dry-run, force, diff, and symlink safety.
- Add unit tests for `AntigravitySkillRenderer` and CLI invocation.

## Required Changes

- Update `src/lrh/skills/installer.py` to add `SkillTarget.ANTIGRAVITY`, target path resolution for user/project scopes, `AntigravitySkillRenderer`, and `plugin.json` generation logic.
- Update `src/lrh/cli/main.py` to accept `antigravity` in `--target`.
- Update `tests/skills_installer_test.py` and `tests/cli_tests/skills_test.py` to cover Antigravity installation.

## Non-Goals

- Does not rewrite all skill bodies to be agent-neutral (scoped separately under `WI-SKILLS-BODY-PROSE-NEUTRALIZATION`).
- Does not modify Claude or Codex renderer behavior.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

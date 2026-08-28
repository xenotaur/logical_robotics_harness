---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-CONFIG-SKILLS
title: Implement /lrh-config-skills skill for inspecting and setting agent_skills.yaml install policy
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design:
  - docs/reference/schemas/agent-skills-config.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "New lrh agent-skills CLI subcommand (a status/inspection command at minimum) exists under src/lrh/cli/main.py, backed by a tested src/lrh/*.py module with unit tests -- not ad hoc bash in skill prose, mirroring the lrh chain-defaults status pattern from WI-SKILLS-LRH-CONFIG-GATES"
  - "New /lrh-config-skills skill presents all 4 configurable fields (sources, targets, scope, install.overwrite) and their resolved effective values (config value if project/agent_skills.yaml exists, else the documented conventional default) in one table before asking anything -- explicitly stating whether the file exists at all"
  - "Unlike /lrh-config-gates, this skill is permitted to create project/agent_skills.yaml from scratch when it does not yet exist, since no other mechanism in the codebase ever creates it -- every write (whether creating the file or editing an existing one) is gated behind an explicit confirm before commit/push"
  - "install.overwrite is never offered as a settable field -- the schema itself (docs/reference/schemas/agent-skills-config.md) documents it as non-destructive-only, and --force stays CLI-only per that doc's own Precedence section; this skill must not treat every schema key as a fair-game toggle"
  - "Skill body content mirrored byte-identical from src/ to .claude/; .agents/ and .gemini/ verified via lrh skills status/check reporting up to date, not a raw byte-diff, since their SKILL.md frontmatter is installer-normalized and never byte-identical to src/; lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-config-skills/SKILL.md
  - src/lrh/skills/lrh-config-skills/references/
  - .claude/skills/lrh-config-skills/
  - .agents/skills/lrh-config-skills/
  - .gemini/plugins/lrh/skills/lrh-config-skills/
---

# Implement `/lrh-config-skills` skill for inspecting and setting agent_skills.yaml install policy

## Summary

Implements a `/lrh-config-skills` skill: a single surface that reads
`project/agent_skills.yaml` (or the conventional defaults if it doesn't
exist), presents the resolved skill-install policy, and lets the human
create or edit it via confirmed field-by-field decisions -- the same
Option C pattern (`WI-SKILLS-LRH-CONFIG-GATES`) applied to a different,
already-built config mechanism (`WI-SKILLS-REPO-CONFIG`).

## Problem / Context

`WI-SKILLS-REPO-CONFIG` (resolved, PR #481) built the `project/agent_skills.yaml`
loader, CLI-over-config-over-default precedence, and documentation
(`docs/reference/schemas/agent-skills-config.md`) -- but no work item ever
built a human-facing status/confirm layer for it. This session hit that
gap directly: every `lrh skills install`/`status` invocation required
`--target`/`--source` typed by hand, and forgetting `--source current-repo`
once produced a misleadingly empty result, since the file doesn't exist in
this repo and the tool silently fell back to package-source defaults.

### Prior Art Check

**Duplication search.** `git grep -liE "config-skills|agent_skills.yaml|lrh-config-skills" --
project/work_items project/design/backlog.md project/design/proposals`
returned `WI-SKILLS-REPO-CONFIG` (resolved -- built the underlying
mechanism, not a human-facing skill), `WI-SKILLS-SOURCE-ABSTRACTION`,
`WI-SKILLS-STATUS-CHECK` (both resolved, unrelated prerequisites), and the
adopted `lrh-skills-target-aware-install` proposal (the design that
produced `WI-SKILLS-REPO-CONFIG`). No existing work item, proposal, or
skill covers presenting/confirming `agent_skills.yaml` changes to a human.

**Demand search.** This session's own conversation (built `/lrh-config-gates`
for `chain-defaults.yaml`, then surveyed for other config surfaces worth
the same treatment) is the demand; no prior backlog entry requested this.

## Scope

Architecture per Option C (CLI-backed, skill-orchestrated), matching
`/lrh-config-gates`'s established pattern (`WI-SKILLS-LRH-CONFIG-GATES`):
`chain_defaults_status.py` + `lrh chain-defaults status` +
`/lrh-config-gates` Step 1-2.

- Add an `lrh agent-skills status` subcommand to `src/lrh/cli/main.py`,
  backed by a tested Python module, that reports whether
  `project/agent_skills.yaml` exists and the *effective* resolved value
  of each field (`sources`, `targets`, `scope`, `install.overwrite`) --
  config value if present, else the conventional default documented in
  `docs/reference/schemas/agent-skills-config.md`'s Precedence section.
- Add a thin `/lrh-config-skills` skill that presents that state in one
  table, then drives the same confirm-then-commit-then-push flow
  `/lrh-config-gates` established -- with one structural difference: this
  skill *may* create `project/agent_skills.yaml` from scratch when absent
  (unlike `/lrh-config-gates`, which refuses to create `chain-defaults.yaml`
  because another mechanism already does that; no other mechanism ever
  creates `agent_skills.yaml`).
- Mirror the new skill to `.claude/skills/`, `.agents/skills/` (via the
  proper installer, not raw `cp`), `.gemini/plugins/lrh/skills/` (same).

## Required Changes

1. Add an `lrh agent-skills status` subcommand to `src/lrh/cli/main.py`,
   backed by a new `src/lrh/*.py` module with unit tests, that reports:
   whether `project/agent_skills.yaml` exists, and each field's effective
   value (`sources`, `targets`, `scope`, `install.overwrite`) with its
   provenance (from-config vs. conventional-default) -- reusing
   `src/lrh/skills/installer.py`'s existing `load_agent_skills_config`/
   `resolve_agent_skills_install_plan` functions rather than
   re-implementing the precedence logic.
2. Create `src/lrh/skills/lrh-config-skills/SKILL.md` (+ `references/` as
   needed): presents that state, elicits field-by-field or batch
   decisions from the human, and commits/pushes confirmed changes to
   `project/agent_skills.yaml` (creating it if absent). Never offers
   `install.overwrite` as a settable-to-destructive field -- only its
   documented non-destructive values (`false`, `skip`, `preserve`).
3. Mirror to `.claude/`, `.agents/` (installer), `.gemini/` (installer).

## Non-Goals

- Does not change `lrh skills install`'s own precedence or loading logic
  -- `WI-SKILLS-REPO-CONFIG` already built and validated that; this WI
  only adds a read/confirm-write presentation layer on top.
- Does not allow `install.overwrite` to be set to a destructive value via
  this skill or the config file it writes -- that stays CLI-`--force`-only
  per `docs/reference/schemas/agent-skills-config.md`.
- Does not decide this repo's own `agent_skills.yaml` policy on the
  user's behalf -- surfaces the decision, does not make it.

## Acceptance Criteria

- New `lrh agent-skills status` CLI subcommand exists, backed by a tested
  Python module that reuses `installer.py`'s existing precedence
  functions rather than re-implementing them.
- `/lrh-config-skills` presents all 4 fields and their resolved effective
  values (with from-config/from-default provenance) before asking
  anything.
- The skill may create `project/agent_skills.yaml` when absent, gated
  behind the same explicit confirm as any other write.
- `install.overwrite` is never offered as a destructive-capable toggle.
- Skill body content mirrored byte-identical `src/` to `.claude/`;
  `.agents/`/`.gemini/` verified via `lrh skills status`/`check`
  reporting up to date; `lrh validate` reports 0 errors.

## Validation

- lrh validate
- New unit tests for the CLI module
- Manual dogfood: run the skill in this worktree (which has no
  `project/agent_skills.yaml` yet) and confirm it correctly offers to
  create one

## Risk Notes

The main risk is scope creep into re-implementing `installer.py`'s own
precedence logic instead of reusing it -- `resolve_agent_skills_install_plan`
already does exactly this computation for install planning; the new status
command should call it (or its constituent pieces) directly, not duplicate
the CLI-over-config-over-default resolution a second time.

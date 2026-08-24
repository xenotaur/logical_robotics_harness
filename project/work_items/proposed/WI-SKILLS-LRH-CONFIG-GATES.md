---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-CONFIG-GATES
title: Implement /lrh-config-gates skill for inspecting and setting chain-defaults gate policy
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
related_design: []
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
  - "New lrh chain-defaults CLI subcommands (a status/inspection command at minimum) exist under src/lrh/cli/main.py, backed by a tested src/lrh/*.py module with unit tests -- not ad hoc bash in skill prose"
  - "New /lrh-config-gates skill presents all 5 human-decidable chain-defaults.yaml fields, the consent-hash validity state, and the staleness status in one table before asking anything"
  - "Every field-value change is gated behind an explicit confirm before the skill commits/pushes to main -- same confirm-then-push pattern used by every other config change this session"
  - "The skill explicitly documents that git-config consent is per-clone (shared across worktrees of one clone, not shared across independent clones), so it never claims consent transferred when it didn't"
  - "Skill mirrored byte-identical to .claude/, .agents/ (via installer), .gemini/ (via installer); lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-config-gates/SKILL.md
  - src/lrh/skills/lrh-config-gates/references/
  - .claude/skills/lrh-config-gates/
  - .agents/skills/lrh-config-gates/
  - .gemini/plugins/lrh/skills/lrh-config-gates/
---

# Implement `/lrh-config-gates` skill for inspecting and setting chain-defaults gate policy

## Summary

Implements the `/lrh-config-gates` skill discussed at length in this
session: a single surface that reads `project/config/chain-defaults.yaml`,
the local git-config consent state, and `lrh chain-defaults
check-staleness`, presents them together, and lets the human make and push
field-by-field decisions instead of the ad hoc multi-message conversation
this session just had.

## Problem / Context

This session repeatedly discovered chain-authorization gates firing when
they didn't need to -- a stale `confirmed_commit`, an invalidated consent
hash, `confirm_fixes_batch` left at its conservative default -- and each
discovery required a separate manual investigation (`git config --get`,
`git hash-object`, `lrh chain-defaults check-staleness`, reading the raw
YAML) spread across several turns. No single command surfaces this state
together.

### Prior Art Check

**Duplication search.** `git grep -li "config-gates\|lrh-config" --
project/work_items project/design/backlog.md project/design/proposals`
returned no matches. No existing work item, backlog entry, or proposal
covers this.

**Demand search.** None found as a prior work item or proposal; this
session's own conversation (culminating in a direct request for the
skill) is the demand.

## Scope

Architecture per Option C (CLI-backed, skill-orchestrated), matching this
codebase's own established pattern for "compute something, then gate on a
human confirm": `confirm_fixes_batch.py` + `lrh confirm-fixes
check-batch-routine` + `/lrh-confirm-fixes` Step 4
(`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`), and `gate_staleness.py` + `lrh
chain-defaults check-staleness` + `/lrh-land`'s Decision 5
(`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`).

- Extend the existing `lrh chain-defaults` subcommand group
  (`src/lrh/cli/main.py:1244`) with the mechanical read/status logic,
  backed by a tested Python module -- not ad hoc bash embedded in skill
  prose (this session's own worktree-`.git/` bug is a direct example of
  what ad hoc skill-prose bash risks).
- Add a thin `/lrh-config-gates` skill that presents the full state (all
  5 human-decidable fields, consent-hash validity, staleness status) in
  one table, then drives the same confirm-then-commit-then-push flow
  every other config change this session used.
- Mirror the new skill to `.claude/skills/`, `.agents/skills/` (via the
  proper installer, not raw `cp`), `.gemini/plugins/lrh/skills/` (same).

## Required Changes

1. Add one or more `lrh chain-defaults` subcommands (e.g. `status`) to
   `src/lrh/cli/main.py`, backed by a new or extended `src/lrh/*.py`
   module with unit tests, that reports: the 5 human-decidable
   `chain-defaults.yaml` field values, whether the local git-config
   consent hash matches the file's current blob hash, and the
   `check-staleness` result -- all in one structured read.
2. Create `src/lrh/skills/lrh-config-gates/SKILL.md` (+ `references/` as
   needed): presents that state, elicits field-by-field or batch
   decisions from the human, and commits/pushes confirmed changes to
   `project/config/chain-defaults.yaml` and/or grants local git-config
   consent -- explicitly scoping the consent grant to the current clone
   only, never implying it propagates to other clones.
3. Mirror to `.claude/`, `.agents/` (installer), `.gemini/` (installer).

## Non-Goals

- Does not decide whether to add new `chain-defaults.yaml` fields (e.g.
  the "self-review preference" gap noted in the now-resolved
  `WS-LRH-CHAIN-DEFAULTS`'s original purpose text,
  `project/workstreams/resolved/WS-LRH-CHAIN-DEFAULTS.md:30`) -- surfaces
  that gap if relevant, does not resolve it.
- Does not change any existing gate's behavior -- read/write config only.
- Does not grant or modify consent on any clone other than the one the
  skill is invoked in, and does not claim consent granted in one clone
  applies to another.

## Acceptance Criteria

- New `lrh chain-defaults` CLI subcommand(s) exist, backed by a tested
  Python module, not ad hoc skill-prose bash.
- `/lrh-config-gates` presents all 5 human-decidable fields, consent
  validity, and staleness status together before asking anything.
- Every field-value change is gated behind an explicit confirm before
  commit/push.
- The skill explicitly documents the per-clone (not per-worktree) scope
  of git-config consent.
- Skill mirrored byte-identical across `.claude/`, `.agents/`,
  `.gemini/`; `lrh validate` reports 0 errors.

## Validation

- lrh validate
- New unit tests for the CLI module
- Manual dogfood: run the skill in this worktree and confirm it correctly
  reports the current consent/staleness state

## Risk Notes

The main risk is the per-clone consent nuance: this session confirmed
empirically that `git config --local` is shared across worktrees of the
*same* clone (via the common `.git/config`, despite
`extensions.worktreeConfig` being set) but not shared across independent
clones. A skill that gets this backwards could tell a human their consent
is valid when it isn't (or vice versa) in a different checkout -- keep the
scope claim narrow and verified, not assumed.

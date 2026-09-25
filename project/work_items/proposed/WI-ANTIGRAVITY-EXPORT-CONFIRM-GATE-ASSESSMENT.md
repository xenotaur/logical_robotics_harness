---
resolution: null
blocked_reason: null
blocked: false
id: WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT
title: "Assess and, if simple, add a confirm-before-write gate to lrh-export-antigravity"
type: evaluation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
depends_on:
  - WI-EXPORT-SKILLS-LIVE-SESSION-WORDING
  - WI-EXPORT-SKILL-FAMILY-RENAME
blocked_by: []
expected_actions:
  - edit_file
  - create_report
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
  - skills_install_force
acceptance:
  - A written assessment compares lrh-export-antigravity with lrh-export-claude and lrh-export-codex on the confirm-before-write step, the proactive-invocation guard in when_to_use, the concrete-path resolution rule, and the privacy risk of an unconfirmed durable write, citing file and line for each
  - The assessment ends in an explicit recommendation (add a gate, or leave as is with rationale)
  - If the recommendation is to add a gate and the change is simple, it is implemented in the same PR, matching the Claude and Codex export skills' Step 3 wording, and the assessment states why the scope stayed reasonable
  - If the change is not simple, or the scope grows beyond what the human and the agent in the implementing session judge reasonable, the gate is not implemented in this PR; the implementing session and the human then judge together whether a separate follow-up work item is warranted or the recommendation is simply reported as a finding
  - Whichever way it resolves, the implementing session reports its scope judgment to the human before finishing
  - If a gate is added, .claude/skills is byte-identical to src/lrh/skills, .agents/skills and .gemini/plugins/lrh/skills are regenerated for lrh-export-antigravity alone, one skill at a time (installer._copy_skill_from_source with a SkillSource from installer.resolve_skill_source), never via a plain or --force lrh skills install (plain install skips an already-installed, differing skill; --force overwrites every locally-modified skill in the target), and the added gate follows whatever marker and watched-file convention the existing export-skill gates use
  - No transcript text is printed or committed
  - scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-export-antigravity/SKILL.md
  - .claude/skills/lrh-export-antigravity/
  - .agents/skills/lrh-export-antigravity/
  - .gemini/plugins/lrh/skills/lrh-export-antigravity/
  - the assessment text, recorded in the implementing PR's execution record
---

## Summary

> **Sequencing note, 2026-09-24:** this item now depends on
> `WI-EXPORT-SKILL-FAMILY-RENAME`, which renames `lrh-antigravity-export` to
> `lrh-export-antigravity` and leaves a deprecated stub under the old name.
> Apply the gate to `lrh-export-antigravity`, not to the stub.

Decide whether `lrh-export-antigravity` needs a confirm-before-write gate like
the Claude and Codex export skills have, and add it in the same PR if the
change is simple.

## Problem / Context

The observations below were made before the rename and use the old skill
names: `lrh-codex-export` is now `lrh-export-codex`, and
`lrh-antigravity-export` is now `lrh-export-antigravity`.

`lrh-export-claude` has a mandatory confirm-before-write step (Step 3) and a
`when_to_use` that forbids proactive invocation, because the export writes a
durable, permanent private copy. `lrh-codex-export` has the same step
(`lrh-codex-export/SKILL.md:144`). `lrh-antigravity-export` has neither: its
steps are resolve input, run the exporter, verify and report, and its
`when_to_use` does not restrict invocation. It also lacks the Claude skill's
rule to resolve a concrete transcript path before exporting so that the same
file is exported and verified.

The question of adding a gate is a policy decision, so it was deliberately not
part of the wording pass (`WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`). The
human's direction for this work item: implement the recommendation if it is
simple; do not force a separate work item regardless; the human and the agent
in the implementing session decide whether the scope is growing beyond what is
reasonable.

Prior art check:

- **Duplication:** none. The Claude and Codex gates are the precedent to match,
  not a duplicate.
- **Demand:** none existing; it arises from a live-session review of the export
  skills.

## Scope

- One skill, `lrh-export-antigravity`, and its mirrors.
- An assessment, plus the gate if the recommendation calls for it and the change
  is simple.

## Required Changes

- Write the comparison and recommendation.
- If a gate is warranted and simple, add it in the same style as the Claude and
  Codex skills, including the proactive-invocation guard and the concrete-path
  rule, and state the `--force` overwrite in the confirm text.

## Non-Goals

- No change to the Claude or Codex export skills.
- No exporter or inspector code change.
- No gate is forced: a "leave as is" recommendation with rationale is a valid
  outcome.

## Acceptance Criteria

- The assessment and its recommendation.
- Either the implemented simple gate, or — when the change is not simple —
  the recommendation reported as a finding, with a follow-up work item
  proposed only if the human and the implementing session judge one
  warranted.
- A scope judgment reported to the human.
- Mirrors and validation clean when a change is made.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- diff -r src/lrh/skills/lrh-export-antigravity .claude/skills/lrh-export-antigravity

## Risk Notes

- Adding a gate changes what a skill invocation does; it must match the
  existing export gates rather than invent a new pattern.
- "Simple" is a judgment; the acceptance criteria require the implementing
  session to report it rather than decide silently.
- Depends on the wording work item so both edit the same skill in sequence
  rather than conflicting.

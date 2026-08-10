---
resolution: "Implemented and merged in PR #539 (commit 0491fdbd07ec7772bcc9aa3e14bb11b55c0851b6)"
blocked_reason: null
blocked: false
id: WI-SKILLS-BODY-PROSE-NEUTRALIZATION
title: Neutralize Claude-specific LRH skill body prose for Codex
type: deliverable
status: resolved
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
  - project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md
depends_on:
  - WI-SKILLS-RENDER-ADAPTERS
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Proposal-local Codex compatibility backlog is reviewed and updated
  - Claude-specific body prose is rewritten or deliberately retained with rationale
  - Codex-installed skills no longer instruct Codex to record itself as Claude
  - Invocation examples are agent-neutral or target-aware where practical
  - Claude install behavior remains usable and intentional
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - manual_review
artifacts_expected:
  - src/lrh/skills
  - .claude/skills
  - project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md
---

# Neutralize Claude-specific LRH skill body prose for Codex

## Summary

Burn down Claude-specific instructions in LRH skill bodies so skills installed
for Codex behave as first-class Codex workflows rather than copied Claude
prompts.

## Problem

The proposal accepts direct-copy Codex output as an interim slice, but current
skill bodies contain Claude Code provenance, slash-command, and mirror-target
assumptions. Those issues should be fixed deliberately now that target-aware
installation and render adapters are in place.

The proposal-local compatibility backlog records concrete Codex dogfooding
friction: Claude-specific execution-record provenance, unsupported invocation
metadata, slash-command-oriented wording, `.claude/skills/` mirror assumptions,
Claude session transcript assumptions, and under-modeled Codex self-review
workflow language.

## Scope

- Review every proposal-local backlog entry.
- Rewrite canonical LRH skill prose where agent-neutral wording is sufficient.
- Use target-aware rendering where Claude and Codex need different installed
  text or metadata.
- Preserve Claude usability in `.claude/skills/`.
- Update backlog status as issues are burned down or deliberately retained.

## Out of Scope

- Does not change core install target mechanics.
- Does not implement ChatGPT export.
- Does not redesign the LRH skill workflow lifecycle beyond the compatibility
  issues captured in the proposal-local backlog.
- Does not require every historical slash-command reference to disappear when
  the command name is the clearest user-facing workflow identifier.

## Required Changes

- Review `project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md`
  and classify each tracked issue as fixed in canonical prose, fixed in a
  target renderer, deliberately retained with rationale, or deferred with a
  follow-up work item.
- Update affected `src/lrh/skills/**/SKILL.md` and directly referenced
  instruction files so Codex-installed skills do not instruct Codex to record
  itself as Claude or rely on Claude-only session identifiers.
- Replace Claude-only installed-target wording with canonical-source and
  selected-target wording where practical.
- Keep Claude-specific behavior available for Claude installs, either through
  unchanged Claude rendering or explicit target-aware output.
- Run or update focused tests when renderer behavior changes.
- Update the compatibility backlog with the final disposition of each issue
  reviewed in this work item.

## Likely Files

- `project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md`
- `src/lrh/skills/**/SKILL.md`
- `src/lrh/skills/**/references/*.md`
- `.claude/skills/**/SKILL.md`
- `.claude/skills/**/references/*.md`
- `src/lrh/skills/installer.py`
- `tests/skills_installer_test.py`
- `tests/cli_tests/skills_test.py`

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test` when source behavior changes
- `lrh skills check --target claude --local`
- `lrh skills status --target codex --local`
- `lrh validate`

## Acceptance Criteria

- Proposal-local Codex compatibility backlog is reviewed and updated.
- Claude-specific body prose is rewritten or deliberately retained with
  rationale.
- Codex-installed skills no longer instruct Codex to record itself as Claude.
- Invocation examples are agent-neutral or target-aware where practical.
- Claude install behavior remains usable and intentional.
- `lrh validate` reports 0 errors.

## Open Questions

- What durable Codex transcript identifier should replace Claude-specific
  `claude-app:<host-uuid-stem>` examples when the Codex app cannot expose a
  repository-stable export identifier?
- Should Codex self-review preference be represented as target-specific skill
  prose, repository policy, or a separate LRH workflow option?

---
resolution: "Delivered /lrh-implement skill (SKILL.md + 3 reference files, self-hosted copy, CLAUDE.md entry) in PR #319"
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-IMPLEMENT
title: Implement lrh-implement Claude Code skill
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/01_lrh_implement_skill.md
depends_on:
  - WI-SKILLS-LRH-WORK-ITEM
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_setup
acceptance:
  - src/lrh/skills/lrh-implement/SKILL.md exists with valid frontmatter
  - All three references/ files exist under both src/ and .claude/ locations
  - diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/ reports no differences
  - CLAUDE.md lists /lrh-implement in the Skills section
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
  - src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md
  - src/lrh/skills/lrh-implement/references/canonical-validation.md
  - .claude/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-implement/references/execution-session-reference.md
  - .claude/skills/lrh-implement/references/lrh-implement-workflow.md
  - .claude/skills/lrh-implement/references/canonical-validation.md
  - CLAUDE.md (Skills section updated with /lrh-implement)
---

## Summary

Implement the `/lrh-implement` Claude Code skill that encodes the instruction
and execution phases of the three-phase execution session model as a
structured, reproducible Claude.app workflow. Given a work item ID or ad-hoc
task description, the skill mints a prompt ID, checks idempotence, confirms
the plan, creates a branch, implements the work, runs canonical validation,
opens a PR, and creates a populated execution record.

## Problem / Context

After `/lrh-work-item` creates a planning artifact, implementation currently
happens via informal Claude.app sessions where the user manually follows the
prompt workflow from `PROMPTS.md`. There is no structured skill to enforce the
three-phase model, remind the user to mint a prompt ID, run the canonical
validation sequence, or populate the new `agent`, `instruction_source`, and
`session_transcript` execution-record fields consistently.

`PROP-LRH-IMPLEMENT-SKILL` (adopted, in
`project/design/proposals/adopted/lrh-project-local-skills/01_lrh_implement_skill.md`)
defines the complete design: a 10-step workflow, three reference files, and key
decisions (skip `prompt-from-work-item`, inline not fork, warn not block,
`<username>/<type>/<slug>` branch namespace).

## Scope

- Implement `src/lrh/skills/lrh-implement/` (SKILL.md and three reference
  files) and mirror byte-for-byte to `.claude/skills/lrh-implement/`
- Update `CLAUDE.md` to add `/lrh-implement` to the Skills section
- Add `WI-SKILLS-LRH-IMPLEMENT` to the `work_items:` list in `WS-SKILLS.md`

## Required Changes

1. Create `src/lrh/skills/lrh-implement/SKILL.md` — the 10-step skill body
   per `PROP-LRH-IMPLEMENT-SKILL`: frontmatter with `name: lrh-implement`,
   `disable-model-invocation: true`, `argument-hint: "[WI-ID or task description]"`.

2. Create three reference files under `src/lrh/skills/lrh-implement/references/`:
   - `execution-session-reference.md` — practical facts from
     `PROP-LRH-EXECUTION-SESSIONS` needed at runtime: `lrh prompt label` and
     `lrh prompt check-execution` syntax, branch naming convention, execution
     record field descriptions for `agent`, `instruction_source`,
     `session_transcript`.
   - `lrh-implement-workflow.md` — lifecycle placement, relationship to
     `lrh work-items readiness`, `ready-work-item`, and post-implementation
     closeout (move work item to `resolved/`, run `lrh work-items audit`).
   - `canonical-validation.md` — the `scripts/` validation command sequence,
     failure handling, and evidence to record in the execution record.

3. Mirror all four files to `.claude/skills/lrh-implement/` (byte-for-byte
   identical, verified with `diff -r`).

4. Update `CLAUDE.md` — add `/lrh-implement` to the `## Skills` section.

5. Add `WI-SKILLS-LRH-IMPLEMENT` to the `work_items:` list in
   `project/workstreams/proposed/WS-SKILLS.md`.

## Non-Goals

- Do not implement `lrh setup` — that is `WI-SKILLS-LRH-SETUP`.
- Do not add CI diff enforcement between the two skill copies — Stage 3 item.
- Do not add skill validation to `lrh validate` in this item.
- Do not implement other workflow skills (`/lrh-workstream`, `/lrh-assess`).
- Do not modify the existing `lrh-work-item` skill.

## Acceptance Criteria

- `src/lrh/skills/lrh-implement/SKILL.md` exists with valid YAML frontmatter
  (`name: lrh-implement`, `disable-model-invocation: true`).
- All three `references/` files exist under both `src/lrh/skills/lrh-implement/`
  and `.claude/skills/lrh-implement/`.
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`
  reports no differences.
- `CLAUDE.md` lists `/lrh-implement` in the Skills section.
- `lrh validate` reports 0 errors.
- The skill successfully guides a Claude.app session through a complete
  implementation of a real LRH work item, producing a PR and a populated
  execution record with `agent: claude_app`.

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`

## Risk Notes

- The SKILL.md body for a 10-step skill is near the ~500-line limit noted in
  the skill pattern reference. Monitor length during authoring; extract to
  reference files if needed.
- Two skill copies must be kept in sync manually until Stage 3 adds CI
  enforcement. This is already documented in `CONTRIBUTING.md`.

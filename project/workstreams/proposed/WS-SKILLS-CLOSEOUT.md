---
id: WS-SKILLS-CLOSEOUT
kind: planning_node
title: LRH Session Closeout Skill
status: proposed
stage: designed
origin: follow_up
summary: >
  Implement the /lrh-closeout skill (Phase 1: edit-in-place) and the
  lrh prompt update-execution CLI command (Phase 2: CLI + skill upgrade),
  automating the post-execution closeout workflow for LRH sessions.
related_design:
  - project/design/proposals/proposed/lrh-closeout/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
work_items:
  - WI-SKILLS-LRH-CLOSEOUT
exit_criteria:
  - /lrh-closeout skill exists at .claude/skills/lrh-closeout/ and src/lrh/skills/lrh-closeout/ and passes lrh validate with 0 errors
  - CLAUDE.md ## Skills index updated with /lrh-closeout entry
  - WI-SKILLS-LRH-CLOSEOUT resolved in project/work_items/resolved/
  - lrh prompt update-execution CLI command implemented and documented
  - skill's Step 5 upgraded to use lrh prompt update-execution (edit-in-place replaced)
  - WI-PROMPT-CLI-CLOSEOUT resolved in project/work_items/resolved/
---

## Purpose

This workstream implements `/lrh-closeout`, the missing third-phase complement
to `/lrh-implement` and `/lrh-review-response` in the LRH three-phase execution
session model (instruction → execution → closeout). It also specifies and
implements `lrh prompt update-execution`, a new CLI subcommand for atomically
updating an execution record to `landed` status.

The closeout phase has been performed manually in every LRH session — editing
execution record frontmatter, moving work items from `proposed/` to `resolved/`,
closing workstreams, and adopting proposals. `WS-SKILLS-DOC` (resolved
2026-06-27) demonstrated the gap: the workstream and proposal closeout steps
were forgotten until explicitly prompted, despite occurring in the same session
that completed all three deliverables.

## Background / Rationale

The design for both deliverables is captured in `PROP-LRH-CLOSEOUT`
(proposed 2026-06-27). Implementation follows skill-first sequencing (Decision
1 of the proposal): the skill is built with edit-in-place first, the CLI spec
is a forward requirement in the proposal, and the skill's Step 5 is upgraded
in WI-2 once the CLI is implemented. This lets observed skill behavior confirm
the CLI interface before it is built.

## Scope

- Implement `/lrh-closeout` skill: 8-step flow (parse → assess → resolve
  transcript → confirm → execute → validate → reflect → report),
  assessment-first decision matrix, one reference file
  (`closeout-workflow.md`)
- Deliver distributable package copies at `src/lrh/skills/lrh-closeout/`
  for global installation via `lrh setup`
- Implement `lrh prompt update-execution` CLI subcommand with the 4-field
  interface specified in PROP-LRH-CLOSEOUT Decision 3
- Upgrade skill Step 5 from edit-in-place to `lrh prompt update-execution`
  call

## Work Items

- **`WI-SKILLS-LRH-CLOSEOUT`** — Implement `/lrh-closeout` skill (Phase 1:
  edit-in-place). Produces `src/lrh/skills/lrh-closeout/SKILL.md`,
  `references/closeout-workflow.md`, `.claude/skills/lrh-closeout/` mirror,
  and `CLAUDE.md` index entry.
- **`WI-PROMPT-CLI-CLOSEOUT`** — Implement `lrh prompt update-execution`
  CLI (Phase 2) and upgrade skill Step 5. Depends on
  `WI-SKILLS-LRH-CLOSEOUT` landing first.

## Exit Criteria

- `/lrh-closeout` skill exists at `.claude/skills/lrh-closeout/` and
  `src/lrh/skills/lrh-closeout/` and passes `lrh validate` with 0 errors
- `CLAUDE.md ## Skills` index updated with `/lrh-closeout` entry
- `WI-SKILLS-LRH-CLOSEOUT` resolved in `project/work_items/resolved/`
- `lrh prompt update-execution` CLI command implemented and documented
- Skill's Step 5 upgraded to use `lrh prompt update-execution`
  (edit-in-place replaced)
- `WI-PROMPT-CLI-CLOSEOUT` resolved in `project/work_items/resolved/`

## Non-Goals

- Does not implement `lrh closeout` as a top-level command — the skill
  is the interface; the CLI subcommand is scoped to execution record
  mutation only (per PROP-LRH-CLOSEOUT Decision 3)
- Does not automate the `resolution:` prose in work items — that is
  human-authored and provided at the confirm gate
- Does not close GitHub PRs — the skill records already-merged PRs; PR
  closing is a human action
- Does not replace human judgment on whether WS exit criteria are met
- Does not write memories automatically — Step 7 prompts the user;
  writing is opt-in
- Does not cover the instruction or execution phases — those remain the
  `/lrh-design`, `/lrh-proposal`, and `/lrh-implement` skills

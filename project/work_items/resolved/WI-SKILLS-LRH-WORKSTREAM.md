---
resolution: implemented
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-WORKSTREAM
title: Implement /lrh-workstream Claude Code skill
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_proposal
  - implement_lrh_design_step4
acceptance:
  - "/lrh-workstream <WS-ID> creates project/workstreams/proposed/<WS-ID>.md with valid kind: planning_node and stage: conceived frontmatter"
  - lrh validate reports 0 errors after the skill creates a workstream
  - Confirm-before-write gate is present in the skill execution steps
  - "CLAUDE.md ## Skills index includes a /lrh-workstream entry"
  - diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/ reports no differences
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-workstream/references/workstream-schema.md
  - src/lrh/skills/lrh-workstream/references/workstream-body-guide.md
  - .claude/skills/lrh-workstream/SKILL.md
  - .claude/skills/lrh-workstream/references/workstream-schema.md
  - .claude/skills/lrh-workstream/references/workstream-body-guide.md
  - CLAUDE.md
---

## Summary

Implement the `/lrh-workstream` Claude Code skill that guides users through
creating a workstream planning node at
`project/workstreams/proposed/<WS-ID>.md` following the LRH workstream
schema. The skill interviews the user, researches existing workstreams,
proposes complete frontmatter and body for review, and writes the file only
after explicit confirmation.

## Problem / Context

Workstreams are the primary unit for grouping related work items into a
coherent delivery arc. Currently there is no `/lrh-workstream` skill to
parallel `/lrh-work-item`, leaving workstream creation as a manual, schema-
dependent task. This skill completes the capture-design primitive trio
alongside `/lrh-proposal` (`WI-SKILLS-LRH-PROPOSAL`) and the `/lrh-design`
Step 4 update (`WI-SKILLS-LRH-DESIGN-STEP4`), giving users a single
slash-command path from design conversation to any control-plane artifact.

## Scope

- Implement `src/lrh/skills/lrh-workstream/` and mirror to
  `.claude/skills/lrh-workstream/`
- Create `SKILL.md` with interview, research, confirm gate, write, and
  validate steps
- Create `references/workstream-schema.md` derived from existing workstream
  YAML frontmatter and the validator
- Create `references/workstream-body-guide.md` for section authoring guidance
- Add `/lrh-workstream` entry to `CLAUDE.md` `## Skills` index

## Required Changes

1. Create `src/lrh/skills/lrh-workstream/SKILL.md` — `disable-model-
   invocation: true`, `argument-hint: [WS-ID]`; execution steps: check
   existing workstream, interview, research existing workstreams and related
   proposals, confirm gate, create branch, write
   `project/workstreams/proposed/<WS-ID>.md`, `lrh validate`, commit/PR,
   offer to link related work items and proposals; quality checklist;
   non-goals.
2. Create `src/lrh/skills/lrh-workstream/references/workstream-schema.md` —
   YAML frontmatter field reference: required fields (`id`, `kind:
   planning_node`, `title`, `status`, `stage`), stage vocabulary (`conceived`,
   `assessed`, `designed`, `planned`, `executing`, `reviewing`, `closed`,
   `abandoned`), lifecycle vocabulary for `status` (`proposed`, `active`,
   `resolved`, `abandoned`), supported list fields (`work_items`,
   `related_design`, `children`). Cross-reference `src/lrh/control/validator.py`
   `WORKSTREAM_REQUIRED_FIELDS` and `WORKSTREAM_LIST_FIELDS` as authoritative.
3. Create `src/lrh/skills/lrh-workstream/references/workstream-body-guide.md`
   — section guide for: Summary, Motivation, Scope, Work Items, Non-Goals,
   Exit Criteria. Mirrors the discipline in `work-item-body-guide.md`.
4. Mirror all files to `.claude/skills/lrh-workstream/` — exact copy of
   `src/lrh/skills/lrh-workstream/`.
5. Edit `CLAUDE.md` — add `/lrh-workstream` entry to `## Skills` index.

## Non-Goals

- Do not create an actual workstream — the skill creates the capability,
  not an instance.
- Do not implement `/lrh-proposal` — that is `WI-SKILLS-LRH-PROPOSAL`.
- Do not update `/lrh-design` Step 4 — that is `WI-SKILLS-LRH-DESIGN-STEP4`.
- Do not add workstream validation logic to `lrh validate` — the existing
  validator already handles workstream frontmatter.
- Do not automatically populate `work_items:` from existing proposed items —
  the skill offers to link items; population is a user decision.

## Acceptance Criteria

- `/lrh-workstream <WS-ID>` creates `project/workstreams/proposed/<WS-ID>.md`
  with valid frontmatter: `id`, `kind: planning_node`, `title`,
  `status: proposed`, `stage: conceived`
- `lrh validate` reports 0 errors after the skill runs
- The skill has an explicit confirm-before-write gate before writing any file
- `CLAUDE.md` `## Skills` index includes a `/lrh-workstream` entry
- `diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/`
  reports no differences

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/`

## Risk Notes

- `references/workstream-schema.md` should be derived from the existing
  workstream files and validated against the validator source
  (`src/lrh/control/validator.py`) to ensure the schema reference stays
  accurate.
- The skill offers (not requires) to link related work items and proposals
  after creation — this matches the pattern in `/lrh-work-item` Step 9
  for workstream updates.

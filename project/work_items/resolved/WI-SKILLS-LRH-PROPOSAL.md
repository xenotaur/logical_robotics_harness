---
resolution: implemented
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-PROPOSAL
title: Implement /lrh-proposal Claude Code skill
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
  - implement_lrh_workstream
  - implement_lrh_design_step4
acceptance:
  - "/lrh-proposal <slug> creates project/design/proposals/proposed/<slug>/00_proposal.md with valid type: design_proposal frontmatter"
  - lrh validate reports 0 errors after the skill creates a proposal
  - Confirm-before-write gate is present in the skill execution steps
  - "CLAUDE.md ## Skills index includes a /lrh-proposal entry"
  - diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/ reports no differences
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-proposal/references/proposal-schema.md
  - src/lrh/skills/lrh-proposal/references/proposal-body-guide.md
  - .claude/skills/lrh-proposal/SKILL.md
  - .claude/skills/lrh-proposal/references/proposal-schema.md
  - .claude/skills/lrh-proposal/references/proposal-body-guide.md
  - CLAUDE.md
---

## Summary

Implement the `/lrh-proposal` Claude Code skill that guides users through
creating a design proposal document at
`project/design/proposals/proposed/<slug>/00_proposal.md` following the LRH
proposal schema. The skill interviews the user, researches existing proposals,
proposes complete frontmatter and body for review, and writes the file only
after explicit confirmation.

## Problem / Context

After `/lrh-design` produces a design, the natural follow-on is to capture it
as a design proposal in the project control plane. Currently `/lrh-design`
Step 4 offers "to produce a proposal document" but has no skill to back that
up. This leaves users without a structured path from design conversation to
durable proposal artifact. Companion skills `/lrh-workstream`
(`WI-SKILLS-LRH-WORKSTREAM`) and an updated `/lrh-design` Step 4
(`WI-SKILLS-LRH-DESIGN-STEP4`) complete the capture-design workflow; this
work item delivers the proposal primitive.

## Scope

- Implement `src/lrh/skills/lrh-proposal/` and mirror to `.claude/skills/lrh-proposal/`
- Create `SKILL.md` with interview, research, confirm gate, write, and
  validate steps
- Create `references/proposal-schema.md` derived from
  `project/design/proposals/README.md`
- Create `references/proposal-body-guide.md` for section authoring guidance
- Add `/lrh-proposal` entry to `CLAUDE.md` `## Skills` index

## Required Changes

1. Create `src/lrh/skills/lrh-proposal/SKILL.md` — `disable-model-invocation:
   true`, `argument-hint: [slug]`; execution steps: check existing proposal,
   interview, research existing proposals and related design context, confirm
   gate, create branch, write
   `project/design/proposals/proposed/<slug>/00_proposal.md`, `lrh validate`,
   commit/PR; quality checklist; non-goals.
2. Create `src/lrh/skills/lrh-proposal/references/proposal-schema.md` —
   YAML frontmatter field reference: required fields (`id`, `type:
   design_proposal`, `title`, `status`, `implementation_status`), lifecycle
   vocabulary (`proposed`, `adopted`, `superseded`, `rejected`),
   `implementation_status` vocabulary, optional traceability fields
   (`implemented_by`, `supersedes`, `superseded_by`, `evidence`). Cross-
   reference to `project/design/proposals/README.md` as authoritative source.
3. Create `src/lrh/skills/lrh-proposal/references/proposal-body-guide.md` —
   section guide for: Summary, Background/Motivation, Design Decisions,
   Non-Goals, Implementation Plan, and cross-references. Mirrors the discipline
   in `work-item-body-guide.md`.
4. Mirror all files to `.claude/skills/lrh-proposal/` — exact copy of
   `src/lrh/skills/lrh-proposal/`.
5. Edit `CLAUDE.md` — add `/lrh-proposal` entry to `## Skills` index.

## Non-Goals

- Do not create an actual design proposal document — the skill creates the
  capability, not an instance.
- Do not implement `/lrh-workstream` — that is `WI-SKILLS-LRH-WORKSTREAM`.
- Do not update `/lrh-design` Step 4 — that is `WI-SKILLS-LRH-DESIGN-STEP4`.
- Do not add proposal validation logic to `lrh validate` — the existing
  validator already handles `type: design_proposal` frontmatter.
- Do not implement multi-file proposal sub-documents — the skill creates the
  umbrella `00_proposal.md` only; sub-proposals are out of scope.

## Acceptance Criteria

- `/lrh-proposal <slug>` creates
  `project/design/proposals/proposed/<slug>/00_proposal.md` with valid
  frontmatter: `id`, `type: design_proposal`, `title`, `status: proposed`,
  `implementation_status: not_started`
- `lrh validate` reports 0 errors after the skill runs
- The skill has an explicit confirm-before-write gate before writing any file
- `CLAUDE.md` `## Skills` index includes a `/lrh-proposal` entry
- `diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/` reports
  no differences

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/`

## Risk Notes

- `references/proposal-schema.md` is derived from `project/design/proposals/
  README.md` and should cross-reference it explicitly so drift is caught on
  review.
- The skill creates `<slug>/00_proposal.md` (proposal-set form) by default,
  which accommodates both single-file proposals and future sub-proposals
  without ambiguity.

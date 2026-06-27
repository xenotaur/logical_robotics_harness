---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-CLOSEOUT
title: Implement lrh-closeout Claude Code skill (Phase 1)
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/proposed/lrh-closeout/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_lrh_prompt_update_execution
acceptance:
  - src/lrh/skills/lrh-closeout/SKILL.md exists with valid frontmatter
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md exists
  - diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/ reports no differences
  - CLAUDE.md lists /lrh-closeout in the Skills section
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - .claude/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/references/closeout-workflow.md
  - CLAUDE.md (Skills section updated with /lrh-closeout)
---

## Summary

Implement the `/lrh-closeout` Claude Code skill (Phase 1: edit-in-place) as
specified in `PROP-LRH-CLOSEOUT`. The skill automates the post-execution
closeout workflow for LRH sessions: updating execution records to `landed`,
resolving work items, closing workstreams, and adopting governing proposals.

## Problem / Context

The LRH three-phase execution session model (design → instruction → execution)
has no tooling for post-execution closeout. Every session requires manual edits
to execution record frontmatter, manual `mv` of work items to `resolved/`, and
ad hoc workstream/proposal closeout steps. The `WS-SKILLS-DOC` workstream
(resolved 2026-06-27) demonstrated the gap: workstream and proposal closeout
were forgotten entirely until the user explicitly asked.

`PROP-LRH-CLOSEOUT` (`project/design/proposals/proposed/lrh-closeout/00_proposal.md`,
proposed 2026-06-27) designs an 8-step skill that assesses artifact state before
acting (assessment-first decision matrix, Decision 2), resolves the session
transcript via a 3-way confirm (Decision 4), presents a full closeout plan at a
human gate (Step 4), and executes all confirmed actions.

This WI implements Phase 1 (edit-in-place). Phase 2 (`WI-PROMPT-CLI-CLOSEOUT`)
will replace the edit-in-place mechanism in Step 5 with a `lrh prompt
update-execution` CLI call; the skill's external interface and step structure
remain stable between phases.

## Scope

- Implement `src/lrh/skills/lrh-closeout/` (SKILL.md and one reference file)
  and mirror byte-for-byte to `.claude/skills/lrh-closeout/`
- Update `CLAUDE.md` to add `/lrh-closeout` to the `## Skills` section
- Add `WI-SKILLS-LRH-CLOSEOUT` to the `work_items:` list in
  `WS-SKILLS-CLOSEOUT.md`

## Required Changes

1. Create `src/lrh/skills/lrh-closeout/SKILL.md` — 8-step skill body per
   PROP-LRH-CLOSEOUT Decision 5:

   - **Step 1 — Parse input**: Accept PR URL, WI-ID, WS-ID, or auto-detect
     from in-progress records via
     `grep -rl '^status: in_progress' project/executions/ --include='*.md'`.
     Read `pr:` field from candidates; if ambiguous, list and ask.
   - **Step 2 — Assess state → build closeout plan**: Apply the decision
     matrix from `references/closeout-workflow.md` to all discovered artifacts
     (PR state, execution record status, WI location, WS stage, proposal
     status). Produce plan as a table of (artifact, current-state,
     intended-action).
   - **Step 3 — Resolve session transcript**: Attempt JSONL auto-detection
     (`~/.claude/projects/<slug>/*.jsonl`); 3-way confirm: found → confirm
     with user, not found → ask user to provide or confirm `pending`, user
     confirms `pending` → set `session_transcript: pending`.
   - **Step 4 — Confirm gate**: Show full closeout plan + resolved session
     transcript value. Wait for explicit confirmation before touching any
     files.
   - **Step 5 — Execute confirmed actions (Phase 1: edit-in-place)**: Edit
     execution record YAML frontmatter in-place (`status: landed`, `pr:`,
     `commit:`, `session_transcript:`); `mv` WI to `resolved/` and set
     `status: resolved`, `resolution:`; if WS offered and confirmed, set
     `stage: closed`, `status: resolved`, `mv` to `workstreams/resolved/`;
     if proposal offered and confirmed, set `status: adopted`,
     `implementation_status: implemented`, `implemented_by: [WI IDs]`,
     `mv` to `proposals/adopted/`.
   - **Step 6 — Validate**: Run `lrh validate`; abort and report if errors.
   - **Step 7 — Session reflection**: Ask whether anything from this session
     is worth persisting to memory; write if yes, proceed if no.
   - **Step 8 — Report**: Summarize all actions taken; remind about `/export`
     to archive session; remind to update `session_transcript` if still pending.

2. Create `src/lrh/skills/lrh-closeout/references/closeout-workflow.md` per
   PROP-LRH-CLOSEOUT Decision 6, containing:
   - Full decision matrix (artifact → condition → action table)
   - Execution record update protocol (field values, valid `in_progress →
     landed` transition, `pending` convention)
   - WI resolution protocol (required frontmatter fields, `mv` command to
     `resolved/`)
   - WS closeout protocol (`stage: closed`, `status: resolved`)
   - Proposal adoption protocol (`status: adopted`,
     `implementation_status: implemented`, `implemented_by: [WI IDs]`)
   - Session transcript auto-detection (JSONL path pattern,
     `claude-app:<uuid>` format, `pending` sentinel)

3. Mirror both files to `.claude/skills/lrh-closeout/`
   (byte-for-byte identical, verified with `diff -r`).

4. Update `CLAUDE.md` — add `/lrh-closeout` to the `## Skills` section.

5. Add `WI-SKILLS-LRH-CLOSEOUT` to the `work_items:` list in
   `project/workstreams/proposed/WS-SKILLS-CLOSEOUT.md`.

## Non-Goals

- Do not implement `lrh prompt update-execution` — that is
  `WI-PROMPT-CLI-CLOSEOUT` (Phase 2).
- Do not call any CLI in Step 5 — Phase 1 uses edit-in-place only.
- Do not add a second reference file (e.g., `diataxis-criteria.md`) — per
  Decision 6 of PROP-LRH-CLOSEOUT, one reference file is sufficient.
- Do not automatically write memories — Step 7 prompts the user; writing
  is always opt-in.
- Do not create `WI-PROMPT-CLI-CLOSEOUT` — that is a separate planning action.

## Acceptance Criteria

- `src/lrh/skills/lrh-closeout/SKILL.md` exists with valid YAML frontmatter.
- `src/lrh/skills/lrh-closeout/references/closeout-workflow.md` exists.
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
  reports no differences.
- `CLAUDE.md` lists `/lrh-closeout` in the Skills section.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`

## Risk Notes

- **Edit-in-place on YAML**: editing frontmatter requires precise string
  matching; the skill must read each file before editing and abort on any
  mismatch rather than partially completing the closeout.
- **Assessment-first is critical**: no files should be touched before Step 4
  (confirm gate); the decision matrix read-only pass must complete first.
- **`mv` not `cp` for WI resolution**: a stale copy in `proposed/` alongside
  a copy in `resolved/` triggers `WORK_ITEM_ID_DUPLICATE` in `lrh validate`.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SKILLS-CLOSEOUT.md`
- Design: `project/design/proposals/proposed/lrh-closeout/00_proposal.md`
- Pattern: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`

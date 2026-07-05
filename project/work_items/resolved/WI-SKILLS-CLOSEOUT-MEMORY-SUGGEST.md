---
resolution: "Implemented and merged in PR #373 (commit 7637db7664b1559b4c49b059e7779af39a1c16fc)"
blocked_reason: null
blocked: false
id: WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST
title: Draft memory candidates in /lrh-closeout Step 7 before asking the user
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - modify_lrh_closeout_proposal
  - automate_memory_write
acceptance:
  - Step 7 in src/lrh/skills/lrh-closeout/SKILL.md drafts 0-3 candidate memory suggestions (rule plus one-line why each) before asking the user, grounded in the session's actual changes and decisions
  - If zero candidates are found, Step 7 states so explicitly rather than silently skipping
  - Step 7 still ends with an explicit confirm/edit/decline gate before any memory is written
  - .claude/skills/lrh-closeout/SKILL.md is byte-identical to src/lrh/skills/lrh-closeout/SKILL.md
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
---

# WI-SKILLS-CLOSEOUT-MEMORY-SUGGEST

## Summary

Change `/lrh-closeout` Step 7 from a blind "is there anything worth
persisting?" question into a self-review step that drafts candidate memory
suggestions (or explicitly states none) before asking for confirmation.

## Problem / Context

Step 7's current wording (`src/lrh/skills/lrh-closeout/SKILL.md:282-290`)
asks an open, context-free question. The user runs closeout sessions but
lacks the assistant's full session context, and has repeatedly found the
blind question hard to answer. The wording is copied verbatim from the
adopted `00_proposal.md:233-235`, so this refines an already-adopted step
rather than introducing a new design decision — following the precedent set
by `WI-SKILLS-CLOSEOUT-UX-FIX` (PR #344), which refined Step 8's behavior
similarly without amending the proposal.

## Scope

- Restructure Step 7 to review the session before asking, draft 0-3
  candidates with one-line whys, and only then present the
  confirm/edit/decline gate.
- Mirror the change to `.claude/skills/lrh-closeout/SKILL.md`.

## Required Changes

1. Edit `src/lrh/skills/lrh-closeout/SKILL.md` Step 7 (lines 282-290):
   before asking the user, review the session's changes and decisions
   against the standard memory criteria (surprising, non-obvious, not
   derivable from code/git history, durable) and draft candidate
   suggestions.
2. If no candidates are found, state that explicitly, mirroring the
   existing Step 8 convention ("Memory: nothing written this session").
3. Preserve the explicit confirm/edit/decline gate before any file is
   written — the write mechanism itself (auto-memory system, `MEMORY.md`
   pointer) is unchanged.
4. Mirror the updated file to `.claude/skills/lrh-closeout/SKILL.md`.

## Non-Goals

- Do not amend `project/design/proposals/adopted/lrh-closeout/00_proposal.md`
  — this refinement preserves its stated principle (`00_proposal.md:270`:
  "writing is always opt-in") and follows the `WI-SKILLS-CLOSEOUT-UX-FIX`
  precedent of not touching the proposal for this class of change.
- Do not change `references/closeout-workflow.md` — it doesn't duplicate
  Step 7's text.
- Do not change the Quality Checklist section — it doesn't quote Step 7's
  literal wording.
- Do not automate memory-writing — Step 7 remains human-confirmed and
  opt-in.

## Acceptance Criteria

- Step 7 drafts 0-3 candidate memory suggestions (rule plus one-line why
  each) before asking the user, grounded in the session's actual changes
  and decisions.
- If zero candidates are found, Step 7 states so explicitly.
- Step 7 still ends with an explicit confirm/edit/decline gate before any
  memory is written.
- `.claude/skills/lrh-closeout/SKILL.md` is byte-identical to
  `src/lrh/skills/lrh-closeout/SKILL.md`.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`

## Risk Notes

- Drafting candidates requires the assistant to actually review the
  session's own changes/decisions, not just re-read the current step
  text — the instruction must be concrete enough to produce real review,
  not a rubber-stamped "no candidates" every time.
- Must not weaken the opt-in confirm gate while making the prompt more
  informative — over-eagerly listing candidates could pressure the user
  toward confirming things that aren't actually memory-worthy.

## Related Workstream and Designs

- `src/lrh/skills/lrh-closeout/SKILL.md` (Step 7, lines 282-290)
- `project/design/proposals/adopted/lrh-closeout/00_proposal.md` (Step 7
  spec, lines 233-235)
- `project/work_items/resolved/WI-SKILLS-CLOSEOUT-UX-FIX.md` (precedent)
- No workstream — scoped directly as a standalone work item via
  `/lrh-design`

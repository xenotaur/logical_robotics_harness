---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-SESSION-SOURCING
title: Make lrh-closeout session-transcript resolution backend-aware
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
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_session_discovery
  - implement_lrh_sessions_command
  - modify_lrh_validate
acceptance:
  - lrh-closeout Step 3 reads $CLAUDE_CODE_HOST_SESSION_ID first for same-session closeouts and stores the host UUID stem with the local_ prefix stripped
  - Step 3 falls back to list_sessions matched by PR number for cross-session closeouts before prompting for a browser URL
  - Step 3 offers `none` as a distinct terminal option (backend produced no retrievable transcript) separate from `pending`
  - Both SKILL.md mirrors and both closeout-workflow.md reference mirrors are updated identically, verified by diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout exiting 0 (no differences)
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - .claude/skills/lrh-closeout/references/closeout-workflow.md
---

# Make lrh-closeout session-transcript resolution backend-aware

## Summary

Make the `/lrh-closeout` skill's Step 3 (Resolve session transcript)
backend-aware, so it emits the canonical host-based Claude pointer and the
`none` terminal sentinel instead of only offering a Claude UUID or `pending`.

## Problem / Context

Two review comments were deferred to a "closeout session-ID redesign" during
the session that shipped PRs #409–#411:

- **#409 (host-id sourcing):** Step 3 auto-detects the session id from the
  `~/.claude/projects/<slug>/<uuid>.jsonl` filename, which is the *child* SDK
  id. The 2026-07-23 decision-log entry establishes that the canonical stored
  value is the *host* id (`$CLAUDE_CODE_HOST_SESSION_ID`, `local_` stripped).
  On resumed or continued sessions the host and child ids differ, so closeout
  can write a `claude-app:<child-uuid>` pointer that session-management tools
  cannot resolve.
- **#411 (`none` path):** Step 3 offers only a Claude UUID or `pending`. For
  Codex or manual executions with no retrievable transcript, that forces the
  exact false-backlog state the new `none` sentinel was created to eliminate
  (`pending` means "exists, not yet recorded"; `none` means "no retrievable
  transcript, terminal").

Prior-art check performed 2026-07-24:

- **Duplication search:** No existing work item covers the closeout skill's
  Step 3 behavior. `WI-EXEC-SESSIONS-SCHEMA` covers the `lrh validate`
  validator (kept out of scope here via the `modify_lrh_validate` forbidden
  action) and `WI-EXEC-SESSIONS-DOCS` covered README/PROMPTS docs (the README
  portion already landed in PR #411). Different deliverable — the closeout
  SKILL.md — so no overlap. Verdict: no duplicate.
- **Demand search:** The two deferred codex review threads (on PRs #409 and
  #411) are the demand; no work item captured them until this one. Verdict:
  demand exists, previously uncaptured.

## Scope

Edit the closeout skill's Step 3 and the session-transcript auto-detection
section of its `references/closeout-workflow.md`, in both the
`src/lrh/skills/lrh-closeout/` and `.claude/skills/lrh-closeout/` mirrors.
The grammar and sentinel definitions already landed in PR #411 (the
decision-log entry and `project/executions/README.md`); this work item only
teaches the closeout skill to *use* them.

## Required Changes

- Rewrite Step 3 resolution order to: `$CLAUDE_CODE_HOST_SESSION_ID`
  (same-session, store host stem with `local_` stripped) → `list_sessions`
  matched by PR number (cross-session) → browser View > Copy URL → sentinel.
- Add a `none` branch distinct from `pending`, with one line on when each
  applies (no retrievable transcript vs. retrievable-but-not-yet-recorded).
- Update the `references/closeout-workflow.md` session-transcript
  auto-detection section to match the new order and sentinels.
- Apply every change to both the `src/lrh/skills/` and `.claude/skills/`
  mirrors identically.

## Non-Goals

- No `lrh validate` grammar enforcement — that is `WI-EXEC-SESSIONS-SCHEMA`.
- No new `lrh sessions` discovery command or Python session-discovery code.
- No changes to record-creation skills (`/lrh-implement`,
  `/lrh-review-response`, `/lrh-confirm-fixes`). Their templates write
  `session_transcript: pending` and do not auto-populate it; teaching them to
  source the host id from `$CLAUDE_CODE_HOST_SESSION_ID` at record-creation
  time is a separate concern from this closeout-focused work item.

## Acceptance Criteria

- lrh-closeout Step 3 reads `$CLAUDE_CODE_HOST_SESSION_ID` first for
  same-session closeouts and stores the host UUID stem with `local_` stripped.
- Step 3 falls back to `list_sessions` matched by PR number for cross-session
  closeouts before prompting for a browser URL.
- Step 3 offers `none` as a distinct terminal option, separate from `pending`.
- Both SKILL.md mirrors and both closeout-workflow.md reference mirrors are
  updated identically (`diff -r src/lrh/skills/lrh-closeout
  .claude/skills/lrh-closeout` exits 0).
- `lrh validate` passes with 0 errors.

## Validation

- `diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout` exits 0
  (no differences between the two closeout-skill trees)
- `lrh validate` reports 0 errors

## Risk Notes

A separate in-progress "closeout session-URL" design touches the same Step 3.
If that design lands first, this work item should be reconciled against it
rather than conflict with it. Until the relationship is settled, this item
stays `proposed`. The change is markdown-only (skill instructions), so the
blast radius is limited to closeout behavior; record-creation skills are
unaffected.

---
resolution: null
blocked_reason: null
blocked: false
id: WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION
title: "Investigate how to identify the current Antigravity conversation, and define its session_transcript pointer format"
type: investigation
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
  - WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/memory/decisions/DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_resolver
  - print_transcript_text
  - commit_raw_transcript_data
acceptance:
  - "A findings document records, with evidence, every candidate source for the current Antigravity conversation ID that was checked (environment variables, files under ~/.gemini/antigravity, agent-visible context, and any documented Antigravity SDK or API) and whether each one reliably identifies the current conversation"
  - "The document picks a session_transcript pointer format for Antigravity (the candidate is antigravity-app:<conversation-id>), or explains why no stable pointer is possible"
  - "The document specifies how a resolver should behave when the current conversation cannot be determined (for example, fall back to --latest with a warning, ask the user, or record pending)"
  - "The document ends with an explicit recommendation: proceed with WI-ANTIGRAVITY-SESSION-ID-RESOLVER as scoped, proceed with a changed scope, or defer it with the reason recorded"
  - "If no live Antigravity session is available to the implementing agent, the document records that as a finding, lists the candidate sources as unverified, and recommends deferring WI-ANTIGRAVITY-SESSION-ID-RESOLVER; this counts as meeting the acceptance criteria, so the item can still resolve"
  - "No transcript text is printed or committed, and lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/appendix_antigravity_session_identity.md
---

# WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION: Find a reliable source for the current Antigravity conversation ID

## Summary

Find out whether an agent running inside Google Antigravity can reliably tell
which conversation it is in, and define the `session_transcript:` pointer
format LRH should record for Antigravity. This is the investigation that
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 5 requires before an
Antigravity session-ID resolver is built.

## Problem / Context

The other two vendors each have a reliable source for the current session's
ID:

| Vendor | Source | Pointer format |
|---|---|---|
| Codex | `CODEX_THREAD_ID` environment variable (`src/lrh/conversations/codex_session.py`) | `codex-app:<task-or-thread-id>` |
| Claude | `CLAUDE_CODE_SESSION_ID` and `CLAUDE_CODE_HOST_SESSION_ID` environment variables (`src/lrh/conversations/claude_session.py`) | `claude-app:<host-uuid-stem>` |

Antigravity has neither:

- **No known source.** Neither `src/` nor the skills contain an Antigravity
  environment variable.
- **No pointer format.** `PROMPTS.md`, `project/executions/README.md` and
  `lrh-closeout`'s `references/closeout-workflow.md` define none for
  Antigravity.
- **Discovery only by path or recency.**
  `lrh conversation export-antigravity-session` finds transcripts by
  `--conversation-id`, which reads
  `~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl`,
  or by `--latest`. Neither can say which conversation is the current one
  when several are active.

Building a resolver on `--latest` alone risks recording the wrong session as
an execution record's provenance. So this investigation comes first, and
`WI-ANTIGRAVITY-SESSION-ID-RESOLVER` depends on it.

### Duplication search
- In-repo: Related: `src/lrh/conversations/antigravity_export.py`, which finds
  transcripts but does not identify the current conversation.
  `DEC-AGENT-SKILL-INTEROPERABILITY-ANTIGRAVITY` covers skill installation,
  not session identity.
- Sibling repos: None identified.
- External libraries: The Google Antigravity SDK (`google-antigravity`, cited
  in `WS-ANTIGRAVITY-CONVERSATION-EXPORT`) may expose conversation context.
  Check it as part of this investigation.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 5.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Check each candidate source for the current conversation ID, from inside a
  live Antigravity session where possible.
- Record findings, a pointer-format decision, fallback behavior, and a
  recommendation for the resolver work item.

## Required Changes

1. From inside a live Antigravity agent session, list environment variable
   **names** only, never values that may be secret, and look for anything
   that names a conversation, trajectory or session.
2. Check whether the agent's own context (system prompt, working paths,
   artifact paths) exposes the current conversation ID or the brain
   directory.
3. Check the structure and modification times of
   `~/.gemini/antigravity/brain/` to see whether the active conversation can
   be told apart from others when several are open.
4. Check any documented Antigravity SDK, API or configuration for a
   current-conversation accessor.
5. Write
   `project/design/proposals/proposed/lrh-export-session-id-skill-families/appendix_antigravity_session_identity.md`
   (with `parent: PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`) containing:
   - the findings table;
   - the chosen pointer format;
   - fallback behavior;
   - the recommendation for `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`.

## Non-Goals

- Does not implement the resolver CLI or the `lrh-session-id-antigravity`
  skill.
- Does not change `export-antigravity-session`.
- Does not print, copy or commit transcript content.

## Acceptance Criteria

- Every candidate ID source checked is recorded with evidence and a verdict on
  whether it is reliable.
- A pointer format is chosen, or its impossibility is explained.
- Resolver fallback behavior is specified.
- The document gives an explicit proceed, change-scope or defer recommendation
  for `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`.
- No transcript text is printed or committed, and `lrh validate` is clean.

## Validation

- `lrh validate`
- `git diff --stat` shows only the appendix, plus this work item's own
  lifecycle edits

## Risk Notes

- Environment variable values may contain tokens. Record names only.
- The investigation needs a real Antigravity session. If none is available to
  the implementing agent, record that and stop, rather than inferring
  behavior. This is still a valid way to resolve the item (see Acceptance
  Criteria): record the candidates as unverified and recommend deferring the
  resolver. `WI-EXPORT-SESSION-ID-DOCS` depends on this item, so it must be
  able to reach `resolved`.

---
resolution: 'Implemented and merged in PR #717 (commit c45420dce5431b5f5425ab2ea5eab7d0cd13eee1)'
blocked_reason: null
blocked: false
id: WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL
title: Distinguish genuine human turns from tool-result turns in Claude export Markdown headers
type: deliverable
status: resolved
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - retrofit_other_exporters
  - change_turn_count_statistics
acceptance:
  - "A tool-result-delivery type==\"user\" JSONL step no longer renders as a ## User Markdown section"
  - "A genuine human-typed type==\"user\" step still renders as ## User, unchanged"
  - "The distinction applies consistently to both the top-level transcript and recursively-inlined subagent transcripts rendered by the same function"
  - "Existing tests for claude_export.py are updated or added to cover both the genuine-human-turn and tool-result-turn rendering cases"
  - "lrh validate reports 0 errors and introduces no new warnings"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
---

# WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL: Distinguish genuine human turns from tool-result turns in Claude export Markdown headers

## Summary

Fix `claude_export.py`'s Markdown renderer so a tool-execution result
delivered back to the assistant (a `type=="user"` JSONL step whose
`message.content` contains a `tool_result` block) is no longer rendered
under an identical `## User` heading to a genuine human-typed message. The
file already has a helper, `_is_genuine_human_turn()`, that makes exactly
this distinction — it is used for the `turn_count` statistic but never at
the render call site.

## Problem / Context

`_render_claude_transcript()` (`src/lrh/conversations/claude_export.py`)
calls `_render_message_block("User", step)` unconditionally for every
step with `type == "user"` (verified directly, `claude_export.py:667-668`).
Claude Code's transcript format overloads `type: "user"` for two different
things: a genuine human-typed message, and a tool-execution result being
delivered back to the assistant (`message.content` containing a
`{"type": "tool_result", ...}` block) — architecturally "the user's turn"
in the API sense, but not human-authored. `_is_genuine_human_turn()`
(`claude_export.py:587-605`) already makes this distinction correctly, but
it is wired only into `_count_turns()` (`claude_export.py:608-616`), not
into the render path. In the rendered Markdown, both cases get an
identical `## User` header — the tool-result case followed by a
`### Tool Result` subheading (`claude_export.py:772-779`), the genuine
case followed by prose directly — with no way to tell them apart short of
reading the body content.

Reported impact (from an informal handoff, not independently reproduced
by this work item's own research — treat the exact count as illustrative,
not verified): on a real ~107K-line/22MB export, ~2625 `## User` sections
total, of which ~2464 were tool-result deliveries — leaving only ~161
genuine human-authored sections. A reader skimming or grepping `## User`
for actual user input is drowned in tool-output noise roughly 15:1 and can
reasonably conclude user content is missing entirely, when it is just
unlabeled.

**Scope check, verified directly against the codebase:** `turn_count`/
`message_count` in `export_manifest.py` are **not** affected by this bug —
`turn_count` already derives from `_count_turns()`, which already calls
`_is_genuine_human_turn()` correctly; only the rendered Markdown body's
section headers are wrong. `export_inspector.py` does not parse `## User`
or any other rendered heading (its only regex splits YAML frontmatter from
body). No doc under `docs/` currently describes the Markdown export's
header/section shape, so nothing there needs updating today.

### Duplication search
- In-repo: no existing work item, proposal, or backlog entry addresses
  this. `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER` and
  `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` (both resolved) touch
  this same exporter but a different concern (session/transcript
  resolution, not turn-type rendering).
- Sibling exporters: `antigravity_export.py` renders `## User` from a
  different, already-disambiguated step-type scheme (`type ==
  "USER_INPUT"` / `source in ("USER_EXPLICIT", "USER")`, distinct from
  whatever type tool results use) — not proven to share this defect.
  `codex_app_server_export.py` has no `## User` header at all. Neither is
  in scope here (see Non-Goals).
- Recommendation: Proceed.

### Demand search
- Raised as an informal handoff from another in-progress session's
  transcript-export review, not yet tracked as a work item until now.
- No open work item or proposal anticipates this fix.
- Recommendation: No action; this item is the tracking artifact.

## Scope

- Edit `src/lrh/conversations/claude_export.py`'s render path only.
- Does not touch the sibling exporters (Codex, Antigravity) or the
  manifest/inspector statistics, which are already correct or unaffected.

## Required Changes

1. Use `_is_genuine_human_turn(step)` at the `## User` render call site
   (`claude_export.py:667-668`), not only in `_count_turns()`.
2. Give the tool-result-delivery case its own heading, not nested under
   `## User` — the exact label is an implementation choice (e.g.
   `## Tool Result`), but it must be visually and grep-distinguishable
   from a genuine human turn's `## User` heading.
3. Verify the fix applies consistently through the existing recursive
   subagent-inlining path (`_render_claude_transcript` calling itself for
   `### Subagent transcript: <id>` sections, `claude_export.py:695-714`)
   without a separate code path — confirm by direct test rather than
   assuming the shared function covers it for free.
4. Re-check `docs/conversations/*.md` and
   `docs/reference/cli/conversation.md` at implementation time for any
   description of the Markdown header shape that may have been added
   since this work item was written; update if one exists.

## Non-Goals

- Does not modify `codex_app_server_export.py` or `antigravity_export.py`
  — neither shares this exact defect as verified above; a similar issue
  in either, if one exists, is out of scope for this item.
- Does not change `turn_count`/`message_count` in `export_manifest.py` —
  already correct.
- Does not change `export_inspector.py` — does not parse rendered
  headings.

## Acceptance Criteria

- A tool-result-delivery `type=="user"` step no longer renders as a
  `## User` Markdown section.
- A genuine human-typed `type=="user"` step still renders as `## User`,
  unchanged.
- The distinction applies consistently to both the top-level transcript
  and recursively-inlined subagent transcripts.
- Existing tests for `claude_export.py` are updated or added to cover
  both the genuine-human-turn and tool-result-turn rendering cases.
- `lrh validate` reports 0 errors and introduces no new warnings.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

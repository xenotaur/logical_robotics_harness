---
execution_id: 2026_10_09_01_59_44_LRH_CONSOLE_INTERACTIVE_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-INTERACTIVE:LRH_CONSOLE_INTERACTIVE_REVIEW)[2026-10-09T01:59:44+00:00]
work_item: WI-LRH-CONSOLE-INTERACTIVE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/801
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/801"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-09T01:59:44+00:00
---

# Summary

This record covers review-response round 1 for PR #801 (`WI-LRH-CONSOLE-INTERACTIVE`), run as
part of `/lrh-land` inside `/lrh-execute`. It combines the bot threads with the owner's hands-on
check of this branch's LRH Console build.

- **CI** passed 7/7 on `b9c65330`.
- **Codex** left 1 P2 thread and **Copilot** left 2 threads. The owner approved all three fixes.
- **The owner's check:** tracing, selection, Escape, filters, the theme switch, and the table
  worked as intended. Their observations (filtered cards keep their space, filters scroll out of
  view, the sidebar scrolls with the content, Settings does not follow the page switch) match the
  work item's specification; at the owner's direction they go to the backlog as layout-redesign
  input rather than into this PR.

# Result

- **Codex P2, `lrh-interactive.js` filter walk:** `data-unmet` was space-joined, so a work-item ID
  containing a space split into nonexistent IDs and an unfinished prerequisite could be hidden.
  `render.py` now writes a JSON list, and the script reads it with a guarded `JSON.parse`.
- **Copilot, `serve.py` `_write_static`:** HEAD for a disabled interactive script returned 404
  with a JSON body. It now uses the headers-only writer.
- **Copilot, `lrh-interactive.js` `showDrawer`:** hiding a drawer that held focus stranded keyboard
  and screen-reader users. Focus now returns to the card or link that opened the drawer, or to
  the map when that trigger cannot take focus (for example, while filtered), before the drawer
  is hidden.
- **Backlog:** `project/design/backlog.md` gains "LRH Console UX feedback from the first
  interactive dogfood (layout redesign input)", covering the as-specified behaviors to revisit and
  the owner's suggestions (content first, sidebar state, pinned views and project groups, less
  vertical height).

Fix commit: `f02282b894b17d2afadcb43bf41394f6159b41aa`.

## Round 2: substitute-review findings

A cold-context review of round 1 (`02c320d6`) rated all three fixes Clear-satisfied, with CI 7/7
green, and raised four low-severity findings. The owner chose to fix all four in this PR:

- Returning focus to a card after its drawer closes fired the card's focus preview, leaving the
  closed item highlighted. A `restoringFocus` guard now skips the preview.
- Blockers entries had no `data-id`, so focus fell back to the whole map. They now carry
  `data-id` (and no `data-state`, so the Blockers tab gains no filters).
- The map fallback now uses `focus({ preventScroll: true })`, and the focused map draws no
  outline.
- The HEAD 404 test dropped a `read() == b""` check that `http.client` makes unfalsifiable, and
  explains that `Content-Length` is the signal.

Fix commit: `664081938e639d1054f5ad92e22f0f0fbd5cdb51`.

# Validation

- `scripts/format --check --diff`, `scripts/lint`: pass.
- `scripts/test`: OK after each round (2134 tests in round 1).
- New tests: a JSON `data-unmet` round trip with an ID containing a space; HEAD 404 with no body
  for both disabled scripts (confirmed failing against the unfixed `serve.py`); script checks that
  the filter parses JSON and that focus moves before the drawer hides.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Confirm-fixes with a substitute cold review, since hosted bots review only the first push.
- The backlog entry above, for the layout redesign.

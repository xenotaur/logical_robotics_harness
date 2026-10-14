---
execution_id: 2026_10_14_23_48_13_LRH_CONSOLE_MAP_OUTLINE_LAYOUT_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT:LRH_CONSOLE_MAP_OUTLINE_LAYOUT_REVIEW)[2026-10-14T23:48:13+00:00]
work_item: WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/842
commit:
created_at: 2026-10-14T23:48:13+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/842
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers review-response round 1 for PR #842 (`WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`), run as part of `/lrh-land` inside `/lrh-execute`. It also covers the owner's comparison of both layouts. CI passed 8/8 on the first push, `61b97bb7`. Copilot left two threads and Codex one, all valid.

# Result

**The owner's comparison, in LRH Console after Server > Restart, quoted:**

1. "Switching between grid and outline works. Event and SF have the longest chains I think"
2. "More is visible with Done off"
3. "Looked at LRH too."
4. Their take:
   - "The outline is more readable than the grid."
   - Both layouts are hard to read where lines overlap: "in outline view some boxes have inputs on the left and right." They suggested revisiting the right-angle language, separate input and output ports, or color.
   - "indentation is good but it's a bit strange the cards get smaller. I'd rather see the cards remain the same size, even if the lane has to get wider (up to some limit)."
   - Many crossing right-angled lines: "This is why we had curved lines in the prototype I think."
   - "Sometimes you can follow the lines, sometimes not ... Even hovering doesn't seem to help."
   - They also asked where "Show on map" was. It appears only on the Table and Blockers tabs; the owner then found it and called it "very useful".
5. "Outline is my favorite so far."

**The owner approved splitting the work:**

- **In this PR:**
  - the cycle fix;
  - full-width cards;
  - Outline as the default, recorded as the owner's decision.
- **Filed separately:** the line drawing, as `WI-LRH-CONSOLE-MAP-EDGE-READABILITY`. Curved lines were decided against together, so revisiting them is "a whole conversation".

**Threads:**

1. **Copilot and Codex P2 (cycle broken at a card not on the cycle):** valid. The pre-push fix broke a stall at the first remaining card by ID, which could be a card that only depends on the cycle. It now breaks at the first card by ID that can reach itself through unplaced prerequisites (`_on_cycle`). A test uses the bots' case: X and Y in a cycle, with an earlier-sorting A depending on X.
2. **Copilot (owner comparison and default decision):** settled.
   - `DEFAULT_LAYOUT` is now the outline, and Grid stays reachable at `?layout=layered-grid`.
   - The decision is recorded in the visual-language proposal ("Default map layout", `updated_on: 2026-10-14`) and in `layout.py`.
   - `serve.md` is updated to match.

**Owner-approved change:** cards keep their full width. A lane now widens by the deepest indent it uses, at most four levels. Lines between cells are computed as if each card spans its column, with the end steps extended along the card's own row to its real edge, so a shallow card in a widened lane still routes outside the column. The crossing test covers that case.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2329 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-MAP-EDGE-READABILITY`: `prompt_ready: yes`.

# Follow-up

- Confirm-fixes with a substitute cold review.
- The owner re-checks the full-width cards and the Outline default.
- `WI-LRH-CONSOLE-DESKTOP-ZOOM` (View > Zoom In / Out / Actual Size, with ⌘=, ⌘− and ⌘0) was proposed to the owner; it is not filed yet.

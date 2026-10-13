---
execution_id: 2026_10_12_22_56_37_LRH_CONSOLE_MAP_FILTER_COLLAPSE_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE:LRH_CONSOLE_MAP_FILTER_COLLAPSE_REVIEW)[2026-10-12T22:56:37+00:00]
work_item: WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit:
created_at: 2026-10-12T22:56:37+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers review-response round 1 for PR #835 (`WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE`), run as part of `/lrh-land` inside `/lrh-execute`. CI passed 8/8 on the first push, `11a79a63`. Copilot left three threads and Codex left one, all valid. The owner approved fixes 2 to 4. Thread 1 waits on the owner's Mac check.

# Result

1. **Copilot (owner check pending):** valid. Acceptance criterion 4 needs the owner's check in LRH Console on LCATS `worldcon-2026` with Done hidden. The owner's notes will be recorded when they arrive. It is not claimed met here.
2. **Copilot (self-review link):** the `AD_HOC` `_SELFREVIEW` record now has `rerun_of: 2026_10_12_21_21_39_LRH_CONSOLE_MAP_FILTER_COLLAPSE`, so closeout treats it as a side record.
3. **Copilot (table caption):** the caption now says the table shows items the filters show, plus items a shown item still needs and items from outside the view.
4. **Codex P2 (tracing across hidden items):** a real bug.
   - **Cause:** the script built its upstream/downstream graph from the drawn lines. A filter that hides the middle of a chain (A → D (done) → C) removed both lines, so clicking A no longer reached C, while `?item=A` on the server did.
   - **Fix:** the map now carries every edge as a JSON `data-edges` attribute, and `readEdges` traces from it, falling back to the lines. Highlighting still applies only to what is drawn.
   - **Tests:** one for the A → D → C case, and script assertions.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2304 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Record the owner's Mac check.
- Confirm-fixes with a substitute cold review, since hosted bots review only a PR's first push.

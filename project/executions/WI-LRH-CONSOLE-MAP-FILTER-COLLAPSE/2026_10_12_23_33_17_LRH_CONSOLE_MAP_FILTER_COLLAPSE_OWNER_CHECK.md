---
execution_id: 2026_10_12_23_33_17_LRH_CONSOLE_MAP_FILTER_COLLAPSE_OWNER_CHECK
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE:LRH_CONSOLE_MAP_FILTER_COLLAPSE_OWNER_CHECK)[2026-10-12T23:33:17+00:00]
work_item: WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit:
created_at: 2026-10-12T23:33:17+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the owner's LRH Console check for PR #835 (`WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE`, acceptance criterion 4) and the two changes it led to. The owner ran the check on the branch code at `e633dd06`, after Server > Restart.

# Result

**The owner's check, quoted:**

1. "Done works as expected and so do the other toggles! Good job."
2. "Changing filters works as expected - selected cards do not disappear"
3. "Hiding done hide SOME of the Done items in the table, but not all of them." The example was `WI-ASSESS-0031` ("Outside this view", Done). "Is this expected?"
4. "In the LRH console map, hiding Done makes all the lines go away. Upstream and downstream cards don't seem to highlight. Yes, that's confirmed, they do not highlight."
5. "Reload on filter change is very fast and smooth, other than the missing lines."

**Diagnosis:**

- **Item 3:** the table always kept rows for items outside the view, a choice made in response to the pre-push review. `WI-ASSESS-0031` is a prerequisite of `WI-EVENT-0030` from outside this view.
- **Item 4:** the data was correct. On the map the app reads (the main LRH checkout), the four cards left with Done hidden have no dependencies between them. Each has 3 or 4 prerequisites, all Done and hidden. There were no lines to draw and no visible upstream to highlight, but nothing on the page said so.

**Changes the owner approved:**

- **Outside rows:** the table now filters rows for items outside the view too. The note counts them separately, for example "Hidden: 39 Done, plus 7 from outside the view." The table caption is updated to match.
- **Hidden upstream:**
  - a card whose in-view prerequisites are hidden shows "+N upstream hidden by filters", next to the existing "+N outside this view" marker;
  - the drawer's Upstream and Downstream rows add "(N hidden by filters)".

**Agent check in the built-in browser:**

- **LRH `lrh-console-l1` with Done hidden:**
  - the cards show +4, +4, +4 and +3 upstream hidden;
  - the drawer reads "Upstream: 4 items (4 hidden by filters)".
- **LCATS table with Done hidden:**
  - 11 rows, none Done, and `WI-ASSESS-0031` is gone;
  - the note reads "Hidden: 39 Done, plus 7 from outside the view."

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2306 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- The owner re-checks items 3 and 4.
- Confirm-fixes for this round.

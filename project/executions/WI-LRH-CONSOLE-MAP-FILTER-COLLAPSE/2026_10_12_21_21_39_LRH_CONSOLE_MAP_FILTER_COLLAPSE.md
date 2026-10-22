---
execution_id: 2026_10_12_21_21_39_LRH_CONSOLE_MAP_FILTER_COLLAPSE
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE:LRH_CONSOLE_MAP_FILTER_COLLAPSE)[2026-10-12T20:58:19+00:00]
work_item: WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit: 4d4efd8751909bd8f6d53446ccbfc24b33771f22
created_at: 2026-10-12T21:21:39+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` under `/lrh-execute`, with the run plan approved by the owner. Filters move to the server, so hiding a state lays the dependency map out again without those cards.

# Result

- **`render.py`:**
  - `parse_hide` reads `?hide=` and keeps only known states.
  - `_visible` keeps the selection, plus any unfinished item a visible card needs, at any depth.
  - `_filtered` gives the layout only the visible items, dropping lanes and phases the filter emptied.
  - The table and the narrow-screen list are filtered. The table keeps rows for items outside the view.
  - `_filters` renders the Show toggles as links, plus a note with **Show all**.
  - Every in-page link now goes through `_Links`, so it keeps `hide`.
  - The unused `data-state` and `data-unmet` attributes are removed.
- **`serve.py`:** passes `hide` to the renderer.
- **`lrh-interactive.js`:**
  - in-place hiding is removed;
  - `syncLinks` covers the filter links;
  - the selected card or list entry is scrolled into view on load.
- **Docs:** `docs/reference/cli/serve.md` documents `?hide=`.
- **Browser check:** LCATS `worldcon-2026` with Done hidden went from 50 cards in 5 lanes (1948 × 3618 px) to 11 cards in 4 lanes (1596 × 932 px). Selecting a done card and then hiding Done kept the card, its drawer and the selection.
- **Pre-push self-review:** 5 Low findings, all fixed in `a7a93550`. See the `AD_HOC` `_SELFREVIEW` record.
- **Pending:** the owner's check in LRH Console. Separately, the drawer covering the rightmost lane at about 1024 px is noted for later; it predates this change.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: all pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`, after the owner's check.

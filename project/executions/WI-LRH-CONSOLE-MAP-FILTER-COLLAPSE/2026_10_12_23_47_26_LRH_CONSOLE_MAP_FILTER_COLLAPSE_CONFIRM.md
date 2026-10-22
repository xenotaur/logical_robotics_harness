---
execution_id: 2026_10_12_23_47_26_LRH_CONSOLE_MAP_FILTER_COLLAPSE_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE:LRH_CONSOLE_MAP_FILTER_COLLAPSE_CONFIRM)[2026-10-12T23:47:26+00:00]
work_item: WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit: 4d4efd8751909bd8f6d53446ccbfc24b33771f22
created_at: 2026-10-12T23:47:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers confirm-fixes for PR #835 (`WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE`), run as part of `/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so cold-context substitute reviews checked each later round.

# Result

- **Round 1 (`11a79a63..e633dd06`, bot threads):** the substitute review found the self-review link, table caption and tracing threads Clear-satisfied, and those three were resolved.
  - The Codex tracing fix was also checked in the built-in browser on LCATS `worldcon-2026` with Done hidden. Client tracing after a click matched the server's `?item=` rendering on the cards compared.
  - No card in the real data has a hidden item between two shown ones, so only the unit test exercises that exact case.
  - Two Low notes were left as is: unresolved edges in `data-edges` have no visible effect, and the script's tests check strings rather than behavior.
- **Owner check (round 2, `e633dd06..97fa6be8`):**
  - the owner's items 3 and 4 led to filtering outside table rows, and to the "+N upstream hidden by filters" marker with drawer counts;
  - a substitute review found no High or Medium issues;
  - the owner's re-check passed both, so acceptance criterion 4 is met;
  - the Copilot thread about the owner check was resolved.
- **Small fixes (round 3, `97fa6be8..7fde475e`):** the owner chose to fix the five Low points from round 2 (wording, tooltip, "1 item", caption, four tests). A quick substitute review found all five clearly addressed.
- **Remaining nits, not changed:**
  - a `title` tooltip is reachable by mouse only, and it is supplementary;
  - `test_hidden_upstream_counts_every_depth` checks card order, so a future layout change could break it.
- **Threads:** all review threads are resolved.

# Validation

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2310 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- CI is checked on the final head before the merge ask.

# Follow-up

- The drawer covering the rightmost lane at about 1024 px predates this PR and remains a follow-up candidate.

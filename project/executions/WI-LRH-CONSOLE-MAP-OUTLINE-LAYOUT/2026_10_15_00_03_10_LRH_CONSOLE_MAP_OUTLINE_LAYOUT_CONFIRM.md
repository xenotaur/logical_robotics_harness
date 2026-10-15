---
execution_id: 2026_10_15_00_03_10_LRH_CONSOLE_MAP_OUTLINE_LAYOUT_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT:LRH_CONSOLE_MAP_OUTLINE_LAYOUT_CONFIRM)[2026-10-15T00:03:09+00:00]
work_item: WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/842
commit:
created_at: 2026-10-15T00:03:10+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/842
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers confirm-fixes for PR #842 (`WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`), run as part of `/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so cold-context substitute reviews checked each later round.

# Result

**Round 1, at `17ae67a1`.** The first substitute review found three problems:

- The cycle-break threads (Copilot and Codex P2) were only **Partial**. The fix broke a stall at a card on *any* cycle, so when one cycle depended on another, the dependent cycle could be placed above the one it needs. The implementing session reproduced it: A and B in one cycle, C and D in another, and A needing C.
- The criterion-3 thread was Partial because the PR description was stale.
- `docs/reference/cli/dependency-map.md` still called `layered-grid` the default.

The cycle finding triggered the run's **stop condition**. The owner chose option A: amend the stop condition and finish in this PR.

**Round 2, at `99043c1e`.**

- `_cycle_to_break` now breaks at a card in a cycle whose unplaced prerequisites all lie on that cycle. Such a cycle is a sink among the unplaced cards' strongly connected components. A two-cycle test was added.
- `dependency-map.md` now describes both layouts, with Outline as the default.
- The PR description now records the owner's comparison and decision.
- The `_REVIEW` record carries a correction note.

**Re-check, at `99043c1e`.** All three findings are Clear-satisfied.

- **Proof:** the reviewer gave a proof that a sink cycle always exists, and that only edges inside a single cycle can point upward.
- **Fuzz:** 400 random maps (crossings plus cycle order) and 20,000 random graphs run against `_cycle_to_break` itself, with 0 failures.
- **Old logic:** the new test fails against the old logic.

Two Low record inaccuracies were fixed in this commit:

- this `_CONFIRM` record now exists, so the `_REVIEW` record's reference to it resolves;
- the primary record notes that review made the outline the default, so its "Grid · Outline" toggle text describes the implementation round only.

**Threads:** all six are resolved.

**Owner checks:**

- The comparison, after which the owner chose the outline as the default.
- A re-check: "Map opens in Outline! Woo. And the full-width cards look great".

# Validation

- `scripts/test`: 2330 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- CI is checked on the final head before the merge ask.

# Follow-up

At closeout, file `WI-LRH-CONSOLE-DESKTOP-ZOOM` and `WI-LRH-CONSOLE-DESKTOP-RESTART-SHORTCUT`, as the owner requested. `WI-LRH-CONSOLE-MAP-EDGE-READABILITY` is already filed in this PR.

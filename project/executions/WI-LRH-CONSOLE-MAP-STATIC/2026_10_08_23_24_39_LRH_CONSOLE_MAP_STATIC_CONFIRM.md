---
execution_id: 2026_10_08_23_24_39_LRH_CONSOLE_MAP_STATIC_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-STATIC:LRH_CONSOLE_MAP_STATIC_CONFIRM)[2026-10-08T23:24:39+00:00]
work_item: WI-LRH-CONSOLE-MAP-STATIC
status: in_progress
rerun_of: 2026_10_08_19_04_48_LRH_CONSOLE_MAP_STATIC
pr: https://github.com/xenotaur/logical_robotics_harness/pull/800
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/800"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T23:24:39+00:00
---


# Summary

This record covers `/lrh-confirm-fixes` for PR #800 (`WI-LRH-CONSOLE-MAP-STATIC`), run inline from
`/lrh-land` after review-response round 1 (`4e24ba7a` and `5b5367f6`, record in `38924217`).

# Result

**Threads.** All 4 threads (3 from Copilot, 1 from Codex) were checked against the diff:

- the narrow-screen list keeps the flag, the outside-view count, and the empty-view message;
- `_unmet_needs` derives unmet needs from the edges;
- `dependency_map_head_status` builds the snapshot.

Each thread was resolved with `resolveReviewThread`.

**Substitute cold review of `f78797c7..38924217`** (the hosted bots reviewed only earlier
commits). Verdict: safe to merge, with no must-fix items. It confirmed:

- the HEAD exception mapping, including that `ViewDeclarationError` is not wrapped as a 500;
- the `_unmet_needs` fallback and missing-target logic;
- `_ready_text`;
- escaping;
- that the record is accurate and both new work items are ready.

Applied in this commit:

- **Should-fix:** `CARD_HEIGHT` 144, so a highlighted card's 2px border cannot clip the third
  title line.
- **Should-fix:** closed items list no unmet needs.
- **Should-fix:** `WI-LRH-CONSOLE-STATUS-SHAPES` now gives Abandoned a muted fill and a
  struck-through title, instead of a dotted border too close to Blocked's dashed one.
- **Should-fix:** `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` now frames lane scope and phase rows as
  open questions for the owner, and says "decide the default" rather than "make it the
  default".
- **Nits:** de-duplicated table IDs, a re-wrapped `serve.md` line, and the closed-readiness test
  now asserts the drawer and the table row separately.

Left as a nit: `_unmet_needs` scans the edges for each node, which is fine at current sizes.

# Validation

- `scripts/format --check --diff` and `scripts/lint` pass.
- The render and serve tests pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Next is CI on the commit that carries this record, then the single ask for merge and closeout.

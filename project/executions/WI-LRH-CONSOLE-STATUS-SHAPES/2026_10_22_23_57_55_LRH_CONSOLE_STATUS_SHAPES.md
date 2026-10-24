---
execution_id: 2026_10_22_23_57_55_LRH_CONSOLE_STATUS_SHAPES
prompt_id: PROMPT(WI-LRH-CONSOLE-STATUS-SHAPES:LRH_CONSOLE_STATUS_SHAPES)[2026-10-17T19:36:28+00:00]
work_item: WI-LRH-CONSOLE-STATUS-SHAPES
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/852
commit: bf8f6fb6d01bbb2fc914a3d9ba83d5744829738c
created_at: 2026-10-22T23:57:55+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/852
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-STATUS-SHAPES` under `/lrh-execute`, with the run plan approved by the owner. The owner also approved striking the Abandoned pill label, which extends the work item's card-only treatment to pills shown without cards.

# Result

- **`render.py`:**
  - `PILL_SHAPES`: Unblocked is `outlined`, Abandoned is `struck`, every other state is `filled`.
  - `_pill` adds `lrh-pill--{shape}` and wraps a struck label in `lrh-pill-struck`.
  - Outlined pills have a transparent fill and a doubled ring (inset box-shadow).
  - `lrh-card--abandoned` gives a sunken fill and a struck-through title.
  - Blocked cards' dashed border is 2px in the Blocked line hue.
  - The legend explains the card treatments.
- **`serve.py`:** the style specimen gains shapes and an Abandoned example (`_specimen_pill`, a four-field `_SPECIMEN_STATES`).
- **Tests:** `render_test`, `serve_test` and `tokens_test`.
- **Docs:** `docs/reference/cli/serve.md`, and the Color vision (Q12) section of the visual-language proposal.
- **Owner check on the branch build, in light and dark:**
  - Both pairs are distinguishable on the specimen and on the LCATS and LRH maps.
  - In progress and Unblocked are "less easy" in the sunken row and in dark mode, but still distinguishable.
  - State cycling is fine.
  - The owner found Blocked's 1px dashes hard to see, a pre-existing issue, and chose to fix them here (2px in the Blocked hue). The owner also chose the doubled Unblocked ring, and confirmed both after a server restart.
  - The owner asked whether Unblocked items staying visible under a filter was intended. They stay when a visible Waiting item still needs them, which is the filter's documented design.
  - No real map shows an Abandoned card, so the specimen stood in.
- **Pre-push self-review:** two visibility questions went to the owner, and three Low items were fixed. See the `AD_HOC` `_SELFREVIEW` record.

# Validation

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2364 OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`.

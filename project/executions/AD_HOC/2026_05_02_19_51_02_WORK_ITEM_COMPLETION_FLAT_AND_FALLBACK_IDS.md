---
execution_id: 2026_05_02_19_51_02_WORK_ITEM_COMPLETION_FLAT_AND_FALLBACK_IDS
prompt_id: PROMPT(AD_HOC:WORK_ITEM_COMPLETION_FLAT_AND_FALLBACK_IDS)[2026-05-02T15:30:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 7926567
created_at: 2026-05-02T19:51:02+00:00
---

# Summary

Implemented a focused completion-provider fix so work-item ID discovery supports
both flat and nested Markdown layouts under `project/work_items/`, with quiet
fallback extraction from frontmatter `id` -> H1 `WI-*` -> filename stem `WI-*`.

# Result

Updated `work_item_ids` discovery to scan `project/work_items/*.md` and
`project/work_items/**/*.md` with deterministic, deduped sorting and prefix
filtering. Added conservative `WI-*` matching and malformed-frontmatter-safe
fallback behavior without changing runtime validation semantics. Added focused
unit tests covering flat layout, nested layout, fallback precedence, dedupe,
prefix filtering, malformed file handling, and missing-directory behavior.

# Validation

- `python -m unittest tests/cli_tests/completion_sources_test.py` (pass)
- `scripts/test` (pass)
- `scripts/lint` (fails: repository-wide black check currently failing)

# Follow-up

- Investigate and resolve repository-wide `black --check` failures surfaced via
  `scripts/lint` so lint gate can pass cleanly end-to-end.

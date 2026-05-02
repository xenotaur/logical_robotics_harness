---
execution_id: 2026_05_02_00_36_48_COMPLETION_PROVIDERS
prompt_id: PROMPT(AD_HOC:COMPLETION_PROVIDERS)[2026-04-29T12:11:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-02T00:36:48+00:00
---

# Summary

Added framework-neutral completion providers for LRH request template names and project work-item IDs, then connected the providers to the current argcomplete adapter without placing argcomplete-specific signatures in provider logic.

# Result

- Added `src/lrh/cli/completion_sources.py` with deterministic, sorted, prefix-filtered providers.
- Wired request parser positional arguments so `template_name` and codex work-item `target` use adapter completers.
- Added tests for provider behavior and adapter delegation.
- Updated README completion docs with `lrh request <TAB>` and `lrh request codex_prompt_from_work_item WI-R<TAB>` examples.

# Validation

- `scripts/test` (pass)
- `scripts/lint --fix` (pass)

# Follow-up

Regenerated PR branch after prior merge errors; no behavior change intended.

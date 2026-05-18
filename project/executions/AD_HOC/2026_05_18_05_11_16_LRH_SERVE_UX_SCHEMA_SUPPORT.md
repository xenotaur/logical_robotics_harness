---
execution_id: 2026_05_18_05_11_16_LRH_SERVE_UX_SCHEMA_SUPPORT
prompt_id: PROMPT(AD_HOC:LRH_SERVE_UX_SCHEMA_SUPPORT)[2026-05-16T00:14:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-18T05:11:16+00:00
---

# Summary

Added a focused UX schema/support package for future `lrh serve` dashboard work. The package defines a dashboard operational status vocabulary, human-facing badge metadata, deterministic operational lane ordering, meta-dashboard/project/evidence/validation view models, and conservative status derivation helpers.

# Result

- Added `src/lrh/ux/dashboard.py` and package scaffolding for reusable dashboard contracts.
- Added operational statuses: `needs_attention`, `active_work`, `awaiting_review`, `stable`, `blocked`, and `unknown`, with labels matching the LRH Console visual-language proposal.
- Added `OperationalStatusInputs` and `derive_operational_status()` with unknown fallback and conservative handling for validation findings, blockers, review-waiting work, active work, and explicitly steady projects.
- Added typed view models for meta dashboard lanes, project cards, status badges, evidence summaries, validation summaries, and project inspector support.
- Added `src/lrh/ux/README.md` documenting that this layer supports future Alternative D / enhanced swimlane dashboard adoption but does not implement the full UI, a frontend framework, mutating routes, or broad serve refactors.
- Serve integration was explicitly deferred because adopting these contracts in the current single-file viewer would require a broader rendering/API refactor than this semantic support PR needs.

# Validation

- `scripts/version tools` completed; pylint is not installed in this environment, while Ruff and Black are available.
- `python -m unittest tests.ux_tests.dashboard_test` passed.
- `lrh validate` passed with 0 errors and 0 warnings.
- `scripts/test` passed.
- `scripts/lint` passed.
- `scripts/format --check` passed after formatting the new module.

# Follow-up

- Wire `lrh serve` meta/project dashboard rendering and JSON APIs to these view models in a follow-up that can intentionally refactor the existing renderer.
- Add richer evidence freshness and last-validation timestamps once the control-plane/runtime model exposes that data directly.

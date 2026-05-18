---
execution_id: 2026_05_18_04_44_19_IMPLEMENT_READY_WORK_ITEM_REQUEST
prompt_id: PROMPT(WI-REQUEST-READY-WORK-ITEM-MVP:IMPLEMENT_READY_WORK_ITEM_REQUEST)[2026-05-17T02:05:00-04:00]
work_item: WI-REQUEST-READY-WORK-ITEM-MVP
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T04:44:19+00:00
---

# Summary

Implemented the `lrh request ready-work-item <WORK_ITEM_ID>` MVP. The command renders a
non-mutating, package-template-backed refinement request for a thin work item, reusing the existing
`prompt-from-work-item` readiness diagnostics from `evaluate_prompt_readiness` and resolving nearby
frontmatter context where practical.

# Result

Added the canonical `ready-work-item` request with no legacy aliases. Dogfooding against
`WI-ASSIST-INSTALLABILITY-HARDENING` rendered a not-ready diagnosis with missing `Scope`, `Required
Changes`, and `Validation` diagnostics, plus resolved context for `ROADMAP-PHASE-02` and dependency
`WI-ASSIST-TEMPLATES-PACKAGING`. The dogfood output was written to `/tmp/ready_work_item_dogfood.md`
during validation and was not committed as a project artifact.

# Validation

- `scripts/version tools` passed.
- `scripts/test` passed: 535 tests after review fixes.
- `scripts/lint` passed.
- `scripts/format --check` passed.
- `lrh work-items validate` passed with 0 errors and 0 warnings.
- `lrh work-items audit --format md` passed and was written to `/tmp/lrh_work_items_audit.md` during validation.
- `lrh request ready-work-item WI-ASSIST-INSTALLABILITY-HARDENING` passed and rendered the expected dogfood request.
- `lrh validate` passed with 0 errors and 0 warnings.

# Review Follow-up

Review fixes constrained direct referenced-context paths to the project root, nested referenced-context headings under the template heading, switched the source wrapper to a four-backtick fence, and reset this execution record to `in_progress` pending merge metadata.

# Follow-up

- Keep `lrh work-items readiness` as the separate deterministic readiness CLI work item.
- Do not implement installability hardening or resolve `WI-ASSIST-INSTALLABILITY-HARDENING` in this PR.

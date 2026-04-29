---
execution_id: 2026_04_28_21_44_22_REFINE_FOR_CODEX_IMPLEMENTATION
prompt_id: PROMPT(WI-RELEASE-TAG-CI:REFINE_FOR_CODEX_IMPLEMENTATION)[2026-04-27T20:55:00-04:00]
work_item: WI-RELEASE-TAG-CI
status: landed
rerun_of:
pr:
commit:
created_at: 2026-04-28T21:44:22+00:00
---

# Summary

Refined `WI-RELEASE-TAG-CI` to be prompt-generation ready by adding concrete `Required Changes` and `Validation Commands` sections, including tag-trigger YAML and guidance to use the pushed tag name (`github.ref_name`) for release checks.

# Result

Updated only the targeted work item content and did not implement any GitHub Actions workflow or publishing behavior. Scope remains restricted to release-tag CI definition and explicitly keeps PyPI/TestPyPI publishing out of scope.

# Validation

- `lrh validate` (pass)
- `scripts/format --check` (fails due to pre-existing formatting issue in `tests/control_tests/parser_test.py`)
- `scripts/lint` (fails because it includes black check and reports the same pre-existing formatting issue)
- `scripts/test` (pass)

# Follow-up

- Implement the release-tag workflow in a separate implementation PR linked to this work item.
- Resolve existing Black formatting drift in `tests/control_tests/parser_test.py` outside this documentation-focused change.

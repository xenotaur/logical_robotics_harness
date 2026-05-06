---
execution_id: 2026_05_06_18_23_44_ADD_BUILD_RELEASE_SMOKE_SCRIPTS
prompt_id: PROMPT(AD_HOC:ADD_BUILD_RELEASE_SMOKE_SCRIPTS)[2026-05-05T23:26:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T18:23:44+00:00
---

# Summary

Refine LRH local build and installed-wheel release-smoke coverage for maintainers preparing release artifacts.

# Result

Updated release-smoke to check built `dist/` artifacts with `twine check`, then install the built wheel in a temporary venv and smoke installed CLI help for `lrh`, `lrh validate`, `lrh request`, `lrh snapshot`, and `lrh survey`. Added `twine` to development tooling dependencies and updated the release-smoke documentation in `README.md` and `scripts/README.md`.

# Validation

- `scripts/version tools` passed for the expected Black and Ruff versions.
- `python -m unittest tests.dev_tests.release_smoke_test` passed.
- `scripts/release-smoke --help` passed.
- `scripts/format --check` passed.
- `scripts/test` passed.
- `scripts/lint` passed.
- `lrh validate` passed.
- `scripts/build` was attempted, but the isolated build dependency installation failed because package-index access returned tunnel `403 Forbidden` while resolving build-system requirements such as `wheel`/`setuptools-scm>=8`.
- `scripts/release-smoke` was attempted, but failed at the same isolated `scripts/build` step before reaching `twine check` or installed-wheel CLI smoke checks.

# Follow-up

Re-run `scripts/build` and `scripts/release-smoke` in a bootstrapped environment with package-index/build dependency access available. No publishing workflows or package publishing were added.

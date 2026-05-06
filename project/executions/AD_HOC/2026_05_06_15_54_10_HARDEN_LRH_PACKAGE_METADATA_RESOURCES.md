---
execution_id: 2026_05_06_15_54_10_HARDEN_LRH_PACKAGE_METADATA_RESOURCES
prompt_id: PROMPT(AD_HOC:HARDEN_LRH_PACKAGE_METADATA_RESOURCES)[2026-05-05T23:25:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-06T15:54:10+00:00
---

# Summary

Harden LRH package metadata and installed-package resource prerequisites for future PyPI publishing without adding publishing workflows or package-splitting changes.

# Result

Updated `pyproject.toml` so the intended distribution name is `lrh`, the existing console script remains wired to `lrh.cli.main:main`, project metadata is more PyPI-ready, and package data explicitly includes runtime assist templates and project-bootstrap templates. Updated runtime version lookup and release-smoke diagnostics to use the `lrh` distribution name. Added packaging metadata tests and extended installed smoke coverage to verify runtime resources load from the installed package.

# Validation

- `scripts/version tools`
- `scripts/test tests/packaging_tests/metadata_test.py`
- `scripts/test tests/dev_tests/release_smoke_test.py`
- `scripts/test tests/cli_tests/request_test.py`
- `scripts/test tests/assist_tests/request_templates_test.py`
- `scripts/test tests/assist_tests/template_resolver_test.py`
- `scripts/format --check`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `scripts/smoke` completed with smoke tests skipped because build dependencies were unavailable through the environment package index.
- `scripts/smoke_assist_install` could not build because installing build dependencies failed with package-index 403 errors for `setuptools>=68`.

# Follow-up

No publishing workflow, TestPyPI/PyPI publication, package split, or `agentic` extra was added. Re-run installed-package smoke checks in a bootstrapped environment with build dependencies available before release.

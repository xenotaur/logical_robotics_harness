---
execution_id: 2026_08_05_21_30_12_VERSION_INSTALL_SMOKE_YAML_DEPS
prompt_id: PROMPT(WI-VERSION-INSTALL-SMOKE-YAML-DEPS:VERSION_INSTALL_SMOKE_YAML_DEPS)[2026-08-05T21:28:45+00:00]
work_item: WI-VERSION-INSTALL-SMOKE-YAML-DEPS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/494
commit: 
created_at: 2026-08-05T21:30:12+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-VERSION-INSTALL-SMOKE-YAML-DEPS.md
session_transcript: claude-app:75bc649d-3851-4e5e-944a-822d6315d2ae
---

# Summary

Implemented `WI-VERSION-INSTALL-SMOKE-YAML-DEPS`: fixed
`tests/smoke/version_install_smoke.py`'s wheel-install case, which failed
on `main` with `ModuleNotFoundError: No module named 'yaml'` independent of
any other pending change.

# Result

Confirmed root cause: the wheel-install step ran
`pip install --no-input --no-deps <wheel>`, skipping the `PyYAML` runtime
dependency declared in `pyproject.toml`, which `lrh.cli.main`'s import
chain (`lrh.conversations.export_inspector`) requires unconditionally at
import time. Traced `--no-deps`'s history on both the wheel-build and
wheel-install commands back to the test's original introduction
(`WI-VERSIONING-HARDENING`'s `SETUPTOOLS_SCM_MIGRATION` execution record)
with no rationale recorded for the install-step instance, consistent with
an unintentional copy of the build-step flag.

Removed `--no-deps` from the wheel-install `pip install` call in
`tests/smoke/version_install_smoke.py`, leaving the separate
`pip wheel --no-deps` build-step call unchanged (it correctly scopes the
build to `lrh`'s own wheel). The install step now matches the
editable-install case earlier in the same test (a full `pip install -e .`,
no `--no-deps`).

# Validation

- `python -m unittest tests.smoke.version_install_smoke` — passes (both
  editable-install and wheel-install cases); previously failed with
  `ModuleNotFoundError: No module named 'yaml'` on the wheel-install case
- `lrh validate` — 0 errors, 0 warnings
- `scripts/format --check --diff` — clean, 188 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 953 tests, OK

# Follow-up

None.

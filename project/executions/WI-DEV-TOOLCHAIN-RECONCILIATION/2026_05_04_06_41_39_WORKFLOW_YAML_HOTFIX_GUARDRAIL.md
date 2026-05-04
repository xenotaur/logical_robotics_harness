---
execution_id: 2026_05_04_06_41_39_WORKFLOW_YAML_HOTFIX_GUARDRAIL
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:WORKFLOW_YAML_HOTFIX_GUARDRAIL)[2026-05-04T09:20:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: landed
rerun_of:
pr:
commit:
created_at: 2026-05-04T06:41:39+00:00
---

# Summary

Applied a focused workflow guardrail hotfix: added workflow YAML syntax checks, added a Meta CI workflow to run the check, and documented the new command.

# Result

- Added `scripts/check-workflows` to parse `.github/workflows/*.yml` and `.yaml` files with UTF-8 reads and `yaml.safe_load`.
- Added `.github/workflows/meta.yml` to run `scripts/check-workflows` on pull requests, pushes to `main`, and manual dispatch.
- Updated docs in `README.md` and `scripts/README.md` to include `scripts/check-workflows` guidance and note that `actionlint` remains deferred.
- Existing workflow files were inspected; no additional YAML syntax edits were required in this run.

# Validation

- `scripts/develop` (failed in this environment due to package-index/proxy access for build dependency resolution).
- `scripts/check-workflows` (failed before dependency install because `PyYAML` was not importable in this environment).
- `scripts/version tools` (passed).
- `scripts/format --check --diff` (passed).
- `scripts/lint` (passed).
- `scripts/test` (passed).

# Follow-up

Consider adding `actionlint` in a separate enhancement once this syntax-only guardrail is established in CI.

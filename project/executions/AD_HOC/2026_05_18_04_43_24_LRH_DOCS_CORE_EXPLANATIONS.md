---
execution_id: 2026_05_18_04_43_24_LRH_DOCS_CORE_EXPLANATIONS
prompt_id: PROMPT(AD_HOC:LRH_DOCS_CORE_EXPLANATIONS)[2026-05-17T02:14:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T04:43:24+00:00
---

# Summary

Added core human-facing explanation docs for LRH's purpose, control-plane model, precedence,
evidence-backed status, repository/runtime state boundary, prompt-driven workflow, and workspace/meta
model.

# Result

- Added seven explanation pages under `docs/explanations/`.
- Updated `docs/explanations/README.md` to list the new conceptual pages and restate that
  `project/` remains the authoritative control plane while `docs/` teaches and guides.
- Kept changes documentation-only and did not alter authoritative project design artifacts.

# Validation

- `scripts/version tools` passed before edits for package/CLI/Python/Ruff/Black/Pyright/pip checks;
  Pylint and Conda were reported as not installed by the script.
- `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:LRH_DOCS_CORE_EXPLANATIONS)[2026-05-17T02:14:00-04:00]" --project-root .` reported no existing execution records for this exact prompt ID before work began.
- `scripts/lint` passed Ruff and Black checks.
- `scripts/test` passed: 529 tests.
- `lrh validate` passed with 0 errors and 0 warnings.
- A local Python relative-link check over `docs/explanations/*.md` passed for 8 explanation Markdown files.

# Follow-up

- Keep this execution record `in_progress` while the PR is open; update it to `landed` with PR and
  commit metadata after the change lands.

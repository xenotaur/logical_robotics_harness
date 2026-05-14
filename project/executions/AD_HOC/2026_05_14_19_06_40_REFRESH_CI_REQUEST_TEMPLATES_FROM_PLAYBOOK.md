---
execution_id: 2026_05_14_19_06_40_REFRESH_CI_REQUEST_TEMPLATES_FROM_PLAYBOOK
prompt_id: PROMPT(WI-CI-REQUEST-TEMPLATES:REFRESH_CI_REQUEST_TEMPLATES_FROM_PLAYBOOK)[2026-05-14T00:20:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T19:06:40+00:00
---

# Summary

Refreshed LRH's CI assessment and implementation request templates so generated agent prompts apply the CI setup and debugging playbook instead of inventing one-off CI behavior.

# Result

- Updated `src/lrh/assist/templates/request/ci_assess_status.md` to reference `docs/project-setup/ci.md`, require project-family discovery, require canonical command discovery from scripts/docs/config, separate setup/bootstrap from validation, and demand evidence-backed CI diagnosis.
- Updated `src/lrh/assist/templates/request/ci_implement_workflow.md` to gate edits on the playbook, avoid universal workflow templates, require workflow YAML checks via `scripts/check-workflows` or the closest approved equivalent when workflows are touched, and defer stronger tooling unless explicitly requested or already canonical.
- Updated `src/lrh/assist/README.md` request-template guidance so the two CI request entries mention the CI playbook path.
- Used `AD_HOC` because no `project/work_items/**/WI-CI-REQUEST-TEMPLATES.md` work-item file exists yet; the ID is currently mentioned only as a proposed seed/follow-up in planning documents.

# Validation

- `python -m lrh.cli.main prompt check-execution --prompt-id 'PROMPT(WI-CI-REQUEST-TEMPLATES:REFRESH_CI_REQUEST_TEMPLATES_FROM_PLAYBOOK)[2026-05-14T00:20:00-04:00]' --project-root .` reported no prior exact execution records before changes.
- `scripts/version tools` passed and reported Python 3.12.13, Ruff 0.15.12, and Black 26.3.1.
- `scripts/check-workflows` passed for all GitHub workflow YAML files.
- `scripts/format --check --diff` passed with 141 files unchanged.
- `scripts/lint` passed.
- `scripts/test` passed with 476 tests.

# Follow-up

Consider adding a dedicated `WI-CI-REQUEST-TEMPLATES` work-item file if this CI request-template refresh line of work should be tracked outside the current AD_HOC execution record.

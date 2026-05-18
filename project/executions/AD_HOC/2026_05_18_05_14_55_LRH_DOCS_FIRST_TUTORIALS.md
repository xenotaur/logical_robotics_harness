---
execution_id: 2026_05_18_05_14_55_LRH_DOCS_FIRST_TUTORIALS
prompt_id: PROMPT(AD_HOC:LRH_DOCS_FIRST_TUTORIALS)[2026-05-17T02:15:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-18T05:14:55+00:00
---

# Summary

Added first-pass guided tutorials for the LRH documentation tutorial section:

- a minimal LRH project/control-plane validation and snapshot walkthrough;
- a lightweight prompt-driven change workflow walkthrough.

# Result

Created `docs/tutorials/first-lrh-project.md` and `docs/tutorials/first-prompt-driven-change.md`, then updated `docs/tutorials/README.md` to list both tutorials. The tutorials use implemented commands only and keep examples copy-paste friendly.

# Validation

- `scripts/version tools` passed before task-phase validation; Ruff `0.15.12` and Black `26.3.1` matched repository expectations.
- Manually walked through the first-project tutorial in a temporary directory: created `project/focus/current_focus.md`, ran `lrh validate --project-dir project`, and generated a snapshot with `lrh snapshot project --project-root . --output /tmp/my-first-lrh-project-snapshot.md`.
- Review feedback addressed: replaced source-checkout-only prompt helper examples with portable `lrh prompt label` and `lrh prompt record-execution --project-root .` examples, while noting repo-local wrappers for LRH maintainers.
- Review feedback addressed: corrected the rerun execution ID example to the documented `YYYY_MM_DD_HH_MM_SS_<SLUG>` format.
- Manually smoke-tested prompt workflow commands used in the prompt-driven tutorial: `lrh prompt label --slug improve-docs-example --project-root .`, `lrh prompt record-execution ... --project-root . --dry-run`, and the rerun `lrh prompt record-execution ... --rerun-of 2026_05_18_12_00_00_IMPROVE_DOCS_EXAMPLE --project-root . --dry-run`.
- Manually checked relative Markdown links in the new tutorial files and `docs/tutorials/README.md` with a small Python script.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` passed: 531 tests.
- `lrh validate --project-dir project` passed.

# Follow-up

No immediate follow-up required. Future tutorial work can add broader project-control examples once those workflows are intentionally documented as beginner-facing paths.

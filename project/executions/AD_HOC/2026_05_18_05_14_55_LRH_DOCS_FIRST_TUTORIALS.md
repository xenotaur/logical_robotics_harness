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
- Manually smoke-tested prompt workflow commands used in the prompt-driven tutorial: `scripts/prompts/label-prompt --slug improve-docs-example`, `lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .`, and `scripts/prompts/record-execution ... --dry-run`.
- Manually checked relative Markdown links in the new tutorial files and `docs/tutorials/README.md` with a small Python script.
- `scripts/lint` passed.
- `scripts/test` passed: 531 tests.

# Follow-up

No immediate follow-up required. Future tutorial work can add broader project-control examples once those workflows are intentionally documented as beginner-facing paths.

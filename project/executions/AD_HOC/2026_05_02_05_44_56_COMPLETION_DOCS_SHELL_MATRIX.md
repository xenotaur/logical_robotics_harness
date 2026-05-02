---
execution_id: 2026_05_02_05_44_56_COMPLETION_DOCS_SHELL_MATRIX
prompt_id: PROMPT(AD_HOC:COMPLETION_DOCS_SHELL_MATRIX)[2026-04-29T12:12:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-02T05:44:56+00:00
---

# Summary

Polished top-level completion documentation for LRH with shell-specific setup guidance, macOS bash caveats, expected completion examples, and troubleshooting notes while keeping scope to lightweight docs updates.

# Result

Updated `README.md` with an expanded command-line completion section covering:

- completion extra installation
- bash registration
- macOS bash version/path caveat and checks
- zsh registration (when supported by argcomplete)
- best-effort fish/PowerShell notes without support guarantees
- expected completion examples
- targeted troubleshooting checklist

# Validation

- `scripts/test` passed.
- `scripts/lint` reported a pre-existing Black formatting failure in `tests/control_tests/parser_test.py` unrelated to this documentation-only change.

# Follow-up

- Optional housekeeping PR: reformat `tests/control_tests/parser_test.py` so `scripts/lint` passes cleanly on this branch.

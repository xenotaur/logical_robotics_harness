---
execution_id: 2026_05_02_22_34_18_COMPLETION_DOCS_AND_INSTALL_HELPER
prompt_id: PROMPT(AD_HOC:COMPLETION_DOCS_AND_INSTALL_HELPER)[2026-05-02T16:00:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-02T22:34:18+00:00
---

# Summary

Polished completion-related CLI help text, refreshed completion quickstart documentation, and added a safe helper script that prints copy-paste completion setup commands without modifying user dotfiles.

# Result

- Updated `lrh`, `lrh request`, and `lrh work-items organize` help text with concise completion/README hints and legacy-repair context.
- Updated README completion guidance with explicit bash/zsh enable commands, macOS shell-version note, examples, and troubleshooting guidance including legacy work-item organization repair.
- Added `scripts/install-completion` helper that detects shell and prints setup/persistence instructions only.
- Added unit coverage for `scripts/install-completion` output basics.

# Validation

- `scripts/test`
- `scripts/lint --fix`
- `lrh --help`
- `lrh request --help`
- `lrh work-items organize --help`
- `scripts/install-completion`
- `python -m unittest tests/scripts_tests/install_completion_test.py`

# Follow-up

- Consider extending script-level tests to assert shell-specific registration output under simulated `bash`/`zsh` environments.

---
execution_id: 2026_05_07_05_53_07_VERSION_TOOLS_INSTALL_HINT
prompt_id: PROMPT(AD_HOC:VERSION_TOOLS_INSTALL_HINT)[2026-05-07T12:30:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-07T05:53:07+00:00
---

# Summary

Improved `scripts/version tools` diagnostics for missing LRH package metadata and/or unavailable `lrh` CLI in the active Python environment.

# Result

- Added LRH-specific version probing and read-only install hints that include the active Python executable, active pip command/path, `scripts/develop`, and the follow-up `scripts/version tools` command.
- Kept successful LRH package metadata and CLI output concise, and avoided install hints when both are known.
- Added focused unit coverage for both-unknown, metadata-known/CLI-unknown, CLI-known/metadata-unknown, and both-known cases.
- Added a short README note explaining how to treat the new `scripts/version tools` install hint during validation.

# Validation

- `scripts/version tools` passed.
- `scripts/test` passed.
- `scripts/lint` passed.
- `scripts/format --check` passed.
- `lrh validate` passed.

# Follow-up

None.

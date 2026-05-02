---
execution_id: 2026_05_01_23_28_43_ARGCOMPLETE_FOUNDATION
prompt_id: PROMPT(AD_HOC:ARGCOMPLETE_FOUNDATION)[2026-04-29T12:10:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/137
commit: d1c8f88
created_at: 2026-05-01T23:28:43+00:00
---

# Summary

Added a minimal argcomplete foundation for the LRH argparse CLI: optional packaging extra, `PYTHON_ARGCOMPLETE_OK` marker, a small no-op-safe adapter module, and parser wiring that enables completion after parser construction and before argument parsing.

# Result

Implemented completion scaffolding without changing command behavior. Added unit tests covering no-op behavior when `argcomplete` is unavailable, successful adapter invocation when present, and continued top-level CLI construction when `argcomplete` is missing. Updated top-level README with concise setup instructions and macOS Bash version note.

# Validation

- `scripts/test` (pass)
- `scripts/lint` (pass)

# Follow-up

- Add project-aware dynamic completion in a follow-up PR (request templates, work-item IDs, etc.).
- Add shell-specific completion docs/files only when richer completion behavior is added.

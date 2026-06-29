---
execution_id: 2026_06_29_00_34_43_CONVENTIONAL_COMMITS_DOC
prompt_id: PROMPT(AD_HOC:CONVENTIONAL_COMMITS_DOC)[2026-06-28T15:30:12-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: "352"
commit: 2e967b7
created_at: 2026-06-29T00:34:43-04:00
agent: claude_app
instruction_source: ad_hoc conversation — document Conventional Commits 1.0.0 in STYLE.md and AGENTS.md
session_transcript: pending
---

# Summary

Document the Conventional Commits 1.0.0 convention already in use in this repo.
Add a "Commit Message Format" section to STYLE.md and a one-sentence reference
in the "Engineering style" section of AGENTS.md.

# Result

- Added `## Commit Message Format` section to `STYLE.md` between "Pull Request
  Guidelines" and "Review Guidance", covering the `type(scope): description`
  format, six required types, optional scope, and breaking-change syntax with
  a citation to the Conventional Commits 1.0.0 spec.
- Added one bullet to the "Engineering style" section of `AGENTS.md` pointing
  to `STYLE.md` for the full format.
- PR [#352](https://github.com/xenotaur/logical_robotics_harness/pull/352) opened.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.15
- `scripts/format --check --diff` — 174 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 688 tests OK
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` when session ends.

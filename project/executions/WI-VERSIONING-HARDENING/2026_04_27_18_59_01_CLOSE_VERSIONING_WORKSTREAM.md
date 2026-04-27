---
execution_id: 2026_04_27_18_59_01_CLOSE_VERSIONING_WORKSTREAM
prompt_id: PROMPT(WI-VERSIONING-HARDENING:CLOSE_VERSIONING_WORKSTREAM)[2026-04-27T14:55:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-04-27T18:59:01+00:00
---

# Summary

Closed out versioning-workstream documentation and control-plane status updates around the now-working LRH release-tag workflow, including explicit `v0.2.2` examples and release-smoke positioning.

# Result

- Reviewed current work-item buckets and found no dedicated `WI-VERSIONING-HARDENING` work-item file to move between buckets.
- Updated top-level release/versioning docs (`README.md`, `scripts/README.md`) to reflect current workflow behavior and include `scripts/version push <tag>`.
- Added evidence note `project/evidence/EV-0002.md` recording successful local release-smoke + pushed `v0.2.2` tag context with appropriate maturity caveat.
- Updated `project/status/current_status.md` and `project/focus/current_focus.md` minimally to mark versioning hardening as complete and operational.

# Validation

- `scripts/format --check` (failed: repository currently has pre-existing Black drift in `tests/control_tests/parser_test.py`)
- `scripts/lint` (failed due Black check, same formatting drift)
- `scripts/test` (passed)
- `scripts/version` (passed; prints LRH package version from metadata)
- `scripts/release-smoke v0.2.2` (failed in this environment: isolated build env could not install `setuptools>=68` because network/index access for build bootstrap failed with repeated tunnel 403 errors)
- `python -m lrh.cli.main validate` (passed)

# Follow-up

- Re-run `scripts/format --check` and `scripts/lint` after resolving existing formatting drift in `tests/control_tests/parser_test.py`.
- Re-run `scripts/release-smoke v0.2.2` in an environment with build dependency installation access so end-to-end smoke can complete.

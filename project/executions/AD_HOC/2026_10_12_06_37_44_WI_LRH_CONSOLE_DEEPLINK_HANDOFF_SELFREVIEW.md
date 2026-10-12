---
execution_id: 2026_10_12_06_37_44_WI_LRH_CONSOLE_DEEPLINK_HANDOFF_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DEEPLINK_HANDOFF_SELFREVIEW)[2026-10-12T06:37:44+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_12_06_41_22_WI_LRH_CONSOLE_DEEPLINK_HANDOFF
pr: https://github.com/xenotaur/logical_robotics_harness/pull/833
commit:
created_at: 2026-10-12T06:37:44+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CONSOLE-DEEPLINK-HANDOFF.md
session_transcript: pending
---

# Summary

Diff-mode /lrh-self-review of the WI-LRH-CONSOLE-DEEPLINK-HANDOFF implementation, run before the first push (/lrh-implement Step 7.5). The diff was taken against this branch's fork point (9178953e), not the moving origin/main, so unrelated main drift was not reviewed.

# Result

Mode: diff-mode, report-only (no --apply). A cold general-purpose subagent reviewed the diff against the work item and found no blocking issues. It judged validate_session_link to have no bypass (every check runs on the parsed Url, validation and launch use the same Url, the shared JSON is parsed fail-closed), the existing http(s) path of LinkHandoff::offer unchanged in order and limiter use, and validate_url, is_external_link, new_window_response, capabilities/main-window.json and the CSP untouched.

Findings: 4 non-blocking observations, 1 acted on.

- Test safety (acted on): a_refused_link_is_never_launched called the real open_session_link, so a future loosening of the allowlist would have launched a real app before the assertion failed. Independently re-verified by the invoking session: validation does run before the launch today, but the test still used the real launcher. Fixed by adding open_session_link_with(url, launcher) and testing refused links with a launcher that panics and allowlisted links with a pretend launcher; no test can start an application now.
- Scheme case (documented, not changed): the Rust side accepts CLAUDE:// because the url crate lowercases the scheme and the opener receives the canonical form, while the Python helper compares raw text and rejects it. Harmless; pinned with a Rust test and noted in the code comment.
- Rate-limit test is timing-based and vacuous on a very slow machine (guarded by an elapsed-time check). Left as is.
- Rust is stricter than Python on the shared definition (schema_version must be 1, {id} exactly once, id_shape uuid), which is on the safe side.

Fixes applied: the test-safety change above (applied by the invoking session in the implementation workflow, after independent verification, not by the reviewer).

# Validation

Pinned dedicated conda env bound to this worktree: apps/desktop/scripts/run fmt --check, lint (clippy -D warnings) and test pass (library 83, capability boundaries 12, supervisor 23); scripts/format --check --diff, scripts/lint and lrh validate clean; scripts/test passes (2288 tests, re-run after the final Rust-only edit).

# Follow-up

rerun_of was empty at creation by construction (no primary record existed yet) and was backfilled with the primary record's execution id (2026_10_12_06_41_22_WI_LRH_CONSOLE_DEEPLINK_HANDOFF) once it existed, as was pr:. session_transcript is pending until closeout.

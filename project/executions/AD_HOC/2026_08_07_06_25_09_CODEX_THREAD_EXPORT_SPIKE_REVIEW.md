---
execution_id: 2026_08_07_06_25_09_CODEX_THREAD_EXPORT_SPIKE_REVIEW
prompt_id: PROMPT(AD_HOC:CODEX_THREAD_EXPORT_SPIKE_REVIEW)[2026-08-07T06:11:37+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/503
commit: 
created_at: 2026-08-07T06:25:09+00:00
agent: codex_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/503
session_transcript: pending
---

# Summary

Address automated review feedback on PR #503, the Codex app-server thread
export spike. The review surfaced six actionable comments against the
experimental app-server probe and findings documentation.

# Result

Fixed all six reported issues:

- Replaced the text-mode stdout reader with a binary JSONL reader that keeps
  its own user-space buffer, so notifications and responses emitted in one
  burst are not lost behind `select()`.
- Changed request waiting to use one overall deadline per JSON-RPC request
  instead of resetting the full timeout after unrelated messages.
- Let app-server stderr inherit from the parent process instead of using an
  unread pipe that could fill and deadlock the probe.
- Required `--raw-out` to be an absolute path outside the repository checkout.
- Wrote raw capture files through `os.open` / `os.fchmod` with mode `0600`.
- Updated the findings document's recommended raw envelope to reflect the
  captured JSON-RPC wrapper: `response.result.thread`.

Also removed trailing blank lines at EOF from the two files flagged by the
independent self-review pass.

# Validation

- `scripts/version tools` — reported Black `25.11.0` while the repository
  requires `26.3.1`; also reported Pyright missing. Treated as a local
  setup/cache mismatch rather than formatter evidence.
- `python -m py_compile experimental/save_codex_threads/probe_app_server_stdio.py
  experimental/save_codex_threads/inspect_read_thread_pages.py` — passed.
- `git diff --check` — passed.
- Targeted raw-output safety check — passed: `_write_raw_capture` forces mode
  `0600`, absolute `/private/tmp` paths normalize, and a repository-local
  `--raw-out` exits with `--raw-out must be outside this repository`.
- `lrh validate` — `Validation completed: 0 error(s), 0 warning(s)`.
- `scripts/test` — first sandboxed run failed with `PermissionError: [Errno 1]
  Operation not permitted` while tests attempted to bind local loopback HTTP
  servers; reran outside the sandbox boundary and passed: 993 tests OK.

# Follow-up

No additional follow-up from this review round beyond the backlog items already
recorded for experimental-code linkage linting and Codex executable trust /
signature investigation.

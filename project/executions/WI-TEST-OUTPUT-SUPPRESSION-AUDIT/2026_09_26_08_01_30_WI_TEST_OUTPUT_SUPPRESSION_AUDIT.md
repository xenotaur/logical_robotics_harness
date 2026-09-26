---
execution_id: 2026_09_26_08_01_30_WI_TEST_OUTPUT_SUPPRESSION_AUDIT
prompt_id: PROMPT(WI-TEST-OUTPUT-SUPPRESSION-AUDIT:WI_TEST_OUTPUT_SUPPRESSION_AUDIT)[2026-09-26T06:55:00+00:00]
work_item: WI-TEST-OUTPUT-SUPPRESSION-AUDIT
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/736
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-TEST-OUTPUT-SUPPRESSION-AUDIT.md
session_transcript: claude-app:42f65eea-a5d0-4b14-b12d-fdac79928916
created_at: 2026-09-26T08:01:30+00:00
---

# Summary

Implemented `WI-TEST-OUTPUT-SUPPRESSION-AUDIT`: a shared output-capture
helper, a STYLE.md policy, migration of all noisy/ad-hoc-pattern test
files, and a new `test_guardrails.py` check enforcing it going forward.

# Result

All five Required Changes completed:

1. `tests/testing_support.py` — `capture_output()`/`suppress_output()`
   context managers, ported from LCATS's `lcats.utils.capture`, including
   the `suppress_file_descriptors` option for real subprocess output.
2. `STYLE.md`'s Testing Principles section gained an "Output Hygiene"
   subsection with the explicit no-global-suppression-in-scripts/test
   constraint.
3. All 14 files using the ad hoc `io.StringIO()`+`contextlib.redirect_stdout`/
   `redirect_stderr` pattern (re-enumerated via `git grep -l 'redirect_stdout'
   -- 'tests/**/*_test.py'` at implementation time — 14, not the audit-time
   12, exactly the drift the work item's own Risk Notes anticipated)
   migrated to the shared helper.
4. Applied the helper to the three confirmed noisy files
   (`pii_test.py`, `secrets_test.py`, `release_smoke_test.py`) plus two
   more found by empirically re-running `scripts/test` after the above and
   checking what still leaked: `versioning_test.py` (4 unmocked-stdout
   `verify_release`/`create_tag`/`push_tag`/`main(["tools"])` calls) and
   `secrets_tests/purge_test.py` (1 unmocked `run_purge` call). Verified
   empirically both before and after: baseline `scripts/test` interleaved
   hundreds of noisy lines throughout the run; after this change, `scripts/test`
   produces only per-test dots, zero unexpected output.
5. Extended `src/lrh/control/test_guardrails.py` with an "Output Hygiene"
   AST check flagging an uncaptured `subprocess.run`/`check_call`/`call`
   not wrapped in `testing_support.suppress_output(suppress_file_descriptors=True)`.
   Running it against the full `tests/` tree once wired up found 8
   pre-existing, previously-undetected uncaptured `subprocess.run` calls
   (a `_run_git` helper repeated across 4 `pii_tests/*` files, one in
   `secrets_tests/purge_test.py`, three inline in `tests/cli_tests/memory_test.py`)
   — all fixed in this PR.

**Self-review (diff-mode, before first push) caught two real issues,
both fixed:**
- 5 sites where the ad-hoc-pattern migration left an unused `captured`
  binding (`F841`) because the original code never read the captured
  stream's content (only checked an exception's exit code) — switched
  those to bare `suppress_output()`. Plus one `E501` (docstring line) and
  3 files needing a black line-collapse after variable renames shortened
  lines below 88 chars. All independently re-verified via `ruff check
  --select E,F,I,TID` and `black --check` using the locally available
  (non-pinned but close) tool versions, since this machine's ruff/black
  are behind `pyproject.toml`'s pins (pre-existing, unrelated).
- A soundness gap in the new guardrail itself: it initially accepted a
  bare `suppress_output()`/`capture_output()` as sufficient cover for a
  subprocess call, but neither actually redirects a real child process's
  inherited file descriptors (only `contextlib.redirect_stdout`/
  `redirect_stderr`, which a subprocess writes past entirely) — verified
  experimentally (a real `subprocess.run` inside a plain `capture_output()`
  block still printed to the real terminal). Tightened the check to
  require `suppress_file_descriptors=True` specifically for subprocess
  calls, updated the 6 real call sites this PR added to match, and added
  two new guardrail tests locking in the distinction.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `scripts/test` — 1806 tests, OK, zero unexpected stdout/stderr output
  (baseline before this PR: hundreds of interleaved noisy lines).
- `scripts/test tests.guardrails_tests.test_framework_guardrails_test -v`
  — 10/10 OK, including the full-repo `test_all_repository_tests_comply_with_guardrails`
  check.
- `ruff check --select E,F,I,TID` / `black --check` on every changed file
  (locally available tool versions) — clean.
- `scripts/lint` / `scripts/format --check --diff` via the canonical
  scripts fail only on this machine's pre-existing, unrelated ruff/black
  version-pin mismatch (`0.15.0` vs. pinned `0.15.12`; `25.11.0` vs.
  pinned `26.3.1`) — not caused by, and invisible to CI relative to, this
  PR.

# Follow-up

None beyond `/lrh-land`'s own review/confirm/merge/closeout chain.

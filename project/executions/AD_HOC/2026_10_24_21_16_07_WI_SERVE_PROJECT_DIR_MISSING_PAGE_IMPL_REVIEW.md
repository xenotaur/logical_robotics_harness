---
execution_id: 2026_10_24_21_16_07_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_REVIEW)[2026-10-23T05:31:38+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_22_18_17_23_WI_SERVE_PROJECT_DIR_MISSING_PAGE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/850
commit:
created_at: 2026-10-24T21:16:07+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/850
session_transcript: pending
---
# Summary

Review-response round 1 for PR 850, run inline from `/lrh-land` Step 4 within
`/lrh-execute`. It addresses the two first-push bot threads. Both found the
same defect, which the pre-push `exists()` to `is_dir()` change introduced.

# Result

Fix commit: `6cf730c634ddfd76a8c1ad21d00fc14061e5dbeb`. Both threads are addressed by the same change.

1. **chatgpt-codex-connector (P2), `PRRT_kwDOR7l1D86vUizK`.** A regular file
   at the project path was reported as nonexistent, and the advertised
   `lrh project init` then fails with `NotADirectoryError`.
2. **copilot-pull-request-reviewer, `PRRT_kwDOR7l1D86vUl6M`.** The same
   defect. The custom init-and-repoint option also fails when
   `<repo>/project` is a file. The reviewer asked for tests of both the
   default and the custom selector.

**Verified:** `bootstrap.apply_plan` calls `target.parent.mkdir`, and that
fails when a file occupies the path (`src/lrh/project/bootstrap.py:100`).

**Fixed in `_no_project_directory_error`:**
- The message says "does not exist" or "exists but is not a directory".
- `lrh project init` is offered only when `<repo>/project` is free. The
  next actions are now:
  - A file at `<repo>/project` gets only the repoint, plus a "move the file
    aside" explanation. This covers both the default path and a custom
    record.
  - A custom record with an existing `<repo>/project` directory gets the
    repoint or `meta set --project-dir project`, and no init.
  - All other cases are unchanged.
- `next_actions` is now always present on `no_project_directory` payloads.
  The `no_local_checkout` payload is unchanged.

**Tests:** the new
`test_project_routes_offer_only_fixes_that_work_around_a_project_file`
covers three cases: a file at the default path, a custom record blocked by
a file, and a custom record with an existing directory. It asserts the
message wording, the exact `next_actions`, and that the page shows no init
command. **Docs:** the "Project selectors" section is updated.

# Validation

Runs used the `LrhLocalAgent` env with `PYTHONPATH=src`.

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2369 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Run confirm-fixes (`/lrh-land` Step 5).

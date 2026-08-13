---
execution_id: 2026_08_02_16_08_07_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
prompt_id: PROMPT(AD_HOC:SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW)[2026-08-02T16:07:52+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_02_15_20_28_SLUG_IDEMPOTENCE_CLI_AND_UTC_TIMESTAMPS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/443
commit: 2b1f3e2a9db294cdd30ee5fa45d97c5064d2ad8d
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/443
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-08-02T16:08:07+00:00
---

# Summary

Round 13 review response for PR #443, driven by a fresh independent
subagent rather than a GitHub bot retrigger, per explicit user direction
that GitHub-hosted review (Codex/Copilot) is a currently expensive,
limited resource and should not be retriggered again this session. The
subagent found 1 confirmed P2 bug (a regression introduced by round 12's
own fix, reproduced two ways before fixing) plus 2 minor doc-completeness
gaps; user approved fixing all 3.

# Result

- **(P2, confirmed by direct reproduction) `--no-remote` did not actually
  bypass the `--output-root` relativization requirement** introduced in
  round 12: `find_local_matches` unconditionally called
  `_relative_output_root`, even though that relativization exists solely
  for the git pathspec `find_remote_matches` needs. `lrh prompt
  check-execution --slug foo --no-remote --output-root <absolute path
  outside project-root>` still raised `SlugCheckError` (exit 3) from the
  local scan alone — and the error text's own suggested fix ("pass
  --no-remote to skip cross-PR search") was already true and hadn't
  helped. Reproduced two ways before fixing: a direct
  `find_local_matches` call, and the actual installed CLI invocation.
  Fixed: `_relative_output_root` now takes a
  `required_for_git_pathspec` keyword — `find_remote_matches` passes
  `True` (unchanged, still raises when relativization fails, since it
  genuinely needs a pathspec), `find_local_matches` passes `False` and
  falls back to using the resolved absolute path as-is when it isn't a
  subpath of `project_root` (a local scan has no pathspec requirement at
  all). Re-verified the fix against the real installed CLI (exit 0, no
  error) in addition to the new unit test. Test:
  `test_absolute_output_root_outside_project_root_is_fine_for_local_only`
  (the existing `..._raises` test, which exercises `find_remote_matches`
  directly, is unaffected and still passes).
- **Doc gap: `--work-item` silently a no-op with `--prompt-id`** (fixed):
  added help text to the `--work-item` argparse argument in
  `prompt_workflow.py` noting it only applies with `--slug`.
- **Doc gap: exit code `1` can also come from unresolved recency alone**
  (fixed): all 5 migrated skills' (and the 3 condensed reference docs')
  "interpret the exit code" sections previously only mentioned
  `landed`/`in_progress`/unrecognized-status as blocking-match causes,
  omitting that a missing/malformed `created_at` on any match also
  produces exit `1` even when every match's status is otherwise
  terminal. Added a clause to the `1` bullet in `lrh-work-item`,
  `lrh-proposal`, `lrh-workstream`, and `lrh-review-response` (and their
  reference-doc mirrors where present). `lrh-confirm-fixes` deliberately
  ignores the exit code entirely (Decision 12), so this gap doesn't
  apply there — left unchanged.

# Validation

- `pytest tests/` — 842 passed (up from 841; +1 new test), same 1
  pre-existing unrelated failure as before this PR
  (`version_integration_test.py`).
- `pytest tests/assist_tests/prompt_workflow_slug_test.py` — 28 passed.
- Manual: `lrh prompt check-execution --slug some-slug --no-remote
  --output-root <absolute-path-outside-project-root> --project-root
  <tmp>` now exits 0 ("No prior execution record found") instead of
  raising, confirmed against the real installed CLI.
- `scripts/format --check` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning.

# Follow-up

None beyond what the primary record already tracks. Per explicit user
direction, further review rounds (if any) should continue to use fresh
independent subagents rather than retriggering GitHub-hosted Codex/
Copilot review.

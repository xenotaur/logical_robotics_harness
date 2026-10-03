---
execution_id: 2026_09_22_04_53_28_WI_LRH_BRANCH_HYGIENE_SURVEY
prompt_id: PROMPT(WI-LRH-BRANCH-HYGIENE-SURVEY:WI_LRH_BRANCH_HYGIENE_SURVEY)[2026-09-22T04:30:03+00:00]
work_item: WI-LRH-BRANCH-HYGIENE-SURVEY
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/700
commit: 
created_at: 2026-09-22T04:53:28+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-BRANCH-HYGIENE-SURVEY.md
session_transcript: pending
---

# Summary

Implemented `WI-LRH-BRANCH-HYGIENE-SURVEY`: a report-only `lrh branches
survey` command that classifies local git branches and can write
reviewable `git branch` delete commands to a file, never deleting
anything itself. Run via `/lrh-execute`; prior-art check re-verified at
Step 1.5, no duplicate found.

# Result

Added `src/lrh/branch_hygiene.py` (classification, quoting, rendering),
`src/lrh/cli/branches.py` (CLI wiring, a new `branches` top-level group),
`docs/reference/cli/branches.md` and a README index line,
`tests/branch_hygiene_test.py`, and `tests/cli_tests/branches_test.py`.
Command group decision (Required Change 1): `branches` is a new group,
not an extension of `github` (PR comments/threads) or `sessions`
(session archive) — neither fits local branch state.

Both safety properties the WI's own review comments flagged (PR #690)
are implemented and covered by dedicated tests: the discovered default
branch always short-circuits to `BranchClass.DEFAULT` before any other
check runs and is excluded from delete output entirely; every branch
name is rendered via `shlex.quote` plus an explicit `--` option
terminator. Class precedence (`DEFAULT` > `IN_WORKTREE` > `OPEN_PR` >
`MERGED_OR_EMPTY` > `SQUASH_MERGED` > `REVIEW_FIRST` > `UNIQUE_WORK`) is
a single ordered if-chain, with dedicated overlap tests (e.g. a branch
that is both in a worktree and an ancestor of the default branch).

Pushed as commit `bcee15b9` to PR #700.

# Validation

scripts/version tools — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff — clean (after one reformat)
scripts/lint — all checks passed (after fixing one E501 in
render_report_markdown)
scripts/test (PYTHONPATH=src, per the worktree editable-install memory
note) — 1677 tests OK
lrh validate — 0 errors, 0 warnings
Item-specific: `lrh branches survey --help`, a live survey against this
repo, and `--write-delete-commands` confirmed `main` never appears in
generated output even though it is checked out in a different worktree
Step 7.5 diff-mode `/lrh-self-review`: no issues found; independently
re-verified the default-branch short-circuit and the absence of any
mutating git call directly against the source

# Follow-up

`session_transcript: pending` should be updated to the durable session
pointer when available. Follow-up work not in scope: remote-branch
cleanup, and the pre-existing `feedback_execution_record_agent_claude_app`
memory convention (`instruction_source` repo-relative) is followed here.

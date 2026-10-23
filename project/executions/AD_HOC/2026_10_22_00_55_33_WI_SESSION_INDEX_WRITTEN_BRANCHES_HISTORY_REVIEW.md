---
execution_id: 2026_10_22_00_55_33_WI_SESSION_INDEX_WRITTEN_BRANCHES_HISTORY_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SESSION_INDEX_WRITTEN_BRANCHES_HISTORY_REVIEW)[2026-10-15T05:39:01+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_12_23_28_06_WI_SESSION_INDEX_WRITTEN_BRANCHES_HISTORY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/838
commit:
created_at: 2026-10-22T00:55:33+00:00
agent: claude_app
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/838"
session_transcript: pending
---

# Summary

Review-response round 1 for PR #838 (the planning PR for
`WI-SESSION-INDEX-WRITTEN-BRANCHES-HISTORY`), run inline from `/lrh-land`
Step 4. There were 8 open threads (4 Copilot on `46ab39b5`, 4 Codex on
`e3721ce9`) covering 5 distinct findings. The user approved fixing all five
at the Step 4 confirm gate.

# Result

All 5 were fixed in the work item, in commit `a834d6f1`:

1. **Empty-string branch** (Copilot + Codex P2). Required Change 1 checked
   only `branch is not None`. `--branch ""` and export metadata both reach
   `_merge` as `""` (`sync_export`). Now: require a non-empty incoming
   branch; an empty string changes neither `branch` nor `written_branches`;
   added a matching test and acceptance criteria.
2. **Module docstring omitted** (Copilot + Codex P2).
   `prompt_workflow_sessions.py:3-5` also says "reserved for later fork
   stitching". Added it to the scope and Required Change 1, and widened the
   completion grep.
3. **`related_design` must be a path** (Copilot). The schema says "File
   paths to relevant design docs", and readiness resolves them under
   `project/design`. Changed to
   `project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md`.
4. **Non-canonical validation** (Copilot + Codex P1). Per AGENTS.md: added
   `scripts/version tools`; replaced the raw `python -m unittest` with
   `scripts/test tests/assist_tests/prompt_workflow_sessions_test.py`;
   replaced the `.claude`-only `diff` with
   `lrh skills check --local --target all --source current-repo`.
5. **Untracked-file grep** (Codex P1). Replaced `grep -rn` with a
   tracked-only `git grep`.

All findings were verified against the repo before fixing. None were
skipped.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness`: prompt_ready = yes, no warnings.
- New validation commands dry-checked:
  - `lrh skills check --local --target all --source current-repo` exits 0;
  - the tracked `git grep` finds 8 old-wording matches today, so it can
    fail;
  - the focused `scripts/test` ran 75 tests OK.

# Follow-up

- Confirm-fixes resolves the 8 threads.

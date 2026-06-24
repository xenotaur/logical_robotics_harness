---
execution_id: 2026_06_24_17_40_47_WI_CI_COPILOT_AUTO_REVIEW
prompt_id: PROMPT(WI-CI-COPILOT-AUTO-REVIEW:WI_CI_COPILOT_AUTO_REVIEW)[2026-06-24T17:36:40-04:00]
work_item: WI-CI-COPILOT-AUTO-REVIEW
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/321
commit: 90d0a1b
created_at: 2026-06-24T17:40:47-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CI-COPILOT-AUTO-REVIEW.md
session_transcript: claude-app:local_16783f02-bd57-4a5d-b624-ec1e7e05681b
---

# Summary

Add `.github/workflows/request-copilot-review.yml` so every non-draft PR
automatically gets Copilot added as a reviewer, eliminating the manual
"Request Review" click needed after each PR is opened.

# Result

PR #321 opened at https://github.com/xenotaur/logical_robotics_harness/pull/321

Files created:

- `.github/workflows/request-copilot-review.yml` — triggers on
  `pull_request: [opened, reopened, ready_for_review]`, skips drafts via
  job-level `if` condition, requests Copilot reviewer via raw GitHub REST API
- `project/work_items/proposed/WI-CI-COPILOT-AUTO-REVIEW.md` — work item
  recording the design decisions (option A/B/C analysis, bot-handle
  confirmation, raw API over gh pr edit rationale)

# Validation

scripts/version tools — lrh 0.2.5.dev404, Python 3.11.8, Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format / lint / test — skipped (no Python changes)
lrh validate — 0 errors, 0 warnings

Self-test: PR #321 is the first live test — the workflow should fire and add
Copilot as a requested reviewer on open.

# Follow-up

- Observe the GitHub Actions run on PR #321; confirm Copilot appears as a reviewer
- Update `session_transcript: pending` to `claude-app:<session-id>` after the session ends
- After PR #321 merges: set `status: landed`, populate `commit:` with the merge SHA,
  move `WI-CI-COPILOT-AUTO-REVIEW` to `project/work_items/resolved/` with
  `status: resolved` and a non-null `resolution` value

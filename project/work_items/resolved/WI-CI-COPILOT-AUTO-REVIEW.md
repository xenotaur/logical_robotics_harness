---
resolution: Implemented and merged in PR #321 (commit 90d0a1b); pull_request_target trigger confirmed working
blocked_reason: null
blocked: false
id: WI-CI-COPILOT-AUTO-REVIEW
title: Add GitHub Actions workflow to auto-request Copilot PR review
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - modify_existing_workflows
  - add_copilot_to_codeowners
acceptance:
  - .github/workflows/request-copilot-review.yml exists and is syntactically valid
  - workflow triggers on pull_request_target types opened, reopened, and ready_for_review
  - draft PRs are excluded via the job-level if condition
  - Copilot appears as a requested reviewer on the PR that introduces the workflow
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - .github/workflows/request-copilot-review.yml
---

## Summary

Add a GitHub Actions workflow that automatically requests a Copilot code review
on every non-draft pull request in the LRH repo, matching the automatic coverage
that chatgpt-codex-connector already provides for Codex reviews.

## Problem / Context

Copilot and Codex automated reviewers catch overlapping but not identical issues.
chatgpt-codex-connector fires automatically on every PR open event. Copilot review
requires a manual "Request Review" click in the GitHub UI, creating inconsistent
coverage: some PRs get both reviewers, others only Codex. A GitHub Actions workflow
is the idiomatic and reliable mechanism for ensuring every non-draft PR receives
both reviews without per-PR cognitive overhead.

Design decision recorded here (2026-06-24 session): GitHub Actions workflow (option C)
was chosen over embedding the reviewer request in the `/lrh-implement` skill (option B)
or continuing to click manually (option A). The disqualifying limitation of option B
is that it only fires when the skill is used — PRs opened via the GitHub UI or other
tools get no Copilot review. Option A does not scale and is easily forgotten.

## Scope

- Create `.github/workflows/request-copilot-review.yml` in the LRH repo
- Record the design decisions and bot-handle discovery that motivate the implementation

## Required Changes

1. Create `.github/workflows/request-copilot-review.yml` with:
   - Trigger: `pull_request_target: types: [opened, reopened, ready_for_review]`
   - Job condition: `if: github.event.pull_request.draft == false` (skip drafts)
   - Permissions block: `pull-requests: write` (required for GITHUB_TOKEN to modify reviewers)
   - Step using the raw GitHub REST API — not `gh pr edit --add-reviewer` (which may reject
     bot handles not in GitHub's user registry):
     ```
     gh api repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}/requested_reviewers \
       -X POST --field 'reviewers[]=Copilot'
     ```
   Note: Copilot's bot handle was confirmed as `"login": "Copilot", "type": "Bot"` via
   `gh api .../pulls/320 --jq '.requested_reviewers[]'` on 2026-06-24.

## Non-Goals

- Do not add Copilot to CODEOWNERS — that triggers file-path-matched requests, not per-PR.
- Do not automate Codex review — chatgpt-codex-connector already handles this.
- Do not modify any existing GitHub Actions workflows.
- Do not implement a skill step for Copilot review requests — CI is the reliable ground
  truth; skill-embedding was option B (rejected).
- Do not add branch protection rules or required reviewer gates.

## Acceptance Criteria

- `.github/workflows/request-copilot-review.yml` exists and is syntactically valid
- Workflow is triggered by `pull_request_target: types: [opened, reopened, ready_for_review]`
- Draft PRs are excluded via `if: github.event.pull_request.draft == false`
- Copilot appears as a requested reviewer on the PR that introduces this workflow (self-test)
- `lrh validate` passes with 0 errors after the file is added

## Validation

- `lrh validate`
- Observe the workflow run in the GitHub Actions tab of the introducing PR; confirm Copilot is added as a requested reviewer

## Risk Notes

- The `Copilot` bot handle was verified from a live PR on 2026-06-24. If GitHub renames
  the bot, `reviewers[]=Copilot` will silently fail — no API error, Copilot simply won't
  appear. The self-test on the introducing PR catches this immediately.
- Without `pull-requests: write` in the workflow `permissions:` block, the default
  `GITHUB_TOKEN` returns a 403. The step may still exit 0 (the API error appears in the
  log, not the job status). Include the permissions block explicitly.

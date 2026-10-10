---
execution_id: 2026_10_10_02_42_50_SERVE_UNRESOLVED_PROJECT_SELECTOR_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:SERVE_UNRESOLVED_PROJECT_SELECTOR_CLOSEOUT_NOTE)[2026-10-10T02:42:50+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_01_17_08_SERVE_UNRESOLVED_PROJECT_SELECTOR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/813
commit: d9f5b1bd2c829e40b366421fecf4a2c83cd3a42a
created_at: 2026-10-10T02:42:50+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/813
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Closeout note for PR #813. The PR was an ad-hoc fix: `lrh serve` project
routes showed the served project's data under another project's name, for
example a repo_locator-only LCATS project showing LRH's dependency map. It
landed through `/lrh-implement` → `/lrh-land`.

# Result

CHAIN-NOTE: cycles=1; stops=1; gates=[implement-plan-confirm, chain-init-live-confirm, review-response-round1-confirm, confirm-fixes-autopilot-routine, stop-work-halt-selfreview-findings, merge-and-closeout-single-ask]; friction=hosted bots review only the first push, so the Step 8 review signal was a substitute PR-mode self-review; its low/nit findings fired the stop-work condition, and the user chose to defer those named findings; self_review_rounds=1; note="PR merged as d9f5b1bd via lrh vcs merge --merge --match-head-commit 4c4e7389. First-push Copilot (ambiguous main fallback) and Codex (project_dir default) threads were fixed in 775275e6 and resolved Clear-satisfied by a cold --subagent pass. The stale PR body was fixed with gh pr edit. Six records landed for this PR, including this note. Ad-hoc task, so there was no WI or WS to resolve."

# Validation

`lrh validate` after closeout: 0 errors, 0 warnings.

# Follow-up

The user deferred these self-review findings at the stop-work gate:

- A registry record whose bound checkout path no longer exists still
  resolves. It gets 200 "No dependency-map views", or a JSON 404 on a view
  route, instead of a framed error.
- HEAD on dependency-map view routes reads the registry twice.
- A loose `assertTrue(... or ...)` in
  `test_project_routes_serve_the_served_projects_own_selectors`.
- Pre-existing: the work-item page's "Download generated prompt" link
  (`/workbench/prompt?work_item=...`) always targets the served project.
  `/project/<id>/work-items/...` has no HEAD handler.

---
execution_id: 2026_10_10_18_06_29_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_REVIEW)[2026-10-10T17:55:33+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_10_05_32_46_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/818
commit:
created_at: 2026-10-10T18:06:29+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/818
session_transcript: pending
---
# Summary

Review-response round 1 for PR 818, run inline from `/lrh-land` Step 4. It
addresses the three first-push bot threads on the new work item
`WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`.

# Result

Fix commit `817c608c964df58f144a355d7183e73369470e28`.

1. **copilot-pull-request-reviewer (medium), `PRRT_kwDOR7l1D86rBZZZ`.** The
   prompt preview page's "Back to workbench" and "Back to viewer context"
   links (`src/lrh/serve.py:2215-2216`) also leave the named project.
   **Fixed:** the links are now in the Summary, Problem, Scope, Required
   Changes, test list, and frontmatter acceptance and body acceptance
   criteria. They target `/project/<id>/work-items/<wi>` and `/project/<id>`,
   and the `/workbench` pages keep their existing links.
2. **chatgpt-codex-connector (P2), `PRRT_kwDOR7l1D86rBbf5`.** The 409
   criterion conflicted with the Non-Goals' excluded HTML routes. **Fixed:**
   the missing-checkout criterion, Problem, and Scope are now limited to the
   routes that use `_config_for_project_selector`: dependency maps (HTML,
   JSON, HEAD), work-item detail, and work-item prompt. The Non-Goal now says
   the dashboard, design, and workstream routes resolve through
   `_project_from_meta_selector` and keep their 404 behavior.
3. **chatgpt-codex-connector (P2), `PRRT_kwDOR7l1D86rBbf9`.** Add the item to
   its parent workstream. **Already satisfied:** commit `0843436d` added it
   to `WS-LRH-CONSOLE-LOCAL-DOGFOOD` (line 40) after Codex reviewed
   `749e7c1f`. No change needed.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`:
  prompt-ready.
- `scripts/format --check --diff`: 295 files unchanged.
- `scripts/lint`: passed.
- `scripts/test`: 2200 tests, OK.

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`.

# Follow-up

- `/lrh-land` Step 5 (confirm-fixes) resolves the three threads.

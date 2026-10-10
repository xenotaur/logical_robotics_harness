---
execution_id: 2026_10_10_01_17_08_SERVE_UNRESOLVED_PROJECT_SELECTOR
prompt_id: PROMPT(AD_HOC:SERVE_UNRESOLVED_PROJECT_SELECTOR)[2026-10-10T00:27:22+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/813
commit:
created_at: 2026-10-10T01:17:08+00:00
agent: claude_app
instruction_source: ad-hoc — fix lrh serve _config_for_project_selector falling back to the served project for registered no-checkout projects and unknown selectors
session_transcript: pending
---
# Summary

Fix a correctness bug in `lrh serve`. `_config_for_project_selector`
returned the served project's config whenever the Meta registry could not
resolve a `/project/<id>/` selector to a local checkout. The dependency-map,
work-item, and prompt routes therefore showed the served project's data
under another project's name. The owner observed this in LRH Console: a
repo_locator-only LCATS project showed LRH's dependency map.

# Result

PR https://github.com/xenotaur/logical_robotics_harness/pull/813 (not merged).

- `src/lrh/serve.py`: new `ProjectSelectorError`, with status 404 or 409
  and a JSON payload, plus `render_project_selector_error_page`. Selectors
  now resolve as follows:
  - A selector that resolves to a checkout reads it, as before.
  - A registered project with no local checkout gets 409 and a framed
    "No local checkout" page with
    `lrh meta set <name> --local-repo-path PATH`.
  - `main` alone still falls back to the served project.
  - Anything else gets 404, carrying the registry's message.

  All six call sites handle the error: the dependency-map page, index, API,
  and HEAD, plus the work-item page and the prompt page. The API returns a
  JSON error.
- Status choice: 409 Conflict. The project exists, but its state (no bound
  checkout) prevents serving it. The choice is documented.
- `docs/reference/cli/serve.md`: a new "Project selectors" section replaces
  the old fallback sentence.
- `tests/cli_tests/serve_test.py`: three new tests, one each for a
  no-checkout project, an unknown selector (with and without a Meta
  workspace), and the served project's own selectors (`served`,
  `proj-served`, `main`).
- Prior-art check: no existing work item, proposal, or execution covers this
  bug. The fix reuses the existing `lrh meta set ... --local-repo-path PATH`
  guidance wording from the project dashboard.
- Self-review: diff-mode `/lrh-self-review`
  (`2026_10_10_01_10_42_SERVE_UNRESOLVED_PROJECT_SELECTOR_SELFREVIEW`). It
  found no blocking issues. One low finding, a misleading 404 message for
  ambiguous selectors or registry errors, was verified and fixed.

# Validation

All runs used the per-worktree `LrhLocalAgent` conda env with
`PYTHONPATH=src`, on the branch rebased onto `origin/main` `5e5b60c7`.
Versions: Python 3.11.16, Black 26.3.1, Ruff 0.15.12.

- `scripts/format --check --diff`: 295 files unchanged.
- `scripts/lint`: passed (ruff, black, and the STYLE.md Rule 5 guardrail).
- `scripts/test`: 2186 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Optional: `/project/<id>/work-items/...` has no HEAD handler, so HEAD
  falls through to the dashboard 404 while GET returns 200, 404, or 409.
  This gap predates the change.
- After merge, run `/lrh-closeout`.

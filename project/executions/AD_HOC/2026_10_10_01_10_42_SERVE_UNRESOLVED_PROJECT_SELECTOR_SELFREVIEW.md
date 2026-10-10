---
execution_id: 2026_10_10_01_10_42_SERVE_UNRESOLVED_PROJECT_SELECTOR_SELFREVIEW
prompt_id: PROMPT(AD_HOC:SERVE_UNRESOLVED_PROJECT_SELECTOR_SELFREVIEW)[2026-10-10T01:10:37+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/813
commit: d9f5b1bd2c829e40b366421fecf4a2c83cd3a42a
created_at: 2026-10-10T01:10:42+00:00
agent: claude_app
instruction_source: ad-hoc — diff-mode self-review of the lrh serve unresolved project-selector fix
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Diff-mode `/lrh-self-review` (report-only, no `--apply`) of the ad-hoc fix
that stops `lrh serve` project routes from falling back to the served
project for registered no-checkout projects and unknown selectors. It ran
once before the first push, against `git diff HEAD` on fork point
`04732ce49207e5c937f20058c9242a3222b3f853` (3 files). `rerun_of` and `pr`
are empty by design: no primary record or PR existed at dispatch time.

# Result

The cold-context subagent found no blocking issues. It confirmed that all
six `_config_for_project_selector` call sites catch `ProjectSelectorError`,
that no route still falls back silently, that GET and HEAD agree on the
dependency-map routes, that the error page is framed, and that the docs match
the code. `tests.cli_tests.serve_test` ran 112 tests, OK. It reported 5 low or
out-of-scope findings:

1. Low: every `MetaRegistryError`, including an ambiguous selector or a
   broken registry, became a "No project matches" 404 message. **Fixed:**
   the invoking session confirmed this by reading `serve.py` and
   `meta/workspace.py:2442`. The 404 now carries the registry's own
   message, and a test asserts the message names the selector.
2. Low: the work-items handler sniffs `<!doctype html>` to choose HTML or
   JSON. Not changed: it works today and the tests cover it.
3. Low: HEAD resolves the selector twice. Harmless; not changed.
4. Edge: a served project registered without a bound checkout returns 409
   under its registry name, while `main` still works. Accepted as correct,
   since the registry says no checkout is bound.
5. Out of scope, pre-existing: `/project/<id>/work-items/...` has no HEAD
   handler, so HEAD falls through to the dashboard 404. Noted as a
   follow-up.

# Validation

- The invoking session independently re-verified finding 1, the top
  finding, by reading the code.
- After the fix: `tests.cli_tests.serve_test` ran 112 tests, OK.
  `scripts/format --check --diff` and `scripts/lint` passed.

# Follow-up

- `/lrh-implement` Step 8 (commit and PR) proceeds next.
- Optional: add HEAD handling for `/project/<id>/work-items/...` routes so it
  matches GET.

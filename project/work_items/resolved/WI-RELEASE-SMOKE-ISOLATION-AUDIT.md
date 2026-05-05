---
resolution: Completed
blocked_reason: null
blocked: false
id: WI-RELEASE-SMOKE-ISOLATION-AUDIT
title: Audit release-smoke preinstall import visibility isolation
type: investigation
status: resolved
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - root cause of preinstall package visibility in `scripts/release-smoke` temp venv is documented with evidence
  - release-smoke behavior is updated if needed to reflect the root-cause decision
  - any strict or diagnostic mode is documented and covered by focused tests
  - smoke validation remains focused on verifying installed-wheel behavior
required_evidence:
  - manual_review
  - smoke_test_output
  - test_result
artifacts_expected:
  - investigation_notes
  - environment_diagnostics
  - code_diff
---

## Summary

Investigate why `scripts/release-smoke` can detect `logical-robotics-harness` before wheel installation in the temporary virtual environment and decide the correct policy response.

## Investigation Goals

- identify why package visibility exists before install
- determine whether the behavior is benign environment leakage or a test-validity risk
- decide whether current warning behavior should remain, become strict-mode optional, or become a hard failure

## Suggested Diagnostics

- `python -m site`
- `python -c "import sys; print('\\n'.join(sys.path))"`
- `python -m pip show -f logical-robotics-harness`
- `python -c "import importlib.util; print(importlib.util.find_spec('lrh'))"`
- inspect `.pth` files in the temporary venv
- capture relevant `PYTHON*`, `PIP*`, `CONDA*`, and `VIRTUAL_ENV` environment variables

## Acceptance Criteria

- investigation artifacts identify and document the concrete root cause of preinstall visibility
- `scripts/release-smoke` behavior is intentionally adjusted (or explicitly retained) based on findings
- any new strict/diagnostic behavior is documented and tested
- release-smoke continues to validate installed wheel behavior rather than source-tree leakage behavior

## Notes

Potential visibility sources include editable install residue, Conda path injection, `.pth` path extensions, pip metadata interactions, and project-local path leakage.

## Completion Notes

Closed on 2026-05-05 after the diagnostic and strict-isolation follow-up changes landed and documentation was reviewed.

Acceptance status:

- Pre-install visibility checks now run with the smoke virtual environment command environment after clearing `PYTHONPATH`, so the thin `scripts/release-smoke` wrapper can keep using the source checkout to load the package-owned implementation without contaminating installed-wheel checks.
- `scripts/release-smoke <tag> --diagnose` prints grouped temporary-venv diagnostics for pre-install package visibility investigations.
- `scripts/release-smoke <tag> --strict-isolation` turns pre-install LRH visibility into a hard failure before wheel installation.
- Default `scripts/release-smoke <tag>` behavior remains warning-oriented when pre-install visibility is detected, preserving local development usability while continuing to validate the installed wheel.
- `scripts/release-smoke <tag> --diagnose --preserve` supports post-failure inspection by printing diagnostics and keeping the temporary smoke environment.
- Focused tests cover diagnostic parsing/rendering, `PYTHONPATH` cleanup for smoke-venv commands, warning-vs-strict behavior, and CLI help coverage for the new options.

Evidence recorded in `project/evidence/EV-0005.md` and the related execution records under `project/executions/WI-RELEASE-SMOKE-ISOLATION-AUDIT/`.

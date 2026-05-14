---
execution_id: 2026_05_14_04_27_53_CI_CAPABILITY_SCAFFOLDING_DESIGN_WORKSTREAM
prompt_id: PROMPT(AD_HOC:CI_CAPABILITY_SCAFFOLDING_DESIGN_WORKSTREAM)[2026-05-14T00:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-14T04:27:53+00:00
---

# Summary

Added a focused CI capability scaffolding design/control-plane update after checking that no prior
exact execution record existed for the prompt ID.

# Result

- Added `project/design/proposals/ci-capability-scaffolding.md` as a proposed design proposal for
  reusable CI capability scaffolding.
- Added `project/workstreams/proposed/WS-CI-CAPABILITY-SCAFFOLDING.md` as a proposed workstream
  describing phases for playbook, request-template refresh, CI Agent Skill prototype design, and
  template/fragments reassessment.
- Updated roadmap, current focus, work-item README guidance, design proposal README navigation, and
  workstream README navigation with minimal links to the proposal and workstream.
- Kept implementation of the CI playbook, CI request-template changes, Agent Skill, CI templates, and
  workflow changes out of scope.

# Review follow-up

- Moved the CI capability scaffolding workstream into `project/workstreams/proposed/` so the
  workstream loader, validation discovery, snapshots, and planning indexes can see it.
- Verified `load_workstreams(Path("project"))` includes `WS-CI-CAPABILITY-SCAFFOLDING` at the
  proposed-bucket path.

# Validation

- `scripts/version tools` passed and reported Ruff 0.15.12 and Black 26.3.1 availability; Pylint and
  Conda were not installed.
- `scripts/check-workflows` passed for all workflow YAML files.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed Ruff checks and Black formatting checks.
- `scripts/test` passed 452 unit tests.
- `lrh validate` was run during control-plane review and reported 0 errors. It reported the existing
  active-work-item planning warnings plus one warning for the explicitly requested unbucketed design
  proposal path.

# Follow-up

Recommended follow-up phases remain separate PRs:

1. create `WI-CI-PLAYBOOK` and implement the human CI setup/debugging playbook;
2. create `WI-CI-REQUEST-TEMPLATES` and refresh CI assessment/implementation request templates;
3. design `WI-CI-SKILL-PROTOTYPE` only after playbook and prompt behavior stabilize; and
4. create `WI-CI-TEMPLATE-FRAGMENTS-ASSESSMENT` to reassess templates or fragments using dogfooding
   evidence.

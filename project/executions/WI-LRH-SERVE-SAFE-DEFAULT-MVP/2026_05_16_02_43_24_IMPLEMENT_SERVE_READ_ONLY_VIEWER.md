---
execution_id: 2026_05_16_02_43_24_IMPLEMENT_SERVE_READ_ONLY_VIEWER
prompt_id: PROMPT(WI-LRH-SERVE-SAFE-DEFAULT-MVP:IMPLEMENT_SERVE_READ_ONLY_VIEWER)[2026-05-15T16:02:00-04:00]
work_item: WI-LRH-SERVE-SAFE-DEFAULT-MVP
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-16T02:43:24+00:00
---

# Summary

Implemented the safe-default `lrh serve` read-only viewer MVP for this prompt.
The existing server skeleton was present and was extended rather than replaced.

# Result

- Added the read-only `/api/project` JSON route.
- Expanded `/` into a package-owned read-only project viewer page.
- Reused `lrh.core_state.load_core_project_state` for validation, focus,
  workstream, work-item, planning-tree, active-leaf, and execution-readiness
  summaries.
- Exposed run-packet and run-report request surfaces as references only; the
  viewer does not generate packets/reports, dispatch agents, mutate branches,
  create pull requests, make external network calls, or serve arbitrary files.
- Updated README documentation for the safe-default viewer routes and behavior.
- Added focused unittest coverage for project summaries, deterministic ordering,
  warnings/errors, empty/no-ready states, non-mutation, write-method rejection,
  and arbitrary-file rejection.

# Validation

- `scripts/version tools` passed; Ruff and Black versions were present.
- `scripts/format --check --diff` passed after formatting.
- `scripts/lint` passed.
- `python -m unittest tests.cli_tests.serve_test -v` passed.
- `scripts/test` passed: 522 tests.
- `lrh validate` completed with 0 errors and 3 pre-existing planning warnings
  about orphaned active work items.
- `lrh snapshot` returned CLI usage error because the installed command requires
  a scope argument.
- `lrh snapshot project --project-root .` passed and produced project snapshot
  output.
- `lrh serve --help` passed.

# Follow-up

The next prompt/run-packet/report workbench prompt is unblocked at the viewer
level: ready leaves now show read-only references to the existing request
surfaces, but no workbench actions or mutation routes were added.

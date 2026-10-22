---
execution_id: 2026_10_22_18_22_55_WI_LRH_CONSOLE_WORK_ITEM_BROWSER
prompt_id: PROMPT(WI-LRH-CONSOLE-WORK-ITEM-BROWSER:WI_LRH_CONSOLE_WORK_ITEM_BROWSER)[2026-10-15T06:02:44+00:00]
work_item: WI-LRH-CONSOLE-WORK-ITEM-BROWSER
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/851
commit:
created_at: 2026-10-22T18:22:55+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CONSOLE-WORK-ITEM-BROWSER.md
session_transcript: pending
---

# Summary

Implemented WI-LRH-CONSOLE-WORK-ITEM-BROWSER via /lrh-implement: a read-only, filterable, workstream-grouped work-item browser in `lrh serve`, plus a typed roadmap loader. The owner approved the plan at the Step 4 gate, including the change from a GET form to filter links.

# Result

- New `src/lrh/control/roadmap.py` (`load_roadmap`, `Roadmap`, `RoadmapRoot`, `RoadmapPhase`, `RoadmapDiagnostic`).
- New `src/lrh/work_item_browser.py`: payload builder and renderer.
  - Planning-tree group order with an Unparented group; open work first.
  - AND filters; roadmap matched directly or through the parent workstream.
  - Glyph-plus-text status pills; HTML-escaped output; a note when the project does not validate.
- `src/lrh/serve.py`:
  - GET and HEAD for `/project/<id>/work-items` and `/api/project/<id>/work-items`, with the selector's 404/409.
  - Links from `/workbench` and the project dashboard.
- `src/lrh/ux/frame.py`: a "Work items" entry in the project sidebar.
- `src/lrh/dependency_maps/render.py`: pill CSS moved into a shared `PILL_STYLES`; the rule set is unchanged.
- Docs: `docs/reference/cli/serve.md`.
- Work-item wording: filters are links, because the CSP has `form-action 'none'`; the serve.py size note is corrected.
- Deviation from Required Change 4: links instead of a GET `<form>`. The owner approved this at the plan gate.
- Capabilities, 405 handlers and CSP unchanged. Nothing under `experimental/` was touched.

# Validation

All in the per-worktree `LrhConsoleBrowser` env (`pip show lrh` confirmed it is bound to this worktree):

- `scripts/version tools`: Black 26.3.1, Ruff 0.15.12.
- `scripts/format --check`: passed.
- `scripts/lint`: passed.
- `scripts/test`: 2384 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Visual check in the browser pane, light and dark, against this repository: 270 work items in 27 groups. The roadmap root is not a phase, and 154 items have no phase.
- The branch LRH Console app bundled successfully (`apps/desktop/scripts/run bundle`) for the owner's check.
- Diff-mode self-review before push: 4 minor findings, all fixed (see the `_SELFREVIEW` record).

# Follow-up

- The owner checks the page in the bundled branch app.
- PROP-LOCAL-AGENT-BENCH (PR #837) builds its console link on this page.

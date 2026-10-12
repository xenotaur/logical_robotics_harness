---
id: "WI-LRH-CONSOLE-WORK-ITEM-BROWSER"
title: "Add a filterable, workstream-grouped work-item browser with roadmap phases to lrh serve"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "docs/reference/cli/serve.md"
depends_on: []
blocked_by: []
expected_actions:
- "create_file"
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "GET /project/<id>/work-items renders every work item of the selected project grouped under its parent workstream (planning tree order), with an Unparented group, and each row links to the existing work-item detail and prompt pages."
- "GET query filters status, type, workstream, roadmap, ready, and active narrow the list, combine with AND, are echoed in the form and the JSON, and an unknown filter value yields an empty result with a diagnostic rather than an error page."
- "A typed roadmap loader in src/lrh/control returns the phases in project/roadmap/*.md (id, title, status, parent, numeric order including 1.5) and the page shows a phase strip; a work item matches a phase if it or its parent workstream lists the phase in related_roadmap, and the row says which."
- "GET /api/project/<id>/work-items returns the same data as JSON; HEAD matches GET on both routes, and a registered project with a missing bound checkout returns the framed 409 no-local-checkout response, as the other project-scoped routes do."
- "_safe_capabilities, the 405 handlers, and the CSP are unchanged; the page needs no JavaScript; every status shows text plus the console's icon/shape cue, never color alone; /workbench and the project dashboard link to the new page."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/control/roadmap.py"
- "src/lrh/serve.py"
- "tests/control_tests/roadmap_test.py"
- "tests/cli_tests/serve_test.py"
- "docs/reference/cli/serve.md"
---

# Work-item browser for LRH Console

## Summary

Add a read-only, filterable work-item browser at `/project/<id>/work-items` (with a JSON twin) that groups work items under their workstreams, and a small typed roadmap loader so the page can show and filter by roadmap phase. This is the first step of turning LRH Console into a project browser, inside the console's existing read-only charter.

## Problem / Context

The owner wants LRH Console to work as a project browser: a navigable view of focus, roadmap, workstreams, proposals, and work items, with local-model toys and follow-up chat to come later. Most of the read side exists. The dashboard shows focus, active workstreams, active and execution-ready leaves (`src/lrh/serve.py:458-531`). Designs, workstreams, and work items have detail pages (`serve.py:1390,1460,2432`). `/workbench` lists every work item with status, type, and preview links (`workbench_payload`, `serve.py:2253-2297`). The gaps are that there is no grouped or filterable list and no roadmap view. The roadmap is only read as a raw file (`src/lrh/assist/snapshot_cli.py:717`), although its phase files carry typed frontmatter (`id`, `status`, `parent`, `order`). Linkage is sparse: only 9 of 35 workstreams set `related_roadmap`. So the tree is rooted at workstreams, and roadmap phase is a label and filter.

This fits the console proposal's L2 "daily workspace console" increment. It deliberately adds no authority. The local-model toys and chat need a separately authenticated surface, which a separate proposal captures. This page is the anchor that surface will link from.

### Duplication search
- In-repo: Related: `/workbench` (flat list, kept for previews), `build_planning_tree` (`src/lrh/control/planning_tree.py:132`, reused for grouping), project dashboard. No grouped/filterable list or roadmap loader exists.
- Sibling repos: None identified.
- External libraries: None identified; this is a view over LRH's own control-plane models.
- Recommendation: Proceed — extend serve, reuse the planning tree.

### Demand search
- Work items: None found requesting a work-item list or roadmap view; `WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES` (resolved) set the project-scoped route conventions this follows.
- Proposals: `lrh-console-local-dogfood` L2 "daily workspace console" (partially satisfied by this item).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- A read-only HTML page and JSON twin listing a project's work items grouped by workstream, with GET-query filters.
- A typed roadmap-phase loader in `src/lrh/control/` and a phase strip and filter on the page.
- Links into the new page from `/workbench` and the project dashboard.

## Required Changes

1. Add `src/lrh/control/roadmap.py` with a frozen `RoadmapPhase` dataclass (`id`, `title`, `status`, `parent`, `order: float`, `path`) and `load_roadmap(project_dir)`. It reads `project/roadmap/*.md` frontmatter, sorts by `order` then `id`, and returns diagnostics instead of raising when a file is malformed or the directory is absent.
2. In `src/lrh/serve.py`, add a `work_item_browser_payload(config, project_selector, filters)` built on the loaded project state and `build_planning_tree`. Groups follow the workstream order, with an `Unparented` group last. Each row has id, title, status, type, active and ready flags, roadmap phases (own or via its workstream), and detail and prompt URLs under `/project/<id>/`.
3. Add routes `GET`/`HEAD /project/<id>/work-items` (HTML) and `/api/project/<id>/work-items` (JSON), with the same selector errors (404, 409 no-local-checkout) as the existing project-scoped routes.
4. Render the filters as a plain GET `<form>` (status, type, workstream, roadmap, ready, active). The page needs no script, and no CSP change. Show the console's existing text-plus-shape status pills.
5. Link to the page from `/workbench` and the project dashboard.
6. Add tests: loader (ordering incl. `1.5`, malformed file, missing dir), payload grouping and filters, routes (GET, HEAD, JSON, 404, 409), and an assertion that `_safe_capabilities()` and the 405 handlers are unchanged.
7. Document the routes in `docs/reference/cli/serve.md`.

## Non-Goals

- Do not add write routes, POST handling, agent dispatch, or any capability change.
- Do not add local-model, toy, chat, or bench integration or links (separate proposal).
- Do not modify `experimental/local_agent/`, `WI-LOCAL-AGENT-001`, or `WS-LOCAL-AGENT-DOGFOOD`.
- Do not backfill `related_roadmap` on existing workstreams or work items.
- Do not add proposal or focus browsing beyond the existing pages.
- Do not change `/workbench`'s list or previews beyond adding a link.

## Acceptance Criteria

- `GET /project/<id>/work-items` renders every work item of the selected project grouped under its parent workstream (planning-tree order), with an Unparented group. Each row links to the existing work-item detail and prompt pages.
- The filters `status`, `type`, `workstream`, `roadmap`, `ready`, and `active` narrow the list and combine with AND. They are echoed in the form and the JSON. An unknown value yields an empty result with a diagnostic, not an error page.
- `load_roadmap` returns the phases from `project/roadmap/*.md` with numeric order (including `1.5`), and the page shows a phase strip. A work item matches a phase if it or its parent workstream lists that phase, and the row says which.
- `GET /api/project/<id>/work-items` returns the same data as JSON. HEAD matches GET on both routes. A missing bound checkout returns the framed 409, as the other project-scoped routes do.
- `_safe_capabilities`, the 405 handlers, and the CSP are unchanged, and the page needs no JavaScript. Every status shows text plus an icon or shape cue, never color alone. `/workbench` and the dashboard link to the new page.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- The agent bundles and launches the branch's LRH Console app and checks the page in light and dark mode; the owner then confirms the grouping and filters are usable.

## Risk Notes

- `serve.py` is already about 4,100 lines. Keep the new payload and renderer in focused helpers (or a small module) rather than growing the request handler.
- Loading the full project state per request could be slow on large projects. Reuse the existing cache and warmup path rather than adding a new loader.
- Sparse `related_roadmap` data will make most items "no phase". The page must say so plainly, not suggest the roadmap is empty.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md` (L2)
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (status pills, color vision)
- `docs/reference/cli/serve.md`

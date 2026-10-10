---
id: "WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES"
title: "Finish project scoping on lrh serve work-item routes"
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
- "docs/reference/cli/serve.md"
depends_on: []
blocked_by: []
expected_actions:
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
- "On /project/<id>/work-items/<wi> and /project/<id>/work-items/<wi>/prompt, every prompt-download link targets the selected project, and following it returns that project's generated prompt Markdown, never the served project's."
- "The /project/<id>/work-items/<wi>/prompt preview page's navigation links stay in the named project: Back to workbench and Back to viewer context point at /project/<id>/work-items/<wi> and /project/<id>, not /workbench or /#work-item-<wi>."
- "A registered project whose bound checkout path no longer exists returns the framed 409 no-local-checkout page on the dependency-map, work-item detail, and work-item prompt HTML routes, and the no_local_checkout JSON error on /api/project/<id>/dependency-maps/<view>, with the lrh meta set <name> --local-repo-path PATH command and a message naming the missing path on both the HTML page and the JSON error, instead of 200 'No dependency-map views' or a bare JSON 404."
- "HEAD on /project/<id>/work-items/<wi> and .../prompt returns the same status and content type as GET, including 404 and 409 selector errors, and HEAD on the dependency-map routes returns 409 for a missing bound checkout, as GET does."
- "test_project_routes_serve_the_served_projects_own_selectors asserts route-specific content instead of assertTrue(a or b)."
- "docs/reference/cli/serve.md describes the project-scoped download and the missing-checkout behavior."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "tests/cli_tests/serve_test.py"
- "docs/reference/cli/serve.md"
---

# Finish project scoping on lrh serve work-item routes

## Summary

PR #813 stopped `/project/<id>/` routes from showing the served project's data
under another project's name. Three gaps remain on the same routes:

- the work-item pages' prompt-download links, and the prompt preview page's
  navigation links, still target the served project;
- a registered project whose bound checkout has moved or been deleted gets a
  misleading page instead of the framed "No local checkout" error;
- the work-item routes have no HEAD handler.

Close these gaps so every project-scoped page and link reads the project it
names.

## Problem / Context

These gaps are follow-ups recorded in PR #813's closeout note
(`project/executions/AD_HOC/2026_10_10_02_42_50_SERVE_UNRESOLVED_PROJECT_SELECTOR_CLOSEOUT_NOTE.md`).
The PR's PR-mode self-review found them, and the owner deferred them at the
stop-work gate.

1. **Download links.** `render_project_work_item_page` builds
   `prompt_download = "/workbench/prompt?work_item=<wi>&download=1"`
   (`src/lrh/serve.py:2296`). The preview page that
   `/project/<id>/work-items/<wi>/prompt` renders through
   `render_workbench_artifact_page` links to
   `/workbench/{kind}?work_item=...&download=1` (`src/lrh/serve.py:2217`).
   `_write_workbench_artifact` (`src/lrh/serve.py:3874`) renders those routes
   with the served `config`. On project Alpha's page, either download returns
   the served project's prompt for the same work-item ID, or a 404. This is the
   PR #813 bug class: one project's data under another project's name. The
   same preview page's "Back to workbench" (`/workbench`) and "Back to viewer
   context" (`/#work-item-<wi>`) links (`src/lrh/serve.py:2215-2216`) also
   take the user out of the named project and back into the served
   project's pages.
2. **Missing bound checkout.** On the routes that use it (dependency maps,
   work-item detail, and work-item prompt), `_config_for_project_selector` returns a
   `ServeConfig` whenever the registry resolves a path, without checking that
   the path exists. If that checkout was moved or deleted:
   - `/project/<id>/dependency-maps` returns 200 "No dependency-map views";
   - a view route returns a JSON 404;
   - the work-item routes return a JSON 404.

   None of these gives the actionable 409 page.
3. **HEAD.** `do_HEAD` has no branch for `/project/<id>/work-items/...`. These
   requests fall through to `render_project_operational_dashboard` and return
   a JSON 404, even when GET returns 200 or 409.

### Duplication search

- In-repo: PR #813 (merged `d9f5b1bd`) fixed selector resolution but left
  these gaps; its closeout note lists them as deferred follow-ups. No other
  work item, proposal, or `project/design/backlog.md` entry covers them.
- External: not applicable; this is internal routing in `lrh serve`.
- Recommendation: proceed.

### Demand search

- The only request is PR #813's closeout note and the owner's decision to file
  a work item. Nothing to close or link beyond citing it here.

## Scope

- The project-scoped prompt download for the work-item detail page and the
  prompt preview page, and the preview page's navigation links.
- Missing-checkout detection in `_config_for_project_selector`, on the routes
  that use it: dependency maps (HTML, JSON API, and HEAD), work-item detail,
  and work-item prompt.
- HEAD parity for `/project/<id>/work-items/<wi>` and `.../prompt`.
- Tightening the one loose served-selectors test assertion.
- Updating the serve reference docs.

## Required Changes

1. Serve the prompt download from the selected project. Either support
   `?download=1` on `/project/<id>/work-items/<wi>/prompt`, using
   `_config_for_project_selector` and the existing download writer, or add an
   equivalent project-scoped route. Point both download links at it:
   - the work-item detail page's link;
   - the "Download Markdown" link on the preview page rendered for
     `/project/<id>/work-items/<wi>/prompt`.

   When `render_workbench_artifact_page` renders for a project-scoped route,
   point its "Back to workbench" link at `/project/<id>/work-items/<wi>` and
   its "Back to viewer context" link at `/project/<id>`. For example, pass
   project-scoped hrefs in from the caller instead of hard-coding the
   served-project links.

   Leave `/workbench/...` routes, their pages' links, and
   `/api/workbench/...` payloads unchanged for the served-project workbench.
2. In `_config_for_project_selector`, when the registry resolves a repo path
   (`selection.resolved_repo_path`) that does not exist, raise the 409
   `no_local_checkout` `ProjectSelectorError` with the
   `lrh meta set <name> --local-repo-path PATH` next action and a message
   that names the missing path.
   - Test the repo path, not `resolved_project_path`. A record without
     `project_dir` resolves to `<repo>/project`, so testing that path would
     report "No local checkout" for a repo that exists but has no `project/`
     directory. That case is a Non-Goal.
   - Update `render_project_selector_error_page` so the no-checkout page shows
     `error.message` with the bind command, instead of its fixed "has no local
     checkout" sentence. That way the missing-path wording reaches the HTML
     page, not only the JSON error. The existing never-bound case keeps a
     message that reads correctly on the page.
   - Keep the existing behavior for existing paths and for `main`.
3. Add HEAD handling for `/project/<id>/work-items/<wi>` and `.../prompt` that
   returns the same status and content type as GET.
4. Replace `assertTrue("WI-A" in body or "dependency-maps/main" in body)` in
   `test_project_routes_serve_the_served_projects_own_selectors` with
   per-route assertions.
5. Add tests:
   - the download from a non-served project returns that project's prompt;
   - the project-scoped preview page's navigation links point at
     `/project/<id>/...`, and the `/workbench/prompt` page keeps its existing
     links;
   - a registry record bound to a nonexistent path returns 409 on the HTML,
     JSON, and HEAD routes, and the HTML page and JSON message name the
     missing path;
   - HEAD on the work-item routes matches GET for 200, 404, and 409.
6. Update the "Project selectors" section of `docs/reference/cli/serve.md`.

## Non-Goals

- No changes to `/workbench/...` or `/api/workbench/...` behavior for the
  served project.
- No changes to the dashboard (`/project/<id>`), design, or workstream routes.
  They resolve projects through `_project_from_meta_selector` and keep
  their existing 404 behavior. The missing-checkout 409 applies only to
  routes that go through `_config_for_project_selector`.
- No change to how the Meta registry resolves or stores checkout bindings.
- No new handling for a bound repo that exists but has no project directory.
  It keeps today's behavior.
- No deduplication of the registry read on HEAD; it is harmless.

## Acceptance Criteria

- Every prompt-download link on a `/project/<id>/work-items/...` page targets
  the selected project and returns that project's prompt.
- The prompt preview page's navigation links stay in `/project/<id>/...`.
- On the dependency-map, work-item detail, and work-item prompt routes, a
  registered project with a missing bound checkout gets:
  - the framed 409 page from the HTML routes;
  - the `no_local_checkout` JSON error from the API route.

  Both carry the `lrh meta set` command and a message naming the missing
  path. The check tests the bound repo path.
- HEAD on the work-item routes matches GET's status and content type,
  including 404 and 409. HEAD on the dependency-map routes returns 409 for a
  missing bound checkout.
- The served-selectors test asserts route-specific content.
- `docs/reference/cli/serve.md` documents the download and missing-checkout
  behavior.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Dependencies / Order

- Builds on PR #813 (merged `d9f5b1bd`). No open dependencies.

## Risk Notes

- The missing-path check runs on every project-scoped request. Use a cheap
  `exists()` check and do not walk the tree.
- An unregistered served project keeps working through `main`. Do not add the
  existence check to the `main` fallback.
- Download responses must keep `_write_download`'s headers
  (Content-Disposition and the CSP). Reuse the existing writer rather than
  writing a new one.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `docs/reference/cli/serve.md`
- PR #813: https://github.com/xenotaur/logical_robotics_harness/pull/813

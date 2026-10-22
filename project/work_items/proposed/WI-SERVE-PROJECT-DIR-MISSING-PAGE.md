---
id: "WI-SERVE-PROJECT-DIR-MISSING-PAGE"
title: "Explain a checkout with no LRH project directory on lrh serve project routes"
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
- "A registered project whose bound checkout exists but whose resolved project directory does not exist returns 409 with a framed 'No LRH project directory' page on the dependency-map, work-item detail, and work-item prompt HTML routes, and a JSON error whose error is no_project_directory on /api/project/<id>/dependency-maps/<view>, instead of 200 'No dependency-map views' or a bare JSON 404."
- "The page and the JSON message name the missing project directory and give fixes that actually resolve the 409 for that record. When the resolved directory is the default <repo>/project, they give lrh project init --project-root <repo> and lrh meta set <name> --project-dir DIR. When the record's project_dir is custom, they give lrh meta set <name> --project-dir DIR, or lrh project init --project-root <repo> followed by lrh meta set <name> --project-dir project, because init always creates <repo>/project."
- "HEAD on those routes returns the same status and content type as GET."
- "A checkout whose project directory exists but declares no views still shows 'No dependency-map views' with 200. The main fallback, the missing-checkout 409, and the never-bound 409 are unchanged."
- "docs/reference/cli/serve.md's Project selectors section documents the new case."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "tests/cli_tests/serve_test.py"
- "docs/reference/cli/serve.md"
---

# Explain a checkout with no LRH project directory on lrh serve project routes

## Summary

When a registered project's local checkout exists but has no LRH control-plane
directory, the `lrh serve` project routes treat it like a project that simply
declares no views. The dependency-map page says "No dependency-map views ...
Add one at project/views/dependency_maps/<name>.md", and the other routes return
bare JSON 404s. The real problem is that the repository was never set up as an
LRH project, or the registry points at the wrong directory. Give this case its
own 409 page that names the missing directory and the commands that fix it.

## Problem / Context

The owner observed this on 2026-10-12, after binding local checkouts for every
registered project. Narramorph's checkout
(`/Users/centaur/Workspace/Narramorph/narramorph`) exists, but its resolved
project directory (`<repo>/project`) does not. Its "Dependency maps" page shows
the "declares none yet" text, which points at the wrong fix.

`WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES` (PR #829) deliberately kept this case
out of scope. Its 409 tests the bound repo path only, and its Non-Goal says "No
new handling for a bound repo that exists but has no project directory."

Current behavior, through `_config_for_project_selector` in
`src/lrh/serve.py`:

- The function returns a `ServeConfig` rooted at the nonexistent project
  directory.
- `/project/<id>/dependency-maps` then renders "No dependency-map views" with
  200, because `discover_views` finds nothing.
- A view route returns a JSON 404, because `build_snapshot` raises
  `FileNotFoundError`.
- The work-item routes return a JSON 404, because the core-state load fails.

The `/meta` statusboard already classifies this state as `missing_project`
with the diagnostic `PROJECT_CONTROL_DIR_NOT_FOUND`
(`_diagnostics_for_source_state`). The project routes ignore it.

Both of the relevant commands exist, but which one fixes the 409 depends on
the record:

- `lrh project init --project-root <repo>` creates the scaffolding. It always
  writes the packaged templates under `<repo>/project`
  (`src/lrh/project/bootstrap.py` `build_plan`), whatever the record's
  `project_dir` says. So it fixes the 409 only when the resolved directory is
  the default `<repo>/project`.
- `lrh meta set <name> --project-dir DIR` repoints a record at a control plane
  that already exists elsewhere in the repo.
- For a record with a custom `project_dir` (for example `control`), init
  alone leaves the registry pointing at the still-missing directory. The fix
  is either to repoint the record at an existing directory, or to run init
  and then `lrh meta set <name> --project-dir project`.

### Duplication search

- In-repo: no work item, proposal, or backlog entry covers serve's handling of
  a missing project directory. PR #829's Non-Goal names it as out of scope.
  The statusboard's `missing_project` classification is related existing
  logic to reuse, not a duplicate.
- External: not applicable; this is internal routing in `lrh serve`.
- Recommendation: proceed.

### Demand search

- The only demand is the owner's request after the Narramorph observation and
  the Non-Goal in `WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`. There is nothing
  to close or link.

## Scope

- Detect, in `_config_for_project_selector`, a bound checkout that exists but
  whose resolved project directory does not. Cover both cases:
  - an explicit `project_dir`;
  - the `<repo>/project` default for records without one.
- Add a 409 `no_project_directory` error, with its own page text and next
  actions, on the routes that go through `_config_for_project_selector`:
  dependency maps (HTML, JSON API, HEAD), work-item detail, and work-item
  prompt.
- Add tests and update the docs.

## Required Changes

1. After the existing checks in `_config_for_project_selector`, raise a
   `ProjectSelectorError` with status 409 and error `no_project_directory`
   when the repo path exists but the resolved project path does not. Use the
   path after the `<repo>/project` default is applied. Name the missing
   directory in the message.
   - `ProjectSelectorError.next_action` currently always returns the
     `--local-repo-path` command. Generalize it so each error carries its own
     next action or actions. For this case, choose them by directory:
     - **Default directory** (the resolved path is `<repo>/project`, whether
       `project_dir` is unset or `project`): give
       `lrh project init --project-root <repo>` and
       `lrh meta set <name> --project-dir DIR`.
     - **Custom `project_dir`**: give `lrh meta set <name> --project-dir DIR`,
       and the combined repair `lrh project init --project-root <repo>`
       followed by `lrh meta set <name> --project-dir project`. Do not offer
       init alone, which would not resolve the 409.
   - Keep `no_local_checkout`'s payload and next action unchanged.
2. Make `render_project_selector_error_page` render this case with the title
   "No LRH project directory", the message, and that record's commands. The existing
   "No local checkout" and "Project not found" pages must not change.
3. HEAD on these routes must return the same status and content type as GET.
   The existing selector pre-checks should cover this automatically; verify it
   in tests.
4. Add tests in `tests/cli_tests/serve_test.py`:
   - A record bound to an existing repo with no `project/` directory returns
     409 on the HTML routes, HEAD, and the JSON API. Assert the page and the
     message name the directory and the default-directory commands.
   - Cover a record without `project_dir`, and one with an explicit
     `project_dir = "project"`. Both get the default-directory commands.
   - Cover a record with a non-default `project_dir` (for example `control`).
     It gets the custom-directory commands, and the page does not offer
     `lrh project init` on its own.
   - A repo whose `project/` exists but has no views still returns 200 "No
     dependency-map views".
5. Update the "Project selectors" section of `docs/reference/cli/serve.md`.

## Non-Goals

- No change to the `/meta` statusboard or the `/project/<id>` dashboard, which
  already report `missing_project` their own way.
- No automatic scaffolding. Serve stays read-only and only suggests
  `lrh project init`.
- No change to the `main` fallback, the missing-checkout 409, or the
  never-bound 409.
- No change to how the Meta registry resolves paths.

## Acceptance Criteria

- On the dependency-map, work-item detail, and work-item prompt routes, a
  bound checkout with no project directory gets:
  - a framed 409 "No LRH project directory" page;
  - a `no_project_directory` JSON error from the API.

  Both name the missing directory and give fix commands that resolve the
  409 for that record. A default `<repo>/project` directory gets init and
  repoint. A custom `project_dir` gets repoint, or init followed by
  repointing to `project`.
- HEAD matches GET's status and content type for those routes.
- A project directory with no views still shows "No dependency-map views"
  with 200. The other selector outcomes are unchanged.
- `docs/reference/cli/serve.md` documents the case.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Dependencies / Order

- Builds on PR #829 (`WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`, merged
  `273c92d4`). No open dependencies.

## Risk Notes

- Check the resolved project path, not the bound repo path. The repo-path 409
  from PR #829 must still win when the checkout itself is gone.
- `ServeConfig.resolved_project_root()` falls back to the given path when it
  finds no project directory. Make sure the new check runs before any route
  builds a config from a nonexistent directory.
- Keep the generalized next-action field backward compatible for the
  `no_local_checkout` JSON payload, which tests and LRH Console may read.
- Don't advertise a fix that leaves the 409 in place. `lrh project init`
  always targets `<repo>/project`, so pair it with repointing for a custom
  `project_dir`.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `docs/reference/cli/serve.md`
- PR #829: https://github.com/xenotaur/logical_robotics_harness/pull/829

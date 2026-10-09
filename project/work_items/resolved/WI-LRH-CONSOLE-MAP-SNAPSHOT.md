---
id: "WI-LRH-CONSOLE-MAP-SNAPSHOT"
title: "Build the typed DependencyMapSnapshot and dependency-map view declarations"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #796 (commit b0f55c74). src/lrh/dependency_maps/ builds the read-only, versioned DependencyMapSnapshot from view declarations at project/views/dependency_maps/<name>.md (ordered workstream lanes, ordered phases, lane overrides with reasons; checked by lrh validate, including the view-id file-name grammar). It carries nodes, typed depends_on and blocked_by edges, lane and phase placement with Unplaced rows and provenance, and no absolute paths; structural state follows the Revision 2 precedence (unknown lifecycles are never eligible), with lifecycle, prompt-ready, and authorization as separate layers. Diagnostics cover missing references, cycles per edge type, unknown view IDs, ambiguous or unplaced placement, unused overrides, invalid lifecycles, and partial sources; offscreen predecessors are kept and counted. GET /api/project/<id>/dependency-maps/<view> and lrh dependency-map snapshot <view> return the same JSON, and from_dict type-checks it. This workstream has its own view, lrh-console-l1. The stale_snapshot check is Python-level; surfacing it is deferred to WI-LRH-CONSOLE-MAP-STATIC. An unresolvable project id falls back to the served project, as the other project routes do.'
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
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
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
- "A declared view produces a versioned snapshot with nodes, typed edges, lane and phase placement (including Unplaced), diagnostics, and provenance, with no absolute paths."
- "Structural states follow the Revision 2 precedence, including `blocked: true` with its reason and abandoned items. Lifecycle, prompt-ready, and authorization stay separate."
- "Missing IDs, cycles, ambiguous placement, and stale sources produce explicit diagnostics. `lrh validate` reports invalid view declarations."
- "`GET /api/project/<project_id>/dependency-maps/<view>` and `lrh dependency-map snapshot <view>` return the same versioned JSON, and an unknown view gives a 404 or a non-zero exit."
- "Tests cover each state, each diagnostic, the serialization round trip, the route, and the CLI."
required_evidence:
- "test_output"
- "lrh_validate"
artifacts_expected:
- "src/lrh/dependency_maps/"
- "src/lrh/serve.py"
- "src/lrh/control/validator.py"
- "project/views/dependency_maps/ (an example or this repository's own view)"
- "src/lrh/cli/main.py"
- "tests/cli_tests/serve_test.py"
- "tests/ (snapshot and CLI tests)"
---

# Dependency-map snapshot

## Summary

Build the typed, versioned projection that every dependency-map view renders from, as decided in the dogfood proposal §5–§6 and the Revision 2 status model (Q3). It covers nodes, typed edges, lane and phase placement, the three status layers, diagnostics, and provenance. Add the view declaration that maps a project's work items onto lanes and phases.

## Problem / Context

The L1 map must be truthful before it is interactive (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:226-275`). Revision 2 fixes the structural states and their precedence: Done, then Blocked (an explicit `blocked_by` that is not done, or the work item's own `blocked` flag with its `blocked_reason`, `src/lrh/control/models.py:46-47`), then In progress, Waiting, and Unblocked. Abandoned items are never Done. "Ready" is split into unblocked, prompt-ready, and authorized. No effort or critical-path data exists or may be invented (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:250`).

### Duplication search

In-repo: `src/lrh/control/planning_tree.py` builds the workstream planning tree and finds workstream cycles (`_find_workstream_cycles`, around line 646), but it models parent and child relationships, not `depends_on` and `blocked_by` edges. Its edge semantics must be reviewed before any reuse (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:267-269`). No dependency-map module exists. Recommendation: proceed with a new module, for example `src/lrh/dependency_maps/`.

## Scope

- A typed snapshot model with a versioned serialization.
- A view declaration file format and its validation.
- Structural-state derivation and readiness layering.
- Diagnostics.
- A read-only JSON route, `GET /api/project/<project_id>/dependency-maps/<view>`, and a CLI command, `lrh dependency-map snapshot <view> [--project-root PATH]`.

## Required Changes

1. Define `DependencyMapSnapshot` with these fields: schema version, project and view IDs, repository and checkout identity, a source fingerprint that also covers uncommitted control-file changes, generation time, nodes, typed edges (`depends_on`, `blocked_by`), lane and phase assignments with a visible Unplaced row, diagnostics, and provenance for derived fields. Do not export absolute local paths.
2. Define the view declaration at `project/views/dependency_maps/<name>.md`. It holds the view identity, ordered lanes and phases, and mappings by canonical ID; it does not duplicate tasks or edges. Validate it in `lrh validate`. Lanes default to canonical workstream grouping (`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md:245`).
3. Derive the structural state using the Revision 2 precedence, including the explicit blocked flag and abandoned items. Carry lifecycle and the existing `prompt_ready` readiness separately. Authorization is never derived.
4. Detect and report missing references, cycles (by edge type), partial source state, ambiguous or unplaced items, and stale snapshots. Filters must never hide a blocker.
5. Expose the snapshot read-only. Serve answers `GET /api/project/<project_id>/dependency-maps/<view>` with the versioned JSON, matching the existing `/project/<project_id>/` routes, and returns 404 for an unknown view. `lrh dependency-map snapshot <view> [--project-root PATH]` prints the same JSON to stdout, exits 0 on success, and exits non-zero with an error on stderr for an unknown or invalid view.

## Non-Goals

- No rendering (`WI-LRH-CONSOLE-MAP-STATIC`).
- No effort, duration, or critical path.
- No scheduling or automatic placement presented as canonical.

## Acceptance Criteria

- A declared view produces a versioned snapshot with nodes, typed edges, lane and phase placement (including Unplaced), diagnostics, and provenance, with no absolute paths.
- Structural states follow the Revision 2 precedence, including `blocked: true` with its reason and abandoned items. Lifecycle, prompt-ready, and authorization stay separate.
- Missing IDs, cycles, ambiguous placement, and stale sources produce explicit diagnostics. `lrh validate` reports invalid view declarations.
- `GET /api/project/<project_id>/dependency-maps/<view>` and `lrh dependency-map snapshot <view>` return the same versioned JSON, and an unknown view gives a 404 or a non-zero exit.
- Tests cover each state, each diagnostic, the serialization round trip, the route, and the CLI.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Dependencies / Order

- No dependencies. It can run in parallel with `WI-LRH-CONSOLE-TOKENS`.
- `WI-LRH-CONSOLE-MAP-STATIC` renders from it.

## Risk Notes

- Reusing the workstream cycle helper as-is would mix parent and child edges with dependency edges. Review its semantics before sharing it.
- A Git HEAD fingerprint alone misses uncommitted control-file edits; include file content in the fingerprint.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (Revision 2 decisions)
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

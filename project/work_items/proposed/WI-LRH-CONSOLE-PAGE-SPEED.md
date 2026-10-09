---
id: "WI-LRH-CONSOLE-PAGE-SPEED"
title: "Make LRH Console pages fast: libyaml, parse once, cache project state, show loading"
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
depends_on:
- "WI-LRH-CONSOLE-STATUSBOARD"
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
- "A before-and-after timing table for /meta, /, /project/<id>, and a dependency map, on the owner's registry, is recorded in the PR."
- "Repeat requests with unchanged control files are served from a cache and are at least 5x faster than today's roughly 3 s."
- "Any change to a project's control files (add, edit, delete, rename) is reflected on the next request; tests prove the cache is invalidated."
- "Validation results, diagnostics, and every rendered page are identical with and without the cache."
- "LRH Console shows a loading indication during slow navigations, and pages work unchanged without scripts."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/control/parser.py"
- "src/lrh/control/validator.py"
- "src/lrh/core_state.py"
- "src/lrh/serve.py"
- "apps/desktop/src-tauri/src/shell.rs"
- "tests/ (cache and parser tests)"
---

# Fast LRH Console pages

## Summary

Every LRH Console page takes about 3 seconds against the owner's registry, and the owner, checking PR #805, thought the app had stalled. Make pages fast by parsing YAML with libyaml, parsing each control file once, and caching each project's state until its files change. Show a loading indication for the slow cases that remain.

## Problem / Context

These timings were measured on 2026-10-09 against the owner's 8-project registry, with the machine busy:

| Page | Time |
|---|---|
| `/meta` | 2.7 to 3.1 s |
| `/` (Workspace) | 3.4 s |
| `/project/logical_robotics_harness` | 3.1 s |
| `/project/logical_robotics_harness/dependency-maps/lrh-console-l1` | 1.0 s |

A profile of `render_meta_dashboard` shows that about 85% of the time is spent in `load_core_project_state`, mostly in `_resolve_validation_report` and `validator.validate_project`. One render makes 28,563 calls to `yaml.safe_load` across 2,836 files: each file's frontmatter is parsed many times, and every parse uses the pure-Python loader (`src/lrh/control/parser.py:79`). PyYAML's C loader (`yaml.CSafeLoader`) is available in the pinned environment. The dependency-map snapshot is rebuilt on every request, which costs about 0.8 s (noted at the PR #800 closeout).

### Duplication search

In-repo: there is no cache in `src/lrh/core_state.py` or `src/lrh/serve.py`. The snapshot fingerprint in `src/lrh/dependency_maps/snapshot.py` already hashes the control files and could key a cache. Recommendation: proceed.

## Scope

- Control-file parsing and project-state loading for `lrh serve`, and a cache in front of them.
- A loading indication in LRH Console and in `--interactive` pages.

## Required Changes

1. **libyaml:** use `CSafeLoader` when it is available, and fall back to `SafeLoader`. Error messages and the data parsed must not change.
2. **Parse once:** within a request, parse each control file's frontmatter once and share the result between the loader and the validator.
3. **Cache:** cache each project's core state (and dependency-map snapshots) per project root, keyed by a cheap fingerprint of control-file paths, sizes, and modification times. A thread-safe store bounds the cache.
4. **Loading indication:** LRH Console shows a native overlay or progress cue while a navigation takes longer than about 300 ms. In `--interactive` mode, the page dims after a same-origin link is clicked. Script-free pages are unchanged.

## Non-Goals

- No background prefetching or file watchers in this item.
- No change to validation rules or to what any page shows.

## Acceptance Criteria

- A before-and-after timing table for /meta, /, /project/<id>, and a dependency map, on the owner's registry, is recorded in the PR.
- Repeat requests with unchanged control files are served from a cache and are at least 5x faster than today's roughly 3 s.
- Any change to a project's control files (add, edit, delete, rename) is reflected on the next request; tests prove the cache is invalidated.
- Validation results, diagnostics, and every rendered page are identical with and without the cache.
- LRH Console shows a loading indication during slow navigations, and pages work unchanged without scripts.

## Validation

- `scripts/format --check --diff [--desktop]`
- `scripts/lint [--desktop]`
- `scripts/test [--desktop]`
- `lrh validate`
- Re-measure the table above. The owner checks navigation speed in LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-STATUSBOARD`, which adds the statusboard this item measures.
- This is the highest-priority remaining LRH Console item: the delay affects every click.

## Risk Notes

- A stale cache would show wrong project state. Key the cache on file metadata, never on time alone, and test every way a file can change. Same-size edits made within the timestamp's resolution are an edge case; document it, or include a content hash for files under a size limit.
- `lrh validate` output must stay byte-identical whichever YAML loader is used.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

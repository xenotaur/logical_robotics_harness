---
id: "WI-LRH-CONSOLE-CACHE-WARMUP"
title: "Warm the lrh serve project-state cache in the background so first visits are fast"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #817 (commit 3cff4c29). All acceptance criteria are met: after lrh serve starts, a daemon thread warms the ProjectStateCache for /meta projects, the served project, and every registered project with a local checkout (core state, loaded control files, and dependency-map views), without delaying the listening line, the desktop-protocol ready event (warm-up starts only after ready, through a new on_ready hook in desktop_protocol, which was not in the planned file list), or any request; ProjectStateCache.get is single-flight, so a request racing warm-up waits for the same build, with a 60 s fallback and published fallback results; failures are listed on stderr and never change a response; and the PR records first-visit times, about 50 to 80 ms after warm-up against 2 to 2.7 s cold. The owner checked it in LRH Console after Server > Restart: first clicks feel instant. The carried-over check that an edited title appears without a restart is still pending, and a server test covers it.'
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
- "WI-LRH-CONSOLE-PAGE-SPEED"
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
- "After lrh serve starts, a background thread fills the ProjectStateCache for the served project and every registered project with a local checkout, without delaying the listening line, the desktop-protocol ready event, or any request."
- "A request that arrives while warm-up is still computing the same value waits for that computation instead of starting a second one, or the PR records why duplicate work is acceptable."
- "Warm-up failures are logged to stderr and never crash the server or change any response; pages stay identical with and without warm-up."
- "A before-and-after table of first-visit times for /meta, /, and a project page, measured a few seconds after start on the owner's registry, is recorded in the PR."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "src/lrh/core_state.py"
- "tests/ (warm-up tests)"
---

# Background cache warm-up

## Summary

Fill `lrh serve`'s project-state cache in the background at startup, so that the first visit to each page is as fast as a repeat visit.

## Problem / Context

`WI-LRH-CONSOLE-PAGE-SPEED` (PR #811) added `core_state.ProjectStateCache`. Repeat visits now take about 55 ms, but the first visit to each project still pays a full validation and load: about 2.7 s for `/meta` on the owner's 8-project registry. The libyaml loader would have cut that to about 1 s, but it was dropped in PR #811 because libyaml and PyYAML's pure-Python loader disagree on some inputs. Fuzzing missed cases twice, and `lrh validate` must not depend on which loader is installed. The owner chose exactness, plus this follow-up. The page-speed work item ruled out background prefetching, so it is a separate item.

### Duplication search

In-repo: `lrh serve` starts no background work today (`src/lrh/serve.py`, `create_http_server` and the desktop-protocol server factory). Recommendation: proceed.

## Scope

- A daemon thread, started after the server binds, warms the cache for the served project and for registered projects with local checkouts.
- Single-flight computation in `ProjectStateCache`, so a request and the warm-up never build the same value twice at once.

## Required Changes

1. Add single-flight `get` to `ProjectStateCache`: concurrent callers for the same key and fingerprint wait for one computation.
2. Start the warm-up after binding, in both foreground and `--desktop-protocol` modes, never blocking startup or the ready event.
3. Log warm-up errors to stderr, and add tests for single-flight, error isolation, and that responses are unchanged.
4. Measure first-visit times shortly after start, and record them in the PR.

## Non-Goals

- No file watchers or periodic re-warming; the fingerprint check on each request stays the freshness mechanism.
- No change to page output.

## Acceptance Criteria

- After lrh serve starts, a background thread fills the ProjectStateCache for the served project and every registered project with a local checkout, without delaying the listening line, the desktop-protocol ready event, or any request.
- A request that arrives while warm-up is still computing the same value waits for that computation instead of starting a second one, or the PR records why duplicate work is acceptable.
- Warm-up failures are logged to stderr and never crash the server or change any response; pages stay identical with and without warm-up.
- A before-and-after table of first-visit times for /meta, /, and a project page, measured a few seconds after start on the owner's registry, is recorded in the PR.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `tests/smoke/desktop_protocol_smoke.py` (startup and ready timing).
- The owner checks first-visit speed in LRH Console.
- Pending owner check, carried over from `WI-LRH-CONSOLE-PAGE-SPEED`: edit a work item title in a registered project's checkout and confirm the next click shows it without a restart. A server test already covers this.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-PAGE-SPEED`, which adds the cache.

## Risk Notes

- Warm-up competes with the first requests for CPU. Keep it to one thread, and let requests take priority by sharing results through single-flight.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`

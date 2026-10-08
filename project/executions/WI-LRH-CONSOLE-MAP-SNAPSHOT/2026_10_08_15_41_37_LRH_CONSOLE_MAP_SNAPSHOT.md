---
execution_id: 2026_10_08_15_41_37_LRH_CONSOLE_MAP_SNAPSHOT
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-SNAPSHOT:LRH_CONSOLE_MAP_SNAPSHOT)[2026-10-08T15:07:33+00:00]
work_item: WI-LRH-CONSOLE-MAP-SNAPSHOT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/796
commit:
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated\")"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T15:41:37+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-MAP-SNAPSHOT` through `/lrh-execute`:
the typed, versioned `DependencyMapSnapshot`, dependency-map view declarations, their
validation, a read-only JSON route, and a CLI. The owner approved the chain and run plan in
this session ("Approve as stated").

# Result

- **`src/lrh/dependency_maps/view.py` (new):** the declaration format at
  `project/views/dependency_maps/<name>.md`: id (matching the file name), title, ordered
  `lanes` (canonical workstreams), ordered `phases` with work-item IDs, and optional
  `lane_overrides` with reasons. It provides `parse_view`, `load_view` (rejecting unsafe ids)
  and `reference_problems`.
- **`src/lrh/dependency_maps/snapshot.py` (new):** `build_snapshot`, `structural_state`,
  `source_fingerprint`, `freshness_diagnostics`, and the dataclasses with a JSON round trip
  (`to_json` and `from_dict`, schema version 1).
  - **State precedence:** done; blocked (flag or unmet `blocked_by`); in progress; waiting;
    unblocked (with `no_prerequisites`); abandoned. Each state carries its reasons, and
    lifecycle, `prompt_ready` and authorization stay separate.
  - **Placement:** by workstream `work_items` or `parent_id`, or by an override with a reason.
    Ambiguous or missing placement uses the Unplaced rows.
  - **Offscreen references** are kept as nodes and counted as distinct items.
  - **Cycles** are found with an iterative Tarjan, separately for each edge type.
  - **No absolute paths:** the checkout ID is a hash of the path, and the Git HEAD comes from
    `git rev-parse` with a timeout.
- **`src/lrh/control/validator.py`:** `_validate_dependency_map_views` reports
  `DEPENDENCY_MAP_VIEW_INVALID` and `DEPENDENCY_MAP_VIEW_UNKNOWN_REFERENCE`.
- **`src/lrh/serve.py`:** `GET /api/project/<project_id>/dependency-maps/<view>`
  (`dependency_map_payload`) returns 200, 404, 422 or 500. HEAD
  (`dependency_map_head_status`) checks the declaration only. The route list is updated.
- **`src/lrh/cli/main.py`:** `lrh dependency-map snapshot <view> [--project-root PATH]` exits
  0, exits 1 with the error on stderr, or exits 2 with no subcommand.
- **`project/views/dependency_maps/lrh-console-l1.md` (new):** this workstream's real view,
  with one lane and five phases (L0, foundation, map, statusboard, evaluation). Its snapshot
  has 17 nodes and no diagnostics.
- **Tests:**
  - `tests/dependency_maps_tests/snapshot_test.py` (31 tests): every state, every diagnostic,
    placement, offscreen nodes, round trip, no absolute paths, staleness, declarations, and
    `lrh validate`.
  - `tests/cli_tests/dependency_map_test.py` (2 tests).
  - `serve_test.py`: the route and HEAD, including errors, and identical JSON from route and
    CLI.
- **Docs:** `docs/reference/cli/dependency-map.md` (new), plus the `lrh serve` route section
  and the CLI index.

**Pre-push cold review.** Verdict: safe to push, with no must-fix items. It verified the
precedence, Tarjan's correctness, traversal safety, determinism, and the git subprocess.
Applied in `7aa6be78`:

- HEAD no longer builds the snapshot;
- `OSError` becomes `SnapshotError`, so the route returns a 500;
- duplicate overrides are rejected, and overrides outside the view are diagnosed;
- cycles through offscreen items are reported, and the cycle message no longer implies edges;
- offscreen predecessors are counted as distinct items;
- added `no_prerequisites` and phase de-duplication;
- `from_dict` raises `ValueError`;
- `--project-root` also accepts the `project/` directory;
- added tests for each of these.

**Decisions recorded:**

- A `project_id` that the registry cannot resolve falls back to the served project, as the
  other `/project/<id>/` routes do. This is documented.
- `stale_snapshot` is a Python-level check (`freshness_diagnostics`). Surfacing it to users is
  deferred to `WI-LRH-CONSOLE-MAP-STATIC`, which shows freshness.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass (2085 tests).
- `lrh validate`: 0 errors, 0 warnings.
- `lrh dependency-map snapshot lrh-console-l1` exits 0 with 17 nodes and no diagnostics.

# Follow-up

- `WI-LRH-CONSOLE-MAP-STATIC` renders this snapshot, and shows freshness through
  `freshness_diagnostics`.

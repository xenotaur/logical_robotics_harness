---
execution_id: 2026_10_08_17_50_05_LRH_CONSOLE_MAP_SNAPSHOT_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-SNAPSHOT:LRH_CONSOLE_MAP_SNAPSHOT_REVIEW)[2026-10-08T17:50:05+00:00]
work_item: WI-LRH-CONSOLE-MAP-SNAPSHOT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/796
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/796"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T17:50:05+00:00
---


# Summary

This record covers review-response round 1 for PR #796 (`WI-LRH-CONSOLE-MAP-SNAPSHOT`), run as
part of `/lrh-land` inside `/lrh-execute`.

- **CI** passed 7/7 on `06caae42`.
- **Copilot** reviewed `06caae42` and left 2 threads.
- **Codex** reviewed `7aa6be78` and left 3 P2 threads.
- **The owner's decision:** "Yes, apply all five".

# Result

All five were fixed in `471278b5`.

1. **Copilot, `snapshot.py` `from_dict`, which accepted wrongly typed payloads.** A
   hint-driven `_typed` and `_value` check every field: str, int (not bool), bool, optional,
   tuple and nested dataclasses, with exact field sets. Allowed values are checked for states,
   edge kinds, reason kinds and severities. Any mismatch raises `ValueError`.
2. **Copilot, `view.py` `parse_view`, which turned `OSError` into a 422.** Read errors now
   propagate. `build_snapshot` wraps them as `SnapshotError`, so GET returns 500, and HEAD
   returns an explicit 500. `lrh validate` still reports them as `DEPENDENCY_MAP_VIEW_INVALID`.
3. **Codex P2, unknown lifecycles fell through to unblocked.** A status outside `proposed`,
   `active`, `resolved` and `abandoned` now gets state `unknown` and an `invalid_lifecycle`
   error diagnostic.
4. **Codex P2, `freshness_diagnostics` mis-hashed the `project/` directory.** It now uses the
   same `repository_root` normalization as `build_snapshot`.
5. **Codex P2, `lrh validate` approved view file names that could never load.** `parse_view`
   now applies the view-id grammar to the file name.

Docs updated: `docs/reference/cli/dependency-map.md` (the `unknown` state,
`invalid_lifecycle`, and `from_dict` checking) and `docs/reference/cli/serve.md` (500 for a
read error).

A correction to the primary record and the PR body: they say "31 snapshot and view tests".
There were 28 snapshot and view tests at `06caae42`, plus 2 CLI tests.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass (2091 tests).
- `lrh validate`: 0 errors, 0 warnings.
- The real view `lrh-console-l1` still has 17 nodes and no diagnostics.

# Follow-up

Next is confirm-fixes: resolve the 5 threads, then re-check CI.

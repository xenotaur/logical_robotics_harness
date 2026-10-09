---
execution_id: 2026_10_08_06_24_55_SERVE_META_WORKSPACE_DETAIL_404_SELFREVIEW
prompt_id: PROMPT(AD_HOC:SERVE_META_WORKSPACE_DETAIL_404_SELFREVIEW)[2026-10-08T06:24:55+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/793
commit: a15e878c1a162fb1dc9ef37a40a269900687c12e
created_at: 2026-10-08T06:24:55+00:00
agent: claude-app
instruction_source: "ad-hoc: lrh-self-review diff-mode from lrh-implement Step 7.5 for PROMPT(AD_HOC:SERVE_META_WORKSPACE_DETAIL_404)[2026-10-08T06:04:24+00:00]"
session_transcript: claude-app:5a942286-523d-4024-a56b-96e1f2a712b6
---

# Summary

Diff-mode `/lrh-self-review` pass, report-only (no `--apply`), run before the
first push of the ad-hoc fix that makes `_project_from_meta_selector` in
`src/lrh/serve.py` catch `MetaWorkspaceResolutionError` and
`MetaRegistryError`. A cold-context `general-purpose` subagent reviewed the
working-tree diff. `rerun_of` stays empty by design, because diff-mode runs
before the primary execution record exists.

# Result

Findings: 0 blocking, 2 minor non-blocking.

- Minor: the new test covers GET only. HEAD uses the same fixed function.
- Minor: the `HTTPError` body is read without closing it. This matches the
  file's existing pattern, and no `ResourceWarning` appeared under
  `-W always::ResourceWarning`.
- Out of scope, already present before this change:
  `control_loader.load_project` in the detail renderers can still raise on a
  malformed project after a workspace resolves.

The invoking session re-verified the top finding directly. The `do_GET`
design and workstream branches (`src/lrh/serve.py` around lines 2918-2935)
send non-200 renderer results through `_write_json`. The new test fails with
2 subtest errors when the fix is stashed and passes when it is restored.

No fixes were applied. The PR proceeds as planned.

# Validation

- Subagent ran the new test and the 81-test `serve_test.py` suite: pass.
- Subagent monkeypatched the old function back in: both subtests fail with
  `RemoteDisconnected`.

# Follow-up

- Optionally wrap `control_loader.load_project` in the detail renderers the
  way the work-item routes already do.

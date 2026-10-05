---
execution_id: 2026_10_04_15_06_24_ACTIVATE_WS_LRH_CONSOLE_LOCAL_DOGFOOD
prompt_id: PROMPT(AD_HOC:ACTIVATE_WS_LRH_CONSOLE_LOCAL_DOGFOOD)[2026-10-04T15:06:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/765
commit: 3915a3dc1f4362fd20a7337d6a80521578fd46e6
agent: "claude_app"
instruction_source: "user request in session: do the data fix to activate WS-LRH-CONSOLE-LOCAL-DOGFOOD"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-04T15:06:24+00:00
---

# Summary

The owner noticed that the LRH Console dashboard's "Active workstreams" list
left out `WS-LRH-CONSOLE-LOCAL-DOGFOOD`, although they had synced to `main`
before building. This ad-hoc planning change fixes the data.

# Result

**Diagnosis.** Serve's dashboard filters on `workstream.status == "active"`
(`src/lrh/serve.py:343-347`). The workstream was still in
`project/workstreams/proposed/` with `status: "proposed"` and `stage:
"planned"`, although five of its six leaves had executed and resolved (PRs
#750 to #763). Under `project/design/workstream_schema_mvp.md` § Status
semantics, that is stale. No chain skill promotes a workstream from
`proposed` to `active`, and earlier activations were manual planning commits
(`b757b20b`, `ebf53365`, `dca956d8`).

**Fix:**

- Moved the workstream to `project/workstreams/active/` and set `status:
  "active"` and `stage: "executing"`.
- Rewrote the body paragraph that called it a proposed node that "does not
  activate execution".
- Repointed path references in the six console work items and in the
  `lrh-console-local-dogfood` proposal. Historical execution records keep
  their original paths.

**Deferred.** The systemic fix is a programmatic LRH state-transition command
that skills call instead of editing files by hand, plus a cheaper
`lrh validate` warning. It is recorded as P5 in the owner's working
dogfood-impressions document. At the owner's direction, it is not filed in
this PR.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `scripts/format --check --diff` and `scripts/lint` passed, using the
  `LrhLocalAgent` env's pinned tools with `PYTHONPATH` set to this worktree.
- `scripts/test` passed.
- `project_viewer_payload(ServeConfig(project_root=Path(".")))` now lists
  `WS-INVOCATION-AND-GATE-RESET`, `WS-LOCAL-AGENT-DOGFOOD`,
  `WS-LRH-ASSISTANTS`, and `WS-LRH-CONSOLE-LOCAL-DOGFOOD`.

# Follow-up

- After merge, the owner should pull the main checkout that the app serves,
  then use Server > Restart. No rebuild is needed, because this is a data
  change.
- When the dogfood work item resolves, `/lrh-closeout` offers to close this
  workstream.

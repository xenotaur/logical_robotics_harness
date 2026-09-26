---
execution_id: 2026_09_26_01_40_23_LOCAL_AGENT_LANE_APPROVAL
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_LANE_APPROVAL)[2026-09-26T01:31:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/730
commit: 5ae4ce54ed59a0cc0165e3578730b61cf050d031
created_at: 2026-09-26T01:40:23+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner-approved WI-LOCAL-AGENT-001 activation packet (readiness review in the same session)
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

PR A of the approved `WI-LOCAL-AGENT-001` activation plan. It records the owner's
stage-0 lane approval in `PROP-LOCAL-AGENT-DOGFOOD`, which stays `proposed`. It
activates `WS-LOCAL-AGENT-DOGFOOD` and `WI-LOCAL-AGENT-001`, and makes the narrow
canonical reconciliations needed before implementation.

# Result

- **Readiness review** (read-only, same session):
  - No canonical sequencing decision blocks the lane.
  - Three tensions were identified and resolved here: the focus non-goal at
    `current_focus.md:102`, the `/private/tmp` rule in `experimental/README.md`,
    and the execution framework's silence on experiments.
  - A misbound global `lrh` install and unpinned dev tools were fixed by
    creating a worktree-bound conda env with `scripts/conda-worktree-env`.
- **Proposal:** adds a Stage-0 Lane Approval section covering approved and
  not-approved scope, the committed-evidence rule, the binding floor plus
  advisory targets, and the local-only adapter checks. Fixes two drifted
  citations and adds an Open Questions note.
- **WS:** now `active/executing`, in `workstreams/active/`.
- **WI-001:** now `active`, in `work_items/active/`. Adds the activation refresh,
  `experiments/01_local_agent_briefing/` in `artifacts_expected`, "scored model
  outputs" in Required Change 5, and a multi-PR resolution note.
- **Focus, execution framework, and `experimental/README.md`:** each gets a
  one-paragraph reconciliation.
- **Unchanged:** `WI-LOCAL-AGENT-002` (still `proposed`). No code was added.
- **Prior art:** no duplication. `WS-LRH-CONSOLE-LOCAL-DOGFOOD` is adjacent
  (local desktop app, not local model).

# Validation

- `scripts/version tools`: Python 3.11.16, ruff 0.15.12, black 26.3.1
  (env `LrhLocalAgent`).
- `scripts/format --check --diff` and `scripts/lint`: clean.
- `scripts/test --log`: Ran 1730 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LOCAL-AGENT-001`: `status: active`,
  `prompt_ready: true`.
- `/lrh-self-review` diff-mode: see
  `2026_09_26_01_39_22_LOCAL_AGENT_LANE_APPROVAL_SELFREVIEW.md`. Five findings
  were fixed.

# Follow-up

- PR B: implement `WI-LOCAL-AGENT-001` (pre-registration plus prototype) via
  `/lrh-execute WI-LOCAL-AGENT-001`. Its closeout records partial progress and
  must not resolve the WI.
- Out of scope: `WS-LRH-CONSOLE-LOCAL-DOGFOOD` and its proposal still describe
  PR #719 as open.

---
execution_id: 2026_10_08_06_19_49_LRH_CONSOLE_FRAME_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-FRAME:LRH_CONSOLE_FRAME_CONFIRM)[2026-10-08T06:19:49+00:00]
work_item: WI-LRH-CONSOLE-FRAME
status: landed
rerun_of: 2026_10_08_06_02_54_LRH_CONSOLE_FRAME
pr: https://github.com/xenotaur/logical_robotics_harness/pull/792
commit: bf4f8f248e15e2319d6adce9c777c3f54db105f3
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/792"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-08T06:19:49+00:00
---


# Summary

This record covers `/lrh-confirm-fixes` for PR #792 (`WI-LRH-CONSOLE-FRAME`), run inline from
`/lrh-land` after review-response round 1 (`05deca2b`, record in `9da05d9c`).

# Result

**Thread.** The single Copilot thread, on unloadable projects being dropped from the scope
switcher, was checked against the diff: `_frame_projects` now builds every entry with
`selector=result.registry_name`. It was resolved with `resolveReviewThread`.

**Substitute cold review of `83a3d3e5..9da05d9c`** (the hosted bots reviewed only earlier
commits). Verdict: safe to merge, with no must-fix or should-fix items. It confirmed:

- the label fallback in every case;
- escaping in `frame.py`;
- that `/project/<registry_name>` matches the unavailable card's own `detail_url`, and
  `render_project_operational_dashboard` returns 200 for it;
- 103 passing tests;
- that the review record is accurate.

Its one nit, the comment wording in `_frame_projects`, is applied in this commit.

**The owner's Mac check** passed on this branch's built app: the gear opens Settings and the
main window doesn't change; Settings opens and closes; the LRH icon goes to the statusboard;
the rail collapses.

# Validation

- `scripts/lint` passes.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Next is CI on the commit that carries this record, then the single ask for merge and closeout.

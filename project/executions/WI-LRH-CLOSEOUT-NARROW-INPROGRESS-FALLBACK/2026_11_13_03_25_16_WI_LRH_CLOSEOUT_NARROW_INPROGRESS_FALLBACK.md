---
execution_id: 2026_11_13_03_25_16_WI_LRH_CLOSEOUT_NARROW_INPROGRESS_FALLBACK
prompt_id: PROMPT(WI-LRH-CLOSEOUT-NARROW-INPROGRESS-FALLBACK:WI_LRH_CLOSEOUT_NARROW_INPROGRESS_FALLBACK)[2026-11-13T03:05:23+00:00]
work_item: WI-LRH-CLOSEOUT-NARROW-INPROGRESS-FALLBACK
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/873
commit:
created_at: 2026-11-13T03:25:16+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CLOSEOUT-NARROW-INPROGRESS-FALLBACK.md
session_transcript: pending
---

# Summary

Narrowed `/lrh-closeout` Step 2's `in_progress` fallback to records that
match the PR (head-branch slug in `execution_id`, `work_item` among the
PR's WI/WS attribution IDs, or a blank/placeholder `pr:` with `created_at`
in the PR's open-to-merge window), and added the pre-mint
`check-execution --slug` check to the new-record path.

# Result

PR #873. Changes in `src/lrh/skills/lrh-closeout/SKILL.md` (Steps 2 and 5)
and `references/closeout-workflow.md`, regenerated into `.claude/skills/`,
`.agents/skills/`, `.gemini/plugins/lrh/skills/`, and `plugins/lrh/skills/`
(the plugin copy via `lrh skills export --target claude-plugin` run from
repo source, since the installed `lrh` lacks that target). The work item
file is added in the same PR, following PR #872's precedent.

- The attribution scan moved ahead of the fallback; an empty narrowed list
  goes straight to the "No execution record" branch, and the full list
  stays available on request.
- The slug check runs in Step 2 so the Step 4 gate's plan shows any prior
  run and its implied `rerun_of`; Step 5 re-runs it and re-asks on change.
- No GATE-DEFINITION region changed; no CLI change.

The plan was taken as approved from the starting session's task brief,
which specified the scope; there was no separate live Step 4 reply.

# Validation

- `scripts/format --check --diff`: clean
- `scripts/lint`: clean
- `scripts/test`: 2410 tests, OK (re-run after the self-review fixes)
- `lrh validate`: 0 errors, 0 warnings
- `diff -r` of src against `.claude/skills/` and `plugins/lrh/skills/`:
  identical
- Diff-mode `/lrh-self-review`: 0 blocking, 2 non-blocking, 2 nits, all
  fixed (see the `_SELFREVIEW` record)

# Follow-up

- Self-review findings 3 to 6 on PR #872 (non-URL `pr:` values, `_`-joined
  branch names, two PR-body nits) remain open and out of scope here.

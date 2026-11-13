---
execution_id: 2026_11_13_00_36_40_WI_LRH_CLOSEOUT_NO_EXECUTION_RECORD
prompt_id: PROMPT(WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD:WI_LRH_CLOSEOUT_NO_EXECUTION_RECORD)[2026-11-09T04:58:59+00:00]
work_item: WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/872
commit:
created_at: 2026-11-13T00:36:40+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD.md
session_transcript: pending
---

# Summary

Give `/lrh-closeout` a documented path for a merged PR that has no execution
record at all, so a closeout session creates the record directly as `landed`
instead of improvising (precedent: xenotaur/prosoc PR #139 closeout,
2026-11-07).

# Result

- `src/lrh/skills/lrh-closeout/SKILL.md`: Step 1 handles zero auto-detect
  candidates and a WI-ID with no record; Step 2 adds the "No execution record"
  branch, a WI/WS attribution scan of PR metadata (direct invocation only),
  creation-field proposals, and a plan-table row; Step 3 resolves the pointer
  for a to-be-created record; the Step 4 gate shows creation fields and asks
  the WI-or-`AD_HOC` question; Step 5 runs `label`, `check-execution`, and one
  `record-execution --status landed` call, then writes the body; Step 8 says
  to stage the new record by path; one quality-checklist item.
- `/lrh-land` interplay: when inlined, closeout defers to `/lrh-land`'s
  no-primary backfill record and its preview row shows that record's `agent`
  and session pointer. `/lrh-land` itself is unchanged.
- `references/closeout-workflow.md`: decision-matrix rows replacing "Missing
  entirely", a transition-rule carve-out, and a "Creating a record when none
  exists" section.
- Work item `WI-LRH-CLOSEOUT-NO-EXECUTION-RECORD` added in the same PR (user
  chose this over a separate WI-creation PR).
- Installed copies regenerated: `.claude/skills`, `.agents/skills`,
  `.gemini/plugins/lrh/skills` (`lrh skills install --local --target all`)
  and `plugins/lrh/skills` (`lrh skills export --target claude-plugin`, run
  from repo source because the `lrh` on PATH lacks that target).
- Prior-art check: `/lrh-land`'s backfill path is related but covers only its
  own chain; no work item or proposal requested this.
- Self-review (diff-mode): 0 blocking, 2 should-fix, 9 nits; all fixed except
  updating the adopted `PROP-LRH-CLOSEOUT`. See
  `project/executions/AD_HOC/2026_11_13_00_35_32_WI_LRH_CLOSEOUT_NO_EXECUTION_RECORD_SELFREVIEW.md`.
- The Step 4 edit is inside a `GATE-DEFINITION` region, so chain-defaults
  gates go stale after merge.

# Validation

- Tools: Python 3.11.8, ruff 0.15.12, black 26.3.1, lrh 0.2.5.dev3658
- `scripts/format --check --diff`: clean
- `scripts/lint`: exit 0
- `scripts/test`: 2410 tests OK
- `lrh validate`: 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout`: identical
- `record-execution --status landed` with all fields confirmed by `--dry-run`;
  the attribution pipeline tested against PRs #825 and #865.

# Follow-up

- Re-confirm chain-defaults gates with `/lrh-config-gates` after merge.

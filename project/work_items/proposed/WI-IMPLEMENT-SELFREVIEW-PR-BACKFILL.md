---
id: WI-IMPLEMENT-SELFREVIEW-PR-BACKFILL
title: "Backfill pr: and rerun_of on the diff-mode _SELFREVIEW record in /lrh-implement Step 9"
type: operation
status: proposed
blocked: false
blocked_reason: null
resolution: null
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "src/lrh/skills/lrh-implement/SKILL.md Step 9 instructs setting pr: to the Step 8 PR URL and rerun_of: to the new primary record's execution_id on the diff-mode _SELFREVIEW record created at Step 7.5, before the Step 9 commit"
  - "Step 9 stages that _SELFREVIEW record in the same commit as the primary execution record, so both reach the open PR together"
  - "A diff-mode _SELFREVIEW record produced by the updated procedure is found by /lrh-land Step 1's grep -rl \"pr: <pr-url>\" project/executions/ and classified as a side record, not primary or ambiguous"
  - ".claude/skills/lrh-implement/SKILL.md is byte-for-byte identical to src/lrh/skills/lrh-implement/SKILL.md"
  - "lrh validate reports 0 errors and lrh chain-defaults check-staleness reports no GATE-DEFINITION region changed"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-implement/SKILL.md
---

## Summary

`/lrh-implement` Step 7.5 runs `/lrh-self-review` in diff-mode before the PR
exists, so the `_SELFREVIEW` execution record it creates has an empty `pr:`
field and an empty `rerun_of:`. Nothing ever fills them in afterward, so
`/lrh-land` Step 1 and `/lrh-closeout` Step 2, which find a PR's records by
grepping the `pr:` field, never see this record. Have Step 9 backfill both
fields once the PR URL and the primary record's `execution_id` are known, and
commit the record together with the primary.

## Problem / Context

Seen on PR #793 (`PROMPT(AD_HOC:SERVE_META_WORKSPACE_DETAIL_404)`). The
diff-mode record
`project/executions/AD_HOC/2026_10_08_06_24_55_SERVE_META_WORKSPACE_DETAIL_404_SELFREVIEW.md`
was pushed to the PR with `pr:` empty. `/lrh-land` Step 1's
`grep -rl "pr: <pr-url>" project/executions/` returned only the primary
record, so the self-review record left the automatic closeout plan and was
added back by hand. If a session forgets it, the record stays `in_progress`
on `main` indefinitely, which `/lrh-work-remains` category 7 can't connect
back to the PR either.

The empty `rerun_of:` is correct by design at creation time
(`src/lrh/skills/lrh-self-review/references/self-review-workflow.md`, the
`rerun_of` section: no primary exists yet at diff-mode dispatch). The design
just never says to fill it in later. By the end of `/lrh-implement` Step 9,
the PR URL (Step 8) and the primary `execution_id` (Step 9) are both known,
in the same session that created the self-review record.

`lrh prompt update-execution` can't do this backfill: it only supports the
`in_progress → landed` transition (`--status {landed}`). So the fix is a
documented frontmatter edit in Step 9, the same way Step 9 already edits the
primary record's `agent` / `instruction_source` / `session_transcript`
fields.

**Prior art check:**
- *Duplication search:* searched `project/work_items/` and
  `project/design/backlog.md` for "selfreview", "diff-mode", "backfill" and
  "pr field". No existing work item or backlog entry covers this.
  `WI-SKILLS-LRH-SELF-REVIEW` (resolved) added `_SELFREVIEW` to the
  primary-record exclusion globs, but it doesn't populate `pr:`.
  `WI-SELF-REVIEW-UNTRACKED-FILE-DIFF` (resolved) touches diff-mode diff
  building only. Open PR #794 adds `--agent` / `--instruction-source` /
  `--session-transcript` flags to `lrh prompt record-execution`
  (`src/lrh/prompt_workflow.py`). It's related but doesn't overlap: it
  touches neither `pr:` / `rerun_of:` nor the skill file.
- *Demand search:* no existing request was found in `project/workstreams/`
  or `project/design/`. This was raised by the user after landing PR #793.

## Scope

- `src/lrh/skills/lrh-implement/SKILL.md` Step 9: after creating and
  populating the primary record, locate the diff-mode `_SELFREVIEW` record
  Step 7.5 created this run. Set its `pr:` to the Step 8 PR URL and its
  `rerun_of:` to the primary's `execution_id`, and stage it in the same
  commit as the primary.
- Mirror the edit to `.claude/skills/lrh-implement/SKILL.md`.

## Required Changes

1. In `src/lrh/skills/lrh-implement/SKILL.md` Step 9, after the paragraph
   that populates `agent` / `instruction_source` / `session_transcript`, add
   a short instruction:
   - Identify the diff-mode `_SELFREVIEW` record from Step 7.5 by the exact
     path that `/lrh-self-review` reported in its Step 7 report. Do not use
     a glob, which could match an unrelated record.
   - Set `pr:` to the PR URL from Step 8.
   - Set `rerun_of:` to the primary record's `execution_id`.
   - If Step 7.5 produced no record (for example, an empty diff), skip this
     step and say so.
2. Change Step 9's "Commit the execution record" wording so the commit
   includes the backfilled `_SELFREVIEW` record as well.
3. Copy the edited file to `.claude/skills/lrh-implement/SKILL.md`.

## Non-Goals

- Does not add a `--pr` / `--rerun-of` update path to
  `lrh prompt update-execution` or any other CLI change.
- Does not change `/lrh-self-review` itself, or the "`rerun_of` starts empty
  by construction" design for diff-mode at creation time.
- Does not change `/lrh-land` Step 1 or `/lrh-closeout` Step 2 search logic
  (for example, adding a slug-based fallback for orphaned `_SELFREVIEW`
  records).
- Does not backfill existing historical diff-mode records already on `main`.
- Does not touch any `<!-- GATE-DEFINITION -->` region. Step 9 sits outside
  Step 4's marked region.

## Acceptance Criteria

- Step 9 of `src/lrh/skills/lrh-implement/SKILL.md` tells the agent to set
  `pr:` (the Step 8 PR URL) and `rerun_of:` (the primary's `execution_id`)
  on the Step 7.5 diff-mode `_SELFREVIEW` record before Step 9's commit.
- Step 9's commit includes that backfilled record together with the primary
  record.
- A record produced this way is found by `/lrh-land` Step 1's
  `pr:` grep and classified as a side record.
- `.claude/skills/lrh-implement/SKILL.md` is byte-for-byte identical to the
  `src/` copy.
- `lrh validate` reports 0 errors, and
  `lrh chain-defaults check-staleness` reports no GATE-DEFINITION change.

## Validation

- lrh validate
- diff src/lrh/skills/lrh-implement/SKILL.md .claude/skills/lrh-implement/SKILL.md
- lrh chain-defaults check-staleness --confirmed-commit "$(grep '^confirmed_commit:' project/config/chain-defaults.yaml | sed 's/^confirmed_commit: *//')" --project-root .
- scripts/test

## Risk Notes

- `src/lrh/skills/lrh-implement/SKILL.md` is in
  `lrh.gate_staleness.DEFAULT_WATCHED_FILES`. Edits outside its
  `<!-- GATE-DEFINITION -->` region don't invalidate stored chain consent,
  but an edit that strays into Step 4's marked region would. The staleness
  check in Validation guards this.
- `/lrh-execute` runs `/lrh-implement` inline, so it picks up the fix
  automatically. No separate change is needed there.
- Installed copies in `~/.claude/skills/` (from `lrh skills install`) keep
  the old behavior until they are re-synced.

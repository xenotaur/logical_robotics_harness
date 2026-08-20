---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE
title: Scope /lrh-closeout session-alias capture to Claude-resolved host ids
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
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
  - src/lrh/skills/lrh-closeout/SKILL.md Step 5's "Session identity capture" step no longer instructs the agent to call record-session-alias "for every record, regardless of which Step 3 path resolved the host id"
  - The step explicitly scopes record-session-alias calls to records where Step 3 resolved a confirmed Claude host id (its paths 1, 2, or 3), and explicitly skips session-alias capture for codex_app, codex_cloud, manual, and other non-Claude backend records
  - The reworded step is consistent with (does not contradict) references/closeout-workflow.md's own "Session identity capture" section, which already scopes correctly to "resolution-order path 1, 2, or 3"
  - .claude/skills/lrh-closeout/SKILL.md is byte-for-byte identical to src/lrh/skills/lrh-closeout/SKILL.md
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-closeout/SKILL.md
  - .claude/skills/lrh-closeout/SKILL.md
---

## Summary

Fix `/lrh-closeout` Step 5's "Session identity capture" instruction, which
currently tells the agent to call `lrh prompt record-session-alias
--host-id <host-uuid-stem-confirmed-in-step-3>` "for every record,
regardless of which Step 3 path resolved the host id." Step 3 branches on
each execution record's `agent` field, and for `codex_app`, `codex_cloud`,
`manual`, or other non-Claude backends it resolves to `codex-app:<id>`,
`codex-cloud:<id>`, `pending`, or `none` — none of which is a usable
`--host-id`. Only the Claude.app branch (Step 3's paths 1, 2, or 3) yields a
confirmed host-uuid-stem. This work item rewords Step 5 so the instruction
matches what actually happens for non-Claude backends: skip session-alias
capture for those records instead of attempting it with an unusable value.

## Problem / Context

Flagged during Taurcode PR #82 triage — a mechanical `lrh skills install
--local --force` resync of this project's own skill package into the
Taurcode repo. Three bots flagged real bugs in the *content* of the synced
skills (this project's canonical source), not anything the resync PR
introduced. Full triage detail is in the Taurcode repo at
`project/executions/AD_HOC/2026_08_20_01_06_17_RESYNC_LRH_SKILLS_REVIEW.md`.
This work item addresses one of the three findings; the other two
(`lrh-self-review` diff-mode missing untracked files, `lrh-land` tmp-branch
cleanup deleting the checked-out branch) are tracked separately.

Read directly against this repo's current source
(`src/lrh/skills/lrh-closeout/SKILL.md:316-334`): Step 5's heading and lead
sentence say session-alias capture applies "for every record, regardless of
which Step 3 path resolved the host id." But Step 3
(`src/lrh/skills/lrh-closeout/SKILL.md:175-193`) is not solely about which
of three Claude-specific paths resolved a host id — it first branches on
the record's backend (`codex_app`, `codex_cloud`, `manual`, other
non-Claude, or Claude.app), and only the Claude.app branch enters paths 1/2/3
to resolve a host-uuid-stem. The other branches produce
`codex-app:<task-or-thread-id>`, `codex-cloud:<task-id>`, `pending`, or
`none` — none of these is a `<host-uuid-stem>` `record-session-alias
--host-id` expects. Following Step 5 literally for a `codex_cloud` or
`manual` record means calling `record-session-alias --host-id
codex-cloud:<task-id>` (or `--host-id pending`/`--host-id none`), which is
not what that flag is for.

Notably, `src/lrh/skills/lrh-closeout/references/closeout-workflow.md`'s own
"Session identity capture" section (lines 294-334) already gets this right:
it scopes the capture to "resolution-order path 1, 2, or 3" — i.e. the
Claude.app sub-paths — and states "Every resolution path (1, 2, or 3)
yields a real, confirmed host id." SKILL.md's Step 5 is the one place that
overgeneralizes this to "every record," contradicting the reference doc it
is supposed to summarize.

This affects every consumer of `lrh skills install` who runs `/lrh-closeout`
on a PR carrying a non-Claude-backend execution record (e.g. a mixed PR with
a `codex_cloud` implementation record and a Claude-authored
review-response record) — not a cosmetic wording issue.

**Prior art check:**
- *Duplication search:* grepped `project/work_items/` and
  `project/design/backlog.md` for "session-alias" and "record-session-alias"
  — no existing work item or backlog entry addresses this scoping bug.
- *Demand search:* grepped `project/workstreams/` and `project/design/` for
  the same terms — no existing request found. `WS-SESSION-ARCHIVE-SYNC`
  (active) is the governing workstream for the session-alias mechanism
  generally (per `PROP-LRH-SESSION-ARCHIVE-SYNC` Stage 1) but has no open
  item covering this specific scoping bug.

## Scope

- `src/lrh/skills/lrh-closeout/SKILL.md` Step 5 ("Session identity
  capture"): reword the heading/lead sentence to scope the
  `record-session-alias` call to records where Step 3 resolved a confirmed
  Claude host id, and add an explicit skip instruction for
  `codex_app`/`codex_cloud`/`manual`/other-non-Claude records.
- Mirror the change to `.claude/skills/lrh-closeout/SKILL.md`.

## Non-Goals

- Does not change `references/closeout-workflow.md`'s "Session identity
  capture" section — it already documents the correct scoping; this WI only
  brings SKILL.md's summary into agreement with it.
- Does not change Step 3's backend-branching logic itself.
- Does not add a new session-pointer mechanism for non-Claude backends —
  out of scope per the existing "Sentinels — `none` vs `pending`" grammar.

## Required Changes

1. Edit `src/lrh/skills/lrh-closeout/SKILL.md` Step 5: change the
   "Session identity capture" lead sentence from "(for every record,
   regardless of which Step 3 path resolved the host id — the
   host-to-PR association is worth recording either way)" to explicitly
   scope it to records where Step 3's Claude.app branch (paths 1/2/3)
   resolved a confirmed host id, and add a sentence stating that for
   `codex_app`, `codex_cloud`, `manual`, or other non-Claude backend
   records, this step is skipped entirely — there is no usable
   `--host-id` value for those backends.
2. Mirror the edited file to `.claude/skills/lrh-closeout/SKILL.md`.

## Acceptance Criteria

- SKILL.md Step 5 no longer claims session-alias capture applies "for every
  record, regardless of which Step 3 path."
- SKILL.md Step 5 explicitly states the step is skipped for
  `codex_app`/`codex_cloud`/`manual`/other-non-Claude records.
- SKILL.md's scoping is consistent with (does not contradict)
  `references/closeout-workflow.md`'s existing "Session identity capture"
  section.
- `.claude/skills/lrh-closeout/SKILL.md` mirrors
  `src/lrh/skills/lrh-closeout/SKILL.md` byte-for-byte.
- `lrh validate` reports 0 errors.

## Validation

- lrh validate
- diff -q src/lrh/skills/lrh-closeout/SKILL.md .claude/skills/lrh-closeout/SKILL.md

## Risk Notes

Low risk — this is a documentation/instruction-wording fix to an agent-facing
skill file. No code or CLI behavior changes. The main risk is
under-specifying the skip condition in a way that's still ambiguous for an
agent executing the skill cold; mitigate by naming the exact backend values
(`codex_app`, `codex_cloud`, `manual`, other non-Claude) explicitly rather
than referring back to Step 3 by number alone.

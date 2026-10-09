---
id: WI-IMPLEMENT-SELFREVIEW-PR-BACKFILL
title: "Link /lrh-implement's primary and diff-mode _SELFREVIEW records to the PR (pr: and rerun_of backfill)"
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
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "src/lrh/skills/lrh-implement/SKILL.md Step 9 creates the primary execution record with --pr set to the Step 8 PR URL"
  - "src/lrh/skills/lrh-implement/SKILL.md Step 9 instructs setting pr: to the Step 8 PR URL and rerun_of: to the new primary record's execution_id on the diff-mode _SELFREVIEW record created at Step 7.5, and stages that record in the same commit as the primary"
  - "For a PR produced by the updated procedure, /lrh-land Step 1's grep -rl \"pr: <pr-url>\" project/executions/ returns both records, and the provenance check classifies the primary as primary and the _SELFREVIEW record as a side record (neither ambiguous)"
  - "src/lrh/skills/lrh-self-review/references/self-review-workflow.md distinguishes diff-mode's creation-time empty rerun_of from /lrh-implement Step 9's later backfill of pr: and rerun_of, with no remaining contradiction between the two skills"
  - "The tracked Claude, Codex, and Antigravity install targets for lrh-implement and lrh-self-review (.claude/skills/, .agents/skills/, .gemini/plugins/lrh/skills/) are regenerated from src/ via lrh skills install --local --source current-repo and carry the new text"
  - "lrh validate reports 0 errors, scripts/test passes, and lrh chain-defaults check-staleness reports no GATE-DEFINITION region changed"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-implement/SKILL.md
  - .agents/skills/lrh-implement/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-self-review/references/self-review-workflow.md
  - .claude/skills/lrh-self-review/references/self-review-workflow.md
  - .agents/skills/lrh-self-review/references/self-review-workflow.md
  - .gemini/plugins/lrh/skills/lrh-self-review/references/self-review-workflow.md
---

## Summary

A direct `/lrh-implement` run leaves two of its execution records
unconnected to the PR it opens.

- **The primary record.** Step 9 creates it without `--pr`, and the manual
  edit that follows only sets `agent` / `instruction_source` /
  `session_transcript`.
- **The diff-mode `_SELFREVIEW` record.** Step 7.5 creates it before the PR
  exists, so `pr:` and `rerun_of:` start empty, and nothing fills them in
  later.

`/lrh-land` Step 1 and `/lrh-closeout` Step 2 find a PR's records by
grepping `pr:`, so both can miss these records. Make Step 9:

- pass `--pr` when creating the primary record;
- backfill `pr:` and `rerun_of:` on the diff-mode `_SELFREVIEW` record once
  the PR URL and the primary `execution_id` are known, and commit it
  together with the primary.

Then update `/lrh-self-review`'s reference so it no longer says that empty
diff-mode `rerun_of` is permanent, and regenerate every tracked install
target.

## Problem / Context

Seen on PR #793 (`PROMPT(AD_HOC:SERVE_META_WORKSPACE_DETAIL_404)`). The
diff-mode record
`project/executions/AD_HOC/2026_10_08_06_24_55_SERVE_META_WORKSPACE_DETAIL_404_SELFREVIEW.md`
was pushed to the PR with `pr:` empty. `/lrh-land` Step 1's
`grep -rl "pr: <pr-url>" project/executions/` returned only the primary
record, so the self-review record left the automatic closeout plan and was
added back by hand. If a session forgets it, the record stays `in_progress`
on `main` indefinitely, which `/lrh-work-remains` category 7 can't connect
back to the PR either. In that run, the primary record had `pr:` only
because the session set it by hand. `/lrh-implement` Step 9 as written
never does.

Backfilling `pr:` on the `_SELFREVIEW` record alone would make things worse
for direct `/lrh-implement` runs. The `_SELFREVIEW` record would become the
only PR-matching candidate. The provenance check in
`src/lrh/skills/lrh-land/references/land-workflow.md` ("Primary vs.
side-record provenance check") classifies a reserved-suffix candidate with
no matching base among the candidates as ambiguous, which makes `/lrh-land`
stop and ask. So the primary record must carry `pr:` too.
`lrh prompt record-execution` already accepts `--pr`, and `/lrh-execute`
already works around this gap when it runs `/lrh-implement` inline (see
its "Populate the execution record's `pr:` field" step).

The empty `rerun_of:` is correct at creation time: no primary exists yet
when diff-mode runs. But `src/lrh/skills/lrh-self-review/references/self-review-workflow.md`
(the "`rerun_of` — differs by mode" section) currently says to leave it
empty and calls that "not a gap to work around". That reads as permanent,
so it has to be reworded to agree with the new Step 9 backfill.

`lrh prompt update-execution` can't do the `_SELFREVIEW` backfill: it only
supports the `in_progress → landed` transition (`--status {landed}`). So
that part is a documented frontmatter edit in Step 9, the same way Step 9
already edits the primary record's optional fields.

The skills are installed into three tracked targets in this repository.
`.claude/skills/` is a byte copy. `.agents/skills/` (Codex) and
`.gemini/plugins/lrh/skills/` (Antigravity) are rendered by
`lrh skills install`, not copied byte for byte
(`docs/how-to/keep-skills-up-to-date.md`). Editing only `src/` and
`.claude/skills/` would leave repo-local Codex and Antigravity runs on the
old procedure.

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
  touches neither `pr:` / `rerun_of:` nor the skill files.
- *Demand search:* no existing request was found in `project/workstreams/`
  or `project/design/`. This was raised by the user after landing PR #793.

## Scope

- `src/lrh/skills/lrh-implement/SKILL.md` Step 9:
  - pass `--pr <Step 8 PR URL>` to `lrh prompt record-execution` for the
    primary record;
  - backfill `pr:` and `rerun_of:` on the Step 7.5 diff-mode `_SELFREVIEW`
    record;
  - include that record in the Step 9 commit.
- `src/lrh/skills/lrh-self-review/references/self-review-workflow.md`:
  reword the diff-mode `rerun_of` guidance so it describes creation-time
  emptiness followed by the caller's Step 9 backfill.
- Regenerate every tracked install target for both skills (`.claude/skills/`,
  `.agents/skills/`, `.gemini/plugins/lrh/skills/`) from `src/`.

## Required Changes

1. In `src/lrh/skills/lrh-implement/SKILL.md` Step 9, add
   `--pr <pr-url-from-step-8>` to the `lrh prompt record-execution` command
   block for the primary record.
2. In the same Step 9, after the paragraph that populates `agent` /
   `instruction_source` / `session_transcript`, add a short instruction:
   - Identify the diff-mode `_SELFREVIEW` record from Step 7.5 by the exact
     path that `/lrh-self-review` reported in its Step 7 report. Do not use
     a glob, which could match an unrelated record.
   - Set its `pr:` to the Step 8 PR URL.
   - Set its `rerun_of:` to the primary record's `execution_id`.
   - If Step 7.5 produced no record (for example, an empty diff), skip this
     step and say so.
3. Change Step 9's "Commit the execution record" wording so the commit
   includes the backfilled `_SELFREVIEW` record as well.
4. In `src/lrh/skills/lrh-self-review/references/self-review-workflow.md`,
   in the diff-mode bullet of the "`rerun_of` — differs by mode" section:
   - keep that `rerun_of` starts empty at creation, because no primary
     exists yet;
   - replace "not a gap to work around" with wording that `/lrh-implement`
     Step 9 later fills in both `pr:` and `rerun_of:` on this record once
     the PR and the primary record exist.
5. Regenerate the tracked install targets with
   `lrh skills install --local --source current-repo --force` for each of
   `--target claude`, `--target codex`, and `--target antigravity` (or
   `--target all`). Confirm with `git diff --stat` that only the
   `lrh-implement` and `lrh-self-review` files changed, and revert any
   unrelated drift the regeneration produces.

## Non-Goals

- Does not add a `--pr` / `--rerun-of` update path to
  `lrh prompt update-execution` or any other CLI change.
- Does not change `/lrh-self-review`'s own creation-time behavior. Diff-mode
  still creates the record with empty `pr:` / `rerun_of:`.
- Does not change `/lrh-land` Step 1 or `/lrh-closeout` Step 2 search logic
  (for example, adding a slug-based fallback for orphaned `_SELFREVIEW`
  records).
- Does not change `/lrh-execute`. Its existing primary-record `pr:`
  compensation becomes redundant but harmless, and can be cleaned up
  separately.
- Does not backfill existing historical records already on `main`.
- Does not touch any `<!-- GATE-DEFINITION -->` region. Step 9 sits outside
  Step 4's marked region.

## Acceptance Criteria

- `/lrh-implement` Step 9 creates the primary record with `--pr` set to the
  Step 8 PR URL.
- Step 9 tells the agent to set `pr:` (the Step 8 PR URL) and `rerun_of:`
  (the primary's `execution_id`) on the Step 7.5 diff-mode `_SELFREVIEW`
  record, and to commit it together with the primary record.
- For a PR produced this way, `/lrh-land` Step 1's `pr:` grep returns both
  records. The provenance check classifies one as primary and the other as
  a side record; neither is ambiguous.
- `self-review-workflow.md` no longer contradicts the Step 9 backfill: it
  separates creation-time emptiness from the later backfill.
- The `.claude/skills/`, `.agents/skills/` and `.gemini/plugins/lrh/skills/`
  copies of both skills are regenerated from `src/` and contain the new
  text.
- `lrh validate` reports 0 errors, `scripts/test` passes, and
  `lrh chain-defaults check-staleness` reports no GATE-DEFINITION change.

## Validation

- lrh validate
- scripts/test
- diff src/lrh/skills/lrh-implement/SKILL.md .claude/skills/lrh-implement/SKILL.md
- diff src/lrh/skills/lrh-self-review/references/self-review-workflow.md .claude/skills/lrh-self-review/references/self-review-workflow.md
- grep -n -- "--pr <pr-url-from-step-8>" .agents/skills/lrh-implement/SKILL.md .gemini/plugins/lrh/skills/lrh-implement/SKILL.md
- lrh chain-defaults check-staleness --confirmed-commit "$(grep '^confirmed_commit:' project/config/chain-defaults.yaml | sed 's/^confirmed_commit: *//')" --project-root .

## Risk Notes

- `src/lrh/skills/lrh-implement/SKILL.md` is in
  `lrh.gate_staleness.DEFAULT_WATCHED_FILES`. Edits outside its
  `<!-- GATE-DEFINITION -->` region don't invalidate stored chain consent,
  but an edit that strays into Step 4's marked region would. The staleness
  check in Validation guards this. `self-review-workflow.md` is not
  watched.
- Regenerating the install targets from `src/` can surface unrelated
  pending drift in other skills. Keep the diff scoped to the two skills
  named here.
- `/lrh-execute` runs `/lrh-implement` inline, so it picks up the fix
  automatically.
- User-scope installs (`~/.claude/skills/`, `~/.agents/skills/`) keep the
  old behavior until they are re-synced.

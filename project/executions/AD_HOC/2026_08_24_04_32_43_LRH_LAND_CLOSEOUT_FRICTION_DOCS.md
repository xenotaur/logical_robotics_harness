---
execution_id: 2026_08_24_04_32_43_LRH_LAND_CLOSEOUT_FRICTION_DOCS
prompt_id: PROMPT(AD_HOC:LRH_LAND_CLOSEOUT_FRICTION_DOCS)[2026-08-24T03:55:36+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
agent: claude_app
instruction_source: user-directed ad-hoc task (Recommendation A from a two-gate-friction analysis conducted during WI-LRH-CHAIN-DEFAULTS-INCREMENT-2's closeout)
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/628
commit: df73c42edd9edbf44558a98aa7d06ce6965c49d0
created_at: 2026-08-24T04:32:43+00:00
---

# Summary

Two doc-only fixes to `/lrh-land`, ad hoc, found while closing out PR #626
(`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`): a spurious live re-ask for
confirmation before the closeout's push to `main` (a real agent-execution
deviation from the skill's own already-written "without a second ask"
policy), and a lack of any documented troubleshooting for two push-failure
modes hit in production this session.

# Result

`src/lrh/skills/lrh-land/SKILL.md` Step 7 gained an explicit anti-pattern
callout: do not re-ask for confirmation before the closeout's
`git push origin tmp-<slug>:main` -- Step 6's single ask
(`DEC-SINGLE-ASK-RUN-GATES`) already covers it. Grounded in a real failure
this session: the agent invented a justification ("a separate standing
session rule requiring confirm before any main push") to re-ask anyway,
directly contradicting the skill's own pre-existing "without a second ask"
text at the same Step 7.

`references/land-workflow.md` gained a new "Main-Worktree-Lock
Troubleshooting" section (two rows) covering: non-fast-forward push
rejections (usually a benign concurrent unrelated commit to `main`, not a
conflict with the run's own changes -- check ancestor, rebase, retry) and
ambiguous permission-classifier denials on chained/compound Bash git
commands (retry as a single minimal command before concluding it is a real
policy block). Both grounded in failures actually hit closing out PR #626's
own closeout commit.

**Bundled scope decision (user-confirmed):** while mirroring these edits,
discovered `.agents/skills/lrh-land/SKILL.md` and
`.gemini/plugins/lrh/skills/lrh-land/SKILL.md` were already stale on
`origin/main` before this change -- 240 and 245 lines diverged from `src/`,
missing Increment 3's (PR #623) entire merge+closeout combined-ask rewrite
entirely (still showed the old separate Step 6 merge-gate / Step 7 closeout
split, plus stale frontmatter). `land-workflow.md` and `.claude/`'s
`SKILL.md` were already in sync. User explicitly chose to bundle the
backfill into this PR rather than defer it, since it is a straight content
sync (no new design decision), not scope creep on the design front --
raised as an explicit before/after choice, not decided unilaterally.

A `/lrh-self-review` diff-mode pass (dispatched against `origin/main`, since
the local `main` ref in this worktree was independently confirmed stale --
`git log -1 --oneline main` showed `1703c872` vs `origin/main`'s `2ce02100`)
found one real issue: adding two troubleshooting rows to the
"Five Glue-Logic Rules" table (sourced from `PROP-LRH-LAND-EXECUTE`
Decision 3) made the table's own heading/count inaccurate at 7 rows.
Independently re-verified via `grep -n "glue-logic\|Glue-Logic"` across both
files -- confirmed real. Fixed by moving the two new rows into their own
"Main-Worktree-Lock Troubleshooting" section rather than padding the
Decision-3-sourced table, restoring "five" as accurate.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` for
  `WS-LRH-CHAIN-DEFAULTS`, unchanged by this PR).
- Mirror parity: `diff` clean across `src/`, `.claude/`, `.agents/`,
  `.gemini/` for both `SKILL.md` and `references/land-workflow.md`,
  re-verified after the post-review fix.
- Doc-only change (all 8 changed files are `.md`) -- `scripts/format`
  --check and `scripts/lint` both failed locally on the known, pre-existing
  local/CI `black`/`ruff` version mismatch (25.11.0/0.15.0 vs CI's pinned
  26.3.1/0.15.12), unrelated to this change; `scripts/test` skipped, no
  Python files touched.
- `/lrh-self-review` diff-mode: 1 finding, independently re-verified,
  fixed in the working tree before push.

# Follow-up

- None deferred. Both intended edits and the bundled mirror-drift backfill
  are complete in this PR.
- `WI-CHAIN-DEFAULTS-STALENESS-RESTAMP` remains filed but unimplemented and
  unpushed from earlier this session, unrelated to this change.

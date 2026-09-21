---
execution_id: 2026_09_21_19_10_56_WI_LRH_LAND_WORDING_AND_CLOSEOUT_PR_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_LAND_WORDING_AND_CLOSEOUT_PR_REVIEW)[2026-09-20T23:55:56+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_20_21_23_57_WI_LRH_LAND_WORDING_AND_CLOSEOUT_PR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/684
commit: 
created_at: 2026-09-21T19:10:56+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR.md
session_transcript: pending
---

# Summary

Review-response round on PR #684 (inlined in an `/lrh-land` run). Two open
threads on `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR`: Codex P1 (the closeout-PR
merge cannot be authorized by a Step 6 reply given before that PR exists,
citing `AGENTS.md:153`) and Copilot (the records-only exemption's "closeout's
own control-plane files" is undefined).

# Result

Both threads passed the presence and validity checks.

- **Codex P1:** valid, and it exposed a real gap: no decision sanctions
  pre-authorizing the merge of a PR that does not yet exist. A separate
  merge gate was rejected by the human because it undoes the single-ask
  design (`DEC-SINGLE-ASK-RUN-GATES`). Adopted instead: a bounded
  pre-authorization checked by a mechanical verifier with a head-SHA lock.
  Because merge authorization is a protected gate, the work item now
  requires a new decision, `DEC-DERIVATIVE-PR-MERGE-PREAUTHORIZATION`, plus a
  matching `AGENTS.md` edit, to be approved at implementation time.
- **Copilot:** valid. The exemption now enumerates the exact allowed paths in
  both the acceptance criteria and Required Changes, and the same set is the
  verifier's allowed set.
- The scope was split across three work items in this PR:
  `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR` (revised, now depends on the
  verifier), `WI-LRH-CLOSEOUT-PR-VERIFIER` (new) and
  `WI-LRH-BRANCH-PROTECTION-PROBE-AND-GUIDE` (new).
- Fixes are committed locally. Per the human's instruction they have not been
  pushed for review yet, and the threads are not resolved (that is
  `/lrh-confirm-fixes` Step 5's job).

# Validation

- `lrh validate`: 0 errors (1 pre-existing warning on an unrelated record).
- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`:
  clean.
- `scripts/test`: exit 0.

# Follow-up

- Push the fix commits when the human says to, then continue the `/lrh-land`
  run at Step 5.
- The implementation must start from current `origin/main`: PR #683 changed
  `/lrh-land` Step 7 after this branch was cut.
- `session_transcript` is `pending` until a durable pointer is available.

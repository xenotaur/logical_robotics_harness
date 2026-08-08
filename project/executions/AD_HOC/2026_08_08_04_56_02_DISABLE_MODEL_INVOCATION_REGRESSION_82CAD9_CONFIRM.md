---
execution_id: 2026_08_08_04_56_02_DISABLE_MODEL_INVOCATION_REGRESSION_82CAD9_CONFIRM
prompt_id: PROMPT(AD_HOC:DISABLE_MODEL_INVOCATION_REGRESSION_82CAD9_CONFIRM)[2026-08-08T04:55:51+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/518
commit: df0133a88fb08c327846601dd118ec2833124bae
created_at: 2026-08-08T04:56:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/518
session_transcript: pending
---

# Summary

Pre-merge confirm-fixes pass on PR #518 (no primary execution record exists
for this PR — planning-artifact edit run outside `/lrh-implement` — so
`rerun_of` is left empty per the backfill path). Independently verified five
review threads (2 Codex, 3 Copilot) against the current `HEAD` diff,
resolved all five, and computed a merge-readiness verdict.

# Result

Five unresolved threads gathered via `lrh github threads --mode raw --state all`,
filtered to `isResolved == false`:

- `chatgpt-codex-connector` (P1) — `lrh-self-review`'s diff-mode has no
  confirm-before-write step, so classifying it as already-gated (tier 2) was
  wrong. **Clear-satisfied**: split into tier 2a, excluded from this WI's
  flag-removal scope until the gate gap is fixed, acceptance criterion added
  (commit 4f871e5).
- `chatgpt-codex-connector` (P2) — `DEC-DELIBERATE-CHAIN-INITIATION.md` was
  left stating the opposite of this WI's decision. **Clear-satisfied**:
  dated addendum recorded, principle 2 marked superseded, revisit condition
  marked met (commit 4f871e5).
- `copilot-pull-request-reviewer` — frontmatter/body acceptance-list
  inconsistency on the chain-runner-invocation-mechanics line.
  **Clear-satisfied**: already resolved as a byproduct of the same sync pass
  (commit 4f871e5); verified both locations now read identically before
  resolving the thread.
- `copilot-pull-request-reviewer` — Claude Code docs reference was a bare
  backticked URL with no scheme, would not render as a link.
  **Clear-satisfied**: wrapped in `<https://...>` (commit df0133a).
- `copilot-pull-request-reviewer` — `lrh-doc-audit` misclassified as tier 1
  (read-only); its `SKILL.md` Step 7 confirm gate precedes a Step 8 write.
  **Clear-satisfied**: moved to tier 2 with citation (commit df0133a).

All five threads resolved via `resolveReviewThread`. Thread-resolution
verdict: **green** (all resolved, no exceptions).

CI on `df0133a` (post-fix commit, pre-`_CONFIRM`-record push): `coverage`,
`installed-wheel-smoke`, `tests`, `Check workflow files`, `lint` — all
`SUCCESS`. No required-check branch protection configured (`rules/branches/main`
returns no `required_status_checks` entry — confirmed absence, not a
reporting delay).

## Round 2 — post-`_CONFIRM`-push retrigger (Step 8)

This record's own commit (`df0133a` → pushed as part of creating this record)
was retriggered per Step 8: `gh pr comment 518 --body "@codex review"` and
`gh pr edit 518 --add-reviewer @copilot`. Both reviewers responded (Codex
`05:00:38Z`, Copilot `04:59:56Z`) on the resulting HEAD. Copilot's review
summary reported "generated no new comments" but its collapsed "Suppressed
comments" section held 2 findings (per
[[feedback_copilot_suppressed_comments_review_body]] — read before trusting
the summary line), and Codex opened 2 new inline threads directly (not
suppressed):

- Codex (P1) — Design Decision's tier-3 claim ("invocation by any route
  still stops at Step 2") is false under `DEC-CHAIN-INIT-SKIP-CONSENT`'s
  `skip_if_opted_in` path, which can display conditions without asking;
  combined with flag removal, a model-initiated invocation of `lrh-land`/
  `lrh-execute` could ride stored consent with no live human reply at all.
  **Clear-satisfied, and substantive**: added tier 3a, excluded `lrh-land`
  and `lrh-execute` from this WI's flag-removal scope pending a verification
  mechanism (separate follow-up), corrected every acceptance-criteria and
  Required-Changes reference from 12/13 skills to 11.
- Codex (P2) — `lrh-closeout` was miscited as having a chain-authorization
  gate (Step 1/2) it doesn't have; its actual safety property is the Step 4
  plan-confirm gate. **Clear-satisfied**: reclassified into its own tier-3
  row with the correct citation, separated from tier 3a's `lrh-land`/
  `lrh-execute`.
- Copilot (suppressed, 2 instances of the same finding) — frontmatter line
  32 / body line 201's resolved-note for mechanic 1 didn't mention the
  tier-2a `lrh-self-review` exception, an internal inconsistency with the
  acceptance list's own later bullet. **Clear-satisfied**: both notes now
  name the tier-2a (and, after Codex's finding, tier-3a) exceptions
  explicitly.

Both new inline threads resolved via `resolveReviewThread`. Thread-resolution
verdict after round 2: **green**.

## Round 3 — post-round-2-push retrigger (Step 8, repeated)

Round 2's commit (`ecd4f79`) was retriggered the same way. Both reviewers
responded (Codex `05:11:46Z`, Copilot `05:11:51Z`). Codex's review body was a
clean pass on the substance but opened 2 new inline threads (not suppressed);
Copilot's summary again said "generated no new comments" while its suppressed
section held 5 duplicate instances of one finding:

- Codex (P2, and Copilot's suppressed section independently, 5 instances
  same root cause) — an arithmetic error introduced in round 2: 13 originally
  flagged skills minus the 3 round-2 exclusions (`lrh-self-review`,
  `lrh-land`, `lrh-execute`) is 10, not 11, and every count in the WI/DEC
  files said 11. **Clear-satisfied and substantive on its own terms**: fixed
  every occurrence.
- Codex (P1) — a genuine new gate gap, same class as `lrh-self-review`'s:
  `lrh-confirm-fixes` Step 2 skips straight to Step 8 (bypassing the Step 4
  confirm gate) when there are no unresolved threads, and Step 8
  unconditionally posts a retrigger comment, requests a reviewer, and
  persists round-state on that path with no human checkpoint. **Clear-satisfied,
  and it changed the count above**: added tier 2b, excluded `lrh-confirm-fixes`
  from this WI's flag-removal scope (now 9 skills, not 10 — the count fix
  above was itself superseded by this finding, corrected in the same pass
  rather than left as a stale intermediate value).

Both new inline threads resolved via `resolveReviewThread`. Thread-resolution
verdict after round 3: **green**.

# Validation

- `lrh validate` — 0 errors (1 pre-existing, unrelated warning) after every
  edit, all three rounds
- `gh pr checks 518` — 5/5 checks green on `df0133a`, `c420b58`/`ecd4f79`
- `resolveReviewThread` — 9/9 threads confirmed `isResolved: true` across
  all three rounds
- `gh api .../commits/<sha>/check-runs` — confirmed `copilot-pull-request-reviewer`
  check-run `completed`/`success` before trusting each round's review as
  landed

## Correction — no further bot retriggers (round 4 onward)

Round 4's push (`2fbaf0b`) was retriggered per Step 8 before the user gave
fleet-wide guidance mid-session: **never manually retrigger GitHub
Codex/Copilot review — it is a limited, near-exhausted monthly resource
(6/7 used), and slow. Use `/lrh-self-review` instead**, which this project
already has a skill for. This matches `feedback_never_manually_retrigger_github_bots`
memory that should have been applied from the start of this land run. Round
4's Codex/Copilot responses (already in flight from the pre-correction
retrigger) surfaced 3 more real findings, fixed — see the `_SELFREVIEW`
record `2026_08_08_05_48_27_DISABLE_MODEL_INVOCATION_REGRESSION_82CAD9_SELFREVIEW.md`
for the round-4-fix verification pass, which used a self-review subagent
instead of a further bot retrigger.

# Follow-up

- Push round-4's fixes as a new commit, run `/lrh-self-review` PR-mode
  again (not a bot retrigger) against that HEAD, and confirm no further
  findings before reporting the final merge-readiness verdict.
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after the session ends.
- Follow-up work (not this WI): a mechanism to verify a genuine human-typed
  slash-command invocation, or a restriction on `DEC-CHAIN-INIT-SKIP-CONSENT`'s
  `skip_if_opted_in` path, before `lrh-land`/`lrh-execute` can drop
  `disable-model-invocation`.
- Follow-up work (not this WI): a confirm gate on `lrh-confirm-fixes`'s
  empty-thread fast path before it can drop `disable-model-invocation`.

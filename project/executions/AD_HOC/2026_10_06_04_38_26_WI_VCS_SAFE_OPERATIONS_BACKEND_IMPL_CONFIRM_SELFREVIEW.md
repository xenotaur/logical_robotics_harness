---
execution_id: 2026_10_06_04_38_26_WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL_CONFIRM_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL_CONFIRM_SELFREVIEW)[2026-10-06T04:38:25+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_05_18_33_04_WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/769
commit: 9a890bca3eddb4be3c71835f4f4d75bdfd23e894
created_at: 2026-10-06T04:38:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/769
session_transcript: claude-app:a4f7b764-fb7e-424a-b0c1-6042007869d3
---

# Summary

PR-mode substitute self-review for PR #769, dispatched from `/lrh-land`'s
inlined `/lrh-confirm-fixes` Step 8 as the REVIEW-LANDED signal for the
`_CONFIRM` commit `e61d4a19`. Both bot reviews (Copilot, Codex) are against
the first commit `91d8e07a`. Neither responded to the content fix push
`f76be0d7`, which was about 44 minutes old when this pass was dispatched, and
these bots are known not to re-review pushes. The newest commit is
record-only.

# Result

A cold-context `general-purpose` subagent reviewed the PR at
`e61d4a19473ad070ed8abc50d78d69b577dcd361`. Verdict: **no P1, no P2; two P3;
safe to merge as is.** It could not verify behavior against a real GitHub
merge queue or branch protection, or whether `lrh` on PATH resolves to this
checkout.

It found no path to merging a different SHA, merging twice, reporting `merged`
when it is not, or hiding that a merge was issued. It checked about 28 audit
citations against `3082dc3b` (all matched), reproduced the audit's counts, found
no normative bare `gh pr merge <pr-url>` left outside the stale `.gemini`
mirror, and ran the four test modules (55 tests, OK).

Findings, all P3, all **deferred** under the run's P3 policy (P3 or lower is
deferred to the closeout note; no further fix round):
1. **A non-`VcsError` raised after the merge was issued exits 1, the code
   documented as "queued".** `_run_merge` in `src/lrh/cli/vcs.py` catches only
   `VcsError`, and the GitHub backend wraps only `RuntimeError`. Example: a
   `UnicodeDecodeError` from non-UTF-8 `gh` output. Independently re-verified
   by this session (Step 4): a fake backend whose post-merge read raised
   `UnicodeDecodeError`, run through the real `lrh.cli.main.main()`, issued
   one merge, then died with an uncaught `UnicodeDecodeError`, which Python
   reports as exit 1 with a traceback. Very unlikely in practice. Suggested
   fix: a catch-all after the merge call that reports "merge issued, state
   unknown" and exits 2.
2. **The skill text does not say exit 2 can coexist with a merged PR.**
   `/lrh-land` and `/lrh-confirm-fixes` summarize exit 2 as "refused or
   failed". The code and `docs/reference/cli/vcs.md` do say a failed merge call
   reports the PR's state, and `/lrh-land` still verifies real state before
   closeout. Suggested fix: add "read the message; exit 2 does not always mean
   nothing merged".

The known deferred P3 (the `MergeVerificationError` docstring) was confirmed by
the reviewer to be only a docstring nit.

No finding was routed through `/lrh-confirm-fixes` Step 3, since none is a P2
or worse. Per the P3 policy this round counts as the REVIEW-LANDED signal for
`e61d4a19`.

# Validation

- Independent re-verification of the top finding: reproduced, see above.
- CI on `e61d4a19` was all green before this pass, and the `Python tests`
  workflow passed on both `f76be0d7` and `e61d4a19`, so the earlier `tests`
  failure on `fcf775c2` did not recur in two re-runs. That is recorded as "not
  reproduced", not as proof it was a flake.
- `lrh validate` to be re-run when this record is committed (at closeout).

# Follow-up

This record is deliberately **not** pushed to the PR branch: doing so would
move the head past the reviewed, CI-green `_CONFIRM` commit and break the
`--match-head-commit` lock. It lands in the post-merge closeout commit.

Deferred P3s to record in the closeout note (three in total):
1. `MergeVerificationError` docstring should cover a failed confirmation,
   including a `CLOSED` read-back (the open review thread
   `PRRT_kwDOR7l1D86pKil_`).
2. Catch non-`VcsError` exceptions after the merge is issued and report
   "merge issued, state unknown" with exit 2.
3. Say in the skill text that exit 2 does not always mean nothing merged.

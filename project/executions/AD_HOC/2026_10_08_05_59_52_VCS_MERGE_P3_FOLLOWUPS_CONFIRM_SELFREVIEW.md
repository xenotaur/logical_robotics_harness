---
execution_id: 2026_10_08_05_59_52_VCS_MERGE_P3_FOLLOWUPS_CONFIRM_SELFREVIEW
prompt_id: PROMPT(AD_HOC:VCS_MERGE_P3_FOLLOWUPS_CONFIRM_SELFREVIEW)[2026-10-08T05:59:52+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/784
commit: d00c2c4420e434031447c9e4a72fc561e45ff722
created_at: 2026-10-08T05:59:52+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/784
session_transcript: claude-app:a4f7b764-fb7e-424a-b0c1-6042007869d3
---

# Summary

PR-mode substitute review of PR #784 at head `c06c1585`, run as `/lrh-land`'s
REVIEW-LANDED signal for that head because no automatic reviewer re-reviewed
the post-push commits. A cold-context subagent reviewed the whole PR with the
most weight on the delta `f9578ed7..c06c1585`. It was report-only. `rerun_of`
is empty: this is the first PR-mode round on this PR.

# Result

Verdict from the reviewer: 3 findings, all P3; safe to merge as is.

- P3, `docs/reference/vcs-backend.md` ~line 66: "every exception ... gets
  issued-merge wording" is accurate but loose. A failed merge call yields
  `<msg>; the pull request is now <STATE>`, which does not literally say
  "merge was issued"; only the read-back failure does. Verified by the reviewer
  with fake backends. Not changed.
- P3, `docs/reference/cli/vcs.md` exit-`2` row: "reported the same way, with its
  type name" glosses over the pre-merge case, which has no PR-state suffix.
  Does not contradict the bullet. Not changed.
- P3, out of the changed lines: `registry.create_backend` and the backend
  constructor run inside the CLI `try`, so a non-`VcsError` raised during
  construction would escape as a traceback with exit 1. Pre-merge, so nothing
  merges, and not a regression. I checked `GitHubBackend.__init__`
  (`src/lrh/vcs/github_backend.py:29`): it only stores `cwd`, and the registry
  raises only `VcsError`, so the built-in path cannot hit it.

Checks the reviewer ran, all clean: the rewritten bullet against the code for
`VcsError` and non-`VcsError` at all three phases; no path merges twice, merges
a different SHA, or reports `merged` unless the read-back shows `MERGED`;
`KeyboardInterrupt` still propagates; `/lrh-land` edit at ~line 514 sits outside
both GATE-DEFINITION blocks (392-511, 537-558); `chain-defaults check-staleness`
reported `stale: False`; `.claude/skills` copies byte-identical; codex mirror
`up to date` for both edited skills; 46 tests in the three touched modules OK.
One side effect noted: a `MergeRefusedError` raised by a backend's merge call is
now wrapped as `VcsError`, so the CLI prints `error:` not `refused:`, which is
right because the merge was attempted.

Not verified by the reviewer: the full suite, any real PR or `gh` call.

Under the agreed P3 policy, P3-only is a clean pass for REVIEW-LANDED. The
three P3s are deferred to the closeout note. This record is deliberately not
pushed to the PR branch, so the merge stays locked to `c06c1585`; it lands in
the closeout commit.

# Validation

- Subagent review of head `c06c1585f6799bc609e20c0386d680a470f4e0a1`, report-only.
- Finding 3 spot-checked by me against `github_backend.py` and `cli/vcs.py`.

# Follow-up

- Three P3 doc/robustness nits above go in the closeout note.
- Land this record with the merge commit and the session pointer at closeout.

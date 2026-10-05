---
execution_id: 2026_10_05_18_29_53_WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL_SELFREVIEW)[2026-10-05T18:29:47+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-10-05T18:29:53+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-VCS-SAFE-OPERATIONS-BACKEND.md
session_transcript: claude-app:a4f7b764-fb7e-424a-b0c1-6042007869d3
---

# Summary

Diff-mode `/lrh-self-review`, run from `/lrh-implement` Step 7.5 before the
first push of the `WI-VCS-SAFE-OPERATIONS-BACKEND` implementation branch
(`xenotaur/feat/wi-vcs-safe-operations-backend-impl`). `rerun_of` is empty by
design: no primary record exists yet at diff-mode dispatch time, and `pr:` is
filled in once the PR is opened.

# Result

Dispatched a cold-context `general-purpose` subagent against the full diff
versus `origin/main` (31 files, 1654 lines; `origin/main` rather than the
stale local `main` ref). Verdict: **no P1; 2 P2, 3 P3**. Every finding was
checked by this session rather than accepted on the report.

Top finding independently re-verified (Step 4): a failed merge call in
`merge_pull_request_locked` propagated with no read-back, and the existing
test asserted exactly that (`get_calls == 1`). The CLI help's claim that
nothing was merged unless the message said so was therefore not guaranteed:
`gh` can fail after GitHub accepted the request.

Disposition of each finding:
- **P2, failed merge call hides a possible merge.** Fixed. The action now
  reads the PR back once (a read, never a second merge) and appends its state
  to the error; if that read also fails it says to check the PR. CLI help,
  `docs/reference/cli/vcs.md`, and `docs/reference/vcs-backend.md` updated.
- **P2, `AGENTS.md:145` still presented a bare `gh pr merge` one-liner.**
  Fixed: it now says `lrh vcs merge`. My first survey had not searched
  root-level docs. The reviewer also found the tracked `.gemini` Antigravity
  mirror still carries the old text. **Not changed, deliberately:** that
  mirror is already broadly stale (17 of 26 skills differ, one missing), so
  re-rendering it would sweep unrelated drift into this PR. Recorded as a
  follow-up.
- **P3, `pr` not enforced to be a URL.** Fixed in the GitHub backend, which
  now refuses anything but an `https://<host>/<owner>/<repo>/pull/<n>` URL
  before any `gh` call.
- **P3, a read-back state of `CLOSED` was reported as `queued`.** Fixed: only
  `OPEN` is `queued`; any other non-`MERGED` state is a
  `MergeVerificationError`.
- **P3, `run_gh` only caught `FileNotFoundError`.** Fixed: other `OSError`s
  become a clean `RuntimeError`.

Also acted on from the report: added the missing tests (CLI exit 2 for an
unreadable final state, `--backend` passthrough, the failed-merge-call paths,
URL refusal, `run_gh` launch failures), made the wiring test's regex tolerate
a line-wrapped command, and corrected the audit's `git add` count from 12 to
13 (the reviewer's count reproduced; the audit now states the looser pattern).
One existing CLI test that encoded the old failure message was replaced by its
stricter successor rather than loosened.

The harness flagged the reviewer's hand-back as matching an
instruction-shaped pattern (`settings-json`). The report contained no
directives; it quoted `.claude/settings.json` while verifying a docs claim.

# Validation

- After the fixes: `scripts/format`, `scripts/lint`, the four affected test
  modules (55 tests), and `lrh validate` (0 errors, 0 warnings) all pass.
- Full `scripts/test` re-run after the fixes; result recorded in the
  implementation PR's execution record.
- Run from the `LRH` conda env, which carries the pinned `ruff 0.15.12` and
  `black 26.3.1`.

# Follow-up

- The tracked `.gemini/plugins/lrh/skills/` Antigravity mirror is broadly
  stale and still presents the raw `gh pr merge` command in
  `lrh-land`/`lrh-confirm-fixes`/`lrh-review-response`. Refreshing it is a
  separate, target-wide decision (`lrh skills install --target antigravity
  --local --force` overwrites every modified skill there).
- `lrh vcs merge` is deliberately not in the project's `allow` list; whether
  to pre-approve it is a settings decision not made here.

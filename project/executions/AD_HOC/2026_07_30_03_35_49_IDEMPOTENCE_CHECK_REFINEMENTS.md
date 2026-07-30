---
execution_id: 2026_07_30_03_35_49_IDEMPOTENCE_CHECK_REFINEMENTS
prompt_id: PROMPT(AD_HOC:IDEMPOTENCE_CHECK_REFINEMENTS)[2026-07-30T03:35:36-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/441
commit: 
agent: claude_app
instruction_source: project/design/backlog.md "Idempotence-check refinements deferred from PR #438"
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-30T03:35:49-04:00
---

# Summary

Follow-up PR resolving all 5 items in `project/design/backlog.md`'s
"Idempotence-check refinements deferred from PR #438" entry: cross-status
`rerun_of` precedence, `find` exit-status/sorting/cross-branch detection,
explicit-rerun branch-name collision, and bringing `lrh-review-response`/
`lrh-confirm-fixes` up to the `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`
trailing-segment invariant. Note: prompt ID was minted after implementing
the fixes rather than before, since this was a direct continuation of an
already-fully-scoped backlog item, not new exploratory work — a deviation
from the mint-first convention, noted for traceability.

# Result

Redesigned the idempotence check in `lrh-proposal`, `lrh-work-item`, and
`lrh-workstream` (SKILL.md + `references/execution-record.md`, 6
locations) to resolve items 1–4 together:

- **Item 1 (cross-status `rerun_of` precedence):** replaced the two-bucket
  ("any blocking match" vs. "all non-blocking matches") logic with a
  single most-recent-by-timestamp selection — combine all matches, sort,
  take the last one, and decide block/continue from *that* match's status
  alone. This also removes the round-5 fix's "ask the user to disambiguate
  among multiple blocking matches" path entirely: recency resolves it
  deterministically instead.
- **Item 2 (`find` exit status + sorting):** added `| sort` to every glob
  (timestamp-prefixed filenames sort chronologically, making "most recent"
  well-defined) and reworded the missing-directory note to say plainly
  that a nonzero exit with no output means no prior record, not a failure,
  rather than relying on `2>/dev/null` alone to convey that.
- **Item 3 (explicit-rerun branch-name collision):** Step 4 now directs
  checking whether the matched record's branch still exists
  (`git rev-parse --verify`) when the user asks for a rerun; Step 6 (branch
  creation) now reuses that branch instead of `git checkout -b`-ing a
  duplicate name when it does.
- **Item 4 (cross-working-tree detection):** added a second search over
  open PRs' remote branches (`gh pr list` + `git ls-tree -r origin/<branch>`)
  alongside the existing current-checkout `find`, so a prior record that
  only exists on another open PR's branch is no longer invisible.

**Item 5** — brought `lrh-review-response` and `lrh-confirm-fixes` up to
the invariant: anchored both skills' globs to the trailing filename
segment (`*_<SLUG>.md` instead of `*<SLUG>*.md`). `lrh-review-response`
additionally gained the same per-match status-handling branch as the
other 3 skills (it previously stopped on *any* match unconditionally,
including non-blocking `failed`/`reverted`/`superseded` ones).
`lrh-confirm-fixes`'s status-handling itself was correct and untouched
(Decision 12 — every match is warning-only, never blocking) — only its
glob needed anchoring. Neither skill needed the branch-reuse (item 3) or
cross-PR search (item 4) additions: `lrh-review-response` and
`lrh-confirm-fixes` both operate on an already-checked-out open PR branch
rather than creating a new one, so those two gaps don't apply to them.

**Noticed but not fixed (out of scope for this PR):**
`lrh-review-response/SKILL.md` Step 7 has a *separate* unanchored
substring `find` (`find project/executions/ -name "*${UPPER_SLUG}*.md"`)
used to locate the *primary* record for `rerun_of` attribution — a
different search than the Step 3 idempotence check this PR fixes, with
lower risk (misattribution, not a false block) but the same underlying
substring-match issue. Not covered by backlog item 5's wording; flagging
here rather than silently expanding scope.

A first review round on commit `9c54c3f` surfaced 4 real findings (9
comments, same root causes), all in the items 1/3/4 cross-PR/branch-reuse
logic added to `lrh-proposal`/`lrh-work-item`/`lrh-workstream` — none in
`lrh-review-response`/`lrh-confirm-fixes`, which didn't get that logic.
Codex (2): the cross-PR search assumed `origin/$branch` was already
fetched locally (it isn't, for a PR created after the last fetch or from
a fork — `2>/dev/null` hid the resulting failure, so the check would
incorrectly conclude no prior record existed); and the branch-reuse check
(`git rev-parse --verify <branch>`) only tested local branches, but the
typical rerun scenario is a branch that only exists as `origin/<branch>`
— the reuse path would silently fall through to creating a duplicate that
later collides on push. Copilot (7, same underlying gap): the cross-PR
search printed only matched file paths with no branch context, so "read
that match's status" couldn't actually be executed for a remote-only
match — no ref to read it from.

Fixed by combining both searches into one pipeline: fetch each open PR's
branch before `ls-tree` (so `origin/$branch` is guaranteed to resolve),
tag each remote match with `<TAB><branch>` so it stays actionable (read
via `git show origin/$branch:$path` without checking out), and pipe the
combined current-checkout + tagged-remote lines through `sort` (still
correct, since every line starts with the same timestamp-prefixed path).
Branch-reuse now checks local, then `git ls-remote --exit-code --heads
origin <branch>` for the remote, tracking it explicitly
(`git checkout -b <branch> --track origin/<branch>`) if only the remote
exists, falling through to fresh-from-`main` only if neither does.

A second review round on commit `d0140f6` surfaced 2 more findings, both
Codex, both real: (1) the fetch-by-branch-name approach still assumed the
PR's head branch lived in `origin` — for a fork-based PR it lives in the
fork, so `origin/$branch` would never resolve regardless of fetching, and
the check would silently conclude no prior record exists. Fixed by
switching to GitHub's `refs/pull/<N>/head` — a ref the base repository
exposes for every open PR unconditionally, fork or not — fetched into a
local `refs/remotes/pr/<N>` ref and tagged in output as `PR#<N>` instead
of a branch name. Step 6's branch-reuse now checks whether a `PR#<N>`
match is cross-repository (`gh pr view <N> --json isCrossRepository`)
before assuming reuse is possible — a fork PR's branch isn't something
this session has push access to, so that case stops and asks the user
rather than silently attempting to continue it. (2) `lrh-review-response`
had a `rerun_of` precedence conflict I introduced: Step 3's new match
wanted to set `rerun_of` to a prior review-response attempt, while Step
7's pre-existing (untouched) primary-record search also wants to set the
same single scalar field to the implementation record. Fixed by defining
explicit precedence in Step 7: a Step-3-matched prior review-response
record wins (it's the more specific "rerun of X" relationship); the
primary-record search is now a fallback used only when Step 3 found
nothing.

A third review round on commit `43c2d9d` surfaced 2 more findings, both
Codex: (1) P1 — any PR descended from a commit that already has the
matched file would re-emit that same path via `ls-tree`, tagged with that
PR's (unrelated) number, since the PR merely inherited the file rather
than introduced it. Because a bare path sorts before its own tagged
duplicate, "take the last line" would pick the spurious `PR#<N>` entry as
the most recent match, and a rerun could check out and push to a
completely wrong branch — a real correctness bug, not a nitpick. Fixed by
capturing local matches first (`LOCAL_MATCHES=$(find ...)`) and excluding
any remote match whose path already appears there
(`grep -vxFf <(echo "$LOCAL_MATCHES")`) before tagging. (2) P2 — the fetch
into `refs/remotes/pr/<N>` was a plain (non-forcing) refspec; if a
previously-scanned PR was later force-pushed, the update would be
rejected as non-fast-forward, `2>/dev/null` would hide the rejection, and
the stale cached ref would keep getting scanned indefinitely. Fixed by
forcing the refspec (`+refs/pull/$pr/head:...`).

This was reported to the user as a 3rd straight round finding deeper
issues in the same cross-PR/fork-branch discovery logic, flagged
explicitly per the established pattern rather than fixed silently — user
confirmed: fix both and continue.

A fourth review round on commit `cef6972` surfaced 2 more findings, both
Codex. Given this was now a 4th straight round on the same logic, both
were reported to the user with explicit severity framing before touching
anything, rather than fixed silently: (1) P2 — `gh pr list` defaults to
`--limit 30`; in a repo with more than 30 open PRs, older ones would be
silently omitted from the scan. Trivial one-line fix, applied regardless
of the decision on (2). (2) P1 — the round-3 local-match dedup only
excluded matches already in the *current checkout*, not matches
duplicated *across* multiple open PRs. If PR B is branched from
still-open PR A, both pull refs contain the same inherited file; both
survive the filter, get tagged (`PR#A`, `PR#B`), and `sort` picks one
arbitrarily by PR number — potentially B (the descendant that only
inherited the record) over A (the true introducer), again risking a
push to the wrong branch on rerun. User chose to fix this properly rather
than defer it.

Fixed by determining, for each open PR, whether it actually *introduced*
the file: fetch the PR's declared base ref (`baseRefName`) alongside its
head, compute `git merge-base` between them, and check whether the file
already existed at that merge-base (`git cat-file -e "$merge_base:$path"`)
— if so, this PR only inherited it and the match is skipped; if the
merge-base lookup itself fails (e.g. an unreachable fork base), the match
is kept rather than silently dropped, since failing to prove inheritance
isn't the same as proving originality. Verified with a local git
simulation before applying: a two-PR stack (PR 1 introduces the file from
`main`; PR 2 branches from PR 1 and only adds an unrelated file) correctly
kept PR 1's match and skipped PR 2's. Bumped `gh pr list --limit` to 1000
in the same change.

A fifth review round on commit `95feb1a` surfaced a finding of a different
character than the previous four: Codex found that
`src/lrh/prompt_workflow.py:299` generates execution-record filename
timestamps via `datetime.now(utc).astimezone()` — converting to the
**local** system timezone before formatting — so filename lexicographic
order is not reliably chronological across machines in different
timezones (a record made at local `09:00-04:00` = `13:00 UTC` sorts
*before* one made at local `12:00+00:00` = `12:00 UTC`, though the first
is chronologically later). This called into question every "sort
filenames, take the last line" recency decision made across this entire
PR (and arguably PR #438's original design too). Verified the claim
directly against the CLI source before reacting. Reported to the user as
a 5th straight round and a deeper, more foundational finding than the
prior four, distinguishing two possible scopes: (a) within this PR's
scope, stop trusting filename order and compare `created_at:` values
instead; (b) the actual root fix, in `prompt_workflow.py` itself — real
Python source with its own test suite, well beyond a skills/docs PR. User
chose: file (b) as its own backlog item, fix (a) now, and continue.

Filed `project/design/backlog.md` "Execution-record filename timestamps
use local time, not UTC" for (b). Fixed (a) across all 7 locations that
relied on filename-sort recency (`lrh-proposal`/`lrh-work-item`/
`lrh-workstream` SKILL.md + references/execution-record.md, and
`lrh-review-response/SKILL.md` Step 3): replaced "take the last line" with
reading every surviving match's `created_at:` frontmatter field and
comparing normalized absolute instants — not raw ISO8601 strings either,
which carry their own UTC offsets and don't sort correctly as text.
Initially suggested GNU `date -d "$created_at" +%s` for normalization;
caught during self-review (verified locally on this macOS sandbox, where
BSD `date` lacks `-d` and the command fails) that this isn't portable, and
replaced it everywhere with a `python3 -c "...fromisoformat(...).timestamp()"`
one-liner, verified to produce the mathematically correct ordering for
the exact 09:00-04:00-vs-12:00+00:00 example Codex cited.

A sixth review round on commit `f1f7aaa` surfaced 2 more Codex findings.
Copilot did **not** review this commit — its last review stayed on
`95feb1a` despite an explicit retrigger, a known pattern (a previously
responsive bot going silent for hours with no error) — reported to the
user explicitly rather than assumed either "still pending" or "clean."
User directed: fix the doc-consistency finding, file the fetch-robustness
one to the backlog, and proceed to the merge gate (not wait further on
Copilot).

(1) Filed to `project/design/backlog.md` ("Idempotence cross-PR discovery
doesn't fail closed on fetch errors"): `gh pr list`/`git fetch` calls in
the cross-PR search all suppress stderr and never check exit status, so a
genuine failure (auth, network, missing ref) is indistinguishable from
"legitimately nothing found" — could report a false "no prior record" or
scan a stale cached ref from an earlier successful fetch. Deferred as a
real design question (what does "abort" mean inside an already-composed
shell pipeline), not a one-line patch, and this PR already fixed 3
separate bugs in the same pipeline.

(2) Fixed: `lrh-review-response/references/review-response-workflow.md`
(a file untouched until now) documented a conflicting, older rerun
convention — `rerun_of` linking only to the primary implementation
record, the same unanchored substring `find` the earlier rounds fixed in
`SKILL.md` itself, and an explicit rerun minting an entirely new
`-review-r2` slug rather than reusing the original. All three contradicted
the precedence logic added to `SKILL.md` in round 2. Rewrote the
reference to describe the two-tier precedence (a Step-3-matched prior
review-response record wins; the primary-record search — now with the
same trailing-segment anchor — is the fallback) and to state explicitly
that reruns reuse the same slug, no `-r2` variant.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- `scripts/format --check --diff`, `scripts/lint` — clean
- `diff -r` clean between each `src/lrh/skills/<skill>` and its
  `.claude/skills/<skill>` mirror, all 5 skills touched

# Follow-up

- Consider anchoring `lrh-review-response/SKILL.md` Step 7's separate
  `rerun_of`-attribution `find` (noticed above, not fixed here).
- The `/lrh-decision` skill is wanted per user confirmation
  (`project/design/backlog.md`) but not yet scoped or built.

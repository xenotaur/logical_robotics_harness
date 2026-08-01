# Round-Cap Gate — Reference

Where `/lrh-confirm-fixes` Step 8's round-cap check comes from, exactly
what it bounds, and the state schema it reads and writes. Read this before
implementing or modifying Step 8's round-cap logic.

---

## Why this exists

PR #442 in this repo drove Step 8's bot-retrigger loop for 14 rounds — 13
real findings, each fixed and re-triggered — while its own CHAIN-NOTE
recorded `cycles=1`, because `cycles` counts
`/lrh-review-response` ↔ `/lrh-confirm-fixes` *invocations*, not the
bot-retrigger batches that actually happened inside a single Step 8 run
(`project/executions/AD_HOC/2026_07_30_05_33_51_LRH_MERGE_GATE_POLICY_391AEF_CONFIRM.md:54-61,102`).
GitHub Copilot's review-bot credit pool is shared across every concurrently
active project in this workspace, with no per-repo partitioning at the
platform level — an unattended long loop on one repo can silently draw
down budget an unrelated, higher-priority repo needs. `DEC-DELIBERATE-CHAIN-INITIATION`
already requires a human-set stop-work condition before any chain of these
rounds runs automatically; this mechanism turns that into a persistent,
recurring, numeric checkpoint instead of prose re-elicited each run.

## What "round" means

One **bot-retrigger batch**: a single pass of Step 8's `gh pr comment
"@codex review"` mention and `gh pr edit --add-reviewer @copilot`
review-request (or whichever reviewers `REVIEWS.md` documents), issued
together. Note the asymmetry: Codex is retriggered by a plain comment
mention, while Copilot must be retriggered via an explicit reviewer
request — a bare `@copilot` comment mention hits GitHub's Copilot coding
agent instead and can push commits directly to the PR branch (see
`SKILL.md`'s retrigger step for the full explanation). This is the unit
PR #442's incident actually repeated 14 times — not `cycles`, which
stayed at `1` throughout that incident and would never have triggered a
cycles-based cap.

## What this bounds — and what it does not

This check governs **only** `/lrh-confirm-fixes` Step 8's own
bot-retrigger action. It does **not**:

- Gate `/lrh-review-response` — that skill has no bot-retrigger action to
  gate (verified by inspection: no `@codex review`/`@copilot review` call
  exists anywhere in `lrh-review-response/SKILL.md`). If a future item
  gives it one, this scope boundary needs revisiting so that addition
  doesn't silently bypass the cap.
- See or limit Jules-originated PR activity, or any human-driven review
  request — both are structurally outside this skill's reach (Codex and
  Jules cannot invoke Claude Code skills at all; see
  `WI-TEMPLATE-AUDIT-WORK-ITEMS.md:47-53`).
- Bound aggregate GitHub Copilot spend — it bounds one specific mechanism
  (unattended, automatic retrigger escalation), not total platform usage.
  No GitHub billing/usage API is queried; the human supplies portfolio
  context (what else is running, what's urgent) at the gate, since no
  automated source for that currently exists in this project. See
  "Detecting a stalled reviewer session" below for a heuristic that
  identifies *a* stalled session without querying billing data — it still
  does not measure or bound aggregate spend.

## Detecting a stalled reviewer session

Step 8.3 in `SKILL.md` needs to tell "reviewer never invoked / not
configured for this repo" apart from "reviewer's own session started and
stalled" before asking the human — those need different answers (wait
longer vs. top up usage/credits and retry vs. authorize a different
remediation), and conflating them into one generic question hides that
choice. GitHub does not expose a billing/credit-usage API (see "What this
bounds" above), and a stalled Copilot coding-agent or code-review session
does not post any comment, review, or check-run output naming the cause —
the exhaustion message ("...you've run out of your included AI credits
for the month...") renders only in the GitHub web UI's session panel and
does not appear on any REST-accessible surface. Verified directly against
a live incident (`xenotaur/LCATS#202`, 2026-07-31): grepping every PR
comment, issue comment, and timeline event body for "credit" returned
nothing.

What *is* available is a stall heuristic, built from two REST calls:

1. **Check-runs on the reviewer's own commit:**

   ```bash
   gh api repos/<owner>/<repo>/commits/<sha>/check-runs \
     --jq '.check_runs[] | select(.name=="copilot-pull-request-reviewer") | {status, conclusion, started_at, completed_at}'
   ```

   A hosted reviewer session that's actually running (rather than simply
   not configured) shows up here. `status: "in_progress"`,
   `conclusion: null`, `completed_at: null` held past a reasonable wait —
   reuse `STALE_AGE_SECONDS` (15 minutes, "Round-state branch mechanics"
   above) as the threshold, since that is this skill's own existing
   "reasonable wait" constant — means the session started and never
   reached a terminal state. (Substitute the check-run `name` this
   repository's reviewer actually reports if not GitHub Copilot code
   review's default; per GitHub's webhook documentation, `check_run`
   events fire only on `created`/`rerequested`/`completed`/
   `requested_action` — there is no periodic "still in progress" event, so
   this must be polled, not subscribed to.)

2. **Issue timeline, for corroboration:**

   ```bash
   gh api repos/<owner>/<repo>/issues/<pr-number>/timeline \
     --jq '.[] | select(.event | startswith("copilot_work"))'
   ```

   A `copilot_work_started` event with no later `copilot_work_finished` or
   `copilot_work_finished_failure` event for the same attempt corroborates
   the check-run reading — the session was invoked and is the thing that
   didn't finish, not a configuration gap.

Both signals together (started, no terminal event, past the threshold) is
**stalled** — distinct from **never invoked**, which shows no check-run
for that reviewer at all and no `copilot_work_started` event since the
retrigger. Neither signal, alone or combined, identifies *why* the
session stalled — credit exhaustion is the observed cause in the verified
incident above, but a platform outage or an unrelated internal error would
look identical from the API side. Surface it to the human as "stalled,
cause unknown, credit exhaustion is one known cause," never as a confirmed
diagnosis: this is a heuristic, not a diagnostic. Symmetrically, do not
treat the *absence* of a stall signal as proof the reviewer is simply
unconfigured — Step 8's existing rule against inferring configuration
state from silence (`SKILL.md`, Step 8, "Do not infer 'no automated
reviewer is configured' from silence either") still applies unchanged.

## State schema

One JSON file per PR, at
`project/executions/round_state/<owner>-<repo>-pr<N>.json`, keyed by the
PR's **immutable identity** — owner, repo, and PR number parsed from the
PR's **canonical** URL (`gh pr view --json url --jq .url`), never from
the branch name or from whatever string form of the URL was passed in or
auto-detected. Three requirements this schema depends on:

- **Canonical identity, not string equality.** A branch-name-derived key
  is unsafe: branch names can be reused after merge, or collide across
  two fork PRs, silently mapping unrelated PRs onto the same state file.
  A raw string comparison of URLs is *also* unsafe on its own — a
  trailing slash or an explicit-argument-vs-auto-detected form can be the
  same PR written two different ways, and comparing them naively would
  read as a false data-integrity mismatch. Resolve to the canonical form
  first, on both sides, before keying or comparing.
- **Every write is atomic.** Write to a temp file in the same directory,
  flush it, then rename it over the target — a plain in-place rewrite
  interrupted mid-write can leave a truncated or partially-updated file
  that the crash-recovery path (below) then cannot even parse, defeating
  the mechanism's own core invariant.
- **Every write is committed and pushed immediately, to the dedicated,
  LRH-namespaced `lrh-round-state` branch — never to the PR branch under
  review.**
  Atomicity protects against a corrupted file; committing protects
  against a purely local edit that's invisible to a different invocation
  or a fresh session; and keeping it off the reviewed PR's own branch
  protects the CI/REVIEW-LANDED evidence Step 8 already gathered from
  being invalidated by state-only commits moving that PR's `HEAD`. See
  "Round-state branch mechanics" below for the exact mechanism.

Deliberately **not** a `.md` file: `lrh validate`'s execution-record scan
globs `project/executions/**/*.md` (`src/lrh/control/validator.py`), so a
non-`.md` extension keeps this file outside that validation surface
without needing a schema exemption.

```json
{
  "pr": "<pr-url>",
  "ceiling": 3,
  "completed_count": 0,
  "pending_attempt": null
}
```

with a batch in flight:

```json
{
  "pr": "<pr-url>",
  "ceiling": 3,
  "completed_count": 1,
  "pending_attempt": {
    "promoted": true,
    "reviewers": {"codex": "submitted", "copilot": "pending"}
  }
}
```

- `pr` — the canonical PR URL this file belongs to (see "Canonical
  identity" above). Checked, not just stored: every read verifies this
  matches the target PR's canonical URL exactly; a mismatch is a
  data-integrity anomaly, surfaced to the human, not guessed through.
- `ceiling` — the currently authorized round limit. Starts at 3 (the
  default first suggestion); updated synchronously whenever the human
  authorizes a new value at the three-way gate. Never reset or
  reconstructed from CHAIN-NOTE — CHAIN-NOTE is written post-hoc, only at
  closeout, and would be stale or absent for an in-progress PR.
- `completed_count` — number of retrigger batches promoted to completed.
  Incremented exactly once per batch, the first time any reviewer in it
  is confirmed submitted (see "Any-side-effect-counts promotion" below).
- `pending_attempt` — `null` when no batch is in flight. While a batch is
  in flight: `promoted` tracks whether `completed_count` has already been
  incremented for this batch (so a later reviewer settling in the same
  batch never double-counts it), and `reviewers` tracks each mentioned
  reviewer's status individually (`"pending"`, `"submitted"`, or
  `"failed"`) — not a single flat marker cleared on the first success.
  This is what lets an interrupted multi-reviewer batch be resolved
  correctly on the next invocation: if Codex submitted but Copilot's call
  never completed, the state still records Copilot's status precisely
  (`"pending"`, not silently dropped or folded into "the batch is done"),
  so the next invocation can resolve it conservatively — see
  "Crash-recovery reconciliation" below for why that resolution does not
  re-mention the reviewer. `pending_attempt` clears to `null` only once
  every reviewer in it has a terminal status.

## Round-state branch mechanics

**Round-state files are never committed to the PR branch under review.**
Every state-file write in this skill's own Step 8 happens *during* the
same run that gathers CI and REVIEW-LANDED evidence for that PR's
current `HEAD` — pushing a state update to that same branch would move
`HEAD` to a new, unreviewed commit mid-check, silently invalidating the
evidence Step 8 already collected and forcing either a stale verdict or
an unbounded re-check loop chasing its own bookkeeping commits.

Instead, all round-state files across all PRs live on one dedicated,
long-lived, **namespaced** `lrh-round-state` branch — content-only,
never merged into any default branch or PR branch, analogous to the
main-worktree-lock pattern `/lrh-land` uses to push housekeeping commits
without disturbing a checked-out branch
(`src/lrh/skills/lrh-land/references/land-workflow.md`). Since LRH is a
reusable harness installed into independent client repositories
(`AGENTS.md:5`), an `lrh-`-prefixed name (not a generic `round-state`)
and an explicit ownership check are both required — a client repository
could otherwise already have an unrelated branch that happens to share
the name, and this mechanism must never silently adopt, write to, or
clean up a branch it doesn't own. **Every operation — including
bootstrap — happens in a throwaway worktree, never in the main
checkout**, so a failure at any step leaves the PR branch's own working
tree untouched; **every worktree operation cleans up stale state from a
prior interrupted invocation first**, but only when it's actually stale
(age-checked, never force-removed on sight — a live concurrent
invocation's worktree must not be destroyed out from under it); and
**every commit follows this repository's Conventional Commits
requirement** (`STYLE.md`, `chore` type — "Maintenance work... planning
artifacts"):

```bash
WT=/tmp/lrh-round-state-<key>-$$   # unique per invocation (PID-suffixed)
BOOTSTRAP_MARKER="chore(round-state): initialize LRH round-state branch"
STALE_AGE_SECONDS=900   # 15 minutes — matches this skill's other "reasonable wait" thresholds

# Clear only genuinely stale registrations — a prior invocation that died
# between `worktree add` and `worktree remove` leaves the branch
# registered as checked out, which blocks every subsequent `worktree add`
# for that branch, including the one this recovery needs to run. But a
# registration less than $STALE_AGE_SECONDS old may belong to a live,
# concurrently-running invocation — force-removing it unconditionally
# could destroy another process's in-progress work. Parse the porcelain
# output's own `worktree <path>` field for the matching record (not an
# adjacent line's field, which can be the wrong one depending on record
# shape), and gate removal on the worktree directory's own mtime:
git worktree prune
STALE_WT=$(git worktree list --porcelain | awk '
  /^worktree /{path=$2}
  /^branch refs\/heads\/lrh-round-state$/{print path}
')
if [ -n "$STALE_WT" ]; then
  # GNU stat's `-f` means "filesystem status", not "use this format" (that's
  # BSD/macOS stat) — on GNU it exits 0 with the wrong multiline output
  # instead of failing, so a `||`-based fallback never triggers. Detect the
  # working flavor explicitly instead of relying on exit-status fallback:
  if MTIME=$(stat -c %Y "$STALE_WT" 2>/dev/null); then
    : # GNU stat succeeded
  else
    MTIME=$(stat -f %m "$STALE_WT")   # BSD/macOS stat
  fi
  AGE=$(( $(date +%s) - MTIME ))
  if [ "$AGE" -ge "$STALE_AGE_SECONDS" ]; then
    git worktree remove --force "$STALE_WT" 2>/dev/null
  else
    echo "lrh-round-state worktree at $STALE_WT is only ${AGE}s old — may be a live concurrent invocation, not stale. Stopping rather than force-removing." >&2
    exit 1   # surface to the human; do not guess
  fi
fi
git worktree prune

# Resolve this repository's actual default branch — never hard-code
# `main`; a client repository may use `master`, `trunk`, or anything else.
# Check emptiness explicitly rather than relying on the pipeline's exit
# status: without `pipefail`, `git symbolic-ref ... | sed ...` reports
# success (sed's own exit code) even when symbolic-ref itself failed and
# produced no output, so a `||`-based fallback would never fire and
# DEFAULT_BRANCH would silently stay empty:
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
  | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
fi

# Bootstrap the branch once, if it doesn't exist yet — in a throwaway
# worktree, so a failed push can never strand the main checkout. If the
# branch *does* already exist, verify LRH actually created it before
# treating it as this mechanism's own — never adopt a pre-existing,
# unrelated branch that happens to share the name:
if git ls-remote --exit-code --heads origin lrh-round-state >/dev/null; then
  git fetch origin lrh-round-state --quiet
  ROOT_MSG=$(git log --format=%s --reverse origin/lrh-round-state | head -1)
  if [ "$ROOT_MSG" != "$BOOTSTRAP_MARKER" ]; then
    echo "origin/lrh-round-state exists but its root commit doesn't match this mechanism's bootstrap marker — likely an unrelated pre-existing branch. Stopping rather than adopting it." >&2
    exit 1   # surface to the human; never silently write to an unowned branch
  fi
else
  git worktree add --detach "$WT-bootstrap" "origin/$DEFAULT_BRANCH"
  git -C "$WT-bootstrap" checkout --orphan lrh-round-state
  git -C "$WT-bootstrap" rm -rf . >/dev/null
  git -C "$WT-bootstrap" commit --allow-empty -m "$BOOTSTRAP_MARKER"
  git -C "$WT-bootstrap" push origin lrh-round-state
  git worktree remove --force "$WT-bootstrap"
fi

# Fetch and fast-forward the *local* branch to match the remote tip
# before using it — `git fetch` alone only updates
# `origin/lrh-round-state`; a stale local branch would base a new commit
# on an old tip and get rejected as non-fast-forward on push, defeating
# this mechanism in the exact concurrent-session case it exists to
# support:
git fetch origin lrh-round-state --quiet
git show origin/lrh-round-state:project/executions/round_state/<key>.json 2>/dev/null   # read, without disturbing the current checkout
git branch -f lrh-round-state origin/lrh-round-state 2>/dev/null \
  || git branch lrh-round-state origin/lrh-round-state

# Write, via a throwaway worktree (keeps the PR branch's checkout untouched).
# Wrap the whole read-modify-write in a bounded retry loop: two clones can
# each fetch the same tip, commit independently, and race to push — the
# second push is then rejected as non-fast-forward even though nothing
# was checked out concurrently (git's worktree-checkout exclusivity only
# prevents *simultaneous* checkouts, not this fetch-then-push race). On
# rejection, re-fetch, re-fast-forward, and reapply the *same logical*
# modification (e.g. "increment completed_count by 1 from its current
# value", not "set it to a hard-coded number") against the new tip —
# never just re-push the same stale commit:
ATTEMPTS=0
until [ "$ATTEMPTS" -ge 5 ]; do
  git worktree add "$WT" lrh-round-state
  # ... write the file atomically inside "$WT/project/executions/round_state/<key>.json",
  #     recomputing the change against this worktree's *current* content
  #     (not a value captured before this retry loop started) ...
  git -C "$WT" add project/executions/round_state/<key>.json
  git -C "$WT" commit -m "chore(round-state): <one-line change summary>"
  if git -C "$WT" push origin lrh-round-state; then
    git worktree remove "$WT"
    break
  fi
  git worktree remove --force "$WT"
  ATTEMPTS=$((ATTEMPTS + 1))
  git fetch origin lrh-round-state --quiet
  git branch -f lrh-round-state origin/lrh-round-state
done
if [ "$ATTEMPTS" -ge 5 ]; then
  echo "lrh-round-state push kept losing the race after 5 retries — surfacing rather than guessing." >&2
  exit 1
fi
```

If `git worktree add "$WT" lrh-round-state` fails at the very first
attempt after pruning (a genuinely concurrent invocation holding the
checkout right now, not a stale leftover), retry with a short backoff a
few times rather than forcing — forcing could corrupt a live concurrent
writer's in-progress commit. If it keeps failing, surface that to the
human rather than guessing; do not silently drop the state update.

`lrh-round-state` is deliberately not merged anywhere and carries no PR of
its own — it is pure bookkeeping data, git-tracked for durability and
history the same way any other committed file is, but fully decoupled
from every PR's own review lifecycle. `lrh validate` never sees it: the
branch isn't checked out during normal work, and the `.json` extension
(not `.md`) keeps it outside the execution-record scan even where it is.

## Check-then-attempt ordering

Settling an in-flight batch (any reviewer still `"pending"` in
`pending_attempt`) always happens first and is **never** blocked by the
ceiling — the batch was already authorized when it started. Only once
`pending_attempt` is `null` does starting a *new* batch check
`completed_count >= ceiling`. If true, stop — present the three-way gate,
do not start the batch. If false, persist a fresh `pending_attempt` (all
reviewers `"pending"`, `promoted: false`) and start the batch, promoting
(`completed_count += 1`, `promoted: true`) as soon as the first reviewer
in it is confirmed submitted.

Worked example, ceiling 3: batches 1, 2, and 3 each pass the check
(`0 >= 3`, `1 >= 3`, `2 >= 3` are all false) and raise the count to 3; a
4th batch is blocked, since `3 >= 3` is true, before it starts. Ceiling
`N` means `N` batches are allowed to run; the gate fires before the
`(N+1)`th.

## Any-side-effect-counts promotion

A batch is promoted to completed (`completed_count += 1`, exactly once)
the moment **any** reviewer in it is confirmed submitted — not only after
every reviewer in the batch succeeds. Requiring full-batch success before
counting creates a real cost-cap loophole: a batch where one mention
posts and another fails could be retried indefinitely, each retry a
real, credit-consuming external side effect, without the counted round
ever reaching the ceiling. An ambiguous submission result (a network
timeout with no confirmed server-side outcome) is treated as
`"submitted"`, not `"pending"`/`"failed"` — conservative toward counting
more, never fewer, side-effect-bearing attempts. A still-`"pending"`
reviewer left over from an earlier, already-promoted batch never
increments `completed_count` again when it's later resolved — that batch
is already counted; resolving the remaining reviewer only updates its
status (see "Crash-recovery reconciliation" for why that resolution does
not re-mention them).

## Crash-recovery reconciliation

Every invocation settles any in-flight `pending_attempt` before running
the ceiling check for a new batch. If a process died mid-batch (one
reviewer submitted, another still `"pending"`), a restart must resolve
that reviewer's status as a continuation of the same batch — not start
counting a new one, and not silently drop the outstanding record —
without necessarily reaching that reviewer again (see below). Treating
the whole marker as resolved-or-discard-only (rather than per-reviewer)
would let an outstanding mention's status go untracked entirely; treating
it as "safe to retry" would risk a real duplicate side effect. Both defeat
the cap this mechanism exists to enforce.

**A `"pending"` status found at reconciliation time is itself
undecidable and must be treated as ambiguous, not as "never attempted."**
A crash cannot distinguish "the `gh pr comment` call never ran" from "it
ran, posting a real comment and consuming a real credit, but the status
write back to the state file never persisted" — both leave the same
on-disk `"pending"` value. Per the same conservative rule as a live
ambiguous result (see "Any-side-effect-counts promotion" above), treat it
as `"submitted"` immediately, promoting the batch if it's the first
submitted reviewer. **Do not re-issue that reviewer's mention as a
recovery action.** Retrying is not the harmless case described under
"Once the round-cap check above has cleared" in `SKILL.md` — that
harmlessness is about a reviewer that genuinely isn't configured for this
repo, not about a reviewer that may have already been reached for real; a
returned comment URL is by this same document's own definition a
confirmed, credit-consuming submission, so retrying one that may have
already succeeded risks two real review requests counted as one round.
If the crash genuinely happened before any side effect occurred, that
reviewer simply gets no mention for this batch — no worse than a
reviewer that's silently unconfigured, which Step 8's existing "no
response after a reasonable wait" path already asks the human about
rather than inferring either way. This is different from a batch member
that's already `"failed"` (a confirmed, decidable outcome) — only
genuinely undecidable `"pending"` status gets the conservative
promote-without-retry treatment.

## The three-way gate

Fires only when the ceiling check blocks. Presents: current
`completed_count`, `ceiling`, and a one-line findings summary from prior
rounds if derivable from earlier review comments. The human answers one
of:

- **Authorize a new ceiling** — default suggestion sequence is
  3 → 10 → 20; beyond 20, ask for the next value directly rather than
  computing a further default (no formula — 30, 40, or doubling are all
  equally plausible and none is grounded). The actual next ceiling is
  always human-supplied, never auto-applied. Written to `ceiling`
  synchronously before the next batch starts.
- **Deny and stop** — no further batches; the PR's review state as of the
  last completed batch stands.
- **Pause** — defer the decision; no batch starts until the human
  responds.

This is the one point in Step 8 that always requires an explicit human
answer — never an inferred signal, and never satisfied by a bot response.

## CHAIN-NOTE relationship

The round-cap counter (`completed_count`) is a distinct, finer-grained
metric from CHAIN-NOTE's `cycles` field — see
`src/lrh/skills/lrh-land/references/land-workflow.md`'s `stops`/`note`
field docs for how a round-cap gate crossing should be recorded there.
`cycles` and `completed_count` measure different things and are not
interchangeable.

## Risk Notes — deferred hardening

The round-state mechanism grew substantially beyond its originating
work item's description ("a field on the execution record, or a small
per-PR state artifact") over eight review rounds on its implementation
PR, each of which found a real, distinct correctness bug: worktree-path
parsing, branch fast-forwarding, default-branch hard-coding, concurrent
force-removal safety, cross-tenant branch-name collisions, Conventional
Commits compliance, `stat` portability, `pipefail` semantics, and
concurrent-push races. All were fixed. The following residual risks are
**deliberately deferred** rather than chased further, consistent with
this project's practice of fixing what's core to a PR's purpose and
deferring narrow, increasingly-rare edge cases to follow-up work:

- **Untested in practice.** Every fix above was verified by careful
  manual reasoning and cross-referencing against `stat`/`git`
  documentation, not by actually exercising a crash, a concurrent
  writer, or a non-GNU/non-BSD `stat` in a real environment. The first
  live use of this mechanism is its actual test.
- **Retry bound is a guess.** The 5-attempt push retry and the
  15-minute staleness threshold are reasonable defaults, not measured
  against real contention patterns — they may need tuning once this
  mechanism sees real concurrent traffic.
- **No automated test coverage.** This mechanism is pure `SKILL.md`
  prose and bash, like every other LRH skill step, so it has no unit
  tests exercising the worktree/branch logic directly (consistent with
  how the rest of `lrh-confirm-fixes` is verified — via review and
  manual reasoning, not `scripts/test`).
- **Further portability gaps may exist.** The `stat` fix addresses the
  one confirmed GNU/BSD divergence found; other shell/OS differences in
  this bash-heavy mechanism are plausible and not exhaustively audited.

If any of these residual gaps cause a real incident once this mechanism
is in use, treat that as evidence to promote — file a follow-up work
item rather than relying on further speculative review rounds to find
it first.

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

Step 8.3 in `SKILL.md` needs to tell "no evidence the reviewer was invoked
this round" apart from "the reviewer's own session started and stalled"
before asking the human — those need different answers (wait
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

**The check-run alone is sufficient evidence of a stall — it is not one
half of a required pair.** An earlier version of this section required
both the check-run *and* a correlated timeline event before calling
anything "stalled," on the theory that the timeline event corroborates
the check-run. That is backwards for a decision that must fail safe: the
timeline correlation below is the fragile signal (shared event vocabulary
across two products, multi-page, dependent on capturing the right
timestamp), so *requiring* it as an AND condition means a genuinely
stalled review check with no correlatable timeline event — a real,
expected case, not a corner case — gets reported as "no stall detected."
Use the check-run as the primary, sufficient signal; treat the timeline
event as optional corroboration that raises confidence when it correlates
cleanly, never as a gate the check-run's own verdict depends on.

**Read `retriggered_at` from this batch's own round-state file — never
mint a fresh timestamp here, never re-issue the retrigger, and never
rely on a shell variable surviving from `SKILL.md` Step 8.1.** Both
signals below need to know "since *this batch's* retrigger," not just
"recently," to stay safe against a stale prior-round check-run still
sitting on the same commit.

Two ways to get that boundary wrong, both real bugs caught in review,
not hypothetical: (1) capture a new timestamp and re-run `gh pr edit
--add-reviewer @copilot` right here, at the moment this diagnostic is
actually consulted (Step 8.3, after the "reasonable wait" already
elapsed) — wrong in precisely the primary case this whole heuristic
exists for, since `SKILL.md` Step 8.1 already documents that call "may
... no-op (already requested)" when Copilot is already a pending
reviewer, which it always is by the time Step 8.3 runs; re-issuing it
would either no-op silently or, if it somehow did start a second
check-run, would still leave `$since` set to a timestamp *after* the
real, already-stalled check-run from Step 8.1. (2) Capture the
timestamp correctly into a plain bash variable in Step 8.1, then expect
it to still be set when Step 8.3 reads it — also wrong, and not an edge
case: Step 8.1 and Step 8.3 are never the same tool invocation (Step
8.2's wait is inherently one or more separate calls, and can span a
session interruption), and shell variable state does not survive across
separate invocations in this harness (confirmed empirically — see the
`retriggered_at` field's own entry in "State schema" above). With
`$since` silently empty, the filter below becomes a no-op (`>=` against
an empty string is true for every timestamp), reintroducing exactly the
stale-check-run misattribution this whole mechanism exists to prevent,
with no error to signal it happened.

The fix for both: `retriggered_at` is written into `pending_attempt` at
batch start (`SKILL.md` Step 8.1, via the "Check-then-attempt ordering"
write above) and read back here, from the same durable, git-committed
round-state file every other piece of this mechanism already depends
on — not captured or re-derived in this section at all. This section is
a **read-only diagnostic** over the batch Step 8.1 already started and
persisted, not a second retrigger action:

```bash
KEY=<owner>-<repo>-pr<N>   # this PR's round-state filename, per "State schema" above
git fetch origin lrh-round-state --quiet
SINCE=$(git show origin/lrh-round-state:project/executions/round_state/$KEY.json \
  | jq -r '.pending_attempt.retriggered_at')
if [ -z "$SINCE" ] || [ "$SINCE" = "null" ]; then
  echo "pending_attempt.retriggered_at is missing or null for this PR's round-state file — a data-integrity anomaly (this diagnostic should only run while Step 8.1's own batch is genuinely still pending). Surfacing to the human rather than guessing." >&2
  exit 1
fi
```

**Check `$SINCE` before using it in either filter below, not after.** `jq
-r` on a `null` value (whether `pending_attempt` itself is `null`, or
`retriggered_at` is simply absent from an older or non-compliant
`pending_attempt`) prints the four-character string `"null"`, not an
empty string — verified directly (`jq -r '.pending_attempt.retriggered_at'`
on `{"pending_attempt":null}` → `null`). Every real ISO-8601 timestamp
starts with a digit, and `'2' < 'n'` lexicographically, so
`.started_at >= "null"` is **false for every real check-run** — the
opposite-direction mirror of the empty-string bug fixed above (empty
string made the comparison true for everything; the literal string
`"null"` makes it false for everything), reaching the same fail-unsafe
outcome from the other side: nothing matches, and a genuinely stalled
reviewer gets reported as "no evidence invoked." The guard above turns
that into an explicit, surfaced anomaly instead of a silently wrong
answer.

1. **Check-runs on the reviewer's own commit — primary signal, filtered
   to this batch's retrigger:**

   ```bash
   CHECK_RUN=$(gh api repos/<owner>/<repo>/commits/<sha>/check-runs --paginate --slurp \
     | jq --arg since "$SINCE" \
       '[.[].check_runs[]] | map(select(.name=="copilot-pull-request-reviewer" and .started_at >= $since)) | sort_by(.started_at) | last | select(. != null) | {name, status, conclusion, started_at, completed_at}')
   echo "$CHECK_RUN"
   ```

   `and .started_at >= $since` is what makes this safe on a same-`HEAD`
   retry: a check-run that started *before* this round's retrigger is
   evidence of a *previous* round, not this one, and must not be
   selected even if it's still the most recent check-run on the commit.
   No match under this filter means "no evidence the reviewer was
   invoked this round" — not "stalled" — even if an older, already-known
   stalled run is still sitting there `in_progress`; that older run
   already got its own answer in an earlier round. `--paginate --slurp`
   (no `--jq` on the `gh api` call itself), the same pattern this
   codebase already uses for paginated GitHub reads
   (`src/lrh/integrations/github/pull_reviews.py:164-173`) — `gh api
   --paginate` runs a combined `--jq` **once per page**, each page a
   separate JSON object (`gh help api`: "Each page is a separate JSON
   array or object"), not once against a merged cross-page result; a
   single-pass `--jq` filter looked correct against this repo's own
   (single-page, 5-6 check-run) commits but silently breaks on any
   commit whose check-runs span more than one page — each page would
   independently compute its own "last," and the true most-recent match
   could be discarded if it isn't on the last page processed. `--slurp`
   instead collects every page into one outer array
   (`[{...page 1...}, {...page 2...}, ...]`); the downstream `jq`
   flattens `.[].check_runs[]` across all of them before sorting, so
   "most recent" is computed over the genuinely complete set.
   `select(. != null)` after `last` keeps the zero-match case truly
   empty output, not a misleading `{"status":null,...}` object.
   `--paginate` matters on its own too: this endpoint's default page
   size can be smaller than a commit's total check-run count on a
   CI-heavy PR, and an unpaginated call can silently miss the reviewer's
   own check-run. A hosted reviewer session that's actually running
   shows up here — this only tells you whether a session started this
   round, not whether the reviewer is configured for this repo at all
   (that remains unknowable from this signal alone; see the caveat at
   the end of this section). `status: "in_progress"`, `conclusion: null`,
   `completed_at: null` held past a reasonable wait means the session
   started and never reached a terminal state — compute the age from
   the matched object's own `started_at` (reuse `STALE_AGE_SECONDS`,
   900 — 15 minutes, "Round-state branch mechanics" below — as the
   threshold value, since that is this skill's own existing "reasonable
   wait" constant, though it is scoped to that section's own worktree
   staleness check, not a shared in-scope variable here). Guard on
   `$CHECK_RUN` before computing an age at all — empty means no match
   (never invoked this round), and any status other than `in_progress`
   means it already reached a terminal state, neither of which has a
   meaningful "age since started" to measure:

   ```bash
   if [ -z "$CHECK_RUN" ]; then
     echo "no evidence the reviewer was invoked this round"
   elif [ "$(echo "$CHECK_RUN" | jq -r .status)" != "in_progress" ]; then
     echo "check-run reached a terminal status — not stalled"
   else
     STARTED_AT=$(echo "$CHECK_RUN" | jq -r .started_at)
     AGE=$(( $(date -u +%s) - $(date -u -d "$STARTED_AT" +%s 2>/dev/null || date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$STARTED_AT" +%s) ))
     [ "$AGE" -ge 900 ] && echo "stalled: ${AGE}s since started_at" || echo "in_progress, not yet past threshold: ${AGE}s"
   fi
   ```

   (GNU `date -d` vs. BSD/macOS `date -j -f` — the same portability split
   `STALE_AGE_SECONDS`'s own worktree-staleness check documents, but
   unlike that check's `stat -f`/`-c` ambiguity — where GNU's `-f` means
   something *else* and exits 0 with the wrong output instead of failing
   — GNU `date -d` fails hard and cleanly on BSD/macOS date, so the `||`
   fallback here is safe as written; no explicit flavor detection
   needed.) This alone is enough to report "stalled."
   (Substitute the check-run `name` this repository's reviewer actually
   reports if not GitHub Copilot code review's default; per GitHub's
   webhook documentation, `check_run` events fire only on
   `created`/`rerequested`/`completed`/`requested_action` — there is no
   periodic "still in progress" event, so this must be polled, not
   subscribed to.)

2. **Issue timeline, for optional corroboration — reuses `$SINCE` from
   the same round-state read above, and filters by the emitting app's
   `slug`, not event type:**

   ```bash
   gh api repos/<owner>/<repo>/issues/<pr-number>/timeline --paginate --slurp \
     | jq --arg since "$SINCE" \
       '[.[][] | select(.event | startswith("copilot_work"))
              | select(.performed_via_github_app.slug == "copilot-pull-request-reviewer")
              | select(.created_at >= $since)] | sort_by(.created_at) | first'
   ```

   `--paginate --slurp` here too: an active PR's timeline can exceed one
   page, and an unpaginated call can miss the corroborating event on a
   PR with a long history; each page is itself a bare JSON array for
   this endpoint (not object-wrapped like check-runs), so `.[][]`
   flattens the slurped array-of-pages directly.

   `copilot_work_started`/`copilot_work_finished`/
   `copilot_work_finished_failure` are emitted for **both** Copilot
   products — verified from two distinct sources within the same
   incident (`xenotaur/LCATS#202`, 2026-07-31), not inferred: the
   **coding agent**, invoked earlier in that PR's timeline by bare
   `@copilot` comment mentions (`SKILL.md` Step 8, "Do not retrigger
   Copilot with a plain `@copilot` PR comment" — the root-caused trigger
   for unwanted commits, a prior incident in this project), fired
   `copilot_work_started` at each such mention; and the **code-review**
   bot this step actually retriggers (`gh pr edit --add-reviewer
   @copilot`) fired its own `copilot_work_started` ~34 seconds after a
   `review_requested` timeline event from the same retrigger action.
   Event *type* alone cannot tell the two products apart, but every such
   event carries `.performed_via_github_app.slug` — verified directly
   against both PRs above: `copilot-pull-request-reviewer` on every
   code-review event, `copilot-swe-agent` on every coding-agent event, no
   exceptions in either PR's real timeline. Filtering on that field
   instead of (not just alongside) timestamp proximity is what actually
   makes this corroboration signal trustworthy — an earlier revision of
   this section relied on `$since` alone to rule out an unrelated
   coding-agent invocation elsewhere on the same PR, which is weaker:
   nothing stops a coding-agent event from landing inside the same
   narrow time window this batch's retrigger falls in. Because this
   signal is corroboration only (per the opening of this section, not a
   gate on the check-run's own verdict), a missed or misattributed
   timeline event downgrades confidence, never flips a real stall to
   "not stalled."

**Never invoked** (as distinct from stalled) is the check-run's own
zero-match case: no check-run for that reviewer at all since `$SINCE`.
This reading depends entirely on `$SINCE` being read from this batch's
own persisted `retriggered_at`, not a freshly re-minted or stale value —
see the caveat at the top of this section. Given that, a zero match means
what it says: nothing observable happened in response to this batch's
retrigger, not "the reviewer is stalled but the evidence got filtered
out."

Neither the check-run nor the timeline event identifies *why*
a stall happened — credit exhaustion is the observed cause in the
verified incident above, but a platform outage or an unrelated internal
error would look identical from the API side. Surface it to the human as
"stalled, cause unknown, credit exhaustion is one known cause," never as
a confirmed diagnosis: this is a heuristic, not a diagnostic.
Symmetrically, do not treat the *absence* of a stall signal as proof the
reviewer is simply unconfigured — Step 8's existing rule against
inferring configuration state from silence (`SKILL.md`, Step 8, "Do not
infer 'no automated reviewer is configured' from silence either") still
applies unchanged.

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
    "reviewers": {"codex": "submitted", "copilot": "pending"},
    "retriggered_at": "2026-08-01T05:33:53Z"
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
- `retriggered_at` — the UTC timestamp of this batch's own retrigger
  call (`SKILL.md` Step 8.1's `gh pr comment`/`gh pr edit
  --add-reviewer` pair), written into this same state-file update at
  batch start, never as a separate write. Exists because "Detecting a
  stalled reviewer session" (below) needs this exact value, and a plain
  shell variable cannot carry it there: Step 8.1 and Step 8.3 are never
  the same tool invocation (Step 8.2's wait is inherently one or more
  separate calls, and can span a session interruption), and shell state
  — variables, not just working directory — does not survive across
  separate invocations in this harness (confirmed empirically: a
  variable set and `export`ed in one call reads back empty in the next).
  A design that captured this timestamp into a bash variable and relied
  on it surviving to Step 8.3 looked correct but was silently broken in
  the normal case, not an edge case — an earlier revision of this
  section had exactly that bug, caught by an independent review that
  tested cross-call variable survival directly rather than assuming it.
  Persisting the value here, in the same durable, git-committed store
  this mechanism already uses for everything else, fixes it for real
  instead of hardening the broken mechanism further.

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
reviewers `"pending"`, `promoted: false`, `retriggered_at` set to this
batch's own retrigger timestamp — see the field's own entry above for
why this must be written here, not captured only in a shell variable)
and start the batch, promoting
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
- **Substitute self-review for this round** — dispatch `/lrh-self-review`
  in PR-mode (`--pr <this-pr-url>`) instead of a bot retrigger. This
  never bypasses the ceiling check above it — it is a fourth *answer* at
  the gate, reached only after the gate has already fired, not a way
  around firing it. On completion, increment `completed_count` by 1
  within the *existing* ceiling — exactly like a bot-triggered batch's
  promotion (see "Any-side-effect-counts promotion" above) — it does not
  require or imply raising the ceiling. Unlike a bot-triggered batch,
  this path is synchronous within one skill invocation (dispatch, get the
  result, done), so it needs none of `pending_attempt`'s async
  bookkeeping — no `"pending"` reviewer status, no crash-recovery
  reconciliation, no "no response yet" ambiguity. If the pass finds a
  genuine issue, route it through `/lrh-confirm-fixes` Step 3's taxonomy
  the same as any bot-sourced finding; a clean pass satisfies
  REVIEW-LANDED for this round the same as an explicit bot clean pass
  would. This matches the actual historical pattern this answer
  formalizes: in this project's own PR #452 and PR #457, the human's live
  response to this exact fired gate was to switch to self-review rather
  than authorize a higher ceiling.

This is the one point in Step 8 that always requires an explicit human
answer — never an inferred signal, and never satisfied by a bot response.

## CHAIN-NOTE relationship

The round-cap counter (`completed_count`) is a distinct, finer-grained
metric from CHAIN-NOTE's `cycles` field — see
`src/lrh/skills/lrh-land/references/land-workflow.md`'s `stops`/`note`
field docs for how a round-cap gate crossing should be recorded there.
`cycles` and `completed_count` measure different things and are not
interchangeable.

`completed_count` is also source-agnostic — it counts bot-triggered and
self-review-substituted rounds identically (see "The three-way gate"'s
fourth answer above), so it cannot be read directly as a bot-round count
either. CHAIN-NOTE's `bot_rounds=<N>` field (alongside
`self_review_rounds=<N>`, both defined in
`src/lrh/skills/lrh-land/references/land-workflow.md`'s own "CHAIN-NOTE
Format" section) must be computed as `completed_count -
self_review_rounds` at closeout, not read straight from `completed_count`
— otherwise every self-review-substituted round gets double-counted as a
bot round too.

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

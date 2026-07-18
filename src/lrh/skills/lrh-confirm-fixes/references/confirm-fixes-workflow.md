# lrh-confirm-fixes Workflow Context

Where `/lrh-confirm-fixes` sits in the LRH lifecycle, the verification
taxonomy, the `lrh github threads` thread-listing command and its
comment-correlation contract, the `gh api graphql` `resolveReviewThread`
primitive, the CI check mechanism, the `_CONFIRM` execution-record
convention, and idempotency / re-run edge cases. Read this before Step 2,
Step 5, Step 7, and Step 8 of `SKILL.md`.

---

## Lifecycle placement

```
/lrh-implement WI-<ID>              ← opens the PR
    │
    ▼
PR review (Codex, Copilot, human)   ← reviewers post comments
    │
    ▼
/lrh-review-response <pr-url>       ← fetches comments, fixes, pushes
    │
    ▼
(repeat if further review rounds)
    │
    ▼
/lrh-confirm-fixes <pr-url>         ← THIS SKILL
    │  Fresh-eyes verification against the current HEAD diff
    │  Resolves threads the diff plainly satisfies (single batch gate)
    │  Surfaces exceptions: unaddressed / partial / ambiguous / problematic
    │  Ends at a merge-readiness verdict + gh pr merge one-liner
    │  Creates AD_HOC _CONFIRM execution record with rerun_of link
    │
    ▼
Merge PR (human) + closeout          ← update records to landed, resolve WI
```

`/lrh-confirm-fixes` is the pre-merge complement `/lrh-review-response` cannot
be (it writes the fixes, so a same-run check is self-attestation) and
`/lrh-closeout` cannot be (it requires `state: MERGED`, so it runs too late).
See `PROP-LRH-CONFIRM-FIXES` for the full design — 14 decisions covering
independence, the verification taxonomy, the confirm-gate shape, and why
merge stays out of scope.

---

## Verification taxonomy

Applied to every unresolved thread at Step 3. The guardrail: **never mark a
thread Clear-satisfied unless the current diff plainly resolves it.**

| Bucket | Definition | Action |
|---|---|---|
| Clear-satisfied | The diff plainly resolves the comment — the exact concern raised is fixed at the location described | Resolve (batch) |
| Unaddressed | The diff does not act on the comment at all | Surface; offer `/lrh-review-response` |
| Partial | Some instances of the pattern are fixed, others are not (e.g. "you fixed line 17, please also fix line 19" and only line 17 changed) | Surface; do not resolve |
| Ambiguous | The diff does not give enough information to decide either way | Surface; do not resolve |
| Problematic resolution | A fix is present but appears wrong, incomplete, or introduces a new issue | Surface as a genuine finding — this is not the same as Clear-satisfied even though *something* changed |
| Problematic comment | The reviewer's comment is itself wrong, or conflicts with a documented design decision (a Non-Goal, a decision in the governing proposal, a trade-off discussed in the implementing session) | Surface with skip-rationale — reuses `/lrh-review-response`'s validity-check reasoning |

Ambiguous is the honest default when uncertain. Resolving a thread is an
outward, GitHub-visible action; a wrong resolution is more costly to notice
and correct than an over-cautious surface.

---

## Thread listing: `lrh github threads`

### List unresolved threads

```bash
lrh github threads <pr-url> --mode raw --state all
```

Filter the returned `threads[]` client-side to `isResolved == false` —
**deliberately ignore `isOutdated`.** A thread whose commented-on diff line
later moved or was removed is marked `isOutdated: true` by GitHub, but it is
still an open, unresolved concern until a human or `resolveReviewThread`
actually resolves it. Do not use `--state unresolved`: that built-in filter
(`_matches_state` in `src/lrh/integrations/github/formatters.py`) requires
*both* `not isResolved` and `not isOutdated`, which silently drops
outdated-but-unresolved threads — exactly the threads a "did the fix really
address this" verification pass most needs to see. This is the authoritative
list per Decision 12: every thread GitHub still considers unresolved,
regardless of diff drift.

`lrh request review_response` uses that narrower `state="unresolved"` filter
internally (`src/lrh/assist/request_service.py`,
`formatters.has_threads_for_state(threads_data, state="unresolved")`), so its
`Nothing to resolve:` report and this broader `isResolved`-only list **can
legitimately disagree** when outdated-but-unresolved threads exist — that is
`/lrh-confirm-fixes` doing its job, not a bug. Both commands still read the
same underlying `get_pull_review_threads()` data (see Step 2 in `SKILL.md`);
only the state filter applied on top differs, and by design.

`get_pull_review_threads()` fully paginates both the thread list (100 per
page, following `pageInfo.hasNextPage`/`endCursor`) and each thread's
comments — there is no 50-thread cap and no missed-thread risk on large PRs,
unlike a hand-rolled single-page GraphQL query.

`--mode raw` returns (verified empirically — the underlying GraphQL query
requests only these fields, no `path`/`line`/`startLine`):

```json
{
  "pull_request": {"owner": "...", "repo": "...", "number": N},
  "threads": [
    {
      "id": "PRRT_...",
      "isResolved": false,
      "isOutdated": false,
      "comments": {
        "nodes": [
          {"id": "PRRC_...", "body": "...", "author": {"login": "..."}, "url": "https://github.com/.../pull/N#discussion_r..."}
        ]
      }
    }
  ]
}
```

`threads[].id` (a `PRRT_...` string) is the thread ID used by the resolve
mutation below. `threads[].comments.nodes[]` includes every comment in the
thread (also fully paginated), each with its own `url`. There is no
file-path or line-number field on a thread — locate the comment's context
via `gh pr diff <pr-url>` and the comment `body` text instead.

### Correlate a thread to its comment data

`lrh request review_response`'s formatter (`formatters.py`,
`format_threads_review`) surfaces the **latest** comment in each thread
(`nodes[-1]`), not the first — a thread with a reply has its earlier
comments dropped from that output. Correlate by matching `threads[].comments.nodes[-1].url`
from the `lrh github threads` output against the `url:` line in
`lrh request review_response`'s comment-data output — both are the same
comment, from the same underlying data, so this match is exact, not
heuristic.

### Resolve one thread

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input:{threadId:"<PRRT_...>"}) {
    thread { id isResolved }
  }
}'
```

Check `isResolved` on the thread (from the Step 2 listing) before calling
this — skip threads already resolved. The mutation is idempotent in effect
(resolving an already-resolved thread is a no-op from GitHub's side), but
skipping avoids an unnecessary API call and keeps the execution record's
"resolved by this run" count accurate.

### Tagging bot vs. human authors

GraphQL's `author { login }` does not reliably distinguish bots via
`__typename` alone — several automated reviewers observed in practice post as
regular-looking logins rather than GitHub App/Bot accounts (e.g.
`copilot-pull-request-reviewer`, `chatgpt-codex-connector`). Tag an author as
bot if either:

- the login ends in `[bot]`, or
- the login matches a known automated-reviewer name (maintain a small list
  seeded with `copilot-pull-request-reviewer`, `chatgpt-codex-connector`,
  `github-actions`; extend as new reviewers are observed).

Otherwise tag as human. This tag drives resolution pre-selection at the
confirm gate (Decision 6) — bot threads are always pre-selected; human
threads are pre-selected unless `--surface-human` was passed.

---

## CI check mechanism

`gh pr view --json statusCheckRollup` returns an *array* of per-check
`CheckRun`/`StatusContext` objects — there is no single top-level rollup
`state` field. Reading it as one aggregate value either fails to parse or
misclassifies CI. Use `gh pr checks` instead, which pre-normalizes each
check into a `bucket`:

```bash
gh pr checks <pr-url> --required --json name,state,bucket
```

`bucket` is one of `pass`, `fail`, `pending`, `skipping`, `cancel`. Aggregate:

- **green** iff every bucket is `pass`
- **failing** if any bucket is `fail` or `cancel`
- **pending** otherwise

`gh pr checks` also exits with code `8` specifically for "checks pending" —
usable as a fast short-circuit before parsing JSON. `--required` scopes the
aggregation to required checks only, avoiding false negatives from optional
or intentionally-skipped checks — always attempt it first, exactly as shown
above; the example above is the default invocation, not an option to skip.
The one documented exception, where `--required` is deliberately dropped
after the distinguishing check below rules out a timing race, is covered
next.

### `--required` error: two different causes, one message

`--required` filters to checks GitHub's branch-protection rules mark as
required. If the target repo has no branch-protection rule marking any
check as required, there is nothing for the flag to filter to and the
command **exits non-zero** with the message `no required checks reported on
the '<branch>' branch` — it does not return an empty list. Observed on this
repo (`logical_robotics_harness` has no required-status-check branch
protection) verifying PR #399: 5 checks (`coverage`, `installed-wheel-smoke`,
`lint`, `Check workflow files`, `tests`) were all `SUCCESS`, yet `--required`
still exited 1. Treating that exit code as "CI failing" would produce a
false not-ready verdict against genuinely green CI.

**But the exact same error also fires for a second, unrelated reason:** `gh
pr checks --required` only reports required checks that have already posted
a status — a required check that is configured but hasn't started yet (or
hasn't posted its first status update) is silently absent from the rollup,
not shown as `pending` (upstream-confirmed, `cli/cli` issue #8855; verified
in the installed `gh` v2.95.0 source, `pkg/cmd/pr/checks/checks.go`: the
error is raised whenever the required-filtered check list is empty,
regardless of *why* it's empty). This is most likely to bite immediately
after a push — exactly when Step 8 runs, right after Step 7 pushes the
`_CONFIRM` commit — because the fresh `HEAD`'s required checks may not have
started reporting yet.

**Do not fall back to the unfiltered aggregate on this error alone** — a
repo with real required-check protection could get a false green built only
from optional/non-required checks. First distinguish which case applies:

```bash
OWNER_REPO=$(echo "<pr-url>" | sed -E 's#https://github.com/([^/]+/[^/]+)/pull/.*#\1#')
BASE_BRANCH=$(gh pr view <pr-url> --json baseRefName --jq '.baseRefName')
gh api "repos/${OWNER_REPO}/rules/branches/${BASE_BRANCH}" --jq '[.[] | select(.type=="required_status_checks")] | length'
```

This is the "Get rules for a branch" REST endpoint, which lists every
active rule (from branch protection *and* repository rulesets) affecting
the branch. Unlike the legacy `repos/{owner}/{repo}/branches/{branch}/protection`
endpoint — which 404s for an unprotected branch and requires admin
permissions to read when protection *does* exist — `rules/branches/{branch}`
returns `200` with a plain array for both protected and unprotected
branches, using the same read access `gh pr checks` already has. Verified
live against this repo: `main` returns
`["copilot_code_review","deletion","non_fast_forward"]` — no
`required_status_checks` entry, confirming the PR #399 case was genuinely
"no protection," not a timing race.

Branch the fallback on that count:

- **Count is `0`** — no `required_status_checks` rule exists on the base
  branch. Confirmed no required-check protection; safe to fall back to the
  unfiltered form and aggregate over every reported check:

  ```bash
  gh pr checks <pr-url> --json name,state,bucket
  ```

  Apply the same green/failing/pending aggregation rules to its output.

- **Count is `> 0`** — a `required_status_checks` rule exists, but
  `--required` reported zero checks. Per the `gh` limitation above, this
  means the required checks likely haven't started reporting yet, not that
  none are required. **Do not fall back.** Treat CI as **pending**
  (re-check later — a Step 8 re-run after the required checks start
  reporting will either resolve cleanly or surface a real failure) — never
  report green in this state.

- **The `gh api rules/branches` call itself fails** (e.g. unexpected
  permission error) — the distinguishing check is inconclusive. Treat CI as
  **pending** and note in the report that required-check status could not
  be verified; do not assume either case.

This distinguishing check applies independently at both CI reads — Step 2's
provisional read and Step 8's post-push re-check — since either may hit a
`--required`-empty result, and each needs its own base-branch rules lookup
(the PR's base branch does not change between the two reads, so the lookup
result may be cached within a single skill run if convenient).

### Why CI is checked twice

Step 2 reads CI early, before any thread is resolved, purely as context shown
at the confirm gate (a human deciding whether to proceed benefits from
knowing CI state, even provisionally). But Step 7 pushes the `_CONFIRM`
execution record as a new commit — this moves `HEAD`. A verdict computed from
the Step 2 read would describe the pre-push commit, not the commit the human
is actually being told to merge. Step 8 re-fetches CI against the post-push
`HEAD` SHA before emitting the final verdict, so the report never claims
"ready to merge" against a commit whose checks haven't actually run yet.

---

## `_CONFIRM` execution-record convention

Confirm-fixes executions use `AD_HOC` as the work item bucket, mirroring
`/lrh-review-response`'s `AD_HOC` convention — one primary execution entry per
work item, with side records linked via `rerun_of`.

**Filename suffix:** `_CONFIRM.md`, parallel to `/lrh-review-response`'s
`_REVIEW.md`.

**Slug derivation:** strip `<username>/<type>/` from the branch name, append
`-confirm`:

```
xenotaur/feat/wi-skills-lrh-confirm-fixes → wi-skills-lrh-confirm-fixes-confirm
```

**`rerun_of` population:** search for the primary record, excluding *both*
review-response and confirm-fixes side records:

```bash
UPPER_SLUG=$(echo "<branch-slug>" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
find project/executions/ -name "*${UPPER_SLUG}*.md" | grep -vE "_(REVIEW|CONFIRM)\.md$"
```

If found, set `rerun_of: <execution_id-from-the-primary-record>`. If not
found (the PR was created outside `/lrh-implement`, as in a planning-only PR
with no primary record), leave `rerun_of:` empty and note it in the body.

**Cross-skill consequence:** `/lrh-review-response`'s own `rerun_of` search
must also exclude `_CONFIRM.md` files (in addition to its existing
`_REVIEW.md` exclusion) — otherwise a confirm-fixes side record could be
mismatched as the primary record for a later review-response run on the same
branch. This exclusion-glob update is applied to both
`src/lrh/skills/lrh-review-response/SKILL.md` and
`references/review-response-workflow.md` (and mirrored to `.claude/skills/`)
as part of this skill's implementation, not as a follow-up.

---

## Idempotency and re-run edge cases

The source of truth is **live GitHub thread state**, not the execution
record. Each run re-queries unresolved threads against the current `HEAD`;
threads resolved by a prior run drop out of the query automatically. This
makes re-runs naturally idempotent without special-casing.

### A prior `_CONFIRM` record exists on this branch

Unlike `/lrh-review-response`'s hard stop on a prior `_REVIEW` record (a
re-run there would double-push code), a prior `_CONFIRM` record is **not** a
blocker. Warn the user and proceed. Rationale: a confirm-fixes re-run is
cheap (mostly reads plus, at most, thread-resolution API calls) and safe —
GitHub thread state may have legitimately changed since the last run (a
reviewer replied, `/lrh-review-response` addressed more comments, CI
finished). A hard stop here would force an unnecessary explicit-rerun dance
for the normal "verify again after another review round" flow.

### All threads already resolved, CI green

A re-run in this state is a clean no-op: Step 2's thread list is empty, Step
6's thread-resolution verdict is green with nothing to do, and Step 8 reports
"already ready to merge" with the current `HEAD` SHA. No execution record
content changes meaningfully, but the record is still created for audit
continuity (each run's `_CONFIRM` record documents what was checked and when).

### Partial resolution across rounds

Run 1 resolves 3 of 5 threads, surfaces 2 as Unaddressed, and the user runs
`/lrh-review-response` to address them. Run 2 of `/lrh-confirm-fixes` sees
only the 2 previously-unaddressed threads (the 3 resolved ones no longer
appear in `lrh github threads`' output) — this is the designed flow, not an
error condition.

### No open comments at all

Treat `lrh github threads --mode raw --state all`, filtered to
`isResolved == false`, as authoritative — not `lrh request review_response`'s
`Nothing to resolve:` report, which uses a narrower filter that excludes
outdated threads (see the Thread listing section above). Skip straight to
the CI-only verdict path (Step 8) only when the `isResolved == false` list
itself is empty. A `Nothing to resolve:` report with a non-empty
`isResolved == false` list means outdated-but-unresolved threads exist —
proceed to verify them normally; do not skip.

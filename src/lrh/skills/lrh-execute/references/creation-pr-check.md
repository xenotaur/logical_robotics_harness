# /lrh-execute Step 1 — Prerequisite Lifecycle Check

This is the algorithmic reference for the check `/lrh-execute` Step 1 runs
before readiness: is the target `WI-ID` actually available to execute on
`origin/main` right now, or is it still waiting on an open prerequisite
lifecycle PR — either the PR that creates its file, or a PR that reopens
it (moves it back to `status: proposed`). Sources:
`WI-EXECUTE-EARLY-CREATION-PR-CHECK` (the file-absent case) and
`WI-EXECUTE-OPEN-PREREQ-PR-STOP` (the status-mismatch case and the
structured stop report).

---

## Why this check exists

`/lrh-execute`'s own readiness check (`lrh work-items readiness <WI-ID>`)
reads whatever WI file is in the *local working tree*, not `origin/main`. If
the session invoking `/lrh-execute` is still checked out on the branch that
created or reopened the WI (a very common sequence — `/lrh-work-item`
immediately followed by `/lrh-execute` in the same session), the file is
locally present and readiness reports a clean `prompt_ready: yes` even
though `origin/main` does not have it, or has it in a state (`resolved`)
that cannot be executed. This is a false-confidence result, not a
correctness check — it passed because of *where the session happens to be
checked out*, not because the WI is actually usable.

`/lrh-implement` Step 5 (added by `WI-LRH-WORK-ITEM-ORDERING-DEP`, merged as
harness PR #602) already makes the underlying bug impossible to actually
hit: it re-verifies the WI file exists on a freshly-pulled `main` right
before branching, and hard-stops if not. But by the time an `/lrh-execute`
run reaches that check, a prompt ID has been minted, an idempotence check
has run, and the Step 2 chain-authorization gate has already fired and the
human has already approved a full run plan. A run that cannot possibly
succeed still costs a full human confirmation cycle before failing. This
check moves that failure to the earliest possible point: before any of that
setup work runs at all — and, when the blocker is an open PR, it tells the
human which PR to land, as the one thing to do now.

The second failure this check closes is a *reporting* one. Before this
check named the blocking PR in a fixed shape, a session could present
`/lrh-execute <WI-ID>` as "the next step" while the PR that reopens the
WI was still open (an LCATS session did exactly this:
xenotaur/LCATS#463, https://github.com/xenotaur/LCATS/pull/463, reopened
`WI-LINGUISTICS-0014`, and `/lrh-execute WI-LINGUISTICS-0014` was
presented as actionable while landing #463 was the real next action). The
stop report below exists so the later command cannot be mistaken for the
current one.

---

## The core gate: availability on `origin/main`

`/lrh-execute` Step 1 runs `git fetch -q origin main` once, ahead of both
the `WI-ID` and `WS-ID` branches — not per candidate. **If the fetch fails,
stop and report that as a blocker; never continue on a stale ref.** A
successful fetch is a **point-in-time snapshot**, not a guarantee:
`origin/main` can move afterward, and because this gate reads mutable
lifecycle status (not just file existence), a snapshot can be wrong in
either direction — for example it can still show `proposed` for a WI that
`main` has since resolved. `/lrh-implement` Step 5 re-verifies against a
freshly pulled `main` right before branching.

For a given `WI-ID`, compute its state on `origin/main`:

```bash
path=$(git ls-tree -r --name-only origin/main -- project/work_items/ \
  | grep -x "project/work_items/[a-z]*/<WI-ID>.md" || true)
if [ -z "$path" ]; then
  echo "state=absent"
else
  status=$(git show "origin/main:./$path" \
    | awk 'NR>1 && /^---$/ {exit} /^status:/ {print $2; exit}' | tr -d "'\"")
  echo "state=present status=$status"
fi
```

If `git show` itself fails (or yields an empty `status`), the WI is still
treated as unavailable — fail safe — but say so in **Why** ("its status on
`origin/main` could not be read") rather than implying it is a known
non-`proposed` status.

The WI is **available** only when it is present on `origin/main` with
`status: proposed`. Anything else — absent, or present with any other
status (for example `resolved` after a reopen is pending) — makes the WI
**unavailable**, and this check hard-stops (`WI-ID`) or skips the candidate
(`WS-ID`).

**This availability check is a hard, unconditional gate.** If the WI is
unavailable, stop — regardless of whether the specific blocking PR can be
identified (below). Treating an inconclusive PR search as license to
proceed would silently reintroduce the bug this check exists to prevent:
the WI genuinely is not executable on `main`, and nothing about being
unable to name the PR that will eventually fix that changes the fact.

This is deliberately **not** modeled on `/lrh-land`'s primary-record
provenance-check algorithm (`references/land-workflow.md` § Primary vs.
side-record provenance check) — that algorithm disambiguates *which of
several execution records* is the primary one for an *already identified*
PR. This check's question — "what is this specific file's state at this
specific ref" — has no equivalent ambiguity; `git ls-tree` and `git show`
against `origin/main` are ground truth.

---

## Naming the blocking PR (verified, never guessed)

The availability gate alone is enough to stop correctly, but "land this
specific PR first" is a far more actionable stop than a bare failure. A PR
is named as the blocker **only after** all of the following hold:

1. It is **open** and **targets `main`**.
2. It touches the WI's file at an exact path match
   (`project/work_items/<bucket>/<WI-ID>.md` — a bucket move shows up as
   the new path in the PR's file list).
3. Its **head version of the WI sets `status: proposed`**. A PR that
   merely edits prose or metadata of a `resolved` WI without reopening it
   is not a prerequisite: after it lands, the WI is still unavailable, so
   naming it would make the reported next action false.

**Enumerate open PRs exhaustively — never rely on the `gh pr list`
default of 30 results.** In a repository with more than 30 open PRs, a
default-limit scan can miss the prerequisite PR entirely and let the run
proceed against an unavailable WI. Use an explicit high limit, or paginate:

```bash
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
gh pr list --state open --base main --limit 1000 \
  --json number,url,headRefOid
```

(`gh api --paginate "repos/$repo/pulls?state=open&base=main"` is an
equivalent exhaustive form.) **Truncation guard:** if the number of PRs
returned equals the limit, the enumeration may be truncated — do not name a
PR; use the no-PR stop form and say the enumeration was truncated.

For each open PR, list its files and test for the WI's exact path. The PR
file list is **repository-root-relative**, while `git ls-tree` output is
relative to the current directory, so when the LRH project sits below the
repository root (a nested project such as `lcats/`) prepend the project's
prefix (`git rev-parse --show-prefix` — empty at the repository root):

```bash
prefix=$(git rev-parse --show-prefix)
gh api --paginate "repos/$repo/pulls/<N>/files" --jq '.[].filename' \
  | grep -x "${prefix}project/work_items/[a-z]*/<WI-ID>.md"
```

The matched `filename` is already repository-root-relative, so it is used
as-is in the contents call below.

For each PR that matches, read the WI as it exists at that PR's head
commit and require `status: proposed`:

```bash
gh api "repos/$repo/contents/<matched-path>?ref=<headRefOid>" --jq .content \
  | base64 -d \
  | awk 'NR>1 && /^---$/ {exit} /^status:/ {print $2; exit}' | tr -d "'\""
```

Call a PR that passes all three conditions a **qualifying PR**.

- **Exactly one qualifying PR** — name it (the stop report's named form).
- **Zero qualifying PRs, or more than one** — the availability gate above
  still fires, but the stop report uses the no-PR form and names **no PR**.
  Do not guess which of several PRs is the right one, and do not fabricate
  a PR reference when none was found — a falsely-confident match would
  itself be the failure mode this check exists to avoid, on the
  *identification* side.
- **Any `gh` call in this lookup fails** (network, auth, rate limit) — the
  lookup is inconclusive. Use the no-PR form, state that the lookup failed,
  and never name a PR from a partial result.

---

## The stop report

Every stop from this check uses the same three-part structure, in this
order: **Immediate next action**, **Why**, **After that**. Render it as
plain text, not inside a fenced code block, with no heading labelled "next
step". The later `/lrh-execute <WI-ID>` command appears only inside the
**After that** line, as inline prose marked as not yet actionable — never in
a standalone code block, and never as the headline action. The only command
presented as actionable is the `/lrh-land` command, or (no-PR form) the
instruction to identify the prerequisite PR.

Named form (exactly one qualifying PR):

- Immediate next action: `/lrh-land <pr-url>`
- Why: `<WI-ID>` is `<absent from origin/main | status: <status> on origin/main>`,
  and `<pr-url>` (open, targets `main`) sets it to `status: proposed`, so
  execution cannot start until that PR is landed.
- After that: once `<pr-url>` is merged and closed out, re-run
  `/lrh-execute <WI-ID>` (not actionable yet).

No-PR form (zero or multiple qualifying PRs, or an inconclusive lookup):

- Immediate next action: identify and land the prerequisite PR for `<WI-ID>`
- Why: `<WI-ID>` is `<absent from origin/main | status: <status> on origin/main>`
  and `<no open PR verified to set it to status: proposed | N open PRs
  qualify (list them) | the open-PR lookup failed or was truncated>`, so
  execution cannot start. No PR is named because none could be verified as
  the single prerequisite.
- After that: once the WI is `proposed` on `origin/main`, re-run
  `/lrh-execute <WI-ID>` (not actionable yet).

### Worked example (the LCATS case)

Input: `/lrh-execute WI-LINGUISTICS-0014`; on `origin/main` the WI is
`status: resolved`; the only open PR touching it is
https://github.com/xenotaur/LCATS/pull/463, whose head version sets
`status: proposed`.

<!-- worked-example:named:start -->
Immediate next action: `/lrh-land https://github.com/xenotaur/LCATS/pull/463`

Why: `WI-LINGUISTICS-0014` is `status: resolved` on origin/main, and
https://github.com/xenotaur/LCATS/pull/463 (open, targets main) sets it to
`status: proposed`, so execution cannot start until that PR is landed.

After that: once https://github.com/xenotaur/LCATS/pull/463 is merged and
closed out, re-run /lrh-execute WI-LINGUISTICS-0014 (not actionable yet).
<!-- worked-example:named:end -->

Input: the same WI, but two open PRs both qualify.

<!-- worked-example:no-pr:start -->
Immediate next action: identify and land the prerequisite PR for
WI-LINGUISTICS-0014

Why: `WI-LINGUISTICS-0014` is `status: resolved` on origin/main and 2 open
PRs qualify, so no single PR is named. Execution cannot start.

After that: once the WI is proposed on origin/main, re-run /lrh-execute
WI-LINGUISTICS-0014 (not actionable yet).
<!-- worked-example:no-pr:end -->

---

## No prompt is minted, and the stop is journaled

This check runs in Step 1, before Step 1.5 mints a prompt ID. A stop here
therefore mints **no prompt ID** and creates no branch, file, or execution
record. Go to Step 5 and record a `stopped` entry using the Step 1 stop
variant (it does not require a resolved `wi`, since a `WS-ID` stop has
none), then report using the stop report above.

---

## `WS-ID` branch: ineligible, not a hard stop

For a `WI-ID` given directly, the human named that specific WI — there is
no alternative candidate to fall back to, so an unavailable WI is a hard
stop.

For a `WS-ID`, the target WI is *resolved* from the workstream's ordered
`work_items:` list (`PROP-LRH-LAND-EXECUTE`'s "Chosen scope" — the first
candidate satisfying `status: proposed`, `depends_on` resolved,
`prompt_ready: yes`, and no blocking execution record). A candidate that is
unavailable on `origin/main` is simply another way for a candidate to be
ineligible, on the same footing as failing `depends_on` or readiness today.
Aborting the entire run because the *first* listed candidate happens to be
blocked would incorrectly prevent selecting a *later*, fully-ready
candidate in the same list. Apply the same availability check per
candidate, in list order; skip an unavailable candidate (recording only why)
and continue to the next one. **Do not run the open-PR lookup per
candidate** — a workstream's list is mostly already-`resolved` WIs, and
enumerating open PRs for each would be slow and noisy. The lookup is lazy
and runs once, only after the whole list is evaluated with no ready WI.

If **no ready WI exists** after the whole list is evaluated, stop and
report, and do not propose creating one. Then run the verified open-PR
lookup **once** for the availability-skipped candidates together: enumerate
open PRs exhaustively one time and match each of their exact paths in the
same pass. **Only candidates skipped by the availability check (absent
from, or not `proposed` on, `origin/main`) are looked up** — never a
candidate that is already `proposed` there but failed `depends_on`,
readiness, or the execution-record check: an unrelated open PR that edits
such a WI while leaving it `proposed` would satisfy the qualifying-PR rules
and be falsely named as the prerequisite, although landing it cannot make
the WI ready. When at least one availability-skipped candidate has exactly
one qualifying PR, use the stop report with: Immediate next action `/lrh-land <pr-url>`
for the **first** such candidate in list order (the one `/lrh-execute`
would pick first once unblocked); Why lists **every** availability-skipped
candidate that has a qualifying PR, naming it, plus a single count line for the other
skipped candidates and their reasons (already `resolved`, failed
`depends_on` or readiness, and so on); After that, re-run
`/lrh-execute <WS-ID>` (not actionable yet). If no skipped candidate has a
qualifying PR, report that no ready WI exists with each candidate's reason,
as before.

A conclusive lookup with zero qualifying PRs for a `WI-ID` whose status is
already `resolved` or `abandoned` is a different situation from a pending
reopen: say so plainly in **Why** (it is already `<status>`, and no open PR
reopens it, so there is nothing to execute unless it is reopened first)
while keeping the fixed no-PR **Immediate next action** line.

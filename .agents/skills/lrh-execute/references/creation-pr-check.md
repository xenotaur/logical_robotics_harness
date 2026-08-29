# /lrh-execute Step 1 — Creation-PR Check

This is the algorithmic reference for the check `/lrh-execute` Step 1 runs
before readiness: does the target `WI-ID`'s own file exist on `origin/main`
yet, or is it still only reachable through an unmerged WI-creation PR.
Source: `WI-EXECUTE-EARLY-CREATION-PR-CHECK`.

---

## Why this check exists

`/lrh-execute`'s own readiness check (`lrh work-items readiness <WI-ID>`)
reads whatever WI file is in the *local working tree*, not `origin/main`. If
the session invoking `/lrh-execute` is still checked out on the branch that
created the WI (a very common sequence — `/lrh-work-item` immediately
followed by `/lrh-execute` in the same session), the file is locally present
and readiness reports a clean `prompt_ready: yes` even though the file does
not exist on `origin/main` at all. This is a false-confidence result, not a
correctness check — it passed because of *where the session happens to be
checked out*, not because the WI is actually usable.

`/lrh-implement` Step 5 (added by `WI-LRH-WORK-ITEM-ORDERING-DEP`, merged as
harness PR #602) already makes the underlying bug impossible to actually
hit: it re-verifies the WI file exists on a freshly-pulled `main` right
before branching, and hard-stops if not. But by the time an `/lrh-execute`
run reaches that check, Step 1's readiness check has already reported clean,
the prior-art check has run, a prompt ID has been minted, an idempotence
check has run, a branch name has been derived, and — most significantly —
the Step 2 chain-authorization gate has already fired and the human has
already approved a full run plan. A run that cannot possibly succeed still
costs a full human confirmation cycle before failing. This check moves that
failure to the earliest possible point: before any of that setup work runs
at all.

## The core gate: existence, not PR identification

The actual fact this check needs is simple and unambiguous: **does the
`WI-ID`'s file exist on `origin/main`, in any status bucket?**

```bash
git fetch origin main -q
git ls-tree -r --name-only origin/main -- project/work_items/ \
  | grep -qx "project/work_items/[a-z]*/<WI-ID>.md"
```

This is deliberately **not** modeled on `/lrh-land`'s primary-record
provenance-check algorithm (`references/land-workflow.md` § Primary vs.
side-record provenance check) — that algorithm exists to disambiguate
*which of several execution records* is the primary one for an *already
identified* PR, a genuinely hard problem this repo's own history shows
broke three times before landing correctly. This check's actual question —
"does this specific, already-known file exist at this specific ref" — has
no equivalent ambiguity. `git ls-tree` against `origin/main` is ground
truth; there is nothing to disambiguate.

**This existence check is a hard, unconditional gate.** If the file is
missing from `origin/main`, stop — regardless of whether the specific
introducing PR can be identified (below). Treating an inconclusive PR
search as license to proceed would silently reintroduce the exact bug this
check exists to prevent: the WI genuinely isn't on `main`, and nothing about
being unable to name the PR that will eventually add it changes that fact.

## Best-effort enrichment: naming the specific PR

The existence check alone is enough to gate correctly, but "the WI-creation
PR must land first" is a much more actionable stop message than a bare
existence failure. This is where `/lrh-land`'s provenance-check *principle*
— gather broadly, narrow to an exact match, never guess when the result is
ambiguous — is genuinely reused, adapted to a different concrete anchor.

`/lrh-land`'s `rerun_of` search (`references/land-workflow.md` § A separate,
narrower algorithm for the two slug-based `rerun_of` searches) works from a
slug mechanically derived from the *current branch name* — a live,
in-session value. `/lrh-execute` Step 1 has no such branch yet; the only
known value is the target `WI-ID` itself. `/lrh-work-item` Step 10 already
writes an exact, deterministic anchor for exactly this case: every
WI-creation execution record's `instruction_source:` field is set to the
literal `project/work_items/<bucket>/<WI-ID>.md` path. That anchor is used
instead of a fuzzy slug-derived glob:

```bash
candidates=$(grep -rl "^instruction_source: project/work_items/.*/<WI-ID>\.md$" \
  project/executions/AD_HOC/*.md 2>/dev/null)
```

For each candidate, read its `pr:` field and check whether that PR is still
`OPEN`:

```bash
gh pr view <pr-url> --json state --jq .state
```

- **Exactly one open match** — name it: "`WI-ID`'s own creation PR
  (`<pr-url>`) is still open. Land it first, then re-run `/lrh-execute`."
- **Zero matches, or more than one open match** — the existence gate above
  still fires (the WI genuinely isn't on `origin/main`), but the stop
  message stays generic: "`WI-ID` does not exist on `origin/main`. If it
  was recently created, land its creation PR first." Do not guess which of
  several open PRs is the right one, and do not fabricate a PR reference
  when none was found — per the WI's own Risk Notes, a falsely-confident
  match here would itself be the failure mode this check exists to avoid on
  the *identification* side, even though the *existence* gate itself never
  has that ambiguity.

This mirrors the land-workflow algorithm's actual lesson, not its literal
shell — a bare substring/slug glob was tried and broken twice there before
an exact-match anchor plus sibling evidence replaced it. Here, an exact
`instruction_source:` field match plays the same role the exact-slug
`target` match played there, and "zero or multiple candidates" plays the
same role `$ambiguous` did: a signal to stay generic, not to skip the gate.

## `WS-ID` branch: ineligible, not a hard stop

For a `WI-ID` given directly, the human named that specific WI — there is no
alternative candidate to fall back to, so a missing file is a hard stop.

For a `WS-ID`, the target WI is *resolved* from the workstream's ordered
`work_items:` list (`PROP-LRH-LAND-EXECUTE`'s "Chosen scope" — the first
candidate satisfying `status: proposed`, `depends_on` resolved,
`prompt_ready: yes`, and no blocking execution record). A candidate whose
creation PR is still open is simply another way for a candidate to be
ineligible, on the same footing as failing `depends_on` or readiness today.
Aborting the entire run because the *first* listed candidate happens to be
blocked would incorrectly prevent selecting a *later*, fully-ready candidate
in the same list — exactly the regression a first draft of this check
introduced, caught in review (Codex, P2) before merge. Apply the same
existence check per candidate, in list order; skip an ineligible candidate
and continue to the next one, same as any other disqualifying condition
already in that loop.

---
name: lrh-pr-triage
description: >
  Investigate an open GitHub pull request — bot-authored (Jules, BOLT,
  Sentinel, or similar) or otherwise — and produce a grounded go/no-go
  landing recommendation: blocked/not-blocked, relevant/obsolete,
  valuable/not-valuable/counterproductive, each backed by evidence cited
  to file paths, commits, or timestamps rather than the PR's own claims.
  Report-only — takes no destructive action (no close, merge, comment, or
  edit); the user acts on the recommendation manually or via another
  skill/command.
when_to_use: >
  Use when the user wants a landing recommendation for a specific open PR
  before deciding whether to merge, close as obsolete/superseded, or hold
  it pending a fix. This is a candidate input to WS-INVOCATION-AND-GATE-RESET
  Stage 5b ("Session and PR triage: related × go/no-go across open PRs and
  live sessions") — until that workstream lands, this skill covers the
  single-PR investigation case standalone.
argument-hint: "<pr-number-or-url>"
context: fork
---

# lrh-pr-triage Skill

Investigates a single open pull request — most often bot-authored (Jules,
BOLT, Sentinel, or similar automated agents) but not exclusively — and
produces a structured, evidence-grounded go/no-go landing recommendation.
Every claim in the report must cite an actual repo state: a file path, a
commit SHA, or a timestamp — not the PR description taken at face value.

This skill is report-only. It never closes, merges, comments on, or edits
the PR under investigation; the recommendation is handed back to the user
to act on directly or via another skill (e.g. `/lrh-land`).

**Relationship to WS-INVOCATION-AND-GATE-RESET Stage 5b:** the proposal
underlying that workstream names "Session and PR triage: related × go/no-go
across open PRs and live sessions" as a later-stage deliverable
(`project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md`,
Stage 5b), not yet owned by a created workstream. This skill is not that
deliverable — it covers only the single-PR investigation case, takes no
action, and is offered as prior art / a candidate input for Stage 5b rather
than a silent duplicate of its scope.

---

## Inputs

```
/lrh-pr-triage 419
/lrh-pr-triage https://github.com/xenotaur/logical_robotics_harness/pull/419
```

A PR number or a full PR URL. If neither is given, ask for one before
proceeding.

---

## Execution Steps

Work through these steps in order. Do not skip ahead — each step can end
the investigation early with its own report.

### Step 1 — Confirm the PR is still open

```bash
gh pr view <n> --json state,mergeable,headRefName,headRefOid,baseRefName,createdAt,updatedAt
```

If `state` is not `OPEN`, stop and report the actual state (`MERGED`,
`CLOSED`) — there is nothing to triage.

Note `mergeable`, `headRefName`, `headRefOid`, and `baseRefName` for later
steps. `baseRefName` is the PR's actual target branch — do not assume
`main`; a PR can target a release or feature branch instead.

### Step 2 — Check whether another session is actively working it

Three checks, in order:

1. **Worktree check** — is any worktree checked out on this PR's branch or
   at its `headRefOid`?

   ```bash
   git worktree list
   ```

2. **Execution-record check** — does any tracked record reference this PR?
   Use `git grep`, not a filesystem-recursive `grep` — the latter also
   matches untracked scratch files outside the control plane, which is not
   evidence of anyone actually owning this PR. Use `-w` (whole-word match)
   — an unanchored `pull/<n>` is a substring match, so investigating PR 54
   would false-positive on any record mentioning `pull/548`, `pull/541`,
   etc.; `-w` requires a non-digit (or line boundary) on both sides of the
   number, which correctly excludes those while still matching `pull/54`
   itself:

   ```bash
   git grep -lw "pull/<n>" -- project/executions/
   ```

3. **Recency and shape of activity** — pull commits, comments, and reviews:

   ```bash
   gh pr view <n> --json comments,reviews,commits
   ```

   Multiple review rounds already in progress, or commits/comments from the
   last few minutes, mean someone is actively iterating on this PR right
   now. A single old commit with one stale review comment does not.

If any check indicates active ownership, **stop and report that** — do not
proceed to Steps 3–5.

### Step 3 — Note mergeable state and CI status

From Step 1's `mergeable` field: `MERGEABLE` or `CONFLICTING`. If
`CONFLICTING`, investigate why — this is often itself a symptom of
obsolescence (Step 4) rather than a separate, independent problem.

`mergeable` alone is not evidence about CI — a PR can be `MERGEABLE` with
failing checks. Fetch the actual status checks:

```bash
gh pr checks <n>
```

or, for the raw data behind it:

```bash
gh pr view <n> --json statusCheckRollup
```

A failing or errored check is grounds for **Blocked** in Step 6's report —
do not report a PR as not-blocked without having read this evidence.

### Step 4 — Check relevance against current base branch

```bash
gh pr diff <n>
```

Also fetch each touched file's diff **status** (added, removed, renamed,
modified) — not just its content — so a file that legitimately doesn't
exist pre-PR (an addition) is never confused with one that used to exist
and was since removed:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/files --jq '.[] | {filename, status, previous_filename}'
```

For each file the diff **modifies or removes** (not files whose `status`
is `added`, or the pre-rename path of a `renamed` file — those are
expected to 404 against the base branch and are not evidence of anything),
fetch its **current** state via the GitHub API against Step 1's actual
`baseRefName` — never hardcode `main`, and not a local checkout, which can
be stale:

```bash
gh api repos/<owner>/<repo>/contents/<path>?ref=<baseRefName>
```

Confirm:

- The file(s)/function(s) the PR modifies still exist at the paths it
  targets (for pre-existing files only — see the addition/rename carve-out
  above).
- The specific problem it fixes hasn't already been fixed some other way.
- Any design doc, convention, or upstream dependency it relies on hasn't
  since changed.

A PR modifying or removing a path that 404s on the current base branch, or
"fixing" pre-existing code that no longer looks like what the diff
assumes, is **obsolete** — say so plainly, citing the specific path or
commit that changed underneath it. A 404 on an added or renamed-from path
is expected, not evidence of staleness.

### Step 5 — Judge value independent of staleness

Even a still-relevant PR can be not-valuable or counterproductive:

- Read the actual diff for correctness — does it do what it claims, safely?
- Check whether it duplicates work already done elsewhere, conflicts with
  an established convention (this repo's style/import/architecture rules),
  or introduces risk disproportionate to its benefit.
- For a claimed optimization or fix, sanity-check the claim is real (e.g.
  does it actually avoid the overhead it says it does) — don't take the PR
  description at face value.

### Step 6 — Report

Produce a structured summary and stop. Do not take any action.

- **Blocked / not-blocked** — by an active session (Step 2), a failing or
  errored CI check (Step 3), or something needing a fix first.
- **Relevant / obsolete** — with the specific evidence from Step 4 (a
  pre-existing path that doesn't exist on the current base branch, a fix
  already applied elsewhere, a changed convention).
- **Valuable / not-valuable / counterproductive** — with the reasoning
  from Step 5.
- **Go/no-go recommendation**: land it, close it as obsolete/superseded
  (draft the explanatory close-comment text), or hold pending a specific
  fix.

State explicitly that this skill takes no action itself — closing,
merging, or commenting is the user's call, made after reading this report.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] PR state confirmed OPEN before any further investigation (Step 1);
      `headRefOid` and `baseRefName` were fetched, not just `headRefName`
- [ ] Active-ownership check covered all three signals: worktree, tracked
      (`git grep`) execution records, and activity recency/shape (Step 2)
- [ ] If actively owned, the investigation stopped there — Steps 3–5 were
      not run
- [ ] CI status checks (not just `mergeable`) were read before reporting
      Blocked/not-blocked (Step 3)
- [ ] Relevance was checked against the PR's actual `baseRefName` via the
      GitHub API — never hardcoded `main` — and not a local checkout,
      which can be stale (Step 4)
- [ ] Added and renamed-from files were excluded from the 404-obsolescence
      check via each file's diff `status` (Step 4) — a 404 on an addition
      is expected, not evidence of staleness
- [ ] Every claim in the final report cites a file path, commit, or
      timestamp — not the PR's own description
- [ ] The report states plainly that no action was taken
- [ ] No `close`, `merge`, `comment`, or file-edit command was run at any
      point

---

## What This Skill Does Not Do

- Does not close, merge, comment on, or edit the PR under investigation —
  report-only, always.
- Does not create an execution record — nothing is written to the repo, so
  there is nothing to land.
- Does not implement bot-specific detection logic — the same procedure
  applies whether the PR is bot-authored or human-authored.
- Does not triage multiple PRs or live sessions at once, and does not
  replace WS-INVOCATION-AND-GATE-RESET Stage 5b's broader "related ×
  go/no-go across open PRs and live sessions" scope — it covers the
  single-PR case only.
- Does not retrigger a GitHub bot review or interact with review-cap state.

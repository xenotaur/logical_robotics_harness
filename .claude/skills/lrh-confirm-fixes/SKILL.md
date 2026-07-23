---
name: lrh-confirm-fixes
description: >
  Pre-merge verification and thread-resolution pass for an LRH pull request.
  Independently verifies pushed review fixes against the current HEAD diff
  (never against the execution record's claims), resolves the review threads
  the diff plainly satisfies, surfaces the exceptions (unaddressed, partial,
  ambiguous, or problematic threads), and ends at a merge-readiness verdict.
  Does not merge the PR. Provide the PR URL as the argument, optionally
  followed by --subagent (dispatch verification to a cold-context subagent)
  and/or --surface-human (leave human-reviewer threads surfaced-only, never
  pre-selected for resolution). Omit the PR URL to auto-detect from the
  current branch.
disable-model-invocation: true
argument-hint: "[pr-url] [--subagent] [--surface-human]"
---

# lrh-confirm-fixes Skill

This skill fills the `[nothing]` gap in the LRH execution lifecycle: the
pre-merge pass that independently verifies pushed review fixes actually
resolved reviewers' comments, resolves the review threads the current `HEAD`
diff plainly satisfies, and surfaces everything else — unaddressed, partial,
ambiguous, or problematic threads — as the report's headline. It ends at a
merge-readiness verdict and a `gh pr merge` one-liner. It does not merge the
PR and does not trigger closeout; see `PROP-LRH-CONFIRM-FIXES` for the full
design (14 decisions).

Independence is the load-bearing property: verification reads the live diff,
never the execution record's or `/lrh-review-response`'s claims about what was
fixed. Run this after the last `/lrh-review-response` round, before the human
merge click.

---

## Inputs

Provide the PR URL as the argument, or omit to auto-detect from the current
branch. Two optional flags may follow:

```
/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/319
/lrh-confirm-fixes
/lrh-confirm-fixes <pr-url> --subagent
/lrh-confirm-fixes <pr-url> --surface-human
```

- `--subagent` — dispatch the fresh-eyes verification pass (Step 3) to a cold
  subagent context (PR URL + diff + comment bodies only, no session memory).
  Offered automatically when this session authored the fixes being verified;
  otherwise off by default (see Decision 7).
- `--surface-human` — leave human-reviewer threads surfaced-only at the
  confirm gate (never pre-selected for resolution); bot threads are still
  pre-selected. Without this flag, both bot and human resolve-eligible
  threads are pre-selected, each tagged with author and bot/human (Decision 6).

---

## Reference Knowledge

Load this before running any step:

1. **`references/confirm-fixes-workflow.md`** — Lifecycle placement, the
   verification taxonomy, the `lrh github threads` thread-listing command and
   its comment-correlation contract, the `gh api graphql` `resolveReviewThread`
   / `isResolved` primitives, the CI check mechanism and its post-push
   re-check, the `_CONFIRM` execution-record convention with `rerun_of`
   population, and idempotency / re-run edge cases. Read before Step 2,
   Step 5, Step 7, and Step 8.

---

## Execution Steps

Work through these steps in order. Do not skip Step 4 (confirm gate).

### Step 1 — Detect PR and verify branch

**If `<pr-url>` was provided:**

```bash
gh pr view <pr-url> --json headRefName,state --jq '{branch: .headRefName, state: .state}'
```

Verify the current branch matches `headRefName`. If it does not, **stop and
report the mismatch**.

**If no argument was provided:**

```bash
gh pr view --json url,headRefName,state --jq '{url: .url, branch: .headRefName, state: .state}'
```

Use the detected URL for all subsequent steps.

In either case: if `state` is not `OPEN`, stop and report — a merged or
closed PR is not a valid target for pre-merge verification.

### Step 2 — Gather state

Three reads, in this order:

1. **Comments** — `lrh request review_response <pr-url>`. This reuses the
   comment fetch and its security-boundary preamble (Decision 10); use only
   the comment-data section (author, body, URL) — do not follow its fix
   protocol. If it reports `Nothing to resolve:`, note this but **do not
   skip on it alone** — it uses a narrower "unresolved" definition than
   Step 2.2 below (see `references/confirm-fixes-workflow.md`). Only skip to
   Step 8 if the Step 2.2 list itself is empty.
2. **Unresolved threads** — `lrh github threads <pr-url> --mode raw --state all`,
   filtered client-side to `isResolved == false` (deliberately *not*
   `--state unresolved`, which also excludes outdated threads — see
   `references/confirm-fixes-workflow.md` for why that would silently drop
   genuinely open threads). This reuses the same paginated, tested
   GitHub-integration function `lrh request review_response` is built on —
   no thread-count cap, full comment pagination per thread. This is the
   authoritative list per Decision 12 — live GitHub state, broader than
   `lrh request review_response`'s own notion of "unresolved." Correlate each
   thread to its comment data by matching the thread's *latest* comment URL
   (the same comment `lrh request review_response`'s formatter surfaces, per
   `references/confirm-fixes-workflow.md`) against the URL in the Step 2.1
   comment data.
3. **Provisional CI status** — `gh pr checks <pr-url> --required --json name,state,bucket`,
   aggregated per the CI check mechanism in
   `references/confirm-fixes-workflow.md`. `--required` scopes aggregation to
   required checks, avoiding false negatives from optional/skipped jobs. If
   this exits non-zero with a message matching "no required checks
   reported", **do not assume the repo has no required-check protection** —
   that exact error also fires when required checks are configured but
   haven't reported yet (a real `gh` limitation, not a repo-config fact; see
   `references/confirm-fixes-workflow.md`). Run the branch-rules check
   described there to distinguish the two cases before deciding whether to
   fall back to the unfiltered `gh pr checks <pr-url> --json name,state,bucket`
   or treat CI as pending. This read is context for the confirm gate only —
   Step 8 re-fetches CI against the post-push `HEAD` before the final
   verdict.

### Step 3 — Fresh-eyes verification

For each unresolved thread, read its comment against the current `HEAD` diff
(`gh pr diff <pr-url>`) — never against the execution record's or
`/lrh-review-response`'s report. Classify into the taxonomy (see
`references/confirm-fixes-workflow.md` for full definitions and examples):

| Bucket | Action |
|---|---|
| Clear-satisfied | Diff plainly resolves the comment → eligible for batch resolution |
| Unaddressed | Comment not acted on in the diff → surface; offer `/lrh-review-response` |
| Partial | Some instances fixed, others missed → surface; do not resolve |
| Ambiguous | Diff does not let this pass decide → surface; do not resolve |
| Problematic resolution | Fix present but wrong/incomplete/introduces a new issue → surface as a finding |
| Problematic comment | Reviewer's comment is wrong or conflicts with a documented design decision → surface with skip-rationale |

**Never classify a thread as Clear-satisfied unless the diff plainly
resolves it.** When uncertain, use Ambiguous — the guardrail is to be honest
about uncertainty, not to guess-resolve.

If `--subagent` was passed (or offered and accepted — see Inputs), dispatch
this classification to a cold subagent given only the PR URL, the diff, and
the comment bodies; no session memory. Otherwise classify inline.

**Offer `--subagent`:** before classifying, check whether a primary or
`_REVIEW` execution record was minted *in this session* for this branch
(same detection as `/lrh-review-response` uses for its own idempotence
check). If so and `--subagent` was not passed, offer it: "These fixes were
authored in this session — run an independent-context pass instead?
(`--subagent`)."

Mint the prompt ID after classification, before the confirm gate. Derive the
slug from the current branch name — strip the `<username>/<type>/` prefix and
append `-confirm` (parallel to `/lrh-review-response`'s `-review` suffix):

```
xenotaur/feat/wi-skills-lrh-confirm-fixes → wi-skills-lrh-confirm-fixes-confirm
```

Check for a prior `_CONFIRM` record on this branch:

```bash
UPPER_SLUG=$(echo "<slug>" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
find project/executions/AD_HOC/ -name "*${UPPER_SLUG}*.md"
```

Unlike `/lrh-review-response`'s hard stop on a prior record, a prior
`_CONFIRM` record here is **not** a blocker — re-verification is cheap and
safe, since live thread state may have legitimately changed between rounds
(Decision 12). If found, **warn** the user and proceed.

Then mint:

```bash
lrh prompt label --slug <slug>
```

### Step 4 — Confirm gate (human gate)

Before resolving any thread, show the user a single batch summary:

- PR URL, number of unresolved threads
- **Clear-satisfied batch** — each thread's author, one-line excerpt, and a
  bot/human tag. Pre-selected for resolution unless `--surface-human` was
  passed, in which case human-authored threads are listed separately as
  surfaced-only (never pre-selected).
- **Surfaced exceptions**, grouped by bucket (Unaddressed / Partial /
  Ambiguous / Problematic resolution / Problematic comment), each with a
  one-line rationale
- Provisional CI status (from Step 2)
- Minted prompt ID

**Wait for explicit confirmation.** This is one gate for the whole batch, not
per-thread — the exceptions are the report; approving the batch approves the
Clear-satisfied resolutions as a set. If the user deselects specific threads
or redirects a classification, adjust and re-show before proceeding.

### Step 5 — Execute confirmed resolutions

For each confirmed thread, resolve via `gh api graphql` `resolveReviewThread`
mutation (see `references/confirm-fixes-workflow.md` for exact syntax). Check
`isResolved` first and skip threads already resolved (idempotent by
construction — live state is the source of truth).

For threads in the Unaddressed bucket, **offer** — do not automatically
invoke — `/lrh-review-response` to address them. Each fix run keeps its own
confirm gate; this skill does not chain into it.

### Step 6 — Compute thread-resolution verdict

Compute the thread component of the verdict: **green** iff every verifiable
thread was resolved in Step 5 and no exceptions remain open; otherwise
**not green**, with the exception list as the reason. This component does
not depend on CI and is not affected by the Step 7 push.

### Step 7 — Create execution record and validate

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

Edit the generated file to populate:

```yaml
agent: claude_app
instruction_source: <pr-url>
session_transcript: pending
```

and the body: which threads were resolved (author, bucket), which were
surfaced (bucket, rationale), and the Step 6 thread-resolution verdict.

Find the primary execution record for `rerun_of`. Convert the branch slug
(without the `-confirm` suffix) to upper-underscore form, and exclude both
`_REVIEW.md` and `_CONFIRM.md` suffixed files (review-response and prior
confirm-fixes records are not primary records):

```bash
UPPER_SLUG=$(echo "<branch-slug>" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
find project/executions/ -name "*${UPPER_SLUG}*.md" | grep -vE "_(REVIEW|CONFIRM)\.md$"
```

If found, set `rerun_of: <original-execution-id>`. If not found, leave empty
and note it in the body.

```bash
lrh validate
```

Commit and push as an additional commit to the open PR. **This is the commit
the human will actually be asked to merge** — CI must be re-evaluated against
the resulting `HEAD`, not the pre-push commit (Step 8).

### Step 8 — Readiness report

Re-fetch CI against the post-push `HEAD` SHA:

```bash
git rev-parse HEAD
gh pr checks <pr-url> --required --json name,state,bucket
```

If this exits non-zero with a message matching "no required checks
reported", run the same branch-rules distinguishing check as Step 2 (see
`references/confirm-fixes-workflow.md`) before deciding whether to fall
back or treat CI as pending. **This risk is sharpest here**: Step 8 runs
immediately after Step 7 pushes the `_CONFIRM` commit, so required checks
on the fresh `HEAD` are more likely than usual to not have started
reporting yet — falling back to the unfiltered aggregate in that window
could report a false green built only from optional checks.

Aggregate per `references/confirm-fixes-workflow.md`. The **final verdict**
is the Step 6 thread-resolution verdict AND this re-checked CI state:

- **Green** — "All threads resolved, CI green on `<sha>` → ready to merge."
  Include the one-liner, locked to the exact commit just checked:
  `gh pr merge <pr-url> --squash --match-head-commit <sha>` (or the project's
  standard merge mode). `--match-head-commit` makes the merge fail rather
  than silently merge a newer, unchecked commit if one lands between this
  report and the human running it.
- **CI pending** — "Threads resolved, CI pending on `<sha>` — not yet ready."
- **CI failing** — "Threads resolved, CI failing on `<sha>` — not ready."
- **Threads outstanding** — "Not ready — `<N>` threads need attention:
  `<list by bucket>`."

If CI is still pending at the post-push SHA, report that explicitly rather
than a false green from the Step 2 provisional read.

Report to the user:

- The final verdict and the `HEAD` SHA it was checked against
- What was resolved (author, one-line description) and what was surfaced
  (bucket, rationale)
- The `gh pr merge` one-liner, only if the verdict is green
- Next step after merging, only if the verdict is green: run
  `/lrh-closeout <pr-url>` to land the execution record, resolve the work
  item, and update the control plane
- Reminder that `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after the session ends

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Branch verified to match the PR before any changes
- [ ] Unresolved threads listed via `lrh github threads --mode raw --state all`,
      filtered to `isResolved == false` client-side (authoritative, fully
      paginated, includes outdated-but-unresolved threads)
- [ ] Each thread correlated to its comment data via the *latest* comment's
      URL, not the first
- [ ] Every thread classified into the taxonomy before the confirm gate; none
      marked Clear-satisfied without the diff plainly supporting it
- [ ] Prompt ID minted before the confirm gate
- [ ] Prior `_CONFIRM` record on this branch surfaced as a warning, not a
      hard stop
- [ ] User confirmed the single batch at Step 4 before any thread was resolved
- [ ] `resolveReviewThread` skipped already-resolved threads
- [ ] Unaddressed threads offered `/lrh-review-response`, not auto-invoked
- [ ] Execution record created with `rerun_of` excluding both `_REVIEW.md`
      and `_CONFIRM.md`
- [ ] `lrh validate` reports 0 errors before the record was pushed
- [ ] CI re-checked against the post-push `HEAD` SHA before the final verdict
- [ ] The reported merge one-liner includes `--match-head-commit <sha>`
- [ ] No `gh pr merge` was executed by this skill — only reported as a
      one-liner

---

## What This Skill Does Not Do

- Does not merge the PR — the readiness verdict and `gh pr merge` one-liner
  are the skill's output; merge is a human action.
- Does not *invoke* `/lrh-closeout` — closeout runs post-merge, this skill
  runs pre-merge, and the merge in between is a human action. Closeout is
  still the user's next step: a green verdict reports `/lrh-closeout` for
  them to run after merging.
- Does not resolve any thread the current diff does not plainly satisfy —
  ambiguous, partial, and problematic threads are surfaced, never
  guess-resolved.
- Does not silently loop `/lrh-review-response` — unaddressed threads are
  detected and the fix skill is offered; each fix run keeps its own confirm
  gate.
- Does not verify against the execution record's or `/lrh-review-response`'s
  claims — only the live `HEAD` diff.
- Does not modify `lrh request review_response` or its template.
- Does not add a new `lrh request` catalog entry — thread listing reuses
  `lrh github threads`; resolution uses raw `gh api graphql`.
- Does not automatically update `session_transcript` from `pending` to the
  real session ID.

---
name: lrh-self-review
description: >
  Dispatch a fresh, cold-context subagent to independently review a diff or
  a PR — a credit-free substitute for a GitHub bot review. Two modes:
  diff-mode (default, no argument) reviews the local branch diff against
  main, for use once before a PR's first push; --pr <url> reviews an
  existing PR as `/lrh-confirm-fixes` Step 8's substitute review signal when
  another manual hosted review-bot retrigger would otherwise have been
  requested. Ends at a report of findings plus an execution record; diff-mode
  is report-only by default and applies fixes only with explicit --apply.
  It does not push, open a PR, resolve GitHub threads, or merge.
when_to_use: >
  Invoke only at the two declared review-substitution trigger points: once in
  diff-mode from /lrh-implement before a PR is opened, or in PR-mode from
  /lrh-confirm-fixes when a fresh substitute review signal is needed instead
  of a hosted GitHub review-bot retrigger. Do not use for ad-hoc review outside
  those caller-owned workflows.
argument-hint: "[--apply | --pr <pr-url>]"
disallowed-tools: Skill
---

# lrh-self-review Skill

This skill formalizes a pattern used ad hoc, successfully, in this
project's own PRs #447, #452, #457, #459, #460, #461, #462, #464: dispatch
a fresh `general-purpose` subagent with no session memory, cold context,
to review a diff or PR independently, in place of a GitHub Copilot/Codex
retrigger. See `PROP-LRH-SELF-REVIEW`
(`project/design/proposals/adopted/lrh-self-review/00_proposal.md`) for
the full design.

**Two invocation modes, one shared procedure** (Decision 5): the target
differs — a local diff plus task orientation (diff-mode), or a PR URL plus
HEAD SHA and comment history (PR-mode) — but dispatch, independent
re-verification, and the execution-record convention are identical.

**Two trigger points** (Decision 1), never more:
- **Diff-mode**, called once from `/lrh-implement` Step 7.5, before the
  PR's first push (`gh pr create`) — this exists because opening a PR in
  this repo auto-triggers bot review within about a minute with no
  explicit retrigger, so there is no "PR open, bot hasn't looked yet"
  window; independent pre-push review is only possible before the PR
  exists.
- **PR-mode**, called from `/lrh-confirm-fixes` Step 8 when no matching
  automatic reviewer response appears after a reasonable wait, or when a
  later review signal is needed for a non-thread finding. It substitutes for
  any manual hosted review-bot retrigger path.

Diff-mode is exempt from review-cap state by construction — no PR exists yet
to attach state to (Decision 2). PR-mode substitute passes count against
`/lrh-confirm-fixes` Step 8's provisional no-progress review cap.

**This skill never authorizes skipping a PR's first real bot round**
(Decision 4) — diff-mode findings get fixed or not, but the PR is pushed
either way, and `/lrh-implement` Step 8 runs regardless of what this skill
found.

---

## Inputs

```
/lrh-self-review
/lrh-self-review --apply
/lrh-self-review --pr https://github.com/xenotaur/logical_robotics_harness/pull/419
```

Omit `--pr` for diff-mode (default): reviews `git diff main` (working tree
against `main`'s tip — see Step 1 for why not the three-dot `main...HEAD`
form) on the current branch. Diff-mode reports findings by default; pass
`--apply` only when the caller explicitly wants this skill to apply verified
fixes to the working tree. Pass `--pr <url>` for PR-mode: reviews that PR's
current `HEAD` diff and comment history. `--apply` is invalid with `--pr`.

---

## Reference Knowledge

Load before running any step:

1. **`references/self-review-workflow.md`** — the shared dispatch
   procedure, the diff-mode vs. PR-mode prompt shapes, the independent
   re-verification requirement, and the `_SELFREVIEW` execution-record
   convention (including the diff-mode `rerun_of`-empty sequencing note).

---

## Execution Steps

Work through these steps in order.

### Step 1 — Determine mode and target

If both `--apply` and `--pr` were passed, stop and report — PR-mode is
report-only by design and routes findings back to `/lrh-confirm-fixes`.

**Diff-mode (no `--pr`):**

```bash
git rev-parse HEAD
git diff main
```

**Not `git diff main...HEAD`.** At `/lrh-implement` Step 7.5's own call
site, Step 6's implementation changes are still uncommitted working-tree
edits — Step 8 (Commit and PR) is what commits them, and it runs *after*
this step. `HEAD` is therefore still the branch's fork point from `main`,
so a three-dot `git diff main...HEAD` (committed changes only) would be
empty in the normal case, triggering a false "nothing to review" exit
without ever reviewing what Step 6 actually did. `git diff main` compares
`main`'s tip directly against the current working tree — staged and
unstaged changes both included — which is what Step 7.5 actually needs to
review.

If the diff is empty, stop and report — nothing to review.

**PR-mode (`--pr <url>`):**

```bash
gh pr view <pr-url> --json state,headRefOid --jq '{state: .state, head: .headRefOid}'
```

If `state` is not `OPEN`, stop and report.

### Step 2 — Gather orientation context

**Diff-mode:** identify the work item or task this diff implements (from
the current branch name, or ask if not derivable) and read its Required
Changes / Acceptance Criteria for orientation — the subagent needs to know
what the diff is *supposed* to do, not just what it does.

**PR-mode:** gather the PR's title, body, issue-comment history, and prior
*review* activity — `--json comments` alone misses inline review threads
and review-body text, which is exactly where prior rounds' findings live:

```bash
gh pr view <pr-url> --json title,body,comments
gh api graphql -f query='query { repository(owner: "<owner>", name: "<repo>") { pullRequest(number: <n>) { reviews(first: 50) { nodes { author { login } body } } reviewThreads(first: 50) { nodes { isResolved comments(first: 5) { nodes { body author { login } } } } } } } }'
```

### Step 3 — Dispatch the subagent

Dispatch a `general-purpose` `Agent` subagent, cold context (no session
memory), per `references/self-review-workflow.md`'s exact prompt shape for
the active mode. Give it only:

- The diff (diff-mode) or PR URL + HEAD SHA (PR-mode)
- The orientation context from Step 2
- Explicit instruction to verify every checkable claim against real repo
  files rather than trust prose — including this skill's own prompt
- Explicit instruction not to assume anything from outside what it finds
  itself (no access to this session's prior context)
- Explicit instruction not to invoke `/lrh-self-review`, run other LRH
  skills, or spawn another review agent

This skill's own frontmatter carries `disallowed-tools: Skill` — a
platform-enforced control verified (see `DEC-SELF-REVIEW-RECURSION-GUARD`) to
remove the `Skill` tool from both the invoking session and the dispatched
subagent while this skill is active. It is the primary recursion guard;
the instruction above not to invoke `/lrh-self-review` or spawn another
review agent is defense-in-depth, not a substitute for it.
Codex installations separately carry `agents/openai.yaml` with
`policy.allow_implicit_invocation: false` for this skill, so removing Claude's
`disable-model-invocation` frontmatter does not make Codex invoke it
implicitly either. Step 4's direct re-verification remains load-bearing
regardless, since the guard bounds recursion, not review quality.

### Step 4 — Independently re-verify the top finding

**Mandatory, not optional** (Decision 6). Before accepting the subagent's
report, the invoking session — not a second subagent — directly
re-verifies its most severe finding: read the actual file(s) it cites, run
the command(s) it claims to have run, confirm the claim holds. This
project's own practice caught a fabricated citation this way earlier in
the same session that produced this skill's design. If the top finding
doesn't hold up under direct re-check, say so explicitly rather than
reporting it as accepted.

### Step 5 — Apply fixes or report findings

**Diff-mode:** report findings by default. If the subagent (and your own
re-verification) found real issues, do not edit the working tree unless
`--apply` was passed. With `--apply`, fix the verified in-scope issues directly
in the working tree. Do not push — that remains `/lrh-implement` Step 8's job,
which runs next regardless of what this step found (Decision 4).

**PR-mode:** do not push fixes as part of this skill's own workflow —
report findings back to the caller (`/lrh-confirm-fixes` Step 8
integration), which routes any genuine finding through
`/lrh-confirm-fixes` Step 3's taxonomy the same as a bot-sourced one. A
clean result (no findings) is itself the report.

### Step 6 — Create execution record

`AD_HOC` bucket, `_SELFREVIEW` filename suffix. See
`references/self-review-workflow.md` for the exact `rerun_of` rule — it
differs by mode: PR-mode always has a primary record to link to; diff-mode
runs before `/lrh-implement` Step 9 creates one, so `rerun_of` starts
empty by construction, not as an oversight.

Capture in the record: mode, findings (count and one-line description each),
whether diff-mode was report-only or `--apply` was used, whether fixes were
applied, whether a finding was routed to `/lrh-confirm-fixes` (PR-mode), and
whether the PR-mode pass was a substitute review signal or a follow-up signal
for a non-thread finding.

```bash
lrh prompt label --slug <slug>-selfreview
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug>-selfreview \
  --status in_progress \
  --project-root .
```

### Step 7 — Report

Report to the caller/user:

- Mode (diff or PR) and target
- Findings: count, one-line description each, severity if applicable
- Whether the top finding was independently re-verified and what that
  check found
- Diff-mode: whether fixes were applied
- PR-mode: the finding(s) to route through `/lrh-confirm-fixes` Step 3, or
  confirmation this round was clean
- Execution record path and prompt ID

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Mode determined correctly (diff vs. PR) before dispatch
- [ ] Subagent dispatched cold — no session memory, only the diff/PR-URL
      and orientation context passed explicitly
- [ ] The subagent's top finding was independently re-verified by the
      invoking session directly, not merely accepted or re-delegated to
      another subagent
- [ ] Diff-mode: report-only by default; fixes applied only when `--apply`
      was explicitly passed, and never pushed by this skill
- [ ] Diff-mode: `/lrh-implement` Step 8 still runs afterward regardless
      of findings — no skip path exists
- [ ] PR-mode: no fix was pushed as part of this skill's own workflow
- [ ] Execution record created (`AD_HOC`, `_SELFREVIEW` suffix) with the
      correct `rerun_of` handling for the active mode
- [ ] `lrh validate` reports 0 errors if any file was edited (diff-mode)

---

## What This Skill Does Not Do

- Does not retrigger a GitHub bot review, or build a second, parallel
  review-cap mechanism — `/lrh-confirm-fixes` Step 8 owns the provisional
  no-progress review cap and calls PR-mode as a substitute review signal.
- Does not push, open a PR, or merge — diff-mode reports by default; with
  explicit `--apply`, it applies verified fixes to the working tree only.
  `/lrh-implement` Step 8 does the push.
- Does not resolve GitHub review threads — that remains
  `/lrh-confirm-fixes`'s job; PR-mode only reports findings back to it.
- Does not run on every push — exactly the two trigger points named
  above, never more (Decision 1).
- Does not authorize skipping a PR's first real bot-review round under any
  circumstance (Decision 4).
- Does not claim cross-vendor blind-spot-equivalent coverage to an
  independent platform reviewer — the subagent runs on the same
  underlying model family as the session driving it.
- Does not measure or report actual GitHub AI-credit cost in currency or
  credit-unit terms — only occurrence counts are tracked.

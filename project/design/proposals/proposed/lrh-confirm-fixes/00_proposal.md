---
id: PROP-LRH-CONFIRM-FIXES
type: design_proposal
title: LRH Pre-Merge Verification — /lrh-confirm-fixes Skill for Fresh-Eyes Thread Resolution
status: proposed
created_on: 2026-07-15
updated_on: 2026-07-15
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - src/lrh/skills/lrh-review-response/references/review-response-workflow.md
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
---

# LRH Pre-Merge Verification — `/lrh-confirm-fixes` Skill for Fresh-Eyes Thread Resolution

## Summary

This proposal introduces a `/lrh-confirm-fixes` Claude Code skill: a pre-merge
pass that independently verifies pushed review fixes against the current `HEAD`
diff, resolves the review threads the diff plainly satisfies, and surfaces the
exceptions — threads that are unaddressed, partial, ambiguous, or whose fix or
originating comment is itself problematic. The skill ends at a readiness verdict
("all threads resolved, CI green → safe to merge") accompanied by a `gh pr merge`
one-liner. It does not merge the PR and does not trigger closeout.

The skill fills a structural gap in the LRH execution lifecycle: today there is
no step between the last `/lrh-review-response` round and the human merge that
*independently* verifies the fixes resolved the reviewers' comments, or that
records the review threads as resolved.

## Background / Motivation

The LRH lifecycle for a reviewed PR is:

```
/lrh-implement → /lrh-review-response (repeat) → [nothing] → human merges → /lrh-closeout
```

The `[nothing]` is the gap this skill fills. It is visible in the
`/lrh-review-response` lifecycle diagram
(`src/lrh/skills/lrh-review-response/references/review-response-workflow.md:22-28`),
which jumps straight from "repeat if further review rounds" to
"Merge PR + closeout (human)" with no verification step in between.

Two forces make that gap worth closing:

1. **Reviewer burden.** Coding agents plus review agents (Codex, Copilot,
   human) generate a high volume of comments. Many are low-effort and plainly
   valid (e.g., "you fixed the SQL-injection cast on line 17, apply it on line
   19 too"). When 9 of 10 comments are valid and 9 of 10 responses are valid,
   ratifying each thread by hand is a lot of "yes, yes, yes" that buries the
   one thread that actually needs a human eye. The exceptions are the product;
   the routine resolutions are noise.

2. **Verification earns its keep.** On a recent downstream PR, external
   reviewers caught a real packaging bug that would otherwise have shipped
   silently. A verification pass *before* the irreversible merge is precisely
   where such a bug is cheap to catch. The human merge click is the last
   circuit breaker, and it is worth preserving.

Two prior proposals establish the context:

- `PROP-LRH-PROJECT-LOCAL-SKILLS` introduced the skill pattern
  (`src/lrh/skills/<name>/`, `lrh setup`) and the confirm-gate convention.
- `PROP-LRH-CLOSEOUT` established the post-execution complement to
  `/lrh-implement` and `/lrh-review-response`, and the assessment-first,
  human-gated skill structure this proposal mirrors.

`/lrh-confirm-fixes` is the missing *pre-merge* complement: it sits after the
last review round and before the human merge, where `/lrh-review-response`
cannot (it writes the fixes, so it cannot independently judge them) and
`/lrh-closeout` cannot (it requires `state: MERGED`, so it runs too late).

## Design Decisions

### Decision 1: A new skill, not an extension of an existing one

**Question:** Should pre-merge verification and thread resolution be folded
into `/lrh-review-response` or `/lrh-closeout`, or be a new skill?

**Options considered:**
- A: Fold into `/lrh-review-response`
- B: Fold into `/lrh-closeout`
- C: New skill

**Chosen: C — new skill.**

Folding into `/lrh-review-response` (Option A) destroys the value. That skill
*writes* the fixes; a verification pass in the same run is self-attestation —
the run that produced the fix cannot be the run that independently judges it.
`/lrh-review-response` already declares "Does not automatically resolve GitHub
review conversations — human decision"
(`src/lrh/skills/lrh-review-response/SKILL.md:255`); the value of a separate
pass is *fresh eyes* re-reading each comment against the actual current diff.

Folding into `/lrh-closeout` (Option B) is structurally too late. Closeout
requires `state: MERGED` and aborts on an open PR
(`src/lrh/skills/lrh-closeout/references/closeout-workflow.md:15-17`). Thread
resolution and merge-readiness are *pre-merge* signals; a post-merge skill
cannot produce them.

### Decision 2: Verify against the live diff, not the execution record

**Question:** What is the source of truth for judging whether a comment was
addressed?

**Chosen: the current `HEAD` diff, never the execution record's claims.**

The execution record and `/lrh-review-response` report describe what the fix
run *believed* it did. Reading those to verify the fixes reintroduces the
self-attestation that Decision 1 avoids. Independence lives in re-deriving the
answer from the diff (`gh pr diff <pr>` and the comment's `path`/`line`
location at current `HEAD`). This applies command-query separation (Meyer,
*Object-Oriented Software Construction*, 1988): the verification is a pure
read of repository state, decoupled from the write history that produced it.

### Decision 3: Exceptions are the product

**Question:** Should the skill surface every open thread for per-thread human
ratification, or resolve the routine ones and surface only the exceptions?

**Options considered:**
- A: Surface all threads; the human ratifies each resolution
- B: Resolve the clearly-satisfied threads; surface only the exceptions

**Chosen: B.** Option A recreates the "yes, yes, yes" burden from the
Motivation — the human's attention is spent on the 9 routine threads and the
1 real exception is buried. Option B inverts the default: the fresh-eyes pass
classifies every open thread into a taxonomy, resolves the clearly-satisfied
ones as a batch, and makes the exceptions the headline of the report.

**Verification taxonomy** (applied to each open thread):

| Bucket | Definition | Action |
|---|---|---|
| Clear-satisfied | Diff plainly resolves the comment | Resolve (batch) |
| Unaddressed | Comment not acted on in the diff | Surface; offer `/lrh-review-response` |
| Partial | Some instances fixed, others missed (e.g. line 17 but not line 19) | Surface; do not resolve |
| Ambiguous | Diff does not let the pass decide | Surface; do not resolve |
| Problematic resolution | Fix present but appears wrong / incomplete / introduces a new issue | Surface as a genuine finding |
| Problematic comment | The reviewer's comment is wrong or conflicts with a documented design decision | Surface with skip-rationale (reuses `/lrh-review-response` validity check) |

The guardrail from the confirm-gate convention holds: **never resolve a thread
the diff does not plainly satisfy.** Only the Clear-satisfied bucket is
resolved. Everything else is surfaced honestly.

### Decision 4: A single batch confirm gate per run

**Question:** How much human confirmation should thread resolution require —
per-thread, one batch per run, or none?

**Options considered:**
- A: Per-thread confirmation
- B: One batch confirmation per run
- C: No gate (fully automatic resolution)

**Chosen: B.** Option A is the burden this skill exists to eliminate
(Decision 3). Option C is rejected for two reasons: (1) the fresh-eyes pass
can misread a diff, and a zero-gate resolver would silently resolve a thread
whose comment was never actually addressed — reintroducing exactly the
"silently shipped" failure mode from the Motivation; (2) resolving review
threads modifies the PR's public review state, which is an outward action that
warrants per-run human authorization under the confirm-gate convention.

Option B collapses the burden from N confirmations to one — "resolving these 8;
here are 2 that need you" — while preserving a circuit breaker on a misread
diff and honoring the public-state boundary. Thread resolution is reversible
(`unresolveReviewThread` is the documented inverse of the `resolveReviewThread`
mutation), so a single batch gate is proportionate to the low, recoverable
consequence.

### Decision 5: Merge stays out of scope

**Question:** Given the skill produces a merge-readiness verdict, should it
also merge the PR when the verdict is green?

**Chosen: no. Merge is out of scope and stays a human action.**

Merge is qualitatively different from thread resolution on the axis that
governs every guardrail in the existing skills — reversibility and outward
consequence:

| Action | Reversible? | Consequence of a wrong call |
|---|---|---|
| Resolve a thread | Yes — one click / `unresolveReviewThread` | A reviewer re-opens the thread |
| Merge a PR | No — code has shipped; revert is a new PR, and any deploy or downstream pull already fired | The exact silently-shipped bug the Motivation describes |

Three reasons compound:

1. **The existing wall is deliberate.** `/lrh-review-response` and
   `/lrh-closeout` both refuse merge on purpose
   (`src/lrh/skills/lrh-review-response/SKILL.md:255`,
   `src/lrh/skills/lrh-closeout/SKILL.md:361-362`). `/lrh-confirm-fixes`
   is the fourth brick, not the breach.
2. **A verify-then-merge pass consumes its own signal.** The value of the
   skill is producing a clear "safe to merge" vs "go look at this" signal so
   the human's merge click becomes a *decided* click. If the skill merges, it
   removes the one moment where a human eye is cheap and an irreversible
   mistake is expensive.
3. **Automating merge buys almost nothing.** The most a skill could safely do
   is ask the human to confirm the merge — which is what clicking merge already
   is. The burden is better killed by making the verdict crisp and handing the
   human a `gh pr merge <pr> --squash` one-liner.

If automated merge is ever wanted, it belongs in a separate, explicitly-named
skill with its own gate — never as a silent tail of a verification pass.

### Decision 6: Verify all open threads; tag bot vs human

**Question:** Should the skill verify all open threads, or only those tied to
this PR's addressed fixes? How should human-reviewer threads be treated
differently from bot threads?

**Chosen: verify all open (unresolved) threads; tag author as bot or human.**

Scoping to "threads tied to addressed fixes" would require trusting the record's
claim about what it addressed — the self-attestation Decision 2 rejects — and a
thread the fix run *skipped* is exactly the one most worth surfacing. So the
skill verifies every unresolved thread identically.

The bot/human distinction matters only for *resolution etiquette*: some
maintainers consider clicking "resolve" on a human reviewer's thread the
reviewer's prerogative. The skill tags each resolve-eligible thread with its
author and a bot/human marker, and pre-selects both for resolution at the gate.
A `--surface-human` flag leaves human-reviewer threads surfaced-only (never
pre-selected), for maintainers who prefer to click those themselves.

### Decision 7: Independence switch (`--subagent`), default inline

**Question:** Should the fresh-eyes pass run inline, or spawn a subagent so a
different context judges the fixes (à la ultrareview)?

**Chosen: default inline; `--subagent` opt-in switch.**

The load-bearing independence is re-reading comments against the diff rather
than the record (Decision 2), which the inline pass already delivers. A cold
subagent context adds value chiefly when the skill runs in the *same session*
that authored the fixes, where the inline pass shares that session's
rationalizations. Spawning a subagent costs latency and tokens and should not
be the default. So: default inline; a `--subagent` switch dispatches
verification to a cold context given only the PR URL, diff, and comment bodies;
and the skill *offers* the switch when it detects same-session authorship (a
primary or `_REVIEW` execution record minted this session).

### Decision 8: CI gates the verdict, not thread resolution

**Question:** Should "merge-ready" require CI green, and how is that checked?

**Chosen: CI green is required for the readiness *verdict*, but does not gate
thread resolution.**

A thread can be correctly resolved on a red build — resolution reflects whether
the diff addresses a comment, which is orthogonal to CI. So CI gates only the
final verdict. The skill checks `gh pr view <pr> --json statusCheckRollup`
(the rollup state is robust across check types) and reports three states:
green → "ready to merge"; pending → "not yet ready — CI pending"; failing →
"not ready — CI failing." Threads are resolved regardless of CI state.

### Decision 9: Execution record — AD_HOC with `rerun_of`

**Question:** Does this create an execution record like `/lrh-review-response`?

**Chosen: yes — a lightweight `AD_HOC` record, suffix `_CONFIRM`, with
`rerun_of` linkage to the primary.**

`/lrh-review-response` creates an `AD_HOC` record because it pushes code
(`src/lrh/skills/lrh-review-response/SKILL.md:186-215`). `/lrh-confirm-fixes`
mostly does not change the repository — its outputs are resolved GitHub threads
and a readiness report. But an audit trail has real value: *these threads were
verified against commit `<sha>` and resolved by `<prompt-id>`*. That record
file is the skill's one repository change and gives closeout something to land.

The record uses slug `<branch>-confirm`, filename suffix `_CONFIRM.md` (parallel
to `_REVIEW.md`), and `rerun_of` pointing to the primary execution record. It
captures the taxonomy outcome (N resolved, M surfaced by bucket) in its body.

**Cross-skill consequence:** `/lrh-review-response` finds the primary record
for its own `rerun_of` by excluding `_REVIEW\.md$`
(`src/lrh/skills/lrh-review-response/references/review-response-workflow.md:44-46`).
Introducing `_CONFIRM.md` records requires updating that exclusion glob to also
exclude `_CONFIRM\.md$`, or a confirm record could be mismatched as a primary.
This is the one unavoidable edit to an existing skill beyond the handoff pointer
(Decision 11), and is scoped into the implementation work item.

### Decision 10: Reuse `lrh request review_response` for comment fetch

**Question:** Does the skill need a new `lrh request confirm_fixes` template?

**Chosen: no — reuse `lrh request review_response`; use raw `gh api graphql`
only for thread-id mapping and resolution.**

`lrh request review_response` already fetches open comments wrapped in a
security-boundary preamble that separates protocol text from reviewer-supplied
content. Reusing it preserves that boundary and avoids a new `request_catalog.py`
entry (a new request template would require a catalog entry plus a routing
test). The thread listing and resolution use raw `gh api graphql`
(`reviewThreads` query for thread ids; `resolveReviewThread` mutation), mapping
a comment's `databaseId` to the numeric id in a review-comment URL
(`…/#discussion_r3591298960` → `3591298960`).

### Decision 11: Handoff wiring in `/lrh-review-response`

**Question:** What is the minimal change to existing skills to wire the handoff?

**Chosen:** insert a `/lrh-confirm-fixes` node into the lifecycle diagram in
`review-response-workflow.md` (between "repeat review rounds" and "Merge +
closeout"), and add a one-line next-step pointer to `/lrh-review-response`'s
Step 7 report ("Suggest running `/lrh-confirm-fixes` before merge to verify
fixes and resolve threads"). Combined with the `rerun_of` glob edit
(Decision 9), these are the only changes to existing skills. All edits are
mirrored to both `src/lrh/skills/` and `.claude/skills/`.

### Decision 12: Idempotency — live thread state is the source of truth

**Question:** How does the skill behave on re-runs and partial-resolution
states?

**Chosen:** the source of truth is live GitHub thread state, not the execution
record. Each run re-queries unresolved threads against current `HEAD`; resolved
threads drop out of the query, so re-runs are naturally idempotent. The
`resolveReviewThread` call checks `isResolved` first and skips already-resolved
threads. Partial state (run 1 resolves 3 of 5, surfaces 2 → user runs
`/lrh-review-response` → run 2 sees only the still-unresolved threads) is the
designed flow, not an error.

The execution-record guard is deliberately *softer* than
`/lrh-review-response`'s hard stop. That skill hard-stops on an existing record
because a re-run would double-push code
(`src/lrh/skills/lrh-review-response/SKILL.md:115-134`). Here a re-run is cheap
and safe (state may legitimately have changed between rounds), so the skill
*warns* if a prior `_CONFIRM` record exists for this round and proceeds. A
fully-resolved, CI-green PR makes a re-run a clean "already ready" no-op.

### Decision 13: Skill step structure

**Chosen: 8 steps**, mirroring the assessment-first, human-gated structure of
`/lrh-closeout`.

```
Step 1 — Detect PR and verify branch
         gh pr view; verify current branch matches headRefName; require state: OPEN

Step 2 — Gather state
         Fetch comments (lrh request review_response); list unresolved threads
         (gh api graphql reviewThreads); check CI (gh pr view --json statusCheckRollup)

Step 3 — Fresh-eyes verification
         Read each thread's comment against the HEAD diff; classify into the
         Decision 3 taxonomy; mint prompt ID. Optional --subagent cold pass.

Step 4 — Confirm gate (human gate)
         Show: batch of Clear-satisfied threads to resolve (author + bot/human
         tag), the surfaced exceptions by bucket, CI status, provisional verdict.
         Wait for explicit confirmation.

Step 5 — Execute confirmed resolutions
         resolveReviewThread for each confirmed thread (skip already-resolved).
         For Unaddressed threads, offer /lrh-review-response (bounded; its own gate).

Step 6 — Compute readiness verdict
         Green iff all verifiable threads resolved AND no open exceptions AND CI green.

Step 7 — Create execution record and validate
         AD_HOC _CONFIRM record with rerun_of; lrh validate; commit + push.

Step 8 — Readiness report
         Verdict + surfaced exceptions + gh pr merge one-liner (human clicks).
```

### Decision 14: Reference file structure

**Chosen: one reference file — `references/confirm-fixes-workflow.md`.**

Contains: lifecycle placement, the verification taxonomy (Decision 3), the
`gh api graphql` primitives (thread listing, `databaseId`→URL mapping,
`resolveReviewThread`, `isResolved` check), the CI check, the `_CONFIRM`
execution-record convention and `rerun_of` population, and the idempotency /
re-run edge cases. Follows the one-reference-file convention of
`PROP-LRH-CLOSEOUT` (Decision 6) and `PROP-LRH-DOC-SKILLS`.

## Non-Goals

- Does not merge the PR — merge is a human action (Decision 5).
- Does not trigger `/lrh-closeout` — closeout runs post-merge.
- Does not resolve any thread the diff does not plainly satisfy — ambiguous,
  partial, and problematic threads are surfaced, never guess-resolved.
- Does not silently loop `/lrh-review-response` — unaddressed threads are
  detected and the fix skill is *offered*; each fix run keeps its own gate.
- Does not modify `lrh request review_response` or its template — it reuses it.
- Does not add a new `lrh request` catalog entry (Decision 10).
- Does not verify against the execution record's claims — only the live diff
  (Decision 2).

## Implementation Plan

Implementation is governed by workstream `WS-SKILLS-CONFIRM-FIXES` and one work
item.

| Work item | Deliverable | Depends on |
|---|---|---|
| `WI-SKILLS-LRH-CONFIRM-FIXES` | `/lrh-confirm-fixes` skill + handoff wiring | This proposal adopted |

**`WI-SKILLS-LRH-CONFIRM-FIXES`** produces:
- `src/lrh/skills/lrh-confirm-fixes/SKILL.md` (8-step flow per Decision 13)
- `src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md`
  (per Decision 14)
- `.claude/skills/lrh-confirm-fixes/` mirror (byte-for-byte, `diff -r` verified)
- `CLAUDE.md ## Skills` entry: `/lrh-confirm-fixes`
- Handoff wiring in `/lrh-review-response` (Decision 11) and the `rerun_of`
  exclusion-glob edit (Decision 9), mirrored to both skill trees

No new CLI is required — thread resolution reuses `gh api graphql` and comment
fetch reuses `lrh request review_response`, so there is no deferred second
phase.

## Cross-References

- Post-execution closeout complement and assessment-first skill structure:
  `project/design/proposals/adopted/lrh-closeout/00_proposal.md`
- Skill distribution pattern and confirm-gate convention:
  `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- The `[nothing]` gap and `rerun_of` convention this skill extends:
  `src/lrh/skills/lrh-review-response/references/review-response-workflow.md`
- Execution record fields and session transcript format:
  `src/lrh/skills/lrh-implement/references/execution-session-reference.md`

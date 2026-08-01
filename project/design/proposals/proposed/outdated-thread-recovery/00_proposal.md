---
id: PROP-OUTDATED-THREAD-RECOVERY
type: design_proposal
title: Outdated-Thread Recovery for /lrh-land's Review-Response ↔ Confirm-Fixes Loop
status: proposed
created_on: 2026-08-01
updated_on: 2026-08-01
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/proposed/lrh-land-execute/00_proposal.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - project/design/backlog.md
---

# Outdated-Thread Recovery for `/lrh-land`'s Review-Response ↔ Confirm-Fixes Loop

## Summary

Gives `/lrh-land`'s review-response ↔ confirm-fixes loop a mechanical,
always-human-gated way to recover when `/lrh-confirm-fixes` surfaces an
outdated-but-unresolved GitHub review thread that needs a real diff fix —
a case `lrh request review_response` cannot see today — without repeating
the governance failure a prose-only attempt produced during PR #453.

## Background / Motivation

PR #453 set out to fix a narrow bug in `/lrh-land` Step 4's loop-exit
condition: it told the agent to loop `/lrh-review-response` until
`lrh request review_response` reported `Nothing to resolve:`, which can
never happen purely as a result of running Step 4, since
`/lrh-review-response` does not itself resolve GitHub review threads —
that is `/lrh-confirm-fixes`'s job.

While fixing that, review (Codex) found a deeper, related gap:
`lrh request review_response`'s notion of "unresolved" excludes outdated
threads — a thread whose commented line has since moved stays
`isResolved: false` while `isOutdated: true`, and
`src/lrh/integrations/github/formatters.py`'s `_matches_state` requires
both `not isResolved` and `not isOutdated` for its default "unresolved"
branch. So an untriaged outdated thread is invisible to Step 4's own
tooling entirely, and only surfaces via `/lrh-confirm-fixes`'s
authoritative `isResolved`-only check.

An attempt to solve the resulting recovery path in `SKILL.md` prose — a
`/lrh-land` Step 5 "not a hard stop" exception for this specific case —
drew nine distinct, individually valid findings across seven further
review rounds, including a P1: the exception could silently override the
human's own Step-2-approved stop-work condition for the run (a reviewer
finding, which the run's own stated stop-work condition — "any reviewer
finding" — explicitly covered). Each fix was individually correct and
narrowly scoped, but the pattern — a mechanism needing a sixth and
seventh patch, each surfacing a new edge case — was itself the signal
that the mechanism's *shape* was wrong, not that it needed one more
patch. The exception was reverted; PR #453 shipped with only the
narrower Step 4 fix, and the deferred work was captured in
`project/design/backlog.md` ("`lrh request review_response` cannot
surface a specific outdated-but-unresolved thread").

This proposal is that deferred work, designed properly — through
`/lrh-design` — instead of patched incrementally under review pressure.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. Related building blocks already
  exist: `--force` on `lrh request review_response`
  (`src/lrh/assist/request_cli.py`) bypasses the "Nothing to resolve"
  early exit but does not widen the thread filter itself
  (`src/lrh/assist/request_service.py:122-142` still hardcodes
  `state="unresolved"`); `formatters._matches_state` already supports
  `state="all"`/`"outdated"`; `lrh github threads --state all` already
  exposes them via `src/lrh/cli/github.py` — none of this is wired into
  the `review_response` template path.
- Sibling repos: Checked Taurcode (`/Users/centaur/Workspace/Taurcode/taurcode`)
  — no `src/` review-response mechanism present; not applicable.
- External libraries: None identified — this is orchestration specific to
  LRH's own review-response/confirm-fixes loop built on GitHub's
  `reviewThreads` GraphQL API; no generic library covers it.
- **Recommendation: Proceed.**

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: Found — `project/design/backlog.md`, "`lrh request
  review_response` cannot surface a specific outdated-but-unresolved
  thread" (noted 2026-08-01, during PR #453's confirm-fixes round). This
  proposal is the design for that entry; the entry stays open (linked,
  not closed) until WI-A and WI-B are actually implemented and resolved.
- **Recommendation: Link the backlog entry to this proposal and both
  work items now; close it only once both are implemented.**

## Design Decisions

### Decision 1: CLI surface for including a specific thread

Options considered:
- **A — `--include-thread <thread-id>` repeatable flag**, sourced from
  `/lrh-confirm-fixes`'s own precise Step 3 classification.
- **B — `--thread-state <all|unresolved|outdated>` override**, reusing
  the existing `_matches_state` state vocabulary end-to-end (minimal
  code change: thread the existing `state` parameter one layer further).

**Chosen: A.** Option B is less code but imprecise — it would re-surface
*every* outdated thread, including ones already Clear-satisfied and
merely waiting on `resolveReviewThread`, mixing "needs a real fix" with
"just needs resolving" in the same confirm-gate batch. That is exactly
the kind of mixed-signal batch PR #453's own reviewers pushed back on
(two of the nine findings concerned batches that reprocessed
already-fixed threads). Option A stays surgical: confirm-fixes already
did the precise classification and already knows the exact thread ID
that needs action.

### Decision 2: Should the recovery path ever run without a live human gate?

Options considered:
- **Automatic exception** ("not a hard stop" once diff-verified) — what
  PR #453's reverted attempt tried.
- **Always-live-gated** — present the specific finding, wait for an
  explicit human answer, every occurrence, no default.

**Chosen: always-live-gated**, but only after a precondition check the
gate itself does not skip: **before presenting fix now / defer / stop,
check whether this newly-surfaced finding falls within the run's own
Step-2-approved stop-work condition** (e.g. "any unexpected reviewer
finding"). A qualifying outdated thread *is* a reviewer finding — if the
stop-work condition already covers it, that condition already requires a
halt-and-report; report the finding and stop, per the original Step 2
agreement, rather than presenting the three-way gate as if it were a
fresh, uncommitted choice. Continuing past an already-fired stop-work
condition requires the human to explicitly amend it — a separate, named,
live decision — not simply answer "fix now" to this gate. Only when the
finding falls *outside* the run's stop-work condition (a narrower
condition, e.g. "stop only on a failing test") does the three-way gate
apply as designed. This check exists because a P1 finding on this exact
proposal's own review showed the gate could otherwise silently let a run
continue past what the human had already committed to halting on —
precisely the failure mode PR #453's reverted automatic exception also
produced, just reached through a different path.

Once that precondition clears, the human answers one of three options,
each with an explicit disposition against `/lrh-land` Step 6's existing
invariant (a green confirm-fixes verdict, checked against the exact
current `HEAD`, is required before the SHA-locked merge command is
presented):

- **fix now** — route through Decision 4's recovery flow, then loop back
  to the top of `/lrh-confirm-fixes` for a fresh verdict against the new
  `HEAD` the fix produced. Step 6 is reached only once that fresh pass is
  green — pushing the fix is not itself sufficient, since
  `/lrh-review-response`'s protocol neither resolves the thread nor
  re-runs confirm-fixes on its own.
- **defer** — the human explicitly authorizes proceeding toward Step 6
  with this one specific, already-surfaced, already-reviewed thread left
  open — and *only* that thread. Every other component of the
  green-verdict invariant (CI, REVIEW-LANDED, and any other exception
  confirm-fixes surfaced) must still independently be green or cleared;
  deferring this one named thread does not touch them. This is a live,
  in-session, scoped override of Step 6's invariant for this thread
  alone — not a new bypass mechanism, but the same category of explicit
  human authorization `DEC-AGENT-EXECUTED-MERGE-GATE` already requires
  for the merge action itself, narrowed further. Step 6's summary must
  name the deferred thread explicitly, so the override is part of the
  audit trail, not a silent gap.
- **stop** — halt the run entirely; no path to Step 6 this run.

The automatic path (an unconditional "not a hard stop") is the proven
failure mode: PR #453's own reverted attempt drew a P1 finding showing it
could silently override a stop-work condition the human explicitly set
at the run's own chain-authorization gate — the original instance of the
same failure category this proposal's own review round 4 (above) later
found again, one layer down, in this design's first draft. This case is
rare in practice — in PR #453's own worked example,
every outdated thread encountered was Clear-satisfied, not needing a new
fix — so the added friction of a live gate per genuine occurrence is
low, and the safety property (no silent governance bypass, ever) is
worth it. This reuses the same three-way-human-gate *structure*
`references/round-cap-gate.md` already established for a different
decision (there: authorize a new ceiling / deny and stop / pause, gating
whether to keep retriggering bot reviewers) rather than inventing new UI
vocabulary for a structurally similar problem — the option labels differ
because the decisions differ, but both are a mandatory three-way human
answer with no inferred-from-silence default.

### Decision 3: Which confirm-fixes taxonomy buckets are ever eligible?

**Chosen: Unaddressed, Partial, and Problematic resolution only** — as a
hard rule enforced before the gate is even presented, not a
per-occurrence question the human answers. Ambiguous and Problematic
comment are, by `/lrh-confirm-fixes` Step 3's own taxonomy, not
actionable (Ambiguous: the diff can't decide the question either way;
Problematic comment: the reviewer's concern is itself wrong or conflicts
with a documented decision) — auto-driving either into a code change
risks an unnecessary or actively harmful edit regardless of who
authorizes it. Threads in either bucket keep today's unconditional hard
stop.

### Decision 4: Preserving review-response's own safeguards and feasibility check

**Chosen:** route the recovery fix through `/lrh-review-response`'s full
protocol — its Step 4 confirm gate, Step 5 canonical validation, and
Step 7 execution record — not just its triage checks. Decision 1's
`--include-thread` flag is what makes this possible in principle, but
only if it actually reaches review-response's own fetch: `--include-thread`
is a flag on `/lrh-review-response` Step 2's inner `lrh request
review_response <pr-url>` command, not something `/lrh-land` inlining
that protocol gets for free. The recovery flow must explicitly carry the
named thread ID from `/lrh-land`'s three-way gate into that specific Step
2 invocation (`lrh request review_response <pr-url> --include-thread
<id>`) when running the protocol inline — without that explicit
propagation, Step 2 still runs its plain, unflagged form and exits
immediately on `Nothing to resolve:` for exactly this thread class,
reproducing PR #453's original bug one layer down. The full protocol
also means `/lrh-review-response`'s own Step 5 feasibility check can
reject the fix as inappropriate for the change; a rejection is treated
the same as Problematic comment — surfaced to the human, hard stop —
not forced through.

### Decision 5: Same-run idempotence

A same-land-run invocation of this recovery path re-invokes
`/lrh-review-response`, which already created an `in_progress` execution
record earlier in the same run (Step 4's normal pass). `/lrh-review-response`
Step 3's own idempotence check treats a matched `in_progress` record as a
hard stop unless the user explicitly requests a rerun.

**Chosen:** encode "an in-session `/lrh-land` continuation" as a
recognized non-blocking condition in `/lrh-review-response` Step 3
itself — alongside its existing `failed`/`reverted`/`superseded`
non-blocking statuses — rather than patching around it from the caller
(`/lrh-land`) side. This keeps the idempotence rule owned by the skill
whose gate it is, consistent with this project's general preference for
a check's exceptions to live next to the check itself.

## Non-Goals

- Does not change `/lrh-confirm-fixes` Step 3's taxonomy — this proposal
  only consumes the existing bucket definitions.
- Does not weaken `/lrh-land` Step 5's default "not green = stop and
  report" rule for any case outside the narrow, explicitly-gated one
  defined here.
- Does not widen `lrh request review_response`'s default (no-flag)
  behavior — it stays scoped to non-outdated unresolved threads by
  design; only an explicit `--include-thread` widens it for a specific
  thread.
- Does not address the separate, already-tracked backlog items on
  execution-record filename timestamps (local time vs. UTC) or
  idempotence cross-PR fetch-error handling.

## Implementation Plan

Two work items, filed together, delivered as **two sequential PRs** —
not one combined PR. `/lrh-execute`'s own dependency gate (`PROP-LRH-LAND-EXECUTE`
Decision 4: "enforce `depends_on` — all entries must be `resolved`;
stop and report if not") requires WI-A to already be `resolved` before
WI-B, which declares `depends_on: [WI-REVIEW-RESPONSE-INCLUDE-THREAD]`,
can be selected through the governed execution path — so a single
combined PR isn't actually deliverable through `/lrh-execute` as
designed, regardless of how meaningful WI-B's diff is without WI-A's
flag. This is the normal, already-well-supported `depends_on` pattern
used everywhere else in this project, not a special case:

- **WI-A (mechanical), first:** `--include-thread <thread-id>` flag on
  `lrh request review_response`, `extra_ids` plumbing through
  `formatters._matches_state`/`format_threads_review`, and unit test
  coverage, in `src/lrh/assist/request_cli.py`,
  `src/lrh/assist/request_service.py`, and
  `src/lrh/integrations/github/formatters.py`.
- **WI-B (skill-flow), after WI-A resolves:** the governance-gated
  recovery path in `/lrh-land` Step 4/5 (Decisions 2–4) and the
  same-run idempotence recognition in `/lrh-review-response` Step 3
  (Decision 5). The backlog entry this design targets stays open across
  both PRs, exactly as it already stays open until both items are
  implemented — an intermediate state where WI-A is done and WI-B is
  not is expected, not a problem.

## Cross-References

- `project/design/proposals/proposed/lrh-land-execute/00_proposal.md` —
  governs `/lrh-land` itself; this proposal extends its Step 4/5 design.
- `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md` — the
  three-way-human-gate *structure* this proposal reuses for Decision 2
  (different decision, different option labels — see Decision 2).
- `project/design/backlog.md` — entry this proposal is the design for;
  linked now, closed only once WI-A and WI-B are implemented.

# No-Progress Review Cap — Reference

Where `/lrh-confirm-fixes` Step 8's provisional no-progress cap comes from,
what it bounds, and how to apply it. Read this before modifying Step 8's
REVIEW-LANDED logic.

---

## Why this exists

PR #442 in this repo drove the previous review-loop mechanism for 14 rounds
inside one `/lrh-confirm-fixes` run. The old cap bounded repeated hosted
reviewer submissions. `PROP-INVOCATION-AND-GATE-RESET` Decision 2 removes
manual GitHub review-bot retriggering from skills unconditionally, because
guidance-level restraint failed in live operation and consumed a scarce shared
review budget.

Removing that retrigger path does not remove the underlying risk: an unfixable
or design-flawed PR can still absorb repeated substitute self-review passes
without making progress. The provisional cap keeps a human checkpoint around
that failure mode while Stage 4 gathers real post-Stage-1 evidence and designs
the canonical policy-derived mechanism.

## What "round" means now

One **substitute review round**: a fresh `/lrh-self-review` PR-mode pass
dispatched by `/lrh-confirm-fixes` Step 8 because no matching automatic
reviewer response has landed for the `_CONFIRM` commit after a reasonable wait.

Automatic first-push or ready-for-review responses are not substitute rounds.
They can satisfy REVIEW-LANDED when they match the current head and are clean,
but this skill does not start a new hosted review-bot round.

## What this bounds — and what it does not

This check governs only consecutive substitute self-review rounds that make no
progress. It does **not**:

- Gate `/lrh-review-response`; that skill does not start review-bot rounds.
- Bound aggregate GitHub review-bot spend; Stage 1 removes this skill's manual
  retrigger surface rather than trying to query or budget the platform.
- Prevent a human from manually requesting a hosted review outside the skill.
  The escape hatch is manual-only and outside the automated workflow, per
  `PROP-INVOCATION-AND-GATE-RESET` Decision 2.
- Restart any in-flight agent session. A session that loaded an older skill
  copy keeps that copy until the human restarts it.

## No-progress definition

A substitute round counts as **no progress** when both are true:

1. The current `/lrh-confirm-fixes` run resolved no previously-unresolved
   review thread.
2. The substitute self-review surfaced no new finding.

Reset the consecutive no-progress counter to zero when either condition is
false. A new finding is progress because it gives the next run something
concrete to fix; resolving a previously-unresolved thread is progress because
the PR moved closer to merge readiness.

## Threshold and gate

The provisional threshold is **3 consecutive no-progress substitute rounds**.
Three inherits the only value with in-repo precedent: the retired mechanism's
default ceiling sequence started at 3, and the governing proposal explicitly
records that larger values are ungrounded until real Stage 1 evidence exists.

When the counter reaches 3, stop and ask the human for a new direction instead
of dispatching another substitute pass. Reasonable choices include:

- wait longer for an automatic reviewer response;
- accept a human review signal for this PR;
- redesign or split the PR;
- authorize another repository-specific remediation.

Do not provide a menu item that starts a hosted review-bot round from this
skill. The manual escape hatch exists outside the skill workflow.

## State

This cap may be tracked in the execution record or run notes for now; no
dedicated round-state branch is required in Stage 1. Record enough evidence for
the next invocation to see:

- the current `_CONFIRM` commit SHA;
- whether a substitute self-review was run;
- whether it found anything;
- whether any previously-unresolved thread was resolved;
- the resulting consecutive no-progress count.

If this evidence is missing or ambiguous, fail safe: ask the human whether to
treat the previous substitute round as no-progress rather than guessing.

## Historical risk notes

The retired hosted-reviewer cap accumulated several correctness lessons that
remain useful if a future stage rebuilds a persistent reviewer-wait primitive:
canonical PR identity beats branch-name-derived identity; state writes must be
atomic and visible to later sessions; branch state must not move the reviewed
PR head; paginated GitHub API reads must aggregate across pages before choosing
"latest"; portable shell snippets need macOS and GNU variants checked; and a
stalled hosted reviewer can look identical to platform lag from API surfaces.

Those lessons are retained here as design constraints for future work, not as
active Stage 1 behavior.

---
resolution: "Implemented and merged in PR #632 (commit 81e519b5). Re-stamps confirmed_commit/confirmed_at on live-answered staleness reconfirmations that agree with the persisted text (exact match or accepted divergence), never on a declined or unreached divergence; also requires the gate's presentation to surface the check-staleness stale-files payload verbatim."
blocked_reason: null
blocked: false
id: WI-CHAIN-DEFAULTS-STALENESS-RESTAMP
title: Re-stamp confirmed_commit on stale-but-reconfirmed chain-defaults values
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-CHAIN-DEFAULTS
related_design:
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
depends_on:
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-3
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - ship_skip_if_opted_in_as_default
  - bypass_two_step_consent
acceptance:
  - The propose-and-confirm flow text explicitly re-stamps confirmed_commit/confirmed_at whenever a live reply and the persisted completion/stop-work text end up agreeing (match, or an accepted divergence) -- never on a declined or unreached divergence
  - The existing "do not silently rewrite the stored value" caution is preserved and scoped explicitly to the no-live-reply case and the diverge-and-decline case
  - The gate's presentation surfaces the check-staleness command's own stale-files list verbatim, not a generic substitute notice
  - Canonical source (_shared/chain-defaults.md) and its inlined copy (lrh-land/references/land-workflow.md) stay identical
  - All installed mirrors (.claude/, .agents/, .gemini/) match the canonical source exactly
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .agents/skills/lrh-land/references/land-workflow.md
  - .gemini/plugins/lrh/skills/lrh-land/references/land-workflow.md
---

# Re-stamp `confirmed_commit` on stale-but-reconfirmed chain-defaults values

## Summary

`DEC-GATE-POLICY-CASCADE`'s Decision 5 staleness fallback (implemented by
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`) correctly forces a live
chain-authorization ask when gate-definition prose has changed since
`confirmed_commit`. But once the human answers that live ask by
reconfirming the *same* completion/stop-work condition text (no
divergence), nothing re-stamps `confirmed_commit`/`confirmed_at` — the
only documented re-stamp paths are the "first encounter" case
(`confirmed_commit` null) and the "user's reply diverges from stored
values" case (the Decision 4 profile-update offer). A matching
reconfirmation falls into neither path, so the same staleness fallback
fires again on every subsequent run indefinitely, even though a human has
now explicitly re-confirmed the values live.

## Problem / Context

Discovered live during a session that had just activated
`chain_init_confirmation: skip_if_opted_in` with valid two-step consent:
the very next `/lrh-execute` run correctly hit the staleness fallback,
since `confirmed_commit` (`66a3f942556641309d7407db140fc8b070f652bd`,
2026-08-17) predated that same session's entire Stage 3.5 / Increment 3
gate-policy body of work (a `git diff --stat` between that commit and
`HEAD` over the watched files showed 591 insertions across 12 files —
unambiguously substantive, not churn). The current governing text in
`src/lrh/skills/_shared/chain-defaults.md`'s Decision 5 section states:

> "Do not silently rewrite the stored value based on this fallback alone
> — it only affects this run's liveness, not the persisted setting."

That caution is correct for a genuinely *silent* fallback (no live
answer ever given — not currently possible on this exact path, since the
staleness fallback always forces a live ask, but worth keeping the
caution precise for any future path that could reach this state without
a live answer). It is being read, as currently worded, to also cover a
live reply that *does* answer the gate and happens to match the stored
text — which was not the intent of the caution and leaves the mechanism
unable to ever clear a stale `confirmed_commit` through ordinary use.

### Prior Art Check

**Duplication search.** No existing work item covers this general
mechanism gap. `WI-RETRIGGER-REMOVAL-STAGE1` and
`WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` both include
`confirmed_commit` re-stamping only as a one-off acceptance-criterion side
effect of landing their own PR, not as a standing fix to the
reconfirmation path. `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` implemented the
staleness *detection* mechanism this depends on but did not address what
happens after a live answer resolves it.

**Demand search.** No existing proposal, backlog entry, or open work item
requests this specific fix. Recommendation: proceed.

## Scope

Fix the propose-and-confirm flow text — canonical source, its inlined
copy, and all installed mirrors — so that a live reply resolving a
staleness-triggered ask re-stamps `confirmed_commit`/`confirmed_at` to the
current commit/time whenever the reply and the values that end up
persisted to disk agree: an exact reconfirmation, or a divergence the
human explicitly accepted via the existing Decision 4 profile-update
offer. Do **not** re-stamp when the reply diverges and the human declines
that offer (or the offer is never reached) — the persisted text in that
case is not what the human just said, and re-stamping would misrepresent
an unratified value as freshly confirmed. Preserve the existing "no silent
rewrite" caution, scoped to both the no-live-reply case and this
diverge-and-decline case.

Out of scope: changing `gate_staleness.py`'s staleness *detection* logic
(hunk/marker overlap, `DEFAULT_WATCHED_FILES`) — this work item only
changes what happens after a live answer to a fallback-triggered ask.

## Required Changes

1. Edit `src/lrh/skills/_shared/chain-defaults.md`'s Decision 5 section:
   when the staleness fallback fires (`exit 1`) and the human gives a
   live reply to the resulting ask, re-stamp
   `confirmed_commit: $(git rev-parse HEAD)` and
   `confirmed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)` only when the reply and
   the persisted completion/stop-work text end up agreeing — an exact
   match, or a divergence accepted via the Decision 4 profile-update
   offer. State explicitly that the "do not silently rewrite" caution
   applies both when no live reply is given at all and when a divergent
   reply's profile-update offer is declined or never reached. Also
   require the gate's presentation to surface the `check-staleness`
   command's own `stale files` list verbatim (not a generic "gate policy
   changed" substitute), per this project's gate-policy principle that a
   gate must show the actual decision payload.
2. Apply the identical edit to `src/lrh/skills/lrh-land/references/land-workflow.md`'s
   inlined copy, keeping the two byte-identical in the edited section.
3. Mirror the change into `.claude/skills/`, `.agents/skills/`, and
   `.gemini/plugins/lrh/skills/`.

## Non-Goals

- Does not change `gate_staleness.py`'s detection logic or its watched-file
  list.
- Does not change `chain_init_confirmation`'s default value or ship
  `skip_if_opted_in` as the default.
- Does not implement `confirm_fixes_batch`'s autopilot predicate — that is
  `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`.
- Does not weaken the two-step consent contract from
  `DEC-CHAIN-INIT-SKIP-CONSENT` — a live reply is still required whenever
  staleness fires; this only fixes what happens to the stored metadata
  after that reply.

## Acceptance Criteria

- The propose-and-confirm flow text explicitly re-stamps
  `confirmed_commit`/`confirmed_at` whenever a live reply and the
  persisted completion/stop-work text end up agreeing (an exact match, or
  a divergence explicitly accepted via the Decision 4 profile-update
  offer) -- never on a declined or unreached divergence
- The "do not silently rewrite" caution is preserved and scoped explicitly
  to the no-live-reply case and the diverge-and-decline case
- The gate's presentation surfaces the `check-staleness` command's own
  `stale files` list verbatim, not a generic substitute notice
- Canonical source and inlined copy remain identical in the edited section
- All installed mirrors match the canonical source exactly
- `lrh validate` reports 0 errors

## Validation

- lrh validate
- Manual dogfooding: trigger the staleness fallback on a real or
  simulated stale `confirmed_commit`, reconfirm matching values, verify
  `confirmed_commit`/`confirmed_at` update, and verify a subsequent run
  against the same `HEAD` (with no further gate-definition changes) does
  not re-trigger the staleness fallback

## Risk Notes

The main risk is re-stamping too eagerly — if a future edit accidentally
treats a *silent* skip (no live reply reached at all) as equivalent to a
live reconfirmation, `confirmed_commit` could advance past a gate change
the human never actually saw. The fix must key specifically on "a live
reply was given," not merely on "the fallback path was entered."

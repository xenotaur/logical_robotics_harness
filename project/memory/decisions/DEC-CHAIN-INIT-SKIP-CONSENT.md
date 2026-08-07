---
id: DEC-CHAIN-INIT-SKIP-CONSENT
---

# Chain-Initiation Skip Consent Narrows the Per-Run Live-Reply Requirement

Status: accepted
Date: 2026-08-07

## Summary

`DEC-DELIBERATE-CHAIN-INITIATION` requires a human to have "provided or
signed off on" a completion condition and a stop-work condition for *each*
chain run before an automatic chain may proceed. This decision narrows that
requirement on one specific, bounded axis: when a user has opted into
`chain_init_confirmation: skip_if_opted_in` — a user-local, value-bound,
revocable consent — a chain-authorization gate may skip re-confirming
pre-filled completion/stop conditions on that run. `always_confirm`
(today's default: pre-filled text, still requiring a live reply) is
completely unaffected. The human's own slash-command invocation remains the
deliberate initiation act in every mode; what changes is only whether a
fresh live reply re-stating already-decided conditions is required on top
of that invocation.

## Context

- `PROP-LRH-CHAIN-DEFAULTS` (PR #490, merged) introduces a persisted
  chain-defaults profile to reduce repeated, identical hand-typed answers
  across `/lrh-land`/`/lrh-execute` invocations. Its Decision 6 (added
  during a design-review steelmanning session,
  `WS-LRH-CHAIN-DEFAULTS`'s hard prerequisite before Increment 1)
  introduced `chain_init_confirmation` as a configurable field, separate
  from the completion/stop-condition text and self-review preference.
- During that PR's own review (PR #499), a Codex finding confirmed the
  proposal's first draft falsely claimed `DEC-DELIBERATE-CHAIN-INITIATION`
  "remains in force unchanged." `DEC-DELIBERATE-CHAIN-INITIATION.md:57-64`
  is explicit: "[a]bsent an explicit initiation carrying both conditions,
  no chain self-starts." A `skip_if_opted_in` run genuinely has no fresh
  live reply carrying those conditions for that specific run. The proposal
  was corrected to say so honestly and blocked `skip_if_opted_in` from
  shipping until this decision landed — see that proposal's Decision 6 and
  Open Questions for the corrected text.
- A second Codex finding on the same PR caught a real design flaw in the
  original mechanism: storing the skip-consent in the shared, git-tracked
  `project/config/chain-defaults.yaml` profile (per Decision 1's own
  "travels with the repo so every collaborator... see the same values")
  would let one collaborator's opt-in commit silently skip the gate for
  every other collaborator, who never performed the required second
  affirmative action themselves. Fixed in the proposal by scoping the
  consent to user-local storage; this decision incorporates that fix.
- `WI-DEC-CHAIN-INIT-SKIP-AMENDMENT` is the work item that produced this
  decision, filed as the direct response to `PROP-LRH-CHAIN-DEFAULTS`'s own
  blocking Open Question.
- `DEC-AGENT-EXECUTED-MERGE-GATE` is the direct structural precedent: it
  narrowed the same governing decision (`DEC-DELIBERATE-CHAIN-INITIATION`)
  on a different axis — who executes the merge command, not whether a live
  reply is required — via its own dedicated decision-log entry, not a
  silent proposal-level assertion. This decision follows that same
  pattern rather than inventing a new one.

## Decision

**`chain_init_confirmation` is a two-valued field: `always_confirm` |
`skip_if_opted_in`.** `always_confirm` is the default and is unaffected by
this decision — the chain-authorization gate still requires a fresh live
reply confirming the completion and stop-work conditions on every run,
exactly as `DEC-DELIBERATE-CHAIN-INITIATION` already requires.

**Under `skip_if_opted_in`, a chain-authorization gate may proceed without
a fresh live reply carrying the completion/stop conditions for that
specific run**, subject to all of the following:

1. **The human's slash-command invocation remains the deliberate
   initiation act.** `/lrh-land <pr>`, `/lrh-execute <target>`, or the
   equivalent explicit trigger is still required to start any chain, in
   every mode. This decision does not touch that requirement.
2. **Two separate affirmative user actions are required to reach
   `skip_if_opted_in`, never one implying the other:** (a) storing default
   completion/stop-condition values, and (b) a distinct, explicit opt-in
   to use those values without re-confirming them. Storing a default value
   is never itself consent to skip confirming it.
3. **The skip-consent is stored user-locally, never in the shared
   repo-level chain-defaults profile.** E.g. local git config (`git config
   --local`) or an equivalent gitignored, per-user record. It must never
   be committed to `project/config/chain-defaults.yaml` or any other
   git-tracked, shared location — a shared-storage skip-consent would let
   one collaborator's opt-in silently apply to another's invocations, who
   never performed action (b) themselves.
4. **The consent is bound to the specific condition values it was granted
   against.** The local record stores a hash (or equivalent fingerprint)
   of the exact completion-condition, stop-work-condition, and
   self-review-preference values active when the opt-in was given. If the
   shared profile's values change — including via the profile-update offer
   this proposal's Decision 4 already defines — the local consent is
   invalidated back to `always_confirm` until the user re-opts-in against
   the new values.
5. **A per-run "special conditions" check runs unconditionally, even in
   `skip_if_opted_in` mode, and forces a live gate when it fires:** an
   unmet `depends_on`, a prior failed or stopped run on the same PR,
   uncommitted stray changes, or a target that doesn't match the stored
   default's assumptions. This generalizes the gate-owned "unusual
   predicate" pattern `PROP-LRH-CHAIN-DEFAULTS` Decision 2 already applies
   to per-gate autopilot, up to the chain-initiation gate itself. A stored
   skip setting can never silently paper over a run that actually needs a
   human look.

**Scope.** This decision narrows `DEC-DELIBERATE-CHAIN-INITIATION`'s
per-run live-reply requirement on exactly this one axis — the
chain-authorization gate's condition-confirmation reply, under the
specific consent model above. It does not touch:
- the merge gate (`DEC-AGENT-EXECUTED-MERGE-GATE`), which is unaffected
  and continues to require its own live, in-session authorization every
  time;
- `/lrh-closeout`'s plan-confirm gate, or any other skill's internal
  confirmation gate — `DEC-DELIBERATE-CHAIN-INITIATION`'s protection of
  those remains in force unchanged, and `PROP-LRH-CHAIN-DEFAULTS`
  Decision 3 already categorically excludes `closeout_plan` from any
  autopilot tier on this same basis;
- any other narrowing of chain-initiation not described above — a future
  proposal to skip a *different* protected gate's live reply must be its
  own explicit decision, not a silent extension of this one.

## Rationale

- Ratifies a real, demonstrated friction pattern rather than a
  hypothetical one: the same session that produced `PROP-LRH-CHAIN-DEFAULTS`
  restated near-identical completion/stop conditions across five separate
  `/lrh-land` invocations, with the self-review preference restated
  verbatim every time.
- Preserves the substance of "no chain starts itself" even though the
  literal per-run condition-confirmation reply is skipped: the slash-command
  invocation is still the deliberate initiation act, and the two-step
  consent plus mandatory special-conditions check mean a stored setting
  can express "I've already decided this and it still applies" rather than
  silently deciding on the user's behalf.
- Mirrors `DEC-AGENT-EXECUTED-MERGE-GATE`'s own pattern: narrow a
  categorical rule on one precisely-specified axis, backed by a
  bright-line test, rather than loosening the rule generally or leaving
  the friction unaddressed.
- The user-local storage and value-hash binding directly close the two
  real gaps a review round caught in the mechanism's first draft — this
  decision incorporates both fixes rather than repeating the mistake of
  asserting safety without having checked it.

## Alternatives considered

1. **Never allow any skip — `always_confirm` only, permanently.**
   Pros: zero risk of the narrowing this decision makes. Cons: leaves the
   demonstrated friction unaddressed indefinitely; the entire motivation
   for `PROP-LRH-CHAIN-DEFAULTS`'s chain-level defaults tier is reduced
   asking, and a defaults mechanism that still asks the same amount every
   time delivers little of that value.
2. **Allow skip from stored defaults alone, with no separate opt-in.**
   Pros: simpler, fewer states. Cons: conflates "the user once set a
   default value" with "the user has authorized skipping confirmation" —
   different acts; this was the original design-review discussion's
   explicit rejection of the two extremes, not a new consideration.
3. **Store the skip-consent in the shared repo-level profile.**
   Pros: simpler storage model, one file. Cons: confirmed as a real
   multi-collaborator consent leak during `PROP-LRH-CHAIN-DEFAULTS`'s own
   review — one collaborator's opt-in would silently apply to everyone.
   Rejected; user-local storage is the only option that keeps consent
   individually earned.

## Consequences

- `PROP-LRH-CHAIN-DEFAULTS`'s Open Question blocking `skip_if_opted_in` is
  resolved — that proposal is updated to cite this decision directly.
- `skip_if_opted_in` is now unblocked for a future Increment 1
  implementation work item under `WS-LRH-CHAIN-DEFAULTS`
  (`WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`), which must implement all five
  numbered requirements in the Decision section above, not only the
  field's existence.
- `DEC-DELIBERATE-CHAIN-INITIATION`'s Consequences section is updated to
  cross-reference this decision directly, per the precedent
  `DEC-AGENT-EXECUTED-MERGE-GATE` set for the same governing decision.

## Revisit conditions

Revisit when:

- evidence emerges that the value-hash invalidation (requirement 4) is
  being bypassed or misread in practice — e.g. a profile update silently
  carries forward a stale consent;
- the special-conditions check (requirement 5) is found to miss a real
  category of risk that should have forced a live gate;
- a future proposal wants a similar skip-consent pattern for a different
  protected gate (e.g. the merge gate or `/lrh-closeout`'s plan-confirm
  gate) — that must be its own explicit decision on its own evidence, not
  a silent extension of this one's scope;
- `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` implementation surfaces a mechanical
  gap this decision's five requirements didn't anticipate.

---
id: PROP-REVIEW-WAIT-POSTURE
type: design_proposal
title: "Review-Wait Posture: Bounded-Poll Wait Mechanism"
status: proposed
created_on: 2026-08-08
updated_on: 2026-08-08
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-self-review/00_proposal.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/workstreams/active/WS-LRH-CHAIN-DEFAULTS.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - project/design/backlog.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
---

## Summary

This proposal is rescoped to the bounded-poll wait mechanism only. Its
original Decisions 1 and 2 are closed as obviated by
`PROP-INVOCATION-AND-GATE-RESET` Decision 2 and
`WI-RETRIGGER-REMOVAL-STAGE1`: manual GitHub review-bot retriggering is
removed from the skill workflow unconditionally, and the dead
`self_review_preference` field is deleted rather than wired. The retained
Decision 3 specifies the supported bounded background-poll shape for waits
that still exist, especially CI waits.

## Stage 1 Rescope

`PROP-INVOCATION-AND-GATE-RESET` resolved the open disposition for this PR on
2026-08-09: Decision 1 (invert Step 8's default hosted-review mechanism) and
Decision 2 (wire `self_review_preference` into `round-cap-gate.md`) are
obviated. With manual review-bot retriggering removed, there is no in-skill
default hosted-review mechanism to invert, and with `self_review_preference`
removed from `project/config/chain-defaults.yaml`, there is no profile field
to wire.

Decision 3 remains independent: a bounded background poll with predicates
matched to what each wait is actually waiting for is still useful for CI waits
and any future explicitly-authorized wait surface. Decisions 4 and 5 remain
non-goal/scope notes.

## Background / Motivation

`round-cap-gate.md`'s three-way gate already offers "substitute self-review
for this round" as a fourth answer, but it fires only after
`completed_count` reaches the ceiling (default 3) — meaning up to three
real, credit-consuming bot-retrigger batches happen before self-review is
even offered. That default was fine when bot-review capacity was abundant;
it no longer is — the motivating context for this proposal is that the
fleet was down to 1/7 monthly Codex credits as of 2026-08-07 (reported by
the user at request time; not itself a durable, in-repo-citable fact, so
treat it as the triggering circumstance rather than a source to look up
later). `project/config/chain-defaults.yaml` already carries a
`self_review_preference: substitute_self_review` field — steelmanned in
`PROP-LRH-CHAIN-DEFAULTS` as "substitute self-review rather than requesting
a new bot-retrigger ceiling, by default" — that has never actually been
wired to anything. This is confirmed directly, not inferred: PR #512's own
`_CONFIRM` record
(`project/executions/AD_HOC/2026_08_07_19_11_00_WI_LRH_CHAIN_DEFAULTS_INCREMENT_1_CONFIRM.md`)
notes plainly that "`self_review_preference` is persisted in the profile
schema but has no consumer yet (`round-cap-gate.md` untouched)."

Separately, this gap is not hypothetical policy drift — the user already
stated a standing preference live, in-session, during PR #469's landing:
"no manual paid GitHub reviewer retriggers beyond the automatic review on
initial PR push; post-fix confirmation should use self-review with a fresh
independent sub-agent instead" (recorded in `project/design/backlog.md`'s
"Self-review-first tier..." entry). That instruction was never formalized
into skill text, so every subsequent `/lrh-confirm-fixes` Step 8 invocation
still defaults to the old, now-unsafe behavior.

`PROP-LRH-SELF-REVIEW` (adopted) deliberately locked only the narrowest
possible guarantee in this space — Decision 4, "never skip a PR's *first*
real bot round" — and explicitly deferred "a broader design-space pass on
later-round skip policy" as future work. `backlog.md`'s own "Self-review-
first tier for reducing GitHub bot-review credit consumption" entry names
this same gap as its Open Question 4 ("who decides 'clean enough to skip a
bot round'"), and marks it explicitly unresolved by that proposal. This
proposal is that deferred design-space pass, scoped to what current
evidence actually supports rather than the full open-ended question.

A second, independently-discovered gap motivates this proposal's other
half: `/lrh-land` Step 8's "wait for CI + bot review to post" step has no
specified wait mechanism. During this session's own work, that gap was
papered over by an improvised call to `ScheduleWakeup` — a tool whose own
description scopes it to `/loop` dynamic-mode self-pacing, not general
mid-skill waits. It happened to work once, but nothing in `/lrh-land`'s or
`/lrh-confirm-fixes`'s `SKILL.md` specifies a supported mechanism for this
recurring situation, and reusing a tool outside its documented contract is
not something to leave undocumented as if it were the intended design.

## Prior Art Check

### Duplication search

- **In-repo:** No duplicate implementation exists. Three real, closely
  related mechanisms already exist and are what this proposal promotes/
  rewires rather than reinvents: `round-cap-gate.md`'s existing fourth
  three-way-gate answer ("substitute self-review for this round"); the
  dead `self_review_preference` field in `project/config/chain-defaults.yaml`;
  and `PROP-LRH-SELF-REVIEW` Decision 4's explicit deferral of later-round
  skip policy to future work.
- **Sibling repos:** None identified.
- **External libraries:** Not applicable — this is a review-policy and
  skill-prose change, not a library concern.
- **Recommendation:** Proceed.

### Demand search

- **Work items:** `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` (proposed) was
  checked in full. It is scoped exclusively to `confirm_fixes_batch`
  per-gate autopilot (whether to auto-continue past the Step 4 confirm
  gate on a clean batch) — its own Non-Goals state it "does not touch...
  any Increment 1 mechanism beyond reusing its existing storage." It does
  not cover wiring `self_review_preference` or the wait mechanism. No
  other open work item covers this gap.
- **Proposals:** `PROP-LRH-SELF-REVIEW` (adopted) and `PROP-LRH-CHAIN-
  DEFAULTS` (proposed) are the two proposals this design amends — neither
  resolves the specific question here (see Background above). No proposal
  duplicates this one.
- **Backlog:** `project/design/backlog.md`'s "Self-review-first tier for
  reducing GitHub bot-review credit consumption" entry names this exact
  gap as its unresolved Open Question 4. This proposal resolves it.
- **Recommendation:** No item to close as duplicate. Offer to cross-link
  this proposal from the backlog entry once adopted.

The wait-mechanism gap (`ScheduleWakeup` misuse) has no prior art at all —
first surfaced this session, with no existing work item, proposal, or
backlog entry naming it.

## Design Decisions

### Decision 1: Invert `/lrh-confirm-fixes` Step 8's default review mechanism — obviated

**Disposition:** Closed as obviated by `PROP-INVOCATION-AND-GATE-RESET`
Decision 2. Stage 1 removes manual GitHub review-bot retriggering from the
skill workflow unconditionally, so there is no in-skill hosted-review default
left for this decision to invert.

**Question:** Should every Step 8 round default to a bot retrigger (today's
behavior, self-review only past the ceiling), or should every round default
to `/lrh-self-review` PR-mode, with a real bot retrigger as the exception?

**Options considered:**
- **Status quo** (ceiling=3, self-review only post-cap) — up to 3 real
  bot-credit-consuming rounds still happen before self-review is offered;
  unsafe at the fleet's current 1/7 monthly Codex credits.
- **Lower the default ceiling to 1** — minimal change, reuses the existing
  mechanism unmodified. Rejected as the sole fix: `round-cap-gate.md`'s own
  ceiling semantics ("`N` batches are allowed to run; the gate fires before
  the `(N+1)`th") mean ceiling=1 still guarantees exactly one real bot batch
  per Step 8 entry — it shrinks the allowance to its floor without
  inverting the default the underlying problem requires, and does nothing
  for the wait-mechanism gap (Decision 3) since bot rounds still happen
  routinely.
- **Invert the default** — every Step 8 round defaults to `/lrh-self-review`
  PR-mode; a real bot retrigger becomes an explicit, opt-in exception.

**Chosen: invert the default.** This is the only option that matches the
user's own already-stated standing policy (PR #469) and actually answers
`backlog.md`'s Open Question 4 rather than shrinking around it.
`PROP-LRH-SELF-REVIEW` Decision 4 is untouched by this choice — the PR's
*first* review still comes from the automatic on-open bot trigger, which
this proposal never touches or skips. Every Step 8 round this proposal
redefines is, by construction, a *later* round in Decision 4's own
terminology — exactly the scope Decision 4 named as deferred, not something
Decision 4 itself locked against.

`round-cap-gate.md`'s numeric ceiling (3 → 10 → 20) is retained unchanged
in shape, but its *scope* shifts to bound self-review rounds by default
(still meaningful — it bounds runaway agent-turns/session-compute spend
even though self-review doesn't draw the metered bot-credit resource).
`completed_count` already counts bot-triggered and self-review-substituted
rounds identically (`round-cap-gate.md`'s existing "Any-side-effect-counts
promotion" section), so no state-schema change is required for this shift.

**Require affirmative evidence the first bot round actually landed —
caught in this PR's own review (Codex, P1).** Decision 1's own rationale
above rests on "the PR's first review still comes from the automatic
on-open bot trigger" — but that trigger firing is an assumption, not a
verified fact, in two real scenarios this design must not silently
assume away: `/lrh-confirm-fixes` can run standalone immediately after PR
creation, before the automatic reviewer has had time to respond; and the
automatic reviewer can simply be delayed, disabled, or unconfigured for a
given repo. Defaulting straight to self-review in either case would let a
clean subagent pass produce REVIEW-LANDED and a merge-ready verdict
without any independent platform reviewer ever having actually responded
— silently defeating `PROP-LRH-SELF-REVIEW` Decision 4's guarantee rather
than resting on it. The wiring this proposal calls for must therefore
check for affirmative evidence of a landed first-round response (e.g. at
least one review or comment from a configured reviewer, dated after the
PR's creation) before treating Decision 4's guarantee as satisfied; if no
such evidence exists, retain bot-first handling for that first round
until it does, rather than assuming the automatic trigger already ran.

**Opt-in surface for a real bot round, corrected — caught in this PR's
own review (Codex, P2).** The original text above named "the existing
Step 4 confirm-gate batch summary" as the visibility point — but
`/lrh-confirm-fixes` Step 2.2 explicitly skips directly to Step 8 when no
unresolved threads exist, meaning Step 4 never runs at all in exactly the
clean/standalone-confirmation case this mechanism most needs to be
visible in. The opt-in surface must instead sit on a path that always
runs: immediately before Step 8's mechanism choice executes, not
contingent on Step 4 having fired. A human who wants a real bot round can
still ask for one at any point in the normal course of the conversation
— this correction is about where the choice is *displayed* by default,
not about adding a fresh mandatory ask, so it stays consistent with this
project's existing `skip_if_opted_in` philosophy and the friction-
reduction goal.

### Decision 2: Wire `self_review_preference` into `round-cap-gate.md` — obviated

**Disposition:** Closed as obviated by `PROP-INVOCATION-AND-GATE-RESET`
Decision 2 and `WI-RETRIGGER-REMOVAL-STAGE1`. Stage 1 deletes
`self_review_preference` from the chain-defaults profile and removes the
manual hosted-review retrigger path this field would have selected between.

**Question:** How does the inverted default in Decision 1 actually get
consumed, given the field already exists but nothing reads it?

**Chosen:** `round-cap-gate.md`'s Step 8.1 (currently an unconditional bot
retrigger) reads `self_review_preference` from
`project/config/chain-defaults.yaml` before choosing which mechanism to
run for the round. The field's current name and documented semantics
("substitute self-review only after the ceiling blocks") no longer match
Decision 1's behavior and need updating — but the **exact new value space**
(e.g. `self_review_first` as the new default literal vs. `always_bot` as an
explicit opt-out; whether the existing `substitute_self_review` literal is
kept, renamed, or retired) is a concrete default-value decision this
proposal deliberately does not invent. Per `WS-LRH-CHAIN-DEFAULTS`'s own
established practice — which required a dedicated steelmanning session
before any Increment 1 default value shipped — this is recorded as
**required follow-up work**, not settled here (see Non-Goals and
Implementation Plan).

**Caught in this PR's own review (Codex, P2): reading the field directly
from Step 8 would bypass the profile's existing trust contract.**
`project/config/chain-defaults.yaml` starts with `confirmed_commit: null`,
and today the only place that confirms and staleness-checks the profile is
`/lrh-land`/`/lrh-execute` Step 2's chain-authorization gate
(`land-workflow.md`'s "Decision 5 — staleness fallback"). `/lrh-confirm-fixes`
can also run standalone, outside any `/lrh-land`/`/lrh-execute` invocation
— so a naive Step 8.1 read would let an unconfirmed or stale
`self_review_preference` silently select bot vs. self-review with no guard
at all. The eventual wiring therefore requires two things beyond a bare
field read, locked here even though the exact value-space literals stay
deferred: (a) Step 8.1 must check the same `confirmed_commit`/staleness
gate `/lrh-land` Step 2 already runs, falling back to the pre-inversion
bot-first default whenever the profile is unconfirmed or stale — the same
fail-safe direction `land-workflow.md`'s staleness fallback already uses
elsewhere; and (b) the staleness diff's own file list (`land-workflow.md`'s
"Decision 5 — staleness fallback", currently `lrh-land/SKILL.md`,
`lrh-land/references/land-workflow.md`, `lrh-execute/SKILL.md`,
`_shared/chain-defaults.md`) must be extended to include
`lrh-confirm-fixes/SKILL.md` and `round-cap-gate.md` themselves — today's
list would silently miss a change to the very files this proposal edits.

**The staleness-file-diff fix above is necessary but not sufficient —
caught in this PR's own review (Codex, P2).** Extending the diffed file
list only detects a change to the *skill-logic files themselves*; it does
not detect a change to the *value* being trusted. A later commit could
edit `project/config/chain-defaults.yaml`'s `self_review_preference`
field directly, in isolation, without touching any of the diffed skill
files at all — the existing `confirmed_commit` would stay non-null and
"not stale" under file-diff staleness alone, even though the human never
actually confirmed *this* value. The eventual wiring must therefore bind
the confirmation to the specific *value* it was granted for, not only to
the skill-logic files being unchanged — e.g. a stored hash of the
confirmed `self_review_preference` value itself (the same value-hash-
binding shape `DEC-CHAIN-INIT-SKIP-CONSENT`'s `skip_if_opted_in` opt-in
already uses for its own consent, per `land-workflow.md`'s "the five
requirements"), invalidated the moment the live value diverges from what
was hashed at confirmation time — not merely an equivalent check in
spirit, a real content binding.

### Decision 3: Specify the wait mechanism as a bounded background poll, with predicates matched to what each wait is actually waiting for

**Question:** What is the supported mechanism for waiting on a bot
response (the now-rare opt-in path) or on CI, given `ScheduleWakeup` is
scoped elsewhere and a foreground `sleep` loop is explicitly discouraged by
this project's own Bash-tool guidance — and what should each wait actually
poll for?

**Options considered:**
- **`ScheduleWakeup`** (this session's improvisation) — rejected as the
  documented default. Its own description scopes it to `/loop` dynamic-mode
  self-pacing; using it for a general mid-skill wait works by accident, not
  by contract.
- **Foreground `sleep` loop** — rejected. This project's own Bash-tool
  guidance explicitly discourages long or chained sleeps in the foreground
  and directs polling loops to run in the background instead.
- **`Bash` with `run_in_background: true`, wrapping a bounded shell polling
  loop** — chosen. The invoking agent harness is designed to notify the
  session when a backgrounded process completes, rather than requiring the
  session to poll for it. This is a property of the harness currently
  driving these sessions, not something this LRH repository itself
  documents or can cite in-repo — an implementer on a different
  harness/backend should verify the equivalent notify-on-completion
  behavior exists there before relying on it (see Decision 5's Claude-Code-
  session scoping).

**Chosen, with a predicate correction caught in this PR's own review
(Codex, P2):** a single check-run/CI-state predicate is wrong for a
bot-response wait. `round-cap-gate.md`'s own existing Step 8.2 already
establishes that a reviewer's real response can arrive as a review, an
issue comment, or an inline thread — not only, or even primarily, as a
check-run — and Codex in particular has no check-run signal at all for a
plain-comment response. Polling only check-run/CI state for a bot-response
wait would therefore either wait the full 900 seconds after Codex had
already replied, or wake on an unrelated CI check reaching a terminal
state before the review content was actually available. The design uses
two distinct predicates instead, matched to what each wait is actually
waiting for:

- **Bot-response wait** (Decision 1's opt-in bot path): poll for a
  response matching the retriggered reviewer(s) and the current SHA across
  every surface `round-cap-gate.md`'s existing Step 8.2 already
  recognizes — a new review, a new issue comment from that reviewer, or a
  new inline thread citing the SHA — not check-run state.
- **CI wait**: poll `gh pr checks` (or equivalent) for required-check
  state — the check-run/CI-state predicate is correct here specifically.

**The CI-wait predicate needs a three-way result, not a binary one —
caught in this PR's own review (Codex, P2), verified independently
against `gh pr checks --help` and `gh help exit-codes` before accepting:
`gh pr checks` documents exit code `8` specifically for "Checks
pending," distinct from exit code `1` for a command/check failure and
`0` for success.** A predicate that only breaks the loop on success
(exit `0`) and otherwise keeps sleeping cannot distinguish "still
pending, keep waiting" from "already failed, stop now" — a required
check that fails early would sit in the loop for the full 900 seconds
producing no useful signal, when the real answer was already known. The
CI-wait predicate must check for a terminal failure explicitly and break
the loop on it (reporting failure, not timeout) rather than treating only
exit `0` as a stopping condition. The bot-response predicate does not
need this distinction — a missing response has no equivalent "terminal
failure" state to detect early, only present-or-absent.

Both predicates run inside the same bounded-loop shape, capped at
`round-cap-gate.md`'s existing `STALE_AGE_SECONDS=900` constant rather than
a second, undocumented magic number. `check_predicate` below stands for
whichever predicate command applies (bot-response or CI-state, per the
two bullets above) — a real, valid placeholder function name, not an
angle-bracket token, since `<...>` is shell redirection syntax and would
break exactly the parsing this snippet exists to get right. The poll
interval is its own named constant, not a second bare magic number:

```bash
STALE_AGE_SECONDS=900       # round-cap-gate.md's existing constant
POLL_INTERVAL_SECONDS=30
START=$(date +%s)
while true; do
  if check_predicate; then
    break          # success (bot response present, or CI required-checks green)
  elif [ $? -eq 1 ]; then
    break           # CI-wait only: terminal failure, not pending -- report now,
                     # don't keep sleeping toward the timeout (see note above)
  fi
  if [ $(( $(date +%s) - START )) -ge "$STALE_AGE_SECONDS" ]; then
    echo "no response after ${STALE_AGE_SECONDS}s" >&2
    break
  fi
  sleep "$POLL_INTERVAL_SECONDS"
done
```

Verified with `bash -n` against the literal snippet above, not just the
shape after substitution — it is genuinely valid shell as written, with
`check_predicate` deliberately left undefined (a real, syntactically
legal bash construct: calling a not-yet-defined function), unlike the
angle-bracket placeholder an earlier revision of this section used.

`round-cap-gate.md` and `land-workflow.md` are both updated to name these
two predicates and this loop shape explicitly, in place of today's
unspecified "wait a reasonable amount of time" prose.

### Decision 4: Budget-signal gating is out of scope for automation

**Question:** Should the design attempt to gate the self-review-vs-bot
default on a live credit/budget signal, given the motivating 1/7-credits
data point?

**Chosen: no automated gate.** `round-cap-gate.md` already established, as
a verified fact (not a gap to re-litigate here), that GitHub exposes no
credit/usage API — the exhaustion message only renders in the web UI's
session panel. No automated source for "current bot-review budget" exists
to gate on. When the rare bot-opt-in path (Decision 1) fires, the human is
asked for current budget context live, matching the existing pattern
`round-cap-gate.md`'s three-way gate already uses ("the human supplies
portfolio context... since no automated source for that currently exists
in this project"). This value is never persisted or cached — a stale
cached credit count is worse than asking, since it goes stale within
minutes of any real usage.

### Decision 5: Scope this increment to Claude Code sessions

**Question:** Does self-review-first apply uniformly across every backend
that might run these skills (e.g. a `codex_cloud` agent), or only to
Claude Code sessions?

**Chosen:** scope explicitly to Claude Code sessions for this increment.
`/lrh-self-review`'s dispatch mechanism (the `Agent` tool,
`general-purpose` subagent type) is a Claude-Code-specific primitive. A
backend without an equivalent cold-context subagent-dispatch primitive
falls back to the pre-existing bot-first default until it has one — stated
here as an explicit, named exception, not silently assumed to hold
everywhere. This mirrors `backlog.md`'s already-recorded Codex-adaptation
gaps entry (missing skill-installation paths, Claude-specific execution-
record defaults) rather than inventing a new blind spot.

## Non-Goals

- Does not settle `self_review_preference`'s exact new value-space literals;
  the field is removed by `WI-RETRIGGER-REMOVAL-STAGE1`, so that question is
  no longer active in this proposal.
- Does not touch `PROP-LRH-SELF-REVIEW` Decision 4's guarantee that a PR's
  *first* real bot round (the automatic on-open trigger) is never skipped.
- Does not change `round-cap-gate.md`'s escalation sequence (3 → 10 → 20)
  or its state schema — `completed_count` already counts both round types
  identically.
- Does not build an automated credit/budget-gating mechanism — no API
  exists to gate on (Decision 4).
- Does not extend self-review-first coverage to `/lrh-review-response`,
  which has no bot-retrigger action to gate in the first place
  (`round-cap-gate.md`'s own existing scope note already establishes this).
- Does not extend this default to any backend other than Claude Code
  sessions (Decision 5).
- Does not itself write the `DEC-*` decision-log entry this change implies
  — because this narrows `PROP-LRH-SELF-REVIEW`'s Decision 4 neighborhood
  and `PROP-LRH-CHAIN-DEFAULTS`'s Increment sequencing, both already
  adopted/steelmanned, a dedicated decision-log entry is required before
  implementation lands, per `DEC-AGENT-EXECUTED-MERGE-GATE`'s own precedent
  for narrowing `DEC-DELIBERATE-CHAIN-INITIATION` — tracked as required
  follow-up in the Implementation Plan below, not asserted quietly here.
- Does not implement any code or `SKILL.md` change — this proposal is
  documentation-only, matching this project's proposal/implementation
  separation.

## Implementation Plan

This proposal now feeds only the bounded-poll wait mechanism into future
implementation work. The retained implementation scope is Decision 3:
document and, where needed, implement a bounded background poll with distinct
predicates for CI waits and any future explicitly-authorized review-response
wait. Decisions 1 and 2 require no implementation because Stage 1 removes the
underlying retrigger/profile-field surface.

## Cross-References

- `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md` — the
  mechanism this proposal rewires (Step 8.1, the three-way gate, the
  stalled-session `STALE_AGE_SECONDS` constant reused in Decision 3).
- `src/lrh/skills/lrh-land/references/land-workflow.md` — the
  chain-defaults propose-and-confirm flow and CHAIN-NOTE
  `self_review_rounds`/`bot_rounds` fields this proposal's implementation
  will need to keep consistent with the new default; its "Decision 5 —
  staleness fallback" section is the confirm/staleness gate Decision 2's
  eventual wiring must reuse, with `lrh-confirm-fixes/SKILL.md` and
  `round-cap-gate.md` added to its staleness-diff file list.
- `project/design/proposals/adopted/lrh-self-review/00_proposal.md` —
  Decision 4 and its "later-round skip policy" deferral, which this
  proposal resolves within the scope stated above.
- `project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md` —
  origin of `self_review_preference` and the steelmanning-before-defaults
  practice this proposal's Implementation Plan follows.
- `project/design/backlog.md` — "Self-review-first tier for reducing
  GitHub bot-review credit consumption" entry, Open Question 4.
- `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md` and
  `DEC-AGENT-EXECUTED-MERGE-GATE.md` — precedent for narrowing an adopted
  decision via a dedicated decision-log entry rather than a silent
  proposal-level assertion.

## Open Questions

- Exact `self_review_preference` value-space literals — closed as obviated by
  Stage 1 field removal.
- Whether any periodic or final-pre-merge round should still get a
  mandatory real bot pass for cross-vendor blind-spot coverage, given
  `PROP-LRH-SELF-REVIEW` Decision 4's own rationale that a same-vendor
  subagent pass is "not a blind-spot-equivalent substitute for an
  independent platform reviewer" — deferred to the same steelmanning
  session.
- Whether `/lrh-review-response` should ever gain a bot-retrigger action of
  its own in the future, which `round-cap-gate.md`'s existing scope note
  already flags as a reason to revisit this proposal's boundaries — not
  applicable today, since it has none.

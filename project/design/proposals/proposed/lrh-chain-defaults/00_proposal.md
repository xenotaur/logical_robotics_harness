---
id: PROP-LRH-CHAIN-DEFAULTS
type: design_proposal
title: Persisted, User-Editable Chain-Defaults Profile for LRH Skill Gates
status: proposed
implementation_status: not_started
created_on: 2026-08-05
updated_on: 2026-08-07
related_design:
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - project/work_items/resolved/WI-SKILLS-LRH-SELF-REVIEW.md
  - project/design/proposals/proposed/lrh-land-execute/00_proposal.md
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
parent: null
---

# Persisted, User-Editable Chain-Defaults Profile for LRH Skill Gates

## Summary

Introduces a repo-level, git-tracked chain-defaults profile that LRH's
chain-running skills (`/lrh-land`, `/lrh-execute`, `/lrh-implement`,
`/lrh-confirm-fixes`, `/lrh-review-response`, `/lrh-closeout`) propose,
the user confirms or amends, and future gates reuse as a pre-filled
default — reducing repeated, identical hand-typed answers across
invocations without weakening `DEC-AGENT-EXECUTED-MERGE-GATE` or
`DEC-DELIBERATE-CHAIN-INITIATION`.

## Background / Motivation

The post-PR lifecycle chain requires the user to restate, at every
`/lrh-land`/`/lrh-execute` invocation, answers that rarely change between
runs: a completion condition, a stop-work condition, and — since
`WI-SKILLS-LRH-SELF-REVIEW` (PR #467) — a preference for self-review over
a GitHub bot retrigger to conserve review credit. This session alone
restated the self-review preference verbatim across five separate
invocations. On Codex.app, the same chain surfaces 4-5 confirm points
instead of Claude's 3-4, most of which are no-ops given how rarely the
answer actually varies.

`DEC-DELIBERATE-CHAIN-INITIATION` already establishes that a human may
authorize an entire chain in one deliberate act rather than
re-authorizing each link, and `WI-REVIEW-ROUND-ESCALATION-GATE` (PR
#445) already proved the pattern of a durable, escalating, human-gated
mechanism for one specific gate (`/lrh-confirm-fixes`'s bot-retrigger
ceiling). Neither generalizes today: chain-level answers (completion/stop
conditions, self-review preference) are still re-derived from scratch
each run, and no other gate has an analogous "trust this the same way
next time, unless something's unusual" mechanism.

This needs addressing now because the friction compounds with every new
gate LRH's skill set adds (self-review's fourth round-cap answer is the
latest example), and because restating the same answer by hand is a
process where a copy-paste or memory slip is more likely than genuine
reconsideration — the boilerplate itself becomes a source of error
rather than a safeguard.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation of a persisted cross-gate defaults
  profile. Closest precedent: `WI-REVIEW-ROUND-ESCALATION-GATE` (resolved,
  PR #445) — an escalating human-gated round cap scoped to one gate
  (`/lrh-confirm-fixes`'s bot-retrigger loop), not a general profile.
  `round-cap-gate.md`'s three/four-way gate is a second narrow instance of
  the same class of problem.
- Sibling repos: None identified.
- External libraries: Not applicable — this is specific to LRH's own
  chain-authorization convention.
- Recommendation: Proceed — no duplicate, but two existing mechanisms
  (`WI-REVIEW-ROUND-ESCALATION-GATE`'s escalation shape,
  `round-cap-gate.md`'s durable-state pattern) to build on rather than
  invent from scratch.

### Demand search
- Work items: None found requesting this specific profile.
- Proposals: None found. `PROP-LRH-LAND-EXECUTE` and
  `PROP-LRH-SELF-REVIEW` both introduce gates this profile would cover,
  but neither proposes persisting defaults across invocations.
- Backlog: No matching entries.
- Recommendation: No action; proceed as new.

## Design Decisions

### Decision 1: Storage location and format

Options considered:
- User-global config (e.g. `~/.claude/...`) — doesn't pollute the repo,
  but doesn't transfer across collaborators or machines, and isn't
  visible to a Codex.app session the same way without duplicated
  plumbing.
- Session-only (re-derived each session, not persisted) — no new
  artifact, but doesn't solve the actual friction (re-typing across
  invocations *within* a session already recurs, e.g. this session's
  five `/lrh-land` calls).
- Repo-level, git-tracked file.

**Chosen: repo-level, git-tracked plain YAML** (e.g.
`project/config/chain-defaults.yaml`). Auditable in git history — a bad
default is a visible, revertible commit, not opaque local state; travels
with the repo so every collaborator and both backends see the same
values; consistent with this project's existing convention of storing
decisions as reviewed files rather than machine-flippable config (the
Taurworks "deliberate user permission... not stored in machine-flippable
config" principle `DEC-DELIBERATE-CHAIN-INITIATION` already cites).
Backend-agnostic plain YAML, not a Claude-specific schema.

### Decision 2: Two-tier structure — chain-level vs. per-gate

Options considered:
- A single flat "autopilot: on/off" switch — simplest, but conflates
  unrelated gates and risks silent scope creep (confirm-fixes autopilot
  quietly also covering closeout, which the user never separately
  opted into).
- Fully generic per-gate rule engine (arbitrary predicates configurable
  per gate) — maximum flexibility, but "unusual" is gate-specific
  domain knowledge (what makes a confirm-fixes batch routine differs
  entirely from what makes a closeout plan routine); a generic engine
  either can't express that or reinvents each gate's own logic anyway.
- Two independent tiers: chain-level defaults (completion/stop text,
  self-review preference) and a small named set of per-gate autopilot
  flags, each with its own gate-owned "unusual" predicate.

**Chosen: two independent tiers**, each gate's "unusual" predicate
implemented in that gate's own `SKILL.md`/reference file — mirroring
`round-cap-gate.md`'s existing self-contained, gate-owned state pattern
— rather than a shared rule library.

**Which gates are eligible for the per-gate autopilot tier at all is
narrower than "any gate" — see Decision 3's amendment below.**
`DEC-DELIBERATE-CHAIN-INITIATION` categorically protects merge, publish,
release, and closeout, "nor any skill's internal confirmation gate," from
being satisfied by chain initiation. `/lrh-closeout` Step 4's plan-confirm
gate is explicitly named there as one such gate. `confirm_fixes_batch` has
a direct, already-adopted precedent for reduced asking
(`WI-REVIEW-ROUND-ESCALATION-GATE`'s durable, human-gated-only-at-the-
ceiling round cap) that `closeout_plan` does not — so the two example
flags are not interchangeable candidates for the same treatment.

### Decision 3: Non-negotiable gates stay live every time

Options considered:
- Extend the profile to eventually cover the merge gate, the chain-
  initiation gate, and `/lrh-closeout`'s plan-confirm gate, once trust is
  established.
- Categorically exclude the merge gate (`DEC-AGENT-EXECUTED-MERGE-GATE`),
  the chain-initiation gate, and `/lrh-closeout`'s plan-confirm gate
  (both under `DEC-DELIBERATE-CHAIN-INITIATION`) from any autopilot tier,
  permanently — leaving only gates without an explicit categorical
  protection, and with their own reduced-asking precedent, as autopilot
  candidates.

**Chosen: categorical exclusion, and it is wider than this proposal's
first draft stated.** `DEC-DELIBERATE-CHAIN-INITIATION` names "merge,
publish, release, and closeout" as protected human/policy gates and adds
that chain initiation "never satisfies a skill's own internal
confirmation gate," citing `/lrh-closeout` Step 4's plan-confirm gate by
name as the example. An earlier draft of this proposal listed
`closeout_plan` as an Increment 2 per-gate autopilot candidate alongside
`confirm_fixes_batch` (Decision 2) — that draft contradicted this
already-adopted decision, caught during this PR's own review round.
Fixed: `/lrh-closeout`'s plan-confirm gate is excluded from the autopilot
tier on the same categorical basis as merge and chain-initiation, not
offered as an `auto_unless_unusual` candidate. `confirm_fixes_batch`
remains a legitimate candidate specifically because
`WI-REVIEW-ROUND-ESCALATION-GATE` already established, and this project
already adopted, a durable-state mechanism that reduces asking frequency
at that exact gate without violating the same decision — no equivalent
precedent exists for closeout's plan-confirm gate. The profile changes
*what's pre-filled and how often a gate asks*, never *whether* an
irreversible, chain-starting, or internally-protected action requires a
live, in-session reply. This is a hard boundary, not a tunable default —
consistent with both decisions' explicit "no chain starts itself" /
"authorization requirement is unchanged" invariants.

### Decision 4: Per-invocation override does not silently rewrite the profile

Options considered:
- A live instruction that diverges from the stored default silently
  updates the stored profile going forward.
- A live instruction that diverges only ever applies to that one run;
  the system explicitly offers, at the end of the run, to update the
  stored default to match.

**Chosen: explicit offer, not silent persistence.** Keeps the profile
itself reviewable and intentional — an ad hoc override during a
one-off run should not permanently redefine "reasonable" for every
future run without the user separately deciding that.

### Decision 5: Staleness handling

Options considered:
- Trust a stored per-gate autopilot rule indefinitely, regardless of
  changes to that gate's own skill logic.
- Stamp the profile with the commit/date it was confirmed at; if the
  referenced gate's skill has changed materially since, fall back to
  `always_ask` for that gate and flag it.

**Chosen: stamped staleness fallback.** Prevents an autopilot rule
silently surviving a skill redesign it was never evaluated against —
the same caution `land-workflow.md`'s "Known limitation" notes on other
matching logic warn about elsewhere in this project.

### Decision 6: Chain-initiation gate liveness is itself a configurable field

Added during the design-review steelmanning session `WS-LRH-CHAIN-DEFAULTS`
required before Increment 1 (see Steelmanned Defaults below). The original
five decisions left one gap: does a pre-filled completion/stop-condition
default still require one live confirming reply every chain-authorization
gate, or can it be skipped entirely once a default is stored? Neither
extreme is right.

Options considered:
- Always require a live reply, even with defaults pre-filled — safest, but
  leaves real friction on the table for a skill triggered repeatedly with
  genuinely identical conditions.
- Skip the live reply entirely once any default is stored — removes the
  friction, but conflates "the user once set a default value" with "the
  user has authorized skipping confirmation," which are different acts.

**Chosen: liveness is a separate, explicit, two-step-gated setting.**
`chain_init_confirmation: always_confirm | skip_if_opted_in` is its own
profile field, independent of the completion/stop-condition text and the
self-review preference. Reaching `skip_if_opted_in` requires two separate
affirmative user actions — storing the default values, and a distinct,
explicit opt-in to actually use them without re-confirming — never one
action implying the other. Even in `skip_if_opted_in` mode, a per-run
"special conditions" check runs unconditionally before the gate is
skipped: an unmet `depends_on`, a prior failed or stopped run on the same
PR, uncommitted stray changes, or a target that doesn't match the stored
default's assumptions each force a live gate regardless of the stored
setting. This generalizes Decision 2's gate-owned "unusual predicate"
pattern up to the chain-initiation gate itself.

This does not weaken `DEC-DELIBERATE-CHAIN-INITIATION`'s "no chain starts
itself": the human's own slash-command invocation (`/lrh-land <pr>`, etc.)
remains the deliberate initiation act in every mode. Skipping the
condition-confirmation reply only removes redundant re-typing of a value
already deliberately set and opted into — it does not remove the human
action that starts the chain, and the special-conditions check ensures a
stored setting can't silently paper over a run that actually needs a human
look.

## Non-Goals

- Does not weaken or amend `DEC-AGENT-EXECUTED-MERGE-GATE` or
  `DEC-DELIBERATE-CHAIN-INITIATION` — both remain in force unchanged;
  this proposal only narrows how often other, already-tolerant gates ask.
- Does not implement a generic, reusable rule engine — each gate's
  "unusual" predicate is gate-owned, hand-written logic.
- Does not itself define the concrete default *values* (exact
  completion-condition wording, which gates start in
  `auto_unless_unusual` vs. `always_ask`) — Decision-level shape only;
  see Open Questions.
- Does not cover backends other than Claude.app and Codex.app for this
  proposal's own implementation work — the on-disk profile format itself
  stays backend-agnostic plain YAML (Decision 1); this Non-Goal scopes
  which backends this proposal's own Increment 1/2 work verifies and
  wires up, not a limitation on the format a future third backend could
  read.

## Implementation Plan

Large scope, multi-stage: reference the governing workstream
(`WS-LRH-CHAIN-DEFAULTS`, to be created next) rather than naming
individual work items here. Expected staging, per the escalation
precedent in `WI-REVIEW-ROUND-ESCALATION-GATE`:

1. **Increment 1 — chain-level defaults only**: profile schema, the
   propose-and-confirm flow at `/lrh-land`/`/lrh-execute` Step 2,
   completion/stop-condition and self-review-preference persistence, and
   the `chain_init_confirmation` liveness field (Decision 6) with its
   two-step opt-in and special-conditions check.
2. **Increment 2 — per-gate autopilot**: `confirm_fixes_batch` autopilot
   flag, once Increment 1 has session evidence to steelman what "unusual"
   should mean for that gate (see Open Questions). `/lrh-closeout`'s
   plan-confirm gate is excluded per Decision 3's amendment and is not an
   Increment 2 candidate; if a future proposal wants to revisit that, it
   must do so as an explicit amendment to `DEC-DELIBERATE-CHAIN-INITIATION`
   itself, not as a quiet inclusion in this profile's per-gate tier.

## Steelmanned Defaults

Produced by the design-review steelmanning session `WS-LRH-CHAIN-DEFAULTS`
required as a hard prerequisite before Increment 1 (see that workstream's
exit criteria). These are concrete, well-justified default *values* —
grounded in three consecutive `/lrh-land` runs in the same session that
independently converged on nearly identical wording — not the mechanism
shape decided above. Do not treat any example value in this proposal's
Background section as a proposed default; these supersede it.

- **Completion condition default:** *"PR merged, its execution records
  landed, and any linked work item resolved."* Matches what `/lrh-closeout`
  actually verifies, rather than the looser phrasing improvised across this
  session's runs.
- **Stop-work condition default:** *"Any failing CI check, a reviewer
  finding that isn't Clear-satisfied on re-verification, or an
  ambiguous/refused merge-authorization reply."* Reflects the wording used,
  near-verbatim, across three separate `/lrh-land` invocations in the same
  session — real convergent judgment, not an invented default.
- **Self-review-vs-bot-retrigger preference default:** when
  `round-cap-gate.md`'s ceiling fires, substitute self-review rather than
  requesting a new bot-retrigger ceiling, by default. **Hard guardrail,
  not optional phrasing:** this default must never be read — by a human or
  an agent — as license for unbounded self-review rounds. It fires *only*
  within `round-cap-gate.md`'s existing ceiling mechanism, which still
  requires its own explicit human sign-off to raise past its escalation
  sequence (3 → 10 → 20, per `WI-REVIEW-ROUND-ESCALATION-GATE`). The
  default changes which kind of round gets substituted at an
  already-bounded gate; it does not remove, raise, or bypass the bound
  itself. A self-review-substituted round still counts against
  `completed_count` identically to a bot round (per `round-cap-gate.md`'s
  existing "Gate integration" note) — this default does not create a
  parallel, uncounted review loop.
- `confirm_fixes_batch`'s `auto_unless_unusual` predicate: deliberately
  left **unresolved**, not defaulted, per the Implementation Plan's own
  sequencing — Increment 2 needs real Increment 1 evidence before this is
  steelmanned, not an invented threshold today. Recorded leaning to inform
  that future session, not a decision: auto-continue only if every finding
  is Clear-satisfied on re-verification *and* none carries a P0/P1
  severity badge, since a P1 surfacing at all seems worth a human glance
  even after it's fixed.

## Open Questions

- Whether the per-gate "unusual" predicates should be documented in a
  shared reference table (for discoverability) even though each is
  gate-owned in implementation — deferred to Increment 2 design.
- Whether Codex.app requires any plumbing beyond reading the same YAML
  file, or whether its own invocation path already surfaces
  `project/config/` files identically to Claude.app — needs
  verification during Increment 1.

## Cross-References

- `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
- `project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md`
- `project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md`
- `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`
- `project/work_items/resolved/WI-SKILLS-LRH-SELF-REVIEW.md`
- `project/design/proposals/proposed/lrh-land-execute/00_proposal.md`

---
id: PROP-INVOCATION-AND-GATE-RESET
type: design_proposal
title: Invocation and Gate Reset — Retrigger Removal, Flag Removal, and a Unified Gate Policy
status: proposed
implementation_status: not_started
created_on: 2026-08-09
updated_on: 2026-08-09
related_design:
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/work_items/proposed/WI-DELIBERATE-MODEL-INVOCATION.md
  - project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-2.md
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
parent: null
---

# Invocation and Gate Reset — Retrigger Removal, Flag Removal, and a Unified Gate Policy

## Summary

A seven-stage program that halts GitHub review-bot spend immediately, removes
`disable-model-invocation` fleet-wide in favor of `when_to_use` plus real
confirm gates, then audits and redesigns LRH's accreted human-gate corpus into
one coherent policy carried by the already-shipped chain-defaults mechanism —
validated by dogfooding before normal work resumes across the fleet.

The program's organizing insight is that three separate pathologies have the
same root cause: safety controls were added as *mechanisms* (a frontmatter
flag, a retrigger ceiling, a per-skill confirm gate) where the project needed
*policy*, and each accreted independently until they began contradicting one
another and defeating the outcomes they were meant to protect.

## Background / Motivation

Three distinct, simultaneous failures motivated this proposal, all observed in
live operation across LRH and sibling repositories (LCATS, PROSOC, Replication
Vector, Velumin) and across three agent harnesses (Claude Code, Codex,
Antigravity).

### 1. Uncontrolled review-bot spend

GitHub review-bot usage moved from 6/7 to 8/7 of budget in a single day —
real overspend — driven by sessions that had explicitly agreed not to
retrigger bot reviews and then retriggered anyway, repeatedly, including after
acknowledging the lapse. `project/design/backlog.md`'s "Self-review-first tier
for reducing GitHub bot-review credit consumption" entry (noted 2026-08-01)
already identified the structural half of this: the `round-cap-gate.md`
mechanism *"bounds how many retriggers happen … but does not reduce how often
a retrigger is actually necessary in the first place."*

Guidance alone demonstrably did not hold. The mechanism must change.

### 2. `disable-model-invocation` blocking legitimate invocation

Per Anthropic's documentation ("Control who invokes a skill"),
`disable-model-invocation: true` means *"Only you can invoke the skill"* — and
Claude Code *"blocks the call and instructs it not to reproduce the [skill's]
steps another way."* The flag blocks every invocation route except a bare
user-typed `/command`, including:

- one skill's instructions invoking another (which is why `/lrh-land` and
  `/lrh-execute` inline their sub-workflows rather than calling them);
- a user naming the skill mid-sentence in a compound instruction;
- a skill offering itself, with the user accepting.

These are most of how skills are actually invoked. `WI-DELIBERATE-MODEL-INVOCATION`
already recorded two incidents where the flag blocked a user's own explicit,
in-session request, and resolved to move enforcement to guidance plus gates
for 9 of 13 flagged skills — leaving 4 flagged pending specific gaps. The
practical result is stochastic: the same skill works in one session and is
blocked in the next, requiring per-command babysitting.

### 3. Confirmation fatigue defeating the gates themselves

Sessions degraded into repeated near-no-op confirmations: the same
completion/stop-condition pair re-elicited every run; obviously-correct
trivial review fixes re-confirmed individually; and a "merge it?" question
followed immediately by a separate "close it out?" question.

The merge/closeout pair is the clearest case of asking one question twice.
`project/config/chain-defaults.yaml`'s own steelmanned completion condition
defines done as a single unit — *"PR merged, its execution records landed, and
any linked work item resolved"* — and `/lrh-land` Step 7 (Closeout) is an
unconditional chain step, not a branch point. A chain that merges without
closing out has not met its completion condition; it is unfinished, not
awaiting a fresh decision.

This is a safety problem, not merely an ergonomic one. Parasuraman & Riley
("Humans and Automation: Use, Misuse, Disuse, Abuse," *Human Factors* 39(2),
1997) establish that poorly-calibrated automation prompts produce both
over-reliance and habituated dismissal. A gate asked so often that answering
becomes reflexive has stopped functioning as a control. Worse, a user who
steps away after answering what they believed was the final question can
return to find the work paused mid-flight on a second, essentially identical
question.

### 4. The defaults mechanism exists but has never been able to fire

`WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` shipped the chain-defaults profile, the
propose-and-confirm flow, and both `chain_init_confirmation` modes. Inspection
of live repository state found it dormant for **three independent reasons,
each sufficient on its own**:

| # | Blocker | Evidence |
|---|---|---|
| 1 | Shipped mode is `always_confirm` | `project/config/chain-defaults.yaml` |
| 2 | Skip consent never granted | `git config --local --get lrh.chainDefaults.skipConsentHash` → unset |
| 3 | Stored confirmation already stale | Decision 5 watch list diffs dirty against `confirmed_commit` `e4a1a34` today |

The repeated condition-asking is therefore a **built mechanism that has never
been placed in a firing state**, not a missing capability. This materially
changes the cost of fixing it.

### 5. The gate corpus has accreted contradictions

Normative gate language is now spread across 28 skill files under
`src/lrh/skills/` (plus their `.claude/skills/` mirrors), five decision
records, several proposals, `AGENTS.md`, `project/roadmap/roadmap.md`, and
per-repo agent memories. Some of it is categorical and mutually constraining:
`DEC-DELIBERATE-CHAIN-INITIATION` principle 1 states chain initiation *"does
not pre-authorize the human/policy gates — merge, publish, release, and
closeout — nor any skill's internal confirmation gate,"* and
`PROP-LRH-CHAIN-DEFAULTS` Decision 3 excludes `/lrh-closeout`'s plan-confirm
gate from any autopilot tier *"permanently."*

Each statement was reasonable when written. The pathology is emergent from
accretion, which is why per-gate incremental amendment cannot fix it — that is
the mechanism that produced it.

## Prior Art Check

### Duplication search

- **In-repo:** No existing gate-policy audit, gate inventory, or gate-policy
  proposal. Adjacent artifacts are complementary, not duplicative:
  `WI-DELIBERATE-MODEL-INVOCATION` covers Stage 2 partially (9 of 13 skills
  completed in PR #533); `WS-LRH-CHAIN-DEFAULTS` owns the defaults *mechanism*
  this proposal uses as substrate; `PROP-CONSTITUTIONAL-SANDBOX-ENVELOPE`
  governs a *different layer* — what LRH's own code may execute under a
  capability policy for future autonomous agents — rather than human-confirmation
  ergonomics inside skills.
- **Sibling repos:** Taurcode (`/Users/centaur/Workspace/Taurcode/taurcode`)
  maintains `:land` / `:execute` prompts that `DEC-DELIBERATE-CHAIN-INITIATION`
  names as this policy's expression. **Not inspected**; whether it falls in the
  Stage 3 cascade scope is an open question below.
- **External libraries:** None identified. This is repository-specific
  governance text, not a library-shaped problem.
- **Recommendation:** Proceed.

### Demand search

- **Backlog:** Found — `project/design/backlog.md`, "Self-review-first tier for
  reducing GitHub bot-review credit consumption" (noted 2026-08-01, promoted to
  its own entry 2026-08-02). Satisfied by Stage 1.
- **Work items:** Found — `WI-DELIBERATE-MODEL-INVOCATION` (Stage 2 completes
  it); `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` (is Stage 4, and is already owned by
  `WS-LRH-CHAIN-DEFAULTS`); `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` (inherits
  this policy).
- **Proposals:** Found — `PROP-LRH-CHAIN-DEFAULTS` (governing design for Stages
  3–4); `PROP-REVIEW-WAIT-POSTURE` (open on PR #522, unmerged, partially
  obviated by Stage 1 — needs a disposition decision).
- **Recommendation:** Link, do not auto-close. Offer the backlog entry and
  `WI-DELIBERATE-MODEL-INVOCATION` for closure as their satisfying stages land.

## Design Decisions

### Decision 1: Provisional-then-canonical sequencing

**Options considered:**

- Block Stages 1–2 until the Stage 3 gate policy exists, so every mechanism
  installed is policy-derived from the start.
- Ship Stages 1–2 with permanent bespoke mechanisms, and let Stage 3 work
  around whatever they established.
- Ship Stages 1–2 with narrow, explicitly-labelled **provisional** mechanisms
  that Stage 3 supersedes by design.

**Chosen: provisional-then-canonical.** Stages 1 and 2 each require a gate or
cap decision that is properly Stage 3's job, creating a circular dependency.
Blocking forfeits the incident-response benefit while real money is being
spent; shipping permanent bespoke mechanisms guarantees rework and drift.

Each provisional mechanism therefore carries an inline marker naming the stage
that supersedes it. This mirrors `WI-REVIEW-ROUND-ESCALATION-GATE`'s own
established precedent — prove the mechanism narrow before widening it — which
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` already inherits.

Ordering Stage 1 before the audit deliberately inverts "root-cause before fix."
That is correct here: an active cost incident is in progress, and standard
incident practice (Beyer et al., *Site Reliability Engineering*, O'Reilly 2016,
Ch. 14) treats mitigation as prior to diagnosis.

### Decision 2: Retrigger removal is unconditional, with a provisional cap retained

**Options considered:**

- Remove manual retrigger entirely, with no cap on what replaces it.
- Remove manual retrigger, and retain a cap on the replacement review path.
- Keep retrigger available but default it off behind an explicit ask.

**Chosen: remove unconditionally, retain a provisional cap.** Guidance-level
prohibition has already failed repeatedly in live operation, so the capability
must leave the skill rather than be discouraged within it.

However, removing the cap along with the retrigger would be a mistake. The
original round-cap gate existed to bound *unproductive review loops*, not only
credit spend — PR #442 drove 14 rounds. A cold-context self-review subagent has
no GitHub credit cost but is not free: an unfixable, design-flawed PR can
absorb 15–25 self-review passes just as readily, with the cost shifted to
subagent tokens and, more importantly, to a human never being pulled in to say
"this needs a different approach."

**Escape hatch: manual-only, outside the skills** (resolved 2026-08-09). A
user-requested retrigger remains possible, but the commands live in
documentation rather than in any skill's workflow. The reasoning is that
guidance-level prohibition demonstrably failed — sessions agreed not to
retrigger and then did, repeatedly — so the capability must leave the automated
path, which is where the failures occurred. It is not removed from the project's
vocabulary, because an externally-visible action of this kind is properly
"ask the human first," not "never." Keeping it in-skill behind a prompt was
rejected: that reinstates the exact surface that produced the overspend.

### Decision 3: `disable-model-invocation` is removed fleet-wide, including chain runners

**Options considered:**

- Retain the flag on chain runners (`/lrh-land`, `/lrh-execute`) per
  `WI-DELIBERATE-MODEL-INVOCATION`'s tier 3a.
- Remove from `/lrh-land` only, retaining it on `/lrh-execute` as the
  top-level entry point.
- Remove fleet-wide, with `when_to_use` and confirm gates carrying enforcement.

**Chosen: remove fleet-wide.** The platform mechanism does not distinguish
"top-level chain runner" from "internal skill" — it is the same binary block
either way — so an asymmetry between `/lrh-land` and `/lrh-execute` would be a
risk-tolerance choice rather than a technical distinction, and would invite a
future session to "fix" the inconsistency by reverting it.

`/lrh-land` in particular must lose the flag: it is routinely invoked as part of
a compound instruction ("`/lrh-proposal` that idea, then `/lrh-land` it"), which
the flag blocks.

This is consistent with OWASP's *Excessive Agency* risk (LLM08 in the 2023 Top
10 for LLM Applications; renumbered LLM06 in 2025), whose control is permission
scoping and human approval on consequential actions — not blocking invocation
routes. It is also consistent with this repository's own authoring guidance,
which already states that the confirm-before-write gate *"is what actually
protects against an unwanted write — not `disable-model-invocation`."*

**Two gaps must close in the same change, not after it:**

1. `/lrh-self-review`'s diff-mode currently applies fixes directly to the
   working tree with no confirm step.
2. Removing the flag makes a skill subagent-preload-eligible (Anthropic docs:
   the flag *"[a]lso prevents the skill from being preloaded into subagents"*),
   while `/lrh-self-review` itself dispatches a subagent — a plausible recursion
   path that would be an unforced error immediately after a stage dedicated to
   bounding runaway spend.

### Decision 4: `/lrh-self-review` diff-mode becomes report-only by default

**Options considered:**

- Add a confirm-before-write gate to diff-mode, matching every other LRH skill.
- Make diff-mode report-only by default, with an explicit `--apply` opt-in.

**Chosen: report-only by default.** Adding a confirm gate would close the safety
gap but add a prompt to the one path that currently flows without one —
directly against this proposal's own confirmation-fatigue goal. A non-writing
default closes the gap with no prompt at all, leaving the invoking skill to
decide whether to apply.

This is the rare case where the safety and ergonomic objectives do not trade
off, and it should be taken.

### Decision 5: The recursion guard is platform-enforced, not advisory

**Options considered:**

- Prompt-level instruction forbidding recursive self-review invocation.
- Platform-enforced tool restriction (`disallowed-tools`) on the dispatched
  subagent.

**Chosen: platform-enforced.** The demonstrated failure mode this entire
proposal responds to is agents agreeing to a constraint and then violating it
anyway. Advisory guidance is not adequate for a cost-bearing loop. The actual
preload behavior must be *verified* rather than assumed —
`WI-DELIBERATE-MODEL-INVOCATION` already carries an acceptance criterion for
exactly this verification that has never been executed.

### Decision 6: Stage 3 emits three artifacts — audit, proposal, and decision record

**Options considered:**

- A single superseding decision record naming what it overrides.
- A proposal alone, with skills updated to match.
- Audit artifact → policy proposal → decision record → cascade.

**Chosen: all three.** The goal contains a completeness claim — revisit *every*
place the corpus states a categorical gate rule — and only an inventory makes
that claim checkable rather than asserted. A proposal alone cannot amend a
decision record: `PROP-LRH-CHAIN-DEFAULTS` required `DEC-CHAIN-INIT-SKIP-CONSENT`
as a separate output, produced by its own work item
`WI-DEC-CHAIN-INIT-SKIP-AMENDMENT`. Without the decision record, the governing
documents keep stating the superseded rule and a future session will reasonably
follow them.

**Authority basis.** This is an amendment along a path the governing decision
designed, not an override of it. `DEC-DELIBERATE-CHAIN-INITIATION`'s own
Revisit conditions open with: *"CHAIN-NOTE evidence shows single-cycle chains
frequently need mid-run human intervention, or shows the merge gate is never
load-bearing (either would change where the gates belong)."* The second
disjunct was marked met on 2026-07-30, producing `DEC-AGENT-EXECUTED-MERGE-GATE`.
The first disjunct is met by current operating experience and has never been
actioned.

**Cascade taxonomy.** `DEC-AGENT-EXECUTED-MERGE-GATE`'s Consequences section is
adopted verbatim as the template, including the correction it documents:
adopted proposals are **updated in place** (per
`project/design/proposals/README.md`'s lifecycle contract), execution records
are **immutable** (historical accounts, not standing governance), resolved work
items are **left untouched**, and cross-repository agent memories are
**corrected, not left stale** — that record found two LCATS memory files
codifying a superseded rule as a hard instruction.

### Decision 7: The merge and closeout questions become one ask, with closeout still post-merge

**Options considered:**

- **(A)** Keep both asks; accept the double-invocation.
- **(B)** Compute closeout content and commit it to the PR branch pre-merge, so
  a single merge event does both.
- **(C)** Present the merge command together with a full closeout plan; a single
  live reply authorizes both; execute merge, then closeout, in sequence;
  surface genuine post-merge divergence as an alert rather than a re-ask.

**Chosen: (C).** Option (B) is disqualified by two hard, independent structural
blockers:

1. **Circular dependency on the merge commit.** `/lrh-closeout` writes execution
   records with `--commit <merge-commit-sha>`. Under merge-commit strategy —
   this repository's confirmed practice — the merge commit is *created by* the
   merge and does not exist beforehand.
2. **It would break the SHA lock it depends on.** `/lrh-land` merges with
   `--match-head-commit <sha>`, whose stated purpose is preventing a merge of a
   newer unchecked commit. Pushing a closeout commit to the PR branch moves
   `HEAD`, so the locked merge command would fail by design — the same hazard
   the round-state branch mechanism was built to avoid.

Option (C) satisfies the requirement because a genuine failure ("I merged, but
closeout hit X") is an **alert about a new condition**, not the same question
asked twice. Most post-merge divergence needs no question at all: if the actual
merge commit differs from what was anticipated, the correct behavior is to read
and use the real value.

**This does not remove the closeout gate; it improves it.** Under (C) the human
approves the actual closeout plan rather than a description of one, in the same
reply that authorizes the merge. That distinction matters and must be stated
explicitly in the amending decision record — conflating "ask once" with "don't
ask" is precisely the error an earlier draft of `PROP-LRH-CHAIN-DEFAULTS` made
and had corrected in review.

### Decision 8: Activation of the defaults mechanism is a distinct, late stage

**Options considered:**

- Activate `skip_if_opted_in` early, since the mechanism already exists and
  dormancy is the immediate cause of repeated asking.
- Activate only after the Stage 3 policy defines a compensating control.

**Chosen: activate late, as an explicit Stage 3.5.** Activating skip mode while
Stages 1–2 remove `disable-model-invocation` from the chain runners recreates
precisely the tier-3a gap `WI-DELIBERATE-MODEL-INVOCATION` identified: under
`skip_if_opted_in` with valid stored consent, a model-initiated invocation could
ride that consent through the chain-authorization gate with no live human reply.

Activation is cheap but order-dependent. It is a deliberate two-step human act
by design (`DEC-CHAIN-INIT-SKIP-CONSENT` requires two separate affirmative
actions, with consent stored user-locally and never in the git-tracked profile),
and that property must be preserved — the shipped default must not become
`skip_if_opted_in`, since a git-tracked default would make every fresh clone
pre-opted-in from a single commit rather than a local human act.

### Decision 9: The staleness watch list is redesigned semantically, not extended

Inspection found Decision 5's watch list wrong in **both** directions:

- **Over-watch (file-granular).** The list watches whole `SKILL.md` files, so a
  typo fix invalidates stored consent identically to a gate redesign — making
  the mechanism self-defeating during exactly the active-development period
  Stages 1–4 constitute.
- **Under-watch (verified).** `/lrh-land` inlines `/lrh-confirm-fixes`,
  `/lrh-review-response`, and `/lrh-closeout` — all gate-bearing — and **none**
  is on the watch list. A real gate change in any of them, including Decision
  7's own `closeout_with_merge` behavior, would not invalidate consent even
  though it materially changes what the human consented to.

**Chosen: watch gate *definitions* semantically rather than extending the file
list.** Extending the list is a one-line fix that leaves the over-watch flaw
intact and requires re-extension whenever a skill is added. The semantic
approach requires defining what constitutes a gate definition — which Stage 3's
audit must produce anyway, making it a byproduct rather than extra cost.

### Decision 10: Ownership splits between two workstreams

**Options considered:**

- One umbrella workstream owning all seven stages.
- Split: a new reset workstream, with defaults-mechanism work staying under
  `WS-LRH-CHAIN-DEFAULTS`.

**Chosen: split.** `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` already exists and is
listed in `WS-LRH-CHAIN-DEFAULTS`'s own `work_items:` field. A workstream's
`work_items:` denotes ownership, not cross-reference, so claiming it would
create duplicate ownership.

| Owner | Scope |
|---|---|
| `WS-INVOCATION-AND-GATE-RESET` (new) | Stages 1, 2, 3, 3.5, 5, 6, 7 |
| `WS-LRH-CHAIN-DEFAULTS` (existing) | Stage 4 — Increment 2, plus a new Increment 3 for policy-derived profile fields |

Related via `related_workstreams:`, not folded. This follows
`DEC-DELIBERATE-CHAIN-INITIATION`'s own Alternatives #3, which rejected folding
into `WS-EXECUTION-FRAMEWORK` because *"folding re-conflates the two axes this
decision exists to separate. Cross-link instead."*

## Non-Goals

- **Does not change control-plane precedence.** `DEC-PRECEDENCE-SEMANTICS`
  governs resolver precedence (principles → goal → roadmap → focus → work items
  → guardrails → runtime), a different axis from human-confirmation gates. No
  change to `src/lrh/control_plane/precedence.py` is implied.
- **Does not weaken merge authorization.** Merging still requires explicit,
  in-session human authorization per `DEC-AGENT-EXECUTED-MERGE-GATE`. Decision 7
  changes how many times the human is asked, not whether authorization is
  required.
- **Does not implement autopilot for the closeout gate.** Decision 7 is
  single-ask, not no-ask. `PROP-LRH-CHAIN-DEFAULTS` Decision 3's exclusion of
  `/lrh-closeout` from the *autopilot tier* is narrowed in form, not abandoned.
- **Does not make `skip_if_opted_in` the shipped default.** The two-step
  human consent requirement of `DEC-CHAIN-INIT-SKIP-CONSENT` is preserved
  intact.
- **Does not rewrite historical records.** Execution records and resolved work
  items remain immutable per the cascade taxonomy in Decision 6.
- **Does not resolve the round-cap gate's final shape.** Stage 1 installs a
  provisional cap; the canonical replacement is Stage 4 scope, informed by real
  post-Stage-1 evidence.
- **Does not itself execute cross-repository changes.** LRH's planning artifacts
  govern this repository. Sibling-repo and Taurcode cascade steps are specified
  here as a runbook but executed per-repo by hand.

## Implementation Plan

Staged delivery. Stages 1 and 2 are independent (they share no files) and may
proceed in parallel or either order; Stage 3 follows both so the corpus it
audits is smaller and stabler.

| Stage | Deliverable | Owner |
|---|---|---|
| **1** | Retrigger removal; provisional self-review round cap; PR #522 disposition; `self_review_preference` cleanup; `confirmed_commit` re-stamp | new WS |
| **2** | Flag removal ×4; `when_to_use` ×4; `/lrh-self-review` report-only default; platform-enforced recursion guard; preload verification; `confirmed_commit` re-stamp | new WS |
| **3** | Gate corpus audit artifact → policy proposal → DEC record → cascade; includes Decision 9's staleness redesign and Decision 7's shape | new WS |
| **3.5** | Activation: set `chain_init_confirmation`, grant two-step consent, stamp — under Stage 3's compensating control | new WS |
| **4** | `confirm_fixes_batch` predicate (Increment 2); Increment 3 policy-derived fields including `closeout_with_merge` | `WS-LRH-CHAIN-DEFAULTS` |
| **5a** | Low-stakes LRH-internal dogfood | new WS |
| **5b** | Session and PR triage: related × go/no-go across open PRs and live sessions | new WS |
| **6** | Feed dogfood findings back into Stages 1–4 | new WS |
| **7** | Resume normal fleet operation | new WS |

**Sequencing constraints:**

- Stages 1 and 2 each edit files on the Decision 5 staleness watch list, so each
  must close with a `confirmed_commit` re-stamp or the program will *increase*
  asking while it runs.
- Deleting the dead `self_review_preference` field changes the profile's blob
  hash, invalidating any consent granted against it — so field cleanup must land
  **before** Stage 3.5 activation, not after.
- Before rewriting `round-cap-gate.md`, recover the original from git history.
  It documents eight distinct correctness bugs found across eight review rounds
  (worktree-path parsing, branch fast-forwarding, default-branch hard-coding,
  concurrent force-removal safety, cross-tenant branch-name collisions,
  Conventional Commits compliance, `stat` portability, `pipefail` semantics, and
  concurrent-push races). That knowledge must survive any replacement mechanism.

**Review-size discipline.** The exploratory change that motivated this proposal
spans +301/−2007 lines across 17 files. Cohen et al. (*Best Kept Secrets of
Peer Code Review*, SmartBear/Cisco) find review defect-detection effectiveness
degrades sharply past roughly 200–400 changed lines, and skill files are prose
and bash with no automated test backstop. Each stage should land as its own
reviewable PR rather than as a combined change.

**Dogfood target.** Stage 5a deliberately uses low-stakes LRH-internal work
before Stage 5b touches urgent LCATS/PROSOC work, so that policy defects delay
only expendable work. This follows `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`'s own
inherited precedent of proving a mechanism narrow before widening it.

## Open Questions

**Resolved 2026-08-09:**

- **Retrigger escape hatch → manual-only, outside the skills.** Recorded in
  Decision 2 above.
- **`PROP-REVIEW-WAIT-POSTURE` (PR #522) → rescope.** Its Decision 1 (invert
  Step 8's default review mechanism) and Decision 2 (wire
  `self_review_preference` into `round-cap-gate.md`) are obviated by Decision 2
  here: with manual retrigger removed there is no default to invert, and the
  `self_review_preference` field is deleted in Stage 1. Its **Decision 3 —
  a bounded background poll with predicates matched to what each wait is
  actually waiting for — is fully independent and retained**, since waiting for
  CI is unaffected by who performs the review. Its Decisions 4 and 5
  (budget-signal gating out of scope; scope limited to Claude Code sessions)
  survive as non-goals. Rescope that PR to Decision 3 rather than closing it.

**Still open** — these require information or judgment the design cannot supply:

1. **Provisional cap threshold.** What count of no-progress review rounds should
   trip the Stage 1 gate? The recommendation is **3**, inheriting the only value
   with in-repo precedent: the retired mechanism's own default ceiling sequence
   was 3 → 10 → 20, and that reference explicitly declined to compute further
   defaults ("no formula — 30, 40, or doubling are all equally plausible and
   none is grounded"). Confirm or override.
2. **Taurcode scope.** Are Taurcode's `:land` / `:execute` prompts inside the
   Stage 3 cascade, or tracked as separate downstream work? Recommendation:
   tracked separately as a named handoff — `taurcode` carries the same gate
   policy (and an identical contributor registry), but LRH's planning artifacts
   do not govern it.
3. **Triage capacity.** Recommendation: the **8 related** open PRs (skills,
   gates, review, closeout, work-items), not all 13. Of the 5 unrelated, three
   are stale "⚡ Bolt" traversal-optimization PRs (#403, #426, #474) better
   triaged as a separate sweep.

## Cross-references

- `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md` — principles 1
  and 2; Revisit conditions supply this proposal's amendment authority.
- `project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md` — the two-step
  consent contract preserved by Decision 8.
- `project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md` — merge
  authorization unchanged by Decision 7; its Consequences section is the
  cascade template adopted in Decision 6.
- `project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md` —
  Decision 3's categorical exclusion, narrowed in form by Decision 7.
- `project/work_items/proposed/WI-DELIBERATE-MODEL-INVOCATION.md` — Stage 2
  completes its remaining scope.
- `src/lrh/skills/_shared/chain-defaults.md` — the mechanism Decisions 8 and 9
  activate and repair.

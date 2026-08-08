---
resolution: null
blocked_reason: null
blocked: false
id: WI-DELIBERATE-MODEL-INVOCATION
title: Formalize deliberate model invocation and chain-runner record hygiene
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - promote_reference_skills
acceptance:
  - flag-vs-guidance enforcement of "no chain starts itself" is decided and recorded (resolved 2026-08-08 -- per-skill tiering, guidance-enforced for all 13 skills)
  - chain-runner invocation mechanics (invoke flagged links vs. inline) are decided
  - CHAIN-NOTE placement is resolved against the immutable-narrative rule
  - find-or-backfill is normalized in the lifecycle guidance
  - each skill's disable-model-invocation setting is removed and when-to-use guidance is tiered per the Design Decision, in both src/lrh/skills/ and .claude/skills/
  - each tier-2/3 skill's confirm-before-write or chain-authorization gate placement is audited, not assumed, before the flag is removed
  - installer.py subagent-preload behavior after flag removal is verified as intended
  - DEC-DELIBERATE-CHAIN-INITIATION.md carries a dated addendum resolving point 2, cross-linked to this WI
required_evidence:
  - manual_review
artifacts_expected:
  - documentation
---

## Summary

Resolve the chain-runner mechanics that `DEC-DELIBERATE-CHAIN-INITIATION`
deferred: where the "no chain starts itself" guarantee is enforced, how a chain
runner invokes lifecycle links, where a run's `CHAIN-NOTE` lives without
violating record immutability, and how record-less PRs are handled — then
cascade the resolutions into skill guidance.

## Problem / Context

`DEC-DELIBERATE-CHAIN-INITIATION` (PR #417) permitted human-initiated chains but
left three mechanics open, all surfaced while dogfooding Taurcode `:land` on that
very PR:

1. **`disable-model-invocation` is a blunt instrument** — it blocks both
   implicit auto-chaining (unwanted) and human-initiated chaining (now wanted).
   Observed cross-repo inconsistency: a chain runner invokes lifecycle subskills
   where they lack the flag and stalls where they carry it (currently
   `lrh-work-item`/`proposal`/`workstream` lack it; the execution/lifecycle
   skills carry it).
2. **`CHAIN-NOTE` vs. immutable narrative** — appending a `CHAIN-NOTE` to an
   existing record's `# Result` at land time conflicts with
   `project/executions/README.md`'s rule that narrative bodies are immutable.
3. **find-or-backfill** — a PR authored outside the skill chain can reach merge
   with no record; the runner must find the review-round record or create an
   honest post-hoc backfill, never rewriting a narrative.

*Prior-art check.* Duplication: none — `WI-SKILLS-PLANNING-SKILLS-COMPOSABLE`
(made planning skills model-invocable) and `WI-SKILLS-NEXT-STEP-CHAIN` (the
lifecycle chain) are related but do not cover these mechanics. Demand:
established — `DEC-DELIBERATE-CHAIN-INITIATION`'s Consequences explicitly defers
this work.

## Design Decision (recorded 2026-08-08, via `/lrh-design`)

Two incidents forced this from "deferred" to "decided": `disable-model-invocation`
blocked `/lrh-land` when a user named it mid-sentence in a compound instruction
("...and land the WI via `/lrh-land`"), and separately blocked `/lrh-design`
after the model correctly matched intent, with Claude Code's documented block
behavior (see `code.claude.com/docs/en/skills#control-who-invokes-a-skill`)
instructing the model not to reproduce the workflow another way — so the
model complied and simply refused a legitimate, explicit request. Both trace
to the same root cause: the flag is a binary *mechanism* (can the Skill tool
fire at all) doing the job of a *policy* question (should this chain run right
now, with what bounds) that LRH already answers elsewhere — the confirm-before-write
gate (per `lrh-work-item-workflow.md`'s already-adopted reasoning, OWASP LLM08)
and, for chain runners, the chain-authorization gate
(`feedback_chain_auth_before_automated_links`: Step 1 assess state → Step 2
elicit completion + stop-work conditions → Step 3+ automated links).

**Decision: mechanic 1 (flag vs. guidance) resolves to per-skill tiering, not
a blanket flip** — enforcement moves from the flag to guidance across *all*
tiers, including chain runners, because the guardrail that actually matters
for chain runners (the chain-authorization gate) does not depend on the flag
and fires regardless of invocation route:

| Tier | Skills | What already enforces safety without the flag |
|---|---|---|
| 1 — read/analyze only | `lrh-design`, `lrh-doc-audit` (analysis branch) | Nothing writes until Step 4's offer-and-wait |
| 2 — writes/PRs, gated | `lrh-create-skill`, `lrh-implement`, `lrh-doc-organize`, `lrh-doc-work`, `lrh-review-response`, `lrh-confirm-fixes`, `lrh-readiness`, `lrh-self-review` | Existing confirm-before-write gate |
| 3 — chain runners / commits to `main` / resolves or closes control-plane state | `lrh-land`, `lrh-execute`, `lrh-closeout` | Existing chain-authorization gate (Step 1/2) plus the hard-preserved merge/publish/closeout gates `DEC-DELIBERATE-CHAIN-INITIATION` does not let any chain skip |

Tier 3's `when_to_use` gets an explicit chain-authorization clause (invocation
by any route still stops at Step 2 for completion + stop-work conditions),
which is what makes the `/lrh-land` incident survive the flag's removal: the
call now succeeds, but still cannot proceed past the gate without the human
answering it.

**Gate audit required before the frontmatter pass, not assumed:** confirm each
tier-2/3 skill's confirm/chain-auth gate genuinely fires *before* its first
side-effecting step (this WI's acceptance criteria below make this an explicit
checklist item — do not treat the tier table above as self-certifying).

**Decision: chain-runner invocation mechanics stay inlined, unchanged by the
flag removal.** Removing the flag makes flagged links `Skill()`-callable again,
but `lrh-land` and `lrh-execute` already inline their sub-workflows rather than
invoking them (per `lifecycle-chain.md`'s consuming-sites table: `lrh-land`
"runs Steps 4–7... internally," `lrh-execute` "inlines `/lrh-implement` Step 9 +
inlined `/lrh-land`'s full Steps 1–8"). The flag removal doesn't require
changing this — it only means the choice to inline is now a design preference
(keeps chain runners self-contained and independently testable) rather than a
platform-forced workaround. No implementation change to the inlining pattern
itself; `lifecycle-chain.md`'s description of *why* it inlines should drop the
now-obsolete "because the flag blocks invoking them" rationale.

**Decision: mechanics 2 (CHAIN-NOTE) and 3 (find-or-backfill) are
documentation-normalization, not new design.** Both patterns already exist in
practice — CHAIN-NOTE lands in a fresh record's own body (the "found primary →
new `_CLOSEOUT_NOTE`" pattern already in `lrh-land/SKILL.md:421`), never
appended to an existing immutable narrative; find-or-backfill is already
specified in `lifecycle-chain.md`'s "Record-less PRs and chain runners"
section. Scope them into the same implementation pass as mechanic 1 since they
touch the same files (`_shared/lifecycle-chain.md` and the skill bodies) and
this WI's acceptance criteria already bundle all three.

## Scope

Cascade the tiering decision above into `src/lrh/skills/_shared/lifecycle-chain.md`,
each affected skill's `disable-model-invocation` setting and `when_to_use`
guidance, the stale flag-first authoring guidance in `lrh-create-skill`'s
references, `installer.py`'s subagent-preload behavior (verify, don't
silently accept, that removing the flag makes all 13 preload-eligible),
`DEC-DELIBERATE-CHAIN-INITIATION.md` (dated addendum, not a rewrite — resolve
point 2), and `project/executions/README.md` (CHAIN-NOTE placement,
normalizing the existing pattern above).

## Required Changes

- Per the Design Decision above: remove `disable-model-invocation: true` from
  all 13 flagged skills (`lrh-closeout`, `lrh-confirm-fixes`, `lrh-create-skill`,
  `lrh-design`, `lrh-doc-audit`, `lrh-doc-organize`, `lrh-doc-work`,
  `lrh-execute`, `lrh-implement`, `lrh-land`, `lrh-readiness`,
  `lrh-review-response`, `lrh-self-review`), add/extend `when_to_use` per the
  tier templates, in both `src/lrh/skills/` and the `.claude/skills/` mirror.
- Audit each tier-2/3 skill's confirm-before-write or chain-authorization gate
  placement before relying on it (do not assume the tier table is correct —
  verify).
- Update `_shared/lifecycle-chain.md`'s now-false claim that "most
  execution/lifecycle skills carry `disable-model-invocation: true`... so the
  model cannot auto-trigger them" to describe the tier/gate model instead.
- Rewrite the stale `disable-model-invocation`-first guidance in
  `lrh-create-skill/references/{lrh-skill-pattern.md,frontmatter-guide.md,worked-example.md}`
  so new skills don't reintroduce this bug.
- Add a dated addendum to `DEC-DELIBERATE-CHAIN-INITIATION.md` resolving point
  2 with the tiering decision, cross-linked to this WI.
- Resolve the `CHAIN-NOTE` home per the Design Decision (fresh record's own
  body, never an append to an existing immutable narrative) and normalize
  find-or-backfill guidance already specified in `lifecycle-chain.md`.
- Verify `installer.py`'s subagent-preload behavior after the flag removal
  (all 13 become preload-eligible; confirm this is intended, matching the
  already-adopted `lrh-work-item` "Preloading into forked subagents"
  precedent).

## Non-Goals

- Do not promote `/lrh-execute` / `/lrh-land` skills (downstream, after this
  lands).
- Do not implement agentic runtime or any LRH-run execution loop.
- Do not edit Taurcode prompts here (separate repo; a handoff prompt already
  covers `:land`/`:execute`).

## Acceptance Criteria

- flag-vs-guidance enforcement of "no chain starts itself" is decided and
  recorded (resolved 2026-08-08 — per-skill tiering, guidance-enforced for
  all 13 skills)
- chain-runner invocation mechanics (invoke flagged links vs. inline) are
  decided (resolved — stays inlined, unchanged by flag removal)
- CHAIN-NOTE placement is resolved against the immutable-narrative rule
- find-or-backfill is normalized in the lifecycle guidance
- each skill's disable-model-invocation setting is removed and when-to-use
  guidance is tiered per the Design Decision, in both `src/lrh/skills/` and
  `.claude/skills/`
- each tier-2/3 skill's confirm-before-write or chain-authorization gate
  placement is audited, not assumed, before the flag is removed
- `installer.py` subagent-preload behavior after flag removal is verified as
  intended
- `DEC-DELIBERATE-CHAIN-INITIATION.md` carries a dated addendum resolving
  point 2, cross-linked to this WI

## Validation

- `lrh validate`
- `lrh work-items validate`
- `scripts/test` when the change touches package behavior or validation logic
- `diff -r src/lrh/skills/ .claude/skills/` when skill files are edited

## Related Workstream and Designs

- Decision: `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md` (feeds
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`)
- `project/executions/README.md`; `src/lrh/skills/_shared/lifecycle-chain.md`;
  `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING`

## Risk Notes

- Relaxing the flag could reopen implicit auto-chaining unless enforcement
  genuinely moves to guidance + the deliberate-initiation contract.
- The frontmatter route for `CHAIN-NOTE` may collide with the new
  execution-record validation.

## Dependencies / Order

- After `DEC-DELIBERATE-CHAIN-INITIATION` (merged). Feeds
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`; unblocks promoting `/lrh-execute` and
  `/lrh-land` as reference implementations.

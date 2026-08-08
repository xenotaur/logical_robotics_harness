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
  - flag-vs-guidance enforcement of "no chain starts itself" is decided and recorded (resolved 2026-08-08 -- per-skill tiering for tiers 1/2/3, guidance-enforced; tier 3a (lrh-land, lrh-execute) keeps the flag pending the skip_if_opted_in verification gap)
  - chain-runner invocation mechanics (invoke flagged links vs. inline) are decided (resolved -- stays inlined, unchanged by flag removal)
  - CHAIN-NOTE placement is resolved against the immutable-narrative rule
  - find-or-backfill is normalized in the lifecycle guidance
  - each of the 9 tier-1/2/3 skills' disable-model-invocation setting is removed and when-to-use guidance is tiered per the Design Decision, in both src/lrh/skills/ and .claude/skills/
  - lrh-self-review (tier 2a) keeps disable-model-invocation until its diff-mode confirm-before-write gate gap is fixed; the flag is not removed as part of the same change that adds the gate
  - lrh-confirm-fixes (tier 2b) keeps disable-model-invocation until its empty-thread fast path (Step 2 skip to Step 8) has a confirm gate before Step 8's unconditional retrigger and round-state write; the flag is not removed as part of the same change that adds the gate
  - lrh-land and lrh-execute (tier 3a) keep disable-model-invocation until DEC-CHAIN-INIT-SKIP-CONSENT's skip_if_opted_in path has a mechanical way to verify a genuine human-typed invocation; closing this gap is separate follow-up scope, not part of this WI
  - each tier-2/3 skill's confirm-before-write or chain-authorization gate placement is audited, not assumed, before its flag is removed
  - installer.py subagent-preload behavior after flag removal is verified as intended
  - DEC-DELIBERATE-CHAIN-INITIATION.md carries a dated addendum resolving point 2, cross-linked to this WI (done 2026-08-08, this PR)
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
behavior (see <https://code.claude.com/docs/en/skills#control-who-invokes-a-skill>)
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
a blanket flip** — enforcement moves from the flag to guidance for tiers 1, 2,
and 3, because the guardrail that actually matters (the confirm-before-write
or chain-authorization gate) does not depend on the flag and fires regardless
of invocation route. Tier 3a is the exception this review surfaced — see below:

| Tier | Skills | What already enforces safety without the flag |
|---|---|---|
| 1 — read/analyze only | `lrh-design` | Nothing writes until Step 4's offer-and-wait |
| 2 — writes/PRs, gated | `lrh-create-skill`, `lrh-doc-audit`, `lrh-implement`, `lrh-doc-organize`, `lrh-doc-work`, `lrh-review-response`, `lrh-readiness` | Existing confirm-before-write gate (`lrh-doc-audit`: `SKILL.md` Step 7 confirm gate before Step 8 writes `project/audits/docs/docs-audit-YYYY-MM-DD.md` — it always writes on that path, not analysis-only, corrected from an earlier misclassification here) |
| 2a — writes, gate gap confirmed | `lrh-self-review` | **Not yet gated — do not remove the flag until fixed.** `lrh-self-review/SKILL.md` Step 5 diff-mode fixes issues directly in the working tree with no confirm-before-write step (confirmed by reading `SKILL.md:151-176`; `when_to_use` alone is not a hard platform guarantee, per this WI's own precedent). Add a diff-mode confirm gate before removing the flag, or exclude `lrh-self-review` from this WI's flag-removal scope and track it separately. |
| 2b — writes/PRs, gate gap confirmed on one path | `lrh-confirm-fixes` | **Not yet gated on its empty-thread fast path — do not remove the flag until fixed.** `SKILL.md` Step 2 explicitly skips Steps 3–7 (including the Step 4 confirm gate) straight to Step 8 when the unresolved-thread list is empty; Step 8 then unconditionally posts a PR comment (`@codex review`) and requests a reviewer (`gh pr edit --add-reviewer @copilot`) and persists round-state, with no human checkpoint on that path (confirmed by reading `SKILL.md:127-130,387-419`). The skill's own text calls these actions "harmless no-ops" that change no PR code, but they are still autonomous GitHub-write actions with zero confirm gate — add a lightweight gate on the empty-thread fast path before removing the flag, or exclude `lrh-confirm-fixes` and track it separately, same treatment as `lrh-self-review`. |
| 3 — commits to `main` / resolves or closes control-plane state, single-workflow (not a chain runner) | `lrh-closeout` | `SKILL.md` Step 4 plan-confirm gate before Step 5 executes any confirmed action (corrected from an earlier misclassification — `lrh-closeout` has no chain-authorization Step 1/2 like `lrh-land`/`lrh-execute`; its own plan-confirm gate is the actual safety property to audit) |
| 3a — chain runners, flag retained pending a real gap | `lrh-land`, `lrh-execute` | **Not yet safe to unflag.** `DEC-CHAIN-INIT-SKIP-CONSENT` condition 1 requires "the human's slash-command invocation remains the deliberate initiation act," but nothing mechanically verifies that once the model can call `Skill()` on these directly — under `chain_init_confirmation: skip_if_opted_in` with valid stored consent and no special condition firing, `lrh-land/SKILL.md:117-139` and `lrh-execute/SKILL.md:151-173` display the completion/stop-work conditions **without asking**, so a model-initiated invocation (not a genuine human-typed command) could ride stored consent through Step 2 with no live human reply at all. This does not affect `chain_init_confirmation: always_confirm` (the default) — that mode still requires a fresh live reply every run regardless of invocation route, which is what actually protected this WI's own `/lrh-land` run. The gap is specific to the opt-in skip path combined with flag removal. |

**Tiers 2b and 3a stay flagged; this WI's flag-removal scope is 9 skills, not
13** (13 originally flagged; excluded: `lrh-self-review` tier 2a,
`lrh-confirm-fixes` tier 2b, `lrh-land` and `lrh-execute` tier 3a — 4
exclusions, 9 remaining). This means the `/lrh-land` mid-sentence
invocation incident that motivated this design is **not** fully resolved by
this WI for users who have opted into `skip_if_opted_in` — it is resolved for
the default `always_confirm` mode, where Step 2's live-reply requirement
already makes the flag redundant regardless of invocation route (the
counterfactual: if the flag had been absent during this WI's own `/lrh-land`
run, Step 2 would still have required the live reply it in fact received,
since `always_confirm` is the default and no opted-in consent exists in this
session). Closing the tier-3a gap requires either a mechanical way to verify
a literal human-typed slash-command invocation (not currently exposed by the
platform — the same ambiguity `WI-DELIBERATE-MODEL-INVOCATION`'s Design
Decision already names for the `/lrh-design` incident) or restricting
`skip_if_opted_in` itself to require that verification. Tracked as follow-up
scope below, not resolved in this pass.

**Gate audit required before the frontmatter pass, not assumed:** confirm each
tier-2/3 skill's confirm/chain-auth gate genuinely fires *before* its first
side-effecting step (this WI's acceptance criteria below make this an explicit
checklist item — do not treat the tier table above as self-certifying). Two
gaps are already confirmed above (`lrh-self-review` tier 2a; `lrh-land`/
`lrh-execute` tier 3a) rather than merely hypothesized — the remaining
tier-2/3 skills still need the same verification before their flags are
removed.

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
silently accept, that removing the flag makes the covered skills
preload-eligible), and `project/executions/README.md` (CHAIN-NOTE placement,
normalizing the existing pattern above).
`DEC-DELIBERATE-CHAIN-INITIATION.md`'s dated addendum resolving point 2 is
already recorded (2026-08-08, this PR) — no longer open scope here.

## Required Changes

- Per the Design Decision above: remove `disable-model-invocation: true` from
  the 9 tier-1/2/3 flagged skills (`lrh-closeout`, `lrh-create-skill`,
  `lrh-design`, `lrh-doc-audit`, `lrh-doc-organize`, `lrh-doc-work`,
  `lrh-implement`, `lrh-readiness`, `lrh-review-response`; `lrh-doc-audit`'s
  Step 8 write path already accounted for in its tier-2 citation above),
  add/extend `when_to_use` per the tier templates, in both
  `src/lrh/skills/` and the `.claude/skills/` mirror.
- **`lrh-self-review` (tier 2a) is excluded from this pass until its diff-mode
  gate gap is fixed** — add a confirm-before-write step to `SKILL.md` Step 5's
  diff-mode branch (or an equivalent explicit approval point) before removing
  its flag; do not remove the flag and add the gate as two unordered changes,
  since removing it first reopens the ungated write path this review caught.
- **`lrh-confirm-fixes` (tier 2b) is excluded from this pass until its
  empty-thread fast path is gated** — add a lightweight confirm step before
  Step 8's unconditional retrigger and round-state write on that path (or an
  equivalent explicit approval point) before removing its flag; do not remove
  the flag and add the gate as two unordered changes, same reasoning as
  `lrh-self-review`.
- **`lrh-land` and `lrh-execute` (tier 3a) are excluded from this pass** —
  their flags stay in place because `DEC-CHAIN-INIT-SKIP-CONSENT`'s
  `skip_if_opted_in` path has no mechanical way to verify condition 1 (a
  genuine human-typed slash-command invocation) once the model can call
  `Skill()` on them directly. Do not remove these two flags until either a
  verification mechanism exists or `skip_if_opted_in` is restricted to close
  the gap — this is separate follow-up scope, not solvable by a frontmatter
  edit in this WI.
- Audit each tier-2/3 skill's confirm-before-write or chain-authorization gate
  placement before relying on it (do not assume the tier table is correct —
  verify; `lrh-self-review`, `lrh-confirm-fixes`, and `lrh-land`/`lrh-execute`
  are the gaps already confirmed, not the only ones assumed absent).
- Update `_shared/lifecycle-chain.md`'s now-false claim that "most
  execution/lifecycle skills carry `disable-model-invocation: true`... so the
  model cannot auto-trigger them" to describe the tier/gate model instead, and
  drop its now-obsolete "flag blocks invoking them" rationale for why chain
  runners inline (see the Design Decision on invocation mechanics above).
- Rewrite the stale `disable-model-invocation`-first guidance in
  `lrh-create-skill/references/{lrh-skill-pattern.md,frontmatter-guide.md,worked-example.md}`
  so new skills don't reintroduce this bug.
- Resolve the `CHAIN-NOTE` home per the Design Decision (fresh record's own
  body, never an append to an existing immutable narrative) and normalize
  find-or-backfill guidance already specified in `lifecycle-chain.md`.
- Verify `installer.py`'s subagent-preload behavior after the flag removal
  (the covered skills become preload-eligible; confirm this is intended,
  matching the already-adopted `lrh-work-item` "Preloading into forked
  subagents" precedent).

## Non-Goals

- Do not promote `/lrh-execute` / `/lrh-land` skills (downstream, after this
  lands).
- Do not implement agentic runtime or any LRH-run execution loop.
- Do not edit Taurcode prompts here (separate repo; a handoff prompt already
  covers `:land`/`:execute`).
- Do not resolve the tier-3a gap (verifying a genuine human-typed
  slash-command invocation, or restricting `skip_if_opted_in` to close it) in
  this WI — surfaced by review as a real, separate mechanism design question,
  not a frontmatter change. Track as follow-up scope before `lrh-land` /
  `lrh-execute` can drop their flags.

## Acceptance Criteria

- flag-vs-guidance enforcement of "no chain starts itself" is decided and
  recorded (resolved 2026-08-08 — per-skill tiering for tiers 1/2/3,
  guidance-enforced; tiers 2b (`lrh-confirm-fixes`) and 3a (`lrh-land`,
  `lrh-execute`) keep the flag pending the gaps below)
- chain-runner invocation mechanics (invoke flagged links vs. inline) are
  decided (resolved — stays inlined, unchanged by flag removal)
- CHAIN-NOTE placement is resolved against the immutable-narrative rule
- find-or-backfill is normalized in the lifecycle guidance
- each of the 9 tier-1/2/3 skills' disable-model-invocation setting is
  removed and when-to-use guidance is tiered per the Design Decision, in both
  `src/lrh/skills/` and `.claude/skills/`
- `lrh-self-review` (tier 2a) keeps `disable-model-invocation` until its
  diff-mode confirm-before-write gate gap is fixed; the flag is not removed
  as part of the same change that adds the gate
- `lrh-confirm-fixes` (tier 2b) keeps `disable-model-invocation` until its
  empty-thread fast path (Step 2 skip to Step 8) has a confirm gate before
  Step 8's unconditional retrigger and round-state write; the flag is not
  removed as part of the same change that adds the gate
- `lrh-land` and `lrh-execute` (tier 3a) keep `disable-model-invocation` —
  `DEC-CHAIN-INIT-SKIP-CONSENT`'s `skip_if_opted_in` path has no mechanical
  verification of a genuine human-typed invocation once the flag is gone;
  closing this is separate follow-up scope, not part of this WI
- each tier-2/3 skill's confirm-before-write or chain-authorization gate
  placement is audited, not assumed, before its flag is removed
- `installer.py` subagent-preload behavior after flag removal is verified as
  intended
- `DEC-DELIBERATE-CHAIN-INITIATION.md` carries a dated addendum resolving
  point 2, cross-linked to this WI (done 2026-08-08, this PR)

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

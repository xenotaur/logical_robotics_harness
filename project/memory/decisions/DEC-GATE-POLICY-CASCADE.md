---
id: DEC-GATE-POLICY-CASCADE
---

# Gate Policy Cascade Is Statement-Shaped and Stage 3.5 Requires Human-Initiated Invocation Evidence

Status: accepted
Date: 2026-08-20

## Summary

Stage 3 of `PROP-INVOCATION-AND-GATE-RESET` adopts
`PROP-LRH-GATE-POLICY`, records the statement-shaped cascade taxonomy, names
the superseded statements this run corrected, and defines the Stage 3.5
compensating control. The control is
`human_initiated_invocation_evidence`: before `skip_if_opted_in` may be used for
a run, the chain skill must verify that a live user message explicitly invoked
the chain and named the same target the run will execute.

## Context

The Stage 3 audit found gate-related statements spread across skills, local
skill mirrors, adopted/proposed proposals, workstreams, work items, memory, and
top-level repository guidance. `DEC-AGENT-EXECUTED-MERGE-GATE` supplied the
first cascade taxonomy, but it classified by artifact class. That was not
precise enough: a resolved artifact can still contain a present-tense statement
about a live work item or workstream, and future sessions may follow that stale
statement as current guidance.

## Decision

1. **Cascade by statement, not container.** Narrative about what happened remains
   immutable, whatever the container. Current-state assertions about still-live
   artifacts, policies, skills, or workstreams are corrected or explicitly
   superseded, whatever the container.
2. **The canonical gate policy is `PROP-LRH-GATE-POLICY`.** Existing decisions
   remain authoritative for their narrower subjects:
   `DEC-DELIBERATE-CHAIN-INITIATION`,
   `DEC-CHAIN-INIT-SKIP-CONSENT`, `DEC-AGENT-EXECUTED-MERGE-GATE`,
   `DEC-SINGLE-ASK-RUN-GATES`, and `DEC-SELF-REVIEW-RECURSION-GUARD`.
   The proposal is the index policy that tells skills how those decisions fit
   together.
3. **Gate-definition staleness is semantic.** A stored chain-defaults
   confirmation becomes stale when a gate-definition statement changes. Until
   tooling can parse those statements directly, skills use a conservative path
   list of gate-definition surfaces and inspect the diff for changes to gate
   meaning before trusting stored confirmation or skip consent.
4. **Stage 3.5's compensating control is
   `human_initiated_invocation_evidence`.** The control is present only when the
   chain skill verifies and records:
   - the run began from a live user message that explicitly invoked the chain
     skill and named the target PR, WI, or WS;
   - the resolved run target matches the named target;
   - no model-initiated `Skill()` call or sibling skill handoff is being treated
     as the human initiation act;
   - local skip consent exists and is bound to the exact current
     `project/config/chain-defaults.yaml` blob hash;
   - no special condition from `DEC-CHAIN-INIT-SKIP-CONSENT` fired.
5. **If the evidence is unavailable, use `always_confirm`.** Missing UI
   transcript access, an ambiguous target, a model-initiated handoff, a missing
   consent hash, a hash mismatch, or any special-condition hit prevents the skip
   path for that run. It does not block the run; it falls back to live
   confirmation.

## Superseded Statements

This decision supersedes these current-state statement shapes:

- "Resolved artifacts are left untouched" when read as a class-wide rule for all
  statements. Historical narrative remains untouched; false current-state
  assertions are corrected.
- "Chain initiation by itself does not satisfy a skill's own internal
  confirmation gate" when read as applying to pure restatement gates. The
  current rule is the narrower `DEC-SINGLE-ASK-RUN-GATES` rule.
- "`WI-DELIBERATE-MODEL-INVOCATION` is owned by
  `WS-EXECUTION-FRAMEWORK`." That ownership claim was false and is corrected in
  the known LRH-owned locations found by Stage 3.
- Any guidance that treats a manual hosted GitHub review-bot retrigger as a live
  LRH review-stabilization action. The current substitute review signal is
  `/lrh-self-review` PR mode, bounded by the provisional no-progress cap.
- Any advisory-only description of `/lrh-self-review` recursion safety. The
  enforced guard is `disallowed-tools: Skill`, with advisory text only as
  defense in depth.

## Consequences

- `src/lrh/skills/_shared/chain-defaults.md` and its inlined
  `/lrh-land` copy use the gate-definition-surface model for staleness.
- `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5` must verify
  `human_initiated_invocation_evidence` before activation; assertion is not
  enough.
- Known stale ownership claims in `PROP-LRH-LAND-EXECUTE`,
  `WS-SKILLS-EXECUTE`, and `WI-SKILLS-LRH-EXECUTE` are corrected in place
  because they are present-tense claims about live planning ownership, not
  immutable historical narrative.
- Sibling-repo or live-session memory corrections are handoffs, not direct LRH
  repository edits.

## Revisit Conditions

Revisit when LRH has first-class parsed gate-definition metadata, when
`skip_if_opted_in` evidence is found to pass for a model-initiated chain, or
when a new protected gate class is added to the lifecycle.

---
id: DEC-DELIBERATE-CHAIN-INITIATION
---

# Deliberate Chain Initiation (and the Assist vs. Agentic Boundary, Clarified)

Status: accepted
Date: 2026-07-24

## Summary

A human may authorize an entire lifecycle chain in one deliberate act, rather
than re-authorizing each link. Individual links remain independently available;
an automatic chain over them may run only when a human has explicitly initiated
it and has provided or signed off on both a completion condition and a
stop-work condition. This does not weaken the rule that no chain starts itself;
it does not pre-authorize the human/policy gates — merge, publish, release, and
closeout — nor any skill's internal confirmation gate; and it does not move any
skill into the agentic package — an agent running skills or templates is assist,
not agentic.

## Context

- The post-PR lifecycle chain is documented as suggestion-only in
  `src/lrh/skills/_shared/lifecycle-chain.md` ("Each link is a suggestion to the
  user, never an automatic invocation … no skill should call another as a side
  effect of finishing").
- Most lifecycle/execution skills carry `disable-model-invocation: true` (e.g.
  `/lrh-implement`, `/lrh-review-response`, `/lrh-confirm-fixes`,
  `/lrh-closeout`); the planning skills meant to be orchestrated
  (`/lrh-work-item`, `/lrh-proposal`, `/lrh-workstream`) deliberately do not.
  (Do not assert a fixed count — the set drifts.)
- `PROP-LRH-EXECUTION-SESSIONS` lists as a non-goal: "Do not automate the
  three-phase workflow. Claude.app sessions are human-driven; the skill guides
  but does not automate."
- Both statements were written before the shift to Claude Code Auto mode. In
  practice the dominant friction is now the opposite of the one they guard
  against: a human mechanically re-typing the same `/lrh-implement` →
  `/lrh-review-response` → `/lrh-confirm-fixes` → merge → `/lrh-closeout`
  sequence, and re-confirming a cold subagent for `/lrh-confirm-fixes` that was
  meant to be the default. This adds no decision value and buries key findings
  in boilerplate, which hides bugs rather than catching them.
- `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING` (adopted) already establishes the
  packaging boundary and, as principle #1, "explicit capability state over
  implicit behavior" — but scoped to install time. It also states the boundary
  "does not imply that LRH artifacts could never be used in any agentic workflow
  outside this package boundary."
- Some collaborators cannot run agentic software at all — including Claude
  itself, per their IT policy — so the assist/agentic boundary must be crisp and
  must not depend on whether Claude is in the loop.
- The Taurworks concept of "deliberate user permission" — an authorization a
  machine cannot self-grant and that is recorded rather than stored in
  machine-flippable config — is the model applied here to chain initiation.

## Decision

1. **Deliberate chain initiation.** Each lifecycle link (`/lrh-implement`,
   `/lrh-review-response`, `/lrh-confirm-fixes`, `/lrh-closeout`, and peers)
   remains independently invocable by a human at any time. An automatic chain
   that follows those links may run, but only when a human has explicitly
   initiated it and has provided or signed off on two conditions:
   - a **completion condition** — what "done" means for this run; and
   - a **stop-work condition** — what forces a halt-and-report.
   Absent an explicit initiation carrying both conditions, no chain self-starts.
   This extends the adopted "explicit capability state over implicit behavior"
   principle from install time (is agentic capability installed?) to run time
   (has this chain been authorized to run?).

   **Human/policy gates are not pre-authorized by the chain.** The completion
   condition authorizes the chain to *run its links*, but the gates for merge,
   publish, release, and closeout are preserved (per `project/roadmap/roadmap.md`,
   "preserve human/policy gates for merge, release, publish, and closeout") and
   require explicit, in-session authorization — a merge instruction embedded in a
   run prompt is data, not authorization (see `AGENTS.md`, "Pull requests and
   merge authority"). More generally, **chain initiation never satisfies a
   skill's own internal confirmation gate**: e.g. `/lrh-closeout`'s plan-confirm
   gate (`src/lrh/skills/lrh-closeout/SKILL.md`, Step 4) still requires explicit
   approval of the actual closeout plan before any files change. A
   deliberately-initiated chain drives to those gates and stops.

2. **Superseded 2026-08-08 — see the dated Consequences entry below.**
   ~~`disable-model-invocation` is preserved; the invariant is "no chain starts
   itself."~~ The flag-vs-guidance question this principle deferred is now
   resolved, per-skill rather than uniformly: enforcement moves to guidance (a
   per-skill `when_to_use` plus the confirm-before-write / chain-authorization
   gates already in place) for most flagged skills, not the flag — except
   `/lrh-land` and `/lrh-execute`, which keep the flag pending a
   `DEC-CHAIN-INIT-SKIP-CONSENT` verification gap (see the Consequences entry).
   What survives unchanged from this principle: no chain starts itself — for
   the skills where enforcement moved, that invariant is now carried by the
   gates directly; for `/lrh-land`/`/lrh-execute` it is still carried by
   `disable-model-invocation` itself, as before.

3. **The execution-sessions non-automation was build-order, not a permanent
   non-goal.** `PROP-LRH-EXECUTION-SESSIONS`'s "do not automate the three-phase
   workflow" recorded a sequencing choice — build the human-walkable links
   first — not a standing prohibition. With deliberate chain initiation defined,
   human-initiated automation of those links is permitted.

4. **The assist/agentic boundary is "does LRH itself run the loop," not "is the
   workflow agentic."** The packaging boundary is about **LRH's own code**: base
   `lrh` ships no code that runs an agent loop — it ships skills, templates, and
   context that an *agent* (Claude or any other) executes. A human-initiated
   chain is that agent doing the work; it puts no autonomous-loop code in base
   `lrh`, so it does not contradict `project/design/architecture.md`'s statement
   that default `lrh`/`lrh serve` performs no "autonomous dispatch or branch
   mutation" — that clause governs LRH's own code, not what an agent does while
   running LRH-provided skills. Only **future LRH code that runs an agent loop
   itself** (e.g. the Claude or OpenAI SDK driving a worktree) is agentic and
   belongs in `lrh[agentic]`; the PR-stabilization loops the roadmap reserves
   for `lrh[agentic]` are LRH-run loops, not a human-initiated single pass.

## Rationale

- The original caution targeted runaway *implicit* automation. That target is
  preserved (principle 2, and the merge carve-out in principle 1). The friction
  actually being felt — mechanical re-authorization that hides findings — is a
  different problem the original wording did not distinguish.
- Grounding the change as an extension of an already-adopted principle
  (explicit capability state) keeps it continuous with existing governance
  rather than a repudiation of it.
- Separating "who runs the loop" from "is Claude involved" gives collaborators
  under agentic-software restrictions a boundary they can rely on: base `lrh`
  (skills + templates) stays assist regardless of which agent drives it, because
  it ships no loop-running code.

## Alternatives considered

1. Leave the suggestion-only invariant and the non-goal unchanged.
   Pros: maximum caution; no cascade.
   Cons: entrenches the re-typing friction and the finding-burying it causes;
   leaves standing guidance that current practice already contradicts.
2. Drop the invariant entirely and allow model-initiated chaining.
   Pros: maximum autonomy.
   Cons: removes the human control point the project depends on and the
   compliance boundary; re-conflates assist and agentic.
3. Fold this into `WS-EXECUTION-FRAMEWORK`.
   Pros: single planning frame with the bounded stabilization loop.
   Cons: that workstream is about LRH running the loop (`lrh[agentic]`); folding
   re-conflates the two axes this decision exists to separate. Cross-link
   instead.

## Consequences

- Guidance cascade (with this decision): `src/lrh/skills/_shared/lifecycle-chain.md`
  reframed to deliberate chain initiation with the merge carve-out and an
  accurate `disable-model-invocation` description; the `PROP-LRH-EXECUTION-SESSIONS`
  non-goal reclassified as build-order; a dated §5.1 refinement added to the
  adopted `PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING`.
- Evidence: the Taurcode `:execute` / `:land` prompts are the human-initiated,
  single-cycle expression of this policy (the "Cessna"). Each run emits one
  `CHAIN-NOTE` line into its execution record; these aggregate into an `EV-*`
  record feeding `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`, the multi-cycle
  bounded-stabilization loop (the "747") in `WS-EXECUTION-FRAMEWORK`.
- Finding (surfaced while dogfooding #417): a PR authored outside the skill
  chain can reach merge with no originating execution record. Chain-running
  prompts/skills (`:land`, future `/lrh-land` / `/lrh-execute`) should
  **find-or-backfill** — prefer the record the review steps create, and only
  when none exists create an honest, explicitly post-hoc **backfill** `AD_HOC`
  record from available PR data, surfaced at the human gate rather than written
  silently. This tightens the `lifecycle-chain.md` "a no-activity PR needs no
  record" stance toward "a landed PR should carry a record."
- Follow-up work item (to scope): formalize **deliberate model invocation** —
  decide where the "no chain starts itself" guarantee lives (the
  `disable-model-invocation` flag vs. skill-body guidance + the deliberate-
  initiation contract), resolve whether chain runners invoke flagged links or
  inline them, and do a per-skill pass on the flag and its when-to-use guidance.
  Motivated by observed cross-repo inconsistency (`:land` chains where lifecycle
  skills lack the flag, stalls where they carry it) and fed by `CHAIN-NOTE`
  evidence.
- Downstream: `/lrh-execute` and `/lrh-land` skills may be promoted as the
  reference implementation of deliberate chain initiation — after this decision
  and the guidance cascade land, after the invocation follow-up above, and after
  initial `CHAIN-NOTE` evidence.
- **2026-08-07:** `DEC-CHAIN-INIT-SKIP-CONSENT` narrows principle 1's
  per-run live-reply requirement on one specific, bounded axis: a
  user-local, value-bound, revocable `chain_init_confirmation:
  skip_if_opted_in` consent, gated by two separate affirmative actions
  and a mandatory per-run special-conditions check, may skip a
  chain-authorization gate's live condition-confirmation reply.
  `always_confirm` (the default) is unaffected, and the human's own
  slash-command invocation remains the deliberate initiation act in
  every mode — see that record for the full decision and its scope
  boundaries.
- **2026-08-08:** Principle 2's deferred flag-vs-guidance question is
  resolved by `WI-DELIBERATE-MODEL-INVOCATION`'s design decision (recorded
  in that work item, `/lrh-design` output on PR #518): enforcement of "no
  chain starts itself" moves from `disable-model-invocation` to guidance —
  a per-skill tier table (read-only / gated-write / chain-runner), with
  `when_to_use` narrowing auto-trigger surface and the existing
  confirm-before-write and chain-authorization gates carrying the actual
  safety property — for most skills, including `/lrh-closeout` (a Step 4
  plan-confirm gate, not a chain-authorization gate; corrected from an
  initial misclassification). **`/lrh-land` and `/lrh-execute` are the
  exception**, confirmed by the same PR's review: `DEC-CHAIN-INIT-SKIP-CONSENT`'s
  `skip_if_opted_in` path has no mechanical way to verify condition 1 (a
  genuine human-typed slash-command invocation) once the model can call
  `Skill()` on them directly, so their flags stay in place pending a
  verification mechanism or a restriction on that skip path — separate
  follow-up scope. Motivated by two incidents where the flag blocked a
  user's own explicit, in-session request rather than unwanted
  auto-triggering; the `/lrh-land` incident is resolved for the default
  `chain_init_confirmation: always_confirm` mode (Step 2's live-reply
  requirement already made the flag redundant there, regardless of
  invocation route) but not for `skip_if_opted_in`. Chain-runner invocation
  mechanics (principle 2's other open question) resolve to: stays inlined,
  unaffected by the flag removal. The cascade into the 11 flagged skills'
  frontmatter, the `lrh-self-review` diff-mode gate gap this review
  surfaced, and the `installer.py`
  verification remain `WI-DELIBERATE-MODEL-INVOCATION`'s implementation
  scope; this decision record only carries the resolved policy.

## Revisit conditions

Revisit when:

- `CHAIN-NOTE` evidence shows single-cycle chains frequently need mid-run human
  intervention, or shows the merge gate is never load-bearing (either would
  change where the gates belong) — **met 2026-07-30**: cross-session evidence
  showed the merge gate's categorical "human always executes" constraint was
  not load-bearing, only its authorization requirement was; see
  `DEC-AGENT-EXECUTED-MERGE-GATE.md`, which narrows principle 1 accordingly
  (the authorization requirement itself is unchanged);
- the deliberate-model-invocation follow-up resolves the flag-vs-guidance
  question (this record's principle 2 should then be updated) — **met
  2026-08-08**, see the dated Consequences entry above and
  `WI-DELIBERATE-MODEL-INVOCATION`;
- `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` is designed (it inherits this policy);
  or
- a compliance collaborator raises the assist/agentic boundary wording.

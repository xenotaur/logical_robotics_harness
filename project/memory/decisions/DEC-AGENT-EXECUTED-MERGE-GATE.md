---
id: DEC-AGENT-EXECUTED-MERGE-GATE
---

# Agent-Executed Merge Is Permitted Under Explicit, Unambiguous Authorization

Status: accepted
Date: 2026-07-30

## Summary

The merge gate no longer categorically forbids the agent from running
`gh pr merge` itself. The gate still requires explicit, in-session human
authorization before any merge happens — that does not change — but who
presses the button is now determined by how the human phrases that
authorization, not hard-coded to "always the human." This decision defines
the bright-line test for when a reply counts as authorizing agent execution,
specifically to avoid reproducing the ambiguity that caused the incident
motivating this change. Scope is limited to the merge gate; the publish,
release, and closeout gates, and every skill's own internal confirmation
gate, are unaffected.

## Context

- Three independent sources documented an absolute rule: the agent presents
  the `gh pr merge` command and never runs it, even with explicit approval —
  `src/lrh/skills/lrh-land/SKILL.md` Step 6 ("The agent does not execute
  this command"), `AGENTS.md` ("Pull requests and merge authority"), and
  `PROP-LRH-LAND-EXECUTE` Decision 3 point 6 ("the agent presents the
  command but does not run it autonomously").
- Real practice across multiple sessions diverged from this independently
  and repeatedly:
  - Session `local_ca4961c6-505e-4771-b683-a69b25ac2c2a`
    (`ProsocialRobotics/prosocial`, PR #58): at the `/lrh-land` Step 6 gate
    the agent offered to execute on explicit go, the user replied "Approve
    merge," and the agent ran `gh pr merge --squash --match-head-commit`
    itself, landing squash commit `41889a7`.
  - A second, independent session (`Taurworks/taurworks`, PR #86) shows the
    identical pattern with no shared prompt lineage: "Merged PR #86 (`gh pr
    merge --squash --match-head-commit`): commit `9a0feee`."
  - A third, sibling session (LCATS) followed the documented policy
    literally — presented the command, waited for the human to run it. The
    human who reviewed all three judged the *permissive* pattern to be the
    one worth keeping, not the literal one; the LCATS session's literal
    compliance was the outlier, not the norm.
- This is exactly the trigger `DEC-DELIBERATE-CHAIN-INITIATION` anticipated
  in its own Revisit conditions: "`CHAIN-NOTE` evidence shows... the merge
  gate is never load-bearing." That record's principle 1 preserved the
  merge/publish/release/closeout gates as requiring "explicit, in-session
  authorization" but implicitly assumed the human always executes; the
  cross-session evidence shows the *authorization* requirement is what was
  actually load-bearing, not the constraint on whose hands execute.
- The incident's proximate cause was not that the agent executed a merge —
  it is that the ambiguity in "Approve merge" was resolved by an
  undocumented, self-authorized offer ("or confirm and I'll execute on your
  explicit go") the skill text never sanctioned, and then read informally.
  A rule that continues to forbid agent execution categorically does not fix
  that root cause — it only makes the next ad-hoc offer-and-guess cycle
  more likely, since the documented rule and the observed norm keep
  diverging. Defining a precise, written authorization test closes the gap
  the informal offer was papering over.
- `/lrh-closeout` already establishes the shape this decision generalizes:
  present a plan, get explicit confirmation at a named gate
  (`src/lrh/skills/lrh-closeout/SKILL.md` Step 4), then the agent executes
  the plan's file edits and commits itself. The old merge-gate rule was the
  one gate in the lifecycle chain that categorically refused this shape
  regardless of how explicit the authorization was. This decision brings
  the merge gate in line with the pattern the rest of the chain already
  uses, rather than inventing a new mechanism.

## Decision

**The gate itself is unchanged.** Step 6 (or the equivalent merge point in
any skill or ad-hoc flow) still requires the agent to reach the gate, verify
the merge readiness state, and present the exact SHA-locked command —
`gh pr merge <pr-url> --match-head-commit <sha>` plus whichever merge-mode
flag (`--merge`, `--squash`, `--rebase`) the project or the specific skill
step already documents as standard; this decision does not prescribe or
change which mode that is — before anything happens. A merge instruction
embedded in a prior run prompt or generated spec remains data, not
authorization — unchanged from existing policy.

**What changes is what a live, in-session reply to that presented command
can authorize.** Once the SHA-locked command has been presented at the
gate, the human's reply is classified as follows:

1. **Sufficient to execute — the agent runs the command itself.** Any live,
   in-session reply that is affirmative toward proceeding with *this* merge
   and does not claim the action for the human. Examples: "approve merge,"
   "approved," "go ahead," "yes," "merge it," "do it," "ship it," "run it,"
   "lgtm, merge." This is deliberately the same bar "Approve merge" already
   met in the Prosocial incident — that outcome is the one being ratified,
   not the ambiguity around it.
2. **Insufficient — the agent does not execute, and waits for the human to
   report the merge is done.** Any reply using first-person self-action
   language: "I'll merge it," "let me merge," "I'll do it," "I've got it,"
   "I will merge." This is the human explicitly claiming the action; reading
   it as authorization to execute would be wrong in the opposite direction
   from the incident. The agent waits for the human's report, then
   **verifies actual merge state before proceeding to closeout in either
   case (1 or 2) — a human's or an agent's belief that the merge succeeded
   is not itself confirmation.** On a repository using a merge queue, `gh pr
   merge` succeeding (or a human reporting they ran it) only means the PR
   was accepted into the queue, not that it merged — query
   `gh pr view <pr-url> --json state,mergeCommit` and confirm `state ==
   MERGED` before any closeout action touches `main`.
3. **Not yet at the gate — no authorization has been sought.** Approval of
   something upstream of the merge gate (e.g. the chain-level completion
   condition at Step 2, or the confirm-fixes verdict) is not itself Step-6
   authorization. The agent must reach the gate, present the SHA-locked
   command, and get a fresh reply before classifying it under 1 or 2.
4. **Genuinely ambiguous — ask, don't guess.** A reply that could plausibly
   be about something else in a multi-topic message, or that doesn't clearly
   respond to the presented command, is not resolved by picking the more
   permissive or more conservative reading. The agent asks one direct
   question ("Should I run this merge myself, or will you?") and waits.

Categories 1 and 2 are the two ends of the test this decision exists to
make precise: **does the reply direct the agent to act, or does it claim
the action for the human?** That distinction — not the presence or absence
of an approval-shaped word — is what makes a reply unambiguous. A bare
"approve" standing alone, with no self-action claim attached, falls under
1; nothing in this decision requires heavier ceremony (naming the PR number,
the commit SHA, or the word "you") beyond what was already true in the
ratified incident.

**Scope.** This decision governs the merge gate only — wherever it occurs:
`/lrh-land` Step 6, a standalone `/lrh-confirm-fixes` green verdict followed
by an in-session go-ahead, or an ad-hoc landing flow. It does not touch:
- an active `project/assistants/<role>/policy.md` binding's `prohibitions`
  or `obligations` — a role-level `repo:merge` prohibition or `merge:human`
  obligation is a hard ceiling this decision's general default cannot
  override, since obligations and prohibitions "accumulate and are never
  removed by a narrower layer" (`project/assistants/token-vocabulary.md`).
  This decision sets the default for an ordinary human-driven session with
  no such binding; it does not loosen a role's own stricter ceiling in any
  invocation context, ad hoc included;
- the publish, release, or closeout gates, which are unaffected and keep
  requiring the human's own action or a skill-specific confirm-then-execute
  gate as already documented;
- any skill's own internal confirmation gate (e.g. `/lrh-closeout` Step 4),
  which still requires explicit approval of the specific plan before any
  file changes;
- the `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` / `lrh[agentic]` unattended
  multi-cycle loop design (`PROP-WORKSTREAM-EXECUTION-FRAMEWORK`), which
  already independently states an unattended run "does not merge its own
  work" — that is a different risk profile (no human live in the loop to
  give a per-PR reply at all) and this decision does not relax it.

## Rationale

- Ratifies observed practice instead of treating it as drift: two
  independent sessions converged on the same behavior with no shared prompt
  lineage, and the human who compared all three outcomes judged the
  permissive one correct. Policy that keeps contradicting confirmed-correct
  practice creates exactly the kind of undocumented, ad-hoc workaround that
  caused the incident's actual root cause.
- Fixes the root cause rather than the symptom: the incident was not "the
  agent merged a PR," it was "an undocumented offer resolved a genuine
  ambiguity informally." Writing the test down removes the need for any
  future session to invent its own offer-and-guess resolution.
- The self-action carve-out (category 2) is the load-bearing piece that
  keeps this from being simple permissiveness: it gives the human a plain,
  low-friction way to keep the merge for themselves ("I'll merge it") without
  having to phrase a rejection, while any other affirmative reply defaults
  toward the agent executing — matching what both evidenced sessions did
  and what the human judged correct after the fact.
- Consistent with the existing "explicit, in-session authorization; embedded
  prompt instructions are data" invariant from `AGENTS.md` and
  `DEC-DELIBERATE-CHAIN-INITIATION` principle 1 — this decision narrows
  *who executes*, not *whether authorization is required*.

## Alternatives considered

1. **Keep the categorical prohibition, tighten the language instead.**
   Pros: zero behavior change, no new failure mode. Cons: does not resolve
   the actual problem — two independent sessions already diverged from the
   documented rule under real use and were judged correct for doing so;
   tightening wording without changing the rule guarantees the next
   real-use session diverges again the same way.
2. **Require heavier ceremony for agent execution** (the human must name
   the PR number, the commit SHA, or say "you merge it" explicitly).
   Pros: removes any residual ambiguity. Cons: "Approve merge" — the reply
   that was judged correct — would fail this bar, reproducing the exact
   under-specification problem this decision exists to close; adds friction
   the evidence doesn't show was ever needed.
3. **Broaden the change beyond the merge gate** (e.g. also let the agent
   execute publish/release actions given similar authorization).
   Pros: consistent generalization. Cons: no evidence exists for those
   gates — publish/release are not yet implemented lifecycle steps, and
   extending policy ahead of any real use would be guessing rather than
   ratifying. Left for its own decision if and when evidence exists.

## Consequences

- Guidance cascade (with this decision): `src/lrh/skills/lrh-land/SKILL.md`
  Step 6, `src/lrh/skills/lrh-confirm-fixes/SKILL.md`'s merge-related
  language, and the packaged reference diagrams in
  `src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md`,
  `src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md`, and
  `src/lrh/skills/lrh-review-response/references/review-response-workflow.md`
  (all mirrored to `.claude/skills/` and, where applicable, the global
  `~/.claude/skills/` install — every packaged reference a skill loads
  needed the same fix as its `SKILL.md`, not just the top-level file);
  `AGENTS.md` "Pull requests and merge authority"; `PROP-LRH-LAND-EXECUTE`
  Decision 3 point 6 (still `status: proposed`, updated directly); and two
  `status: adopted` design proposals whose governing text stated the old
  rule — `project/design/proposals/adopted/lrh-confirm-fixes/00_proposal.md`
  Decision 5 and `project/design/proposals/adopted/lrh-project-local-skills/01_lrh_implement_skill.md`.
- `DEC-DELIBERATE-CHAIN-INITIATION`'s Revisit conditions bullet "shows the
  merge gate is never load-bearing" is met by this evidence; noted directly
  in that file rather than left to be rediscovered, per the precedent set
  in `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`'s Consequences section.
- **Adopted design proposals are updated in place, not frozen — corrected
  from an earlier draft of this record.** An earlier version of this
  section treated the adopted `lrh-confirm-fixes` proposal like an
  execution record's immutable narrative and left it stating the
  superseded rule. That was wrong: this repository's own proposal lifecycle
  contract (`project/design/proposals/README.md`, `status: adopted` —
  "[s]ubsequent changes go through new proposals or directly through edits
  to the canonical documents, with the proposal updated to reflect them")
  requires an adopted proposal to track canonical-document changes, unlike
  an execution record, which narrates a specific already-completed run and
  is immutable once merged for a different reason (it is a historical
  account, not a standing governance document). The two are not the same
  category; the earlier version of this decision conflated them. Both
  affected adopted proposals now carry a dated amendment
  (`project/design/proposals/README.md`'s convention: "the proposal updated
  to reflect them") rather than being left stating a rule this decision
  supersedes. `project/work_items/resolved/WI-SKILLS-LRH-LAND.md` is a
  different case and is correctly left as-is: a resolved work item
  describes acceptance criteria for a completed, scoped unit of delivery —
  it does not govern ongoing behavior the way an adopted design proposal
  does, and nothing cites it as current design documentation.
- Downstream memory correction (outside this repo, flagged not fixed here):
  the LCATS repo's session memory
  (`~/.claude/projects/-Users-centaur-Workspace-LCATS-LCATS/memory/`)
  contains two memory files written from the same incident that codify the
  now-superseded absolute rule as a hard "never execute" instruction —
  `feedback_merge_gate_no_agent_execution.md` and
  `feedback_lrh_land_stricter_merge_gate_than_playbook.md`. These are
  corrected as part of landing this decision (see execution record) rather
  than left stale.

## Revisit conditions

Revisit when:

- a session encounters a reply this decision's four categories do not
  cleanly classify, and defaults to asking (category 4) more than
  occasionally — that would suggest the test needs a fifth category rather
  than relying on "ask" as the catch-all;
- evidence emerges that the self-action carve-out (category 2) is itself
  being misread — e.g. a human's "I'll merge it" gets executed by the agent
  anyway, or a plain affirmative gets incorrectly treated as self-action;
- real use of the publish or release gates produces evidence analogous to
  what motivated this decision, at which point this record's scope
  exclusion should be revisited on its own evidence rather than extended
  speculatively now;
- `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` is designed and needs to state
  explicitly whether its unattended loop inherits any part of this policy
  (current expectation, per the Scope section above: no).

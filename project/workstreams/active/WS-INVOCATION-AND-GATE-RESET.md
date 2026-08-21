---
id: WS-INVOCATION-AND-GATE-RESET
kind: planning_node
title: Invocation and Gate Reset
status: active
stage: executing
origin: incident
summary: >
  Governs delivery of PROP-INVOCATION-AND-GATE-RESET: halt GitHub review-bot
  spend, remove disable-model-invocation fleet-wide in favor of when_to_use plus
  real confirm gates, audit and redesign the accreted human-gate corpus into one
  policy carried by the existing chain-defaults mechanism, and validate the
  result by dogfooding before normal fleet operation resumes.
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-CHAIN-DEFAULTS
  - WS-EXECUTION-FRAMEWORK
work_items:
  - WI-RETRIGGER-REMOVAL-STAGE1
  - WI-DELIBERATE-MODEL-INVOCATION
  - WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL
  - WI-FRONT-OF-RUN-GATE-COLLAPSE
  - WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE
  - WI-GATE-POLICY-CASCADE-STAGE3
  - WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5
  - WI-INVOCATION-GATE-RESET-DOGFOOD-RESUME
  - WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL
exit_criteria:
  - Stage 1 landed - manual GitHub bot retrigger removed from all skills, a provisional no-progress loop cap in place, PROP-REVIEW-WAIT-POSTURE rescoped, self_review_preference removed, a disposition recorded for the two stalled-reviewer-detection backlog entries scoped to the gutted files, lrh skills install run for Claude and Codex user-scope and project-scope installs, the retrigger commands verified absent from ~/.claude/skills/, ~/.agents/skills/, this repository's .claude/skills/ mirror, and this repository's .agents/skills/ Codex mirror (not just the source tree), and confirmed_commit re-stamped
  - Stage 2 landed - disable-model-invocation removed from all remaining skills with when_to_use added, /lrh-self-review report-only by default with a platform-enforced recursion guard, the /lrh-confirm-fixes empty-thread fast path gated, a deliberate decision recorded for installer.py's Codex allow_implicit_invocation emission with tests updated, WI-DELIBERATE-MODEL-INVOCATION's two same-change acceptance criteria explicitly amended, the three inlining-is-permanent statements updated, subagent-preload behavior verified, lrh skills install run for Claude and Codex user-scope and project-scope installs, disable-model-invocation verified absent from the relevant installed corpora (not just the source tree), and confirmed_commit re-stamped
  - Stage 3 landed - gate corpus audit artifact written, gate policy proposal adopted, a DEC record naming exactly what it supersedes recorded, a named and checkable Stage 3.5 compensating control produced, the DEC record carrying the extended cascade taxonomy (statement-shaped, not artifact-class-shaped) per PROP-INVOCATION-AND-GATE-RESET Decision 6, the four known stale ownership claims corrected (WS-SKILLS-EXECUTE.md:77,114,133 and WI-SKILLS-LRH-EXECUTE.md:70), the front-of-run gate pair collapsed per PROP-INVOCATION-AND-GATE-RESET Decision 11 with the same DEC record carrying both ends of the run, and the cascade applied including cross-repo memory correction
  - Stage 3.5 complete - chain-defaults mechanism activated under the compensating control Stage 3 produced, with the two-step consent contract of DEC-CHAIN-INIT-SKIP-CONSENT preserved and skip_if_opted_in never becoming the shipped default
  - Stages 5-6 complete - a low-stakes LRH-internal dogfood run clean, the related open PRs triaged with go/no-go decisions, and findings fed back into Stages 1-4
  - Stage 7 complete - normal fleet operation resumed across the repositories and harnesses paused for this program, with the resumption criterion met and recorded
  - PROP-INVOCATION-AND-GATE-RESET status updated to adopted
  - AGENTS.md, CLAUDE.md, and STYLE.md carry the new policy guidance, and session memories encoding superseded gate rules are corrected rather than left stale
---

## Purpose

This workstream delivers `PROP-INVOCATION-AND-GATE-RESET`. It exists because
three operational failures arrived at once and share a root cause: safety
controls were added as *mechanisms* — a frontmatter flag, a retrigger ceiling,
a per-skill confirm gate — where the project needed *policy*, and each accreted
independently until they began contradicting one another and defeating the
outcomes they were meant to protect.

The three failures, in the proposal's own framing: GitHub review-bot spend moved
from 6/7 to 8/7 of budget in a single day, driven by sessions that had agreed
not to retrigger and did anyway; `disable-model-invocation` blocked legitimate
invocation routes stochastically, so the same skill worked in one session and
was refused in the next; and repeated near-no-op confirmations degraded the
gates into reflexive rubber-stamps, which is a safety regression rather than
merely an ergonomic one.

## Scope

Stages 1, 2, 3, 3.5, 5, 6, and 7 of the proposal's implementation plan:

- **Stage 1** — retrigger removal, a provisional no-progress loop cap, PR #522
  rescope, `self_review_preference` cleanup, `confirmed_commit` re-stamp.
- **Stage 2** — `disable-model-invocation` removal across the remaining skills,
  `when_to_use` for each, `/lrh-self-review` report-only default plus a
  recursion guard, the `/lrh-confirm-fixes` empty-thread gate, the `installer.py`
  Codex-policy decision, amending `WI-DELIBERATE-MODEL-INVOCATION`'s two
  same-change criteria, updating the three inlining statements and the two
  apply-behaviour statements, subagent-preload verification, re-stamp.
- **Stage 3** — gate corpus audit artifact, gate policy proposal, DEC record
  (carrying the extended cascade taxonomy), correction of the four known stale
  ownership claims, and the cascade into skills, guidance docs, and memories.
- **Stage 3.5** — chain-defaults activation, sequenced deliberately after
  Stage 3 so it does not recreate the `skip_if_opted_in` consent-riding gap.
- **Stages 5–7** — LRH-internal dogfood, related-PR triage, feedback into
  Stages 1–4, and resumption of normal fleet operation.

**Explicitly not in this workstream's scope: Stage 4.** The
`confirm_fixes_batch` predicate and the Increment 3 profile fields belong to
`WS-LRH-CHAIN-DEFAULTS`, which already owns
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`. Claiming them here would create duplicate
ownership. The two workstreams are cross-linked instead, following
`DEC-DELIBERATE-CHAIN-INITIATION`'s own Alternatives #3, which rejected folding
into `WS-EXECUTION-FRAMEWORK` because "folding re-conflates the two axes this
decision exists to separate. Cross-link instead."

## Prior Art Check

### Duplication search

- **In-repo:** No existing workstream covers invocation policy or the gate
  corpus. `WS-LRH-CHAIN-DEFAULTS` governs the defaults *mechanism* this
  workstream's Stage 3.5 activates and Stage 4 extends — a substrate, not an
  overlap. `WS-EXECUTION-FRAMEWORK` concerns LRH running an agent loop, a
  different axis. `WS-SKILLS` is `resolved`.
- **Sibling repos:** `taurcode` carries the same gate policy through its
  `:land` / `:execute` prompts, and `DEC-DELIBERATE-CHAIN-INITIATION` names
  them as this policy's expression. Tracked as a named handoff rather than
  folded in, since LRH planning artifacts do not govern that repository.
- **External libraries:** Not applicable; this is governance and skill text.
- **Recommendation:** Proceed.

### Demand search

- **Work items:** The program now has explicit leaves for each remaining
  executable phase. `WI-DELIBERATE-MODEL-INVOCATION`,
  `WI-RETRIGGER-REMOVAL-STAGE1`, `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL`, and
  `WI-FRONT-OF-RUN-GATE-COLLAPSE` are already resolved; the remaining tracked
  leaves are `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE`,
  `WI-GATE-POLICY-CASCADE-STAGE3`,
  `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5`, and
  `WI-INVOCATION-GATE-RESET-DOGFOOD-RESUME`.
- **Proposals:** `PROP-LRH-CHAIN-DEFAULTS` governs the mechanism Stages 3.5 and
  4 touch. `PROP-REVIEW-WAIT-POSTURE` was rescoped to its bounded-poll wait
  mechanism and landed as `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL`.
- **Backlog:** `project/design/backlog.md`'s "Self-review-first tier for
  reducing GitHub bot-review credit consumption" is satisfied by Stage 1.
- **Recommendation:** Continue with Stage 3 next; do not expand this planning
  cleanup into the gate-policy audit/cascade implementation.

## Work Items

`WI-RETRIGGER-REMOVAL-STAGE1` removed the live retrigger mechanism before later
gate-corpus work proceeded. `WI-DELIBERATE-MODEL-INVOCATION` completed the
scoped flag-removal and `when_to_use` work. `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL`
landed the retained CI-wait portion of `PROP-REVIEW-WAIT-POSTURE`.
`WI-FRONT-OF-RUN-GATE-COLLAPSE` implemented Decision 11's front-of-run single
ask. These resolved leaves stay listed so schema-level ownership matches the
history the proposal now cites.

`/lrh-execute <WS-ID>` selects the first proposed entry in `work_items:` whose
`depends_on` is satisfied (`lrh-execute/SKILL.md` Step 1). Listing Stage 1 is
therefore now the intended behavior: it is the unblocked first item and reports
`prompt_ready: yes`. Future proposed stage items should be added only when their
machine-readable `depends_on:` fields preserve the strict order below; do not
rely on prose sequencing alone.

The planned decomposition is now:

| Stage | Work item |
|---|---|
| 1 | `WI-RETRIGGER-REMOVAL-STAGE1` -- resolved |
| 2 | `WI-DELIBERATE-MODEL-INVOCATION` -- resolved scoped flag-removal work |
| 1/5 support | `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL` -- resolved bounded CI-wait follow-up |
| 3 Decision 11 support | `WI-FRONT-OF-RUN-GATE-COLLAPSE` -- resolved front-of-run collapse |
| 2 completion | `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` -- proposed retained-flag completion |
| 3 | `WI-GATE-POLICY-CASCADE-STAGE3` -- proposed gate audit, policy proposal, DEC record, and cascade |
| 3.5 | `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5` -- proposed activation under the Stage 3 control |
| 5-7 | `WI-INVOCATION-GATE-RESET-DOGFOOD-RESUME` -- proposed dogfood, triage, feedback, and fleet resumption |

**Stages 1, 2, and 3 are strictly sequential.** An earlier revision of this
workstream and its proposal both claimed Stages 1 and 2 were independent
"because they share no files." That is false: the exploratory branch interleaves
both stages' changes across four files (`lrh-confirm-fixes/SKILL.md`,
`lrh-self-review/SKILL.md`, `lrh-land/SKILL.md`, `land-workflow.md`) plus their
`.claude/` mirrors. Running them in parallel would also break the
`confirmed_commit` re-stamp constraint — whichever landed second would
invalidate the other's stamp, increasing the asking this program exists to
reduce. See `PROP-INVOCATION-AND-GATE-RESET`'s Implementation Plan, which is
authoritative on sequencing. Stage 3.5 must follow Stage 3.

## Exit Criteria

**The `exit_criteria:` frontmatter list above is the single authoritative
statement of this workstream's exit conditions. Consult that field; it is not
restated here.**

This section previously carried a second, human-readable copy of that list,
with an instruction to change both whenever either changed. That arrangement
failed twice in the ways it was meant to prevent: an independent review caught
the two lists drifting on the `skip_if_opted_in` clause, and a later change
adding Decision 11's front-of-run collapse updated the frontmatter alone,
leaving the body able to certify Stage 3 complete without it.

Two copies of a mutable list are two things to get right and one thing that
will eventually be wrong, and a workstream's exit criteria are precisely where
being wrong is expensive — they are the check that decides whether the
workstream may close. Restating them buys readability at the cost of the
property that matters. This is the same restatement-drift failure
`PROP-INVOCATION-AND-GATE-RESET` documents, so leaving it in place inside the
workstream that delivers that proposal would be self-refuting.

Five sibling workstreams already carry a populated `exit_criteria:` with no
body restatement — `WS-EXECUTION-FRAMEWORK` and `WS-CI-CAPABILITY-SCAFFOLDING`
(proposed), `WS-LRH-ASSISTANTS` (active), and `WS-PRIOR-ART-CHECK` and
`WS-SKILLS` (resolved) — so this is existing practice across every bucket
rather than a new deviation. It does depart from
`lrh-workstream/references/workstream-body-guide.md:96`, which still says this
section "mirrors and expands" the frontmatter list. That guidance should be
revisited so the convention and the practice agree; the follow-up is carried in
`WI-FRONT-OF-RUN-GATE-COLLAPSE`'s Risk Notes.

## Non-Goals

- **Does not own Stage 4.** `confirm_fixes_batch` and the Increment 3 profile
  fields belong to `WS-LRH-CHAIN-DEFAULTS`.
- **Does not execute cross-repository changes.** Stage 3's cascade and Stage 5b's
  triage are specified here but carried out per-repo by hand; LRH planning
  artifacts govern this repository only.
- **Does not weaken merge authorization.** `DEC-AGENT-EXECUTED-MERGE-GATE`'s
  requirement for explicit in-session authorization is unchanged; the proposal
  changes how many times the human is asked, not whether they are.
- **Does not implement autopilot for the closeout gate.** The single-ask design
  is ask-once, not ask-never.
- **Does not rewrite historical records.** Execution records and resolved work
  items stay immutable.
- **Does not resolve the round-cap gate's final shape.** Stage 1 installs a
  provisional cap; the canonical replacement is Stage 4 scope, informed by real
  post-Stage-1 evidence.

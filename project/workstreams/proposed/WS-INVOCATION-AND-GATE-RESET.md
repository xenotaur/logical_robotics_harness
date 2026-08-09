---
id: WS-INVOCATION-AND-GATE-RESET
kind: planning_node
title: Invocation and Gate Reset
status: proposed
stage: assessed
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
  - WI-DELIBERATE-MODEL-INVOCATION
exit_criteria:
  - Stage 1 landed - manual GitHub bot retrigger removed from all skills, a provisional no-progress loop cap in place, PROP-REVIEW-WAIT-POSTURE rescoped, self_review_preference removed, a disposition recorded for the two stalled-reviewer-detection backlog entries scoped to the gutted files, and confirmed_commit re-stamped
  - Stage 2 landed - disable-model-invocation removed from all remaining skills with when_to_use added, /lrh-self-review report-only by default with a platform-enforced recursion guard, the /lrh-confirm-fixes empty-thread fast path gated, a deliberate decision recorded for installer.py's Codex allow_implicit_invocation emission with tests updated, WI-DELIBERATE-MODEL-INVOCATION's two same-change acceptance criteria explicitly amended, the three inlining-is-permanent statements updated, subagent-preload behavior verified, and confirmed_commit re-stamped
  - Stage 3 landed - gate corpus audit artifact written, gate policy proposal adopted, a DEC record naming exactly what it supersedes recorded, a named and checkable Stage 3.5 compensating control produced, the DEC record carrying the extended cascade taxonomy (statement-shaped, not artifact-class-shaped) per PROP-INVOCATION-AND-GATE-RESET Decision 6, the four known stale ownership claims corrected (WS-SKILLS-EXECUTE.md:77,114,133 and WI-SKILLS-LRH-EXECUTE.md:70), and the cascade applied including cross-repo memory correction
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

- **Work items:** `WI-DELIBERATE-MODEL-INVOCATION` (proposed) is completed by
  Stage 2. It declared `related_workstreams: [WS-EXECUTION-FRAMEWORK]`, but that
  workstream's `work_items:` list did not include it — so it was related to, but
  owned by, no workstream. **Adopted here 2026-08-09**, with the author's
  approval: this workstream now owns it, and the work item's
  `related_workstreams:` lists both. Stage 2 both completes it and amends two of
  its acceptance criteria, so this is its real home.
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` inherits this policy.
- **Proposals:** `PROP-LRH-CHAIN-DEFAULTS` governs the mechanism Stages 3.5 and
  4 touch. `PROP-REVIEW-WAIT-POSTURE` (PR #522) is partially obviated by Stage
  1 and is being rescoped to its bounded-poll wait mechanism.
- **Backlog:** `project/design/backlog.md`'s "Self-review-first tier for
  reducing GitHub bot-review credit consumption" is satisfied by Stage 1.
- **Recommendation:** `WI-DELIBERATE-MODEL-INVOCATION` is now owned here (see
  above); mark the backlog entry shipped when Stage 1 lands.

## Work Items

`WI-DELIBERATE-MODEL-INVOCATION` is owned here — Stage 2 completes it and amends
two of its acceptance criteria.

No per-stage work items exist yet; they are described below rather than listed
speculatively in `work_items:`. The planned decomposition, one per stage:

| Stage | Planned work item |
|---|---|
| 1 | Retrigger removal, provisional cap, PR #522 rescope, profile cleanup |
| 2 | Flag removal, `when_to_use`, self-review gate and recursion guard |
| 3 | Gate corpus audit, policy proposal, DEC record, cascade |
| 3.5 | Chain-defaults activation under the Stage 3 control |
| 5–7 | Dogfood, triage, feedback, resumption |

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

Kept in sync with the `exit_criteria:` frontmatter list above — if you change
one, change both. (An independent review caught the two lists already drifting
on the `skip_if_opted_in` clause.)

- Stage 1 landed: manual GitHub bot retrigger removed from all skills, a
  provisional no-progress loop cap in place, `PROP-REVIEW-WAIT-POSTURE`
  rescoped, `self_review_preference` removed, a disposition recorded for the two
  stalled-reviewer-detection backlog entries (`backlog.md:622`, `:678`) scoped
  to the files this stage guts, `confirmed_commit` re-stamped.
- Stage 2 landed: `disable-model-invocation` removed from all remaining skills
  with `when_to_use` added, `/lrh-self-review` report-only by default with a
  platform-enforced recursion guard, the `/lrh-confirm-fixes` empty-thread fast
  path gated, a deliberate decision recorded for `installer.py`'s Codex
  `allow_implicit_invocation` emission with `tests/skills_installer_test.py`
  updated, `WI-DELIBERATE-MODEL-INVOCATION`'s two "not removed as part of the
  same change" acceptance criteria explicitly amended, the three
  inlining-is-permanent statements updated, subagent-preload behavior verified,
  `confirmed_commit` re-stamped.
- Stage 3 landed: audit artifact written, gate policy proposal adopted, a DEC
  record naming exactly what it supersedes recorded, a **named and checkable
  Stage 3.5 compensating control** produced, the DEC record carrying the
  **extended cascade taxonomy** (classify by statement — narrative vs. assertion
  of current state about a still-live artifact — not by artifact class; see
  `PROP-INVOCATION-AND-GATE-RESET` Decision 6), the **four known stale ownership
  claims corrected** (`WS-SKILLS-EXECUTE.md:77`, `:114`, `:133`,
  `WI-SKILLS-LRH-EXECUTE.md:70`), and the cascade applied — including
  cross-repository memory correction, which `DEC-AGENT-EXECUTED-MERGE-GATE`
  documents as a step a prior decision initially missed.
- Stage 3.5 complete: chain-defaults activated under the compensating control
  Stage 3 produced, with `DEC-CHAIN-INIT-SKIP-CONSENT`'s two-step consent
  contract preserved and `skip_if_opted_in` never becoming the shipped default.
- Stages 5–6 complete: a low-stakes LRH-internal dogfood run clean, the related
  open PRs triaged with go/no-go decisions, and findings fed back.
- Stage 7 complete: normal fleet operation resumed across the repositories and
  harnesses paused for this program, with the resumption criterion met and
  recorded.
- `PROP-INVOCATION-AND-GATE-RESET` status updated to `adopted`.
- `AGENTS.md`, `CLAUDE.md`, and `STYLE.md` carry the new policy guidance, and
  session memories encoding superseded gate rules are corrected rather than
  left stale.

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

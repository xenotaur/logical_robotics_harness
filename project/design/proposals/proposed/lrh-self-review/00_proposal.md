---
id: PROP-LRH-SELF-REVIEW
type: design_proposal
title: LRH Self-Review — /lrh-self-review Skill for Pre-Push and Post-Ceiling Independent Review
status: proposed
created_on: 2026-08-02
updated_on: 2026-08-02
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
  - project/design/proposals/adopted/lrh-confirm-fixes/00_proposal.md
  - project/design/backlog.md
  - project/work_items/proposed/WI-REVIEW-LANDED-CANONICAL-CHECK.md
  - project/design/proposals/proposed/lrh-land-execute/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
---

# LRH Self-Review — `/lrh-self-review` Skill for Pre-Push and Post-Ceiling Independent Review

## Summary

This proposal introduces `/lrh-self-review`: a Claude Code skill that dispatches
a fresh, cold-context subagent to independently review a diff or PR, in two
modes — **diff-mode** (a single proactive pass on the local diff, before a PR
ever exists) and **PR-mode** (a substitute for a GitHub bot retrigger once
`round-cap-gate.md`'s ceiling is reached). It formalizes a pattern already
used ad hoc, successfully, four times in this project (PRs #447, #452, #457,
#459), reducing dependence on metered GitHub Copilot/Codex review credits
without altering `round-cap-gate.md`'s existing ceiling semantics.

## Background / Motivation

GitHub bot-review retriggers draw on a metered, cross-project-shared credit
pool — `round-cap-gate.md`'s own stated rationale
(`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md:17-19`).
`round-cap-gate.md` bounds *how many* retriggers happen once a PR exists and
requires human reauthorization past a ceiling, but does nothing about the
first review pass, and nothing about self-inflicted regressions introduced
between review rounds.

The following real, cited data points motivate this (fully accounted in
`project/design/backlog.md`'s "Self-review-first tier..." entry):

- **PR #452**: the `round-cap-gate.md` state ledger
  (`project/executions/round_state/xenotaur-logical_robotics_harness-pr452.json`
  on the `lrh-round-state` branch) shows `completed_count: 10, ceiling: 10`
  — 10 completed bot-retrigger batches, ceiling escalated 3→10. After
  exhausting the ceiling, 3 independent subagent passes substituted for
  further bot retriggers. Only the *first* pass found a bug bot review had
  genuinely missed across its prior rounds — a harness-level discovery
  that shell variables don't survive across separate tool calls, uncaught
  in 8 prior rounds. The second and third passes instead found regressions
  introduced by that first pass's own fix — not bugs bots had
  independently missed, but exactly the class of self-inflicted-regression
  issue a *pre-push* self-review pass could plausibly catch for free.
- **PR #447**: the earliest live trial. A subagent substituted for a bot
  retrigger caught 2 real issues, one that 3 prior Codex rounds had
  missed. This substitution replaced the PR's eventual bot round entirely
  — every recorded bot review on this PR predates the fix commit by
  nearly a day, and none reviewed it or anything after before merge.
- **PR #457**: 4 bot rounds (13 findings, all legitimate, all fixed), then
  1 self-review round after the ceiling (3) was reached. Unlike the other
  mechanism-trial cases, this round converged **clean** — no defects
  found, two candidate issues explicitly considered and ruled out. A
  genuine "self-review trusted with a clean verdict" data point, not just
  a "self-review catches bugs" one.
- **PR #459**: 3 sequential subagent rounds, each finding a new, distinct
  real issue rather than narrowing into refinement noise.

**PR #453** (9 retrigger batches in one session — the idea's original
motivating incident) is cited as evidence of the *problem* only. No
subagent-substitution pass is recorded in its execution records, so unlike
the four cases above it is not a mechanism trial.

A live-verified fact from this session closes off one design option outright:
opening a PR in this repo triggers an automatic review from **both**
`copilot-pull-request-reviewer` and `chatgpt-codex-connector` within about a
minute, with **no explicit retrigger required** (observed directly: PRs #460
and #461 were opened with zero retrigger comments and both bots posted
reviews unprompted). There is no "PR open, bot hasn't looked yet" window —
independent pre-push review is only possible *before* `gh pr create` runs,
never after.

Prior art already names this gap without filling it.
`lrh-confirm-fixes/SKILL.md`'s stalled-reviewer escalation question already
lists "a documented self-review fallback, if one exists" as a hypothetical
remediation option (`SKILL.md:419-438`) — hypothetical, because none exists.
`WI-REVIEW-LANDED-CANONICAL-CHECK` (proposed) explicitly excludes building it
from its own scope, naming it "a separate, not-yet-filed future work item"
(`forbidden_actions: implement_self_review_agent`). This proposal is that
future work item's design.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. Named without being built at
  `src/lrh/skills/lrh-confirm-fixes/SKILL.md:419-438` (hypothetical
  escalation option) and re-derived by hand each time in PRs #447, #452,
  #457, #459 (an `Agent`-tool dispatch pattern, not a skill).
- Sibling repos: None identified.
- External libraries: None identified — composes this project's own `Agent`
  subagent tool with existing LRH skill/execution-record conventions; no
  external review-automation library fits "same toolset, no new
  credentials, cold context."
- Recommendation: Proceed.

### Demand search
- Work items: Found: `WI-REVIEW-LANDED-CANONICAL-CHECK` (proposed) —
  explicitly defers this exact capability as "a separate, not-yet-filed
  future work item." This proposal is that item's design.
- Proposals: None found.
- Backlog: Found: "Self-review-first tier for reducing GitHub bot-review
  credit consumption" (`project/design/backlog.md`) — this proposal
  formalizes that entry.
- Recommendation: Offer to cross-link both once this proposal exists (not
  close — the backlog entry describes the problem broadly; this proposal is
  the first concrete design on it, not yet implemented).

## Design Decisions

### Decision 1: Two distinct trigger points, not one

**Question:** When does a self-review pass run?

**Options considered:**
- A: Every push (pre- and post- every retrigger)
- B: Only as a post-ceiling substitute for a bot round (the existing ad hoc
  pattern)
- C: Once, proactively, before the very first push — then the normal cycle
  proceeds regardless of findings

**Chosen: C, in addition to B — not a replacement for it.** Option A is
rejected: nothing in the evidence supports firing on every push, and the
live-verified auto-review fact means only the very first push has a
"before any bot has looked" window at all — every push after that already
has a bot in the loop, so self-review there is properly Decision 2's
*substitute* case, not a layer stacked on top of a bot round. The result is
two trigger points: a single proactive diff-mode pass before the first
`gh pr create`, and the already-practiced PR-mode substitute after the
ceiling fires.

### Decision 2: `round-cap-gate.md` interaction — pre-push is exempt by construction; substituted rounds count identically

**Question:** Does a self-review round count against the ceiling?

**Chosen:** The pre-push pass never counts — this falls out structurally,
not as a special-cased exemption. `round-cap-gate.md`'s state file is keyed
by canonical PR URL and only created once a PR exists
(`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md:308-313`);
there is nothing to attach state to before that point. Every PR-mode round
after the PR opens counts identically whether GitHub-triggered or
self-review-substituted: `round-cap-gate.md`'s `completed_count` increments
the same way either way.

**Gate integration:** a self-review substitution never bypasses the
ceiling check — it is a fourth answer at the existing three-way gate
(`round-cap-gate.md`'s "The three-way gate" section), alongside
authorize-a-new-ceiling / deny-and-stop / pause: **substitute self-review
for this round**. The gate still fires whenever `completed_count >=
ceiling`, before any new round (bot or self-review) starts; choosing the
substitution answer dispatches the self-review pass instead of a bot
retrigger, and its completion increments `completed_count` by 1 within the
*existing* ceiling — it does not require or imply raising the ceiling.
This matches the actual historical pattern: in both PR #452 and PR #457,
the human's live response to the fired gate was to switch to self-review
rather than authorize a higher ceiling.

**Mechanism note:** a bot-triggered round's `pending_attempt` tracks
asynchronous per-reviewer status (`reviewers: {"codex": "pending", ...}`)
because the retrigger call and its result arrive in separate tool
invocations, possibly across a session interruption
(`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md:379-391`,
the `pending_attempt` field description). A self-review-substituted round
is synchronous within one skill invocation — dispatch the subagent, get
the result, done — so it does not need `pending_attempt`'s async
bookkeeping; it increments `completed_count` directly on completion, no
`pending_attempt` state required for that path.

**Rejected alternative:** adding a `source: "bot" | "self_review"` field to
`round_state`'s own schema, so the ceiling mechanism itself can report a
bot/self-review breakdown. Rejected to minimize churn to a schema that took
8 review rounds to harden (`round-cap-gate.md`'s own history); source
tracking belongs in the self-review skill's own execution record and
CHAIN-NOTE instead (Decision 3), leaving `round_state` an unchanged, source-
agnostic count.

### Decision 3: Record occurrence, not currency

**Question:** How is "credit avoided" tracked, given no GitHub API exposes
per-review credit cost?

**Chosen:** Record what happened, not a cost figure. Each `/lrh-self-review`
run creates its own execution record (`AD_HOC` bucket, suffix
`_SELFREVIEW`, `rerun_of` linking to the primary record — the same
convention `_REVIEW`/`_CONFIRM` already use), capturing mode (diff/PR),
findings count and severity, whether fixes were applied, and — for PR-mode
— which round it substituted for. CHAIN-NOTE gains two lightweight
fields — `self_review_rounds=<N>` and `bot_rounds=<N>` — alongside its
existing `cycles=`/`stops=` fields. **`bot_rounds` must be computed as
`completed_count - self_review_rounds`, never read directly from
`round-cap-gate.md`'s own `completed_count`** — `completed_count` is
source-agnostic (Decision 2: bot-triggered and self-review-substituted
rounds increment it identically), so reading `bot_rounds` straight from it
would double-count every self-review-substituted round as a bot round too.
Both fields are needed together regardless: `cycles` alone cannot stand in
for a bot-round count (`round-cap-gate.md`'s own documented history: PR
#442 recorded `cycles=1` while 14 bot-retrigger batches actually ran
inside it), so a CHAIN-NOTE reporting only `self_review_rounds=` would
still leave the bot-side count unrecoverable from the note itself. This
paragraph corrects an earlier draft's imprecision, caught during
`WI-SKILLS-LRH-SELF-REVIEW`'s own implementation review (harness PR #464,
#467) — the two fields' canonical definition lives in
`src/lrh/skills/lrh-land/references/land-workflow.md`'s "CHAIN-NOTE
Format" section, not duplicated here.

**Diff-mode sequencing note:** diff-mode's `_SELFREVIEW` record is created
before `/lrh-implement` Step 9 ever runs — Step 7.5 (Decision 1) precedes
Step 8's PR-open and Step 9's primary-record creation — so there is no
primary record to link via `rerun_of` at creation time. It is left empty,
matching the existing convention for a record authored before its primary
exists (this proposal's own creation record,
`project/executions/AD_HOC/2026_08_02_02_16_47_LRH_SELF_REVIEW.md`, has an
empty `rerun_of` field for the same reason — no primary existed yet).
PR-mode's `_SELFREVIEW` record, by
contrast, always has a primary to link to, since it only fires after
`/lrh-implement` Step 9 has already run.

### Decision 4: Never skip a PR's first real bot round

**Question:** Given a clean pre-push self-review, can the first bot round be
skipped entirely?

**Chosen: no, never.** Push and get at least one round of real GitHub
review regardless of what the pre-push pass found. A same-vendor subagent
pass is not a blind-spot-equivalent substitute for an independent platform
reviewer, especially on governance-critical changes — PR #457's clean
self-review verdict (see above) is a real instance of self-review
converging clean, but it is one data point, not proof that a clean
same-vendor pass is safe to treat as merge-ready on its own. No skip
policy exists at any point in this design — Decision 1 rules it out for
the first round categorically; a broader design-space pass on later-round
skip policy is explicitly future work (see Open Questions), not decided
here.

### Decision 5: One skill, two invocation shapes

**Question:** Should diff-mode and PR-mode be separate skills?

**Chosen: one skill, argument-driven mode selection.** The core procedure —
dispatch a `general-purpose` `Agent` subagent with cold context, instruct it
to verify claims against real files rather than trust prose, independently
re-verify its own top finding before accepting it (Decision 6), write an
execution record — is identical; only the target differs: a local diff
against a base ref plus task/WI orientation context (diff-mode), or a PR
URL, HEAD SHA, and comment history (PR-mode — the shape already used in all
four evidence PRs). A `--pr <url>` argument (default: local diff) avoids
duplicating the procedure in two files, matching this project's existing
anti-duplication reasoning (`lifecycle-chain.md`).

### Decision 6: Independent re-verification is a mandatory documented step

**Question:** Should the skill require re-verifying the subagent's top
finding, or leave that to the calling context's discipline?

**Chosen: mandatory, documented step.** This project's own practice —
dispatch a subagent, then independently re-verify its most severe finding
before accepting it — caught a fabricated citation earlier in this same
session. Leaving it as an implicit habit means it depends on which session
happens to remember to do it; the skill's own step sequence requires it.

### Decision 7: Governance home — a new single-skill workstream

**Question:** Where does this skill live in the planning tree?

**Chosen:** its own workstream, `WS-SKILLS-SELF-REVIEW`, following the exact
precedent of `WS-SKILLS-CONFIRM-FIXES` (a resolved, single-skill workstream
for `/lrh-confirm-fixes`), not folded into `WS-SKILLS-EXECUTE` (scoped to
chain-*running* skills — `/lrh-land`, `/lrh-execute`, `/lrh-next`,
`/lrh-run-tree`). `/lrh-self-review` is a review primitive, architecturally
a sibling of `/lrh-confirm-fixes`/`/lrh-review-response`, not a chain runner.

## Non-Goals

- Does not implement diff-mode beyond `/lrh-implement`'s new Step 7.5, or
  PR-mode beyond `/lrh-land`'s post-ceiling substitution — expansion to
  `/lrh-work-item`, `/lrh-proposal`, `/lrh-workstream`, `/lrh-doc-work`,
  etc. is explicitly deferred pending evidence those skills hit the same
  multi-round bot-review problem in practice. `/lrh-execute` needs no
  separate wiring — it inherits both call sites by inlining `/lrh-implement`
  and `/lrh-land` wholesale.
- Does not change `round-cap-gate.md`'s ceiling values, escalation gate, or
  stalled-session detection heuristic — the pre-push pass sits structurally
  outside that mechanism (Decision 2); the post-ceiling substitute reuses
  the existing ceiling/escalation flow unchanged.
- Does not measure or report actual GitHub AI-credit cost in currency or
  credit-unit terms — no API exposes it; only occurrence counts are tracked
  (Decision 3).
- Does not authorize skipping a PR's first real bot-review round under any
  circumstance (Decision 4).
- Does not change `/lrh-implement`'s or `/lrh-land`'s existing
  confirm/authorization gates — self-review dispatch is autonomous within
  the run; only its outcome surfaces at the existing gates, not a new one.
- Does not claim cross-vendor blind-spot-equivalent coverage — the subagent
  runs on the same underlying model family as the session driving it
  (Decision 4).

## Implementation Plan

Single work item, matching `WI-SKILLS-LRH-CONFIRM-FIXES`'s shape (skill +
handoff wiring bundled into one PR):

| Work item | Deliverable | Depends on |
|---|---|---|
| `WI-SKILLS-LRH-SELF-REVIEW` (to be filed) | `/lrh-self-review` skill, Step 7.5 wiring in `/lrh-implement`, post-ceiling wiring in `round-cap-gate.md`, CHAIN-NOTE field addition | This proposal adopted |

Produces:
- `src/lrh/skills/lrh-self-review/SKILL.md`
- `src/lrh/skills/lrh-self-review/references/self-review-workflow.md`
- `.claude/skills/lrh-self-review/` mirror (byte-for-byte, `diff -r` verified)
- `CLAUDE.md ## Skills` entry
- New Step 7.5 in `/lrh-implement/SKILL.md` (+ mirror)
- `round-cap-gate.md` addition documenting the post-ceiling substitution
  path as a call to `/lrh-self-review` PR-mode, and the fourth three-way-gate
  answer (Decision 2)
- `self_review_rounds=`/`bot_rounds=` addition to the CHAIN-NOTE convention
  (wherever canonically defined — `PROP-LRH-LAND-EXECUTE` Decision 8
  currently)
- Update the primary-record exclusion globs in `/lrh-review-response`,
  `/lrh-confirm-fixes`, and `/lrh-land` (and their `references/`/`.claude/`
  mirrors) to also exclude `_SELFREVIEW.md`, matching the exact precedent
  set when `_CONFIRM.md` was introduced
  (`PROP-LRH-CONFIRM-FIXES` Decision 9, "Cross-skill consequence") —
  otherwise a `_SELFREVIEW` file containing the branch slug can be
  returned as a primary candidate, producing incorrect `rerun_of` and
  closeout attribution

How the `PROP-LRH-LAND-EXECUTE` cross-reference edit gets made (a new
amendment to that proposal vs. a direct canonical-doc update vs. deferred
entirely) is left as a `WI-SKILLS-LRH-SELF-REVIEW`-level detail, not decided
here.

## Cross-References

- `project/design/backlog.md` — "Self-review-first tier..." entry (the
  evidence this formalizes)
- `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md` — the
  ceiling mechanism this integrates with
- `project/design/proposals/adopted/lrh-confirm-fixes/00_proposal.md` —
  structural template this follows
- `project/work_items/proposed/WI-REVIEW-LANDED-CANONICAL-CHECK.md` —
  anticipates and defers this exact gap
- `project/design/proposals/proposed/lrh-land-execute/00_proposal.md`
  Decision 8 — CHAIN-NOTE/run-journal shape this extends

## Open Questions

- Should `round_state`'s own schema eventually gain a per-round `source`
  field, or does execution-record + CHAIN-NOTE-level tracking stay
  sufficient indefinitely? Decision 2 chooses the latter for now; revisit
  if an aggregate count without source breakdown proves not useful in
  practice.
- Should a zero-finding pre-push pass be recorded with the same weight as
  one that produced fixes, or is a zero-finding record noise? Default:
  always record (uniform with Decision 3); revisit once real usage data
  exists.
- The full design-space survey requested once Decisions 1-4 were locked
  (e.g. trust-scored skip policies for later rounds, cross-vendor
  blind-spot mitigation) is future work, not blocked by this proposal
  shipping — this proposal locks the minimal, evidence-backed version only.

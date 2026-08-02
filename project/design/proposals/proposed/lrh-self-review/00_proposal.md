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
(`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md:12-14`).
`round-cap-gate.md` bounds *how many* retriggers happen once a PR exists and
requires human reauthorization past a ceiling, but does nothing about the
first review pass, and nothing about self-inflicted regressions introduced
between review rounds.

Four real, cited data points motivate this (fully accounted in
`project/design/backlog.md`'s "Self-review-first tier..." entry):

- **PR #452**: 12 bot-retrigger batches, ceiling escalated 3→10. After
  exhausting the ceiling, 3 independent subagent passes substituted for
  further bot retriggers — each found a real bug all 12 bot rounds had
  missed, including the single most severe bug in the PR. Separately,
  several bot-found issues across those 12 rounds were self-inflicted
  regressions from the same session's own prior-round fixes.
- **PR #447**: the first live trial. A subagent substituted for a bot
  retrigger caught 2 real issues, one that 3 prior Codex rounds had missed.
- **PR #453**: 9 retrigger batches in one session — the original incident
  that raised this idea.
- **PR #459**: 3 sequential subagent rounds, each finding a new, distinct
  real issue rather than narrowing into refinement noise.

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
  #459 (an `Agent`-tool dispatch pattern, not a skill).
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
(`round-cap-gate.md:308-313`); there is nothing to attach state to before
that point. Every PR-mode round after the PR opens counts identically
whether GitHub-triggered or self-review-substituted:
`round-cap-gate.md`'s `completed_count` increments the same way either way.

**Mechanism note:** a bot-triggered round's `pending_attempt` tracks
asynchronous per-reviewer status (`reviewers: {"codex": "pending", ...}`)
because the retrigger call and its result arrive in separate tool
invocations, possibly across a session interruption
(`round-cap-gate.md:365-372`). A self-review-substituted round is
synchronous within one skill invocation — dispatch the subagent, get the
result, done — so it does not need `pending_attempt`'s async bookkeeping;
it increments `completed_count` directly on completion, no `pending_attempt`
state required for that path.

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
— which round it substituted for. CHAIN-NOTE gains a lightweight
`self_review_rounds=<N>` field alongside its existing `cycles=`/`stops=`
fields, so a PR's chain summary shows bot-round and self-review-round
counts side by side, without claiming a $ or credit-unit comparison that
isn't measurable.

### Decision 4: Never skip a PR's first real bot round

**Question:** Given a clean pre-push self-review, can the first bot round be
skipped entirely?

**Chosen: no, never.** Push and get at least one round of real GitHub
review regardless of what the pre-push pass found. This also matches
established caution from this project's own experience
(`feedback_round_cap_self_review_alternative` in agent memory): a
same-vendor subagent pass is not a blind-spot-equivalent substitute for an
independent platform reviewer, especially on governance-critical changes,
and a clean self-review result should be treated as provisional, not
automatically merge-ready. No skip policy exists at any point in this
design — Decision 1 rules it out for the first round categorically; a
broader design-space pass on later-round skip policy is explicitly future
work (see Open Questions), not decided here.

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
  path as a call to `/lrh-self-review` PR-mode
- `self_review_rounds=` addition to the CHAIN-NOTE convention (wherever
  canonically defined — `PROP-LRH-LAND-EXECUTE` Decision 8 currently)

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

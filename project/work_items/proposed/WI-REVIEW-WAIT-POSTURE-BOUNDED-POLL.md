---
resolution: null
blocked_reason: null
blocked: false
id: WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL
title: Specify a bounded-poll CI-wait mechanism (PROP-REVIEW-WAIT-POSTURE Decision 3, CI-wait only)
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
  - WS-INVOCATION-AND-GATE-RESET
related_design:
  - project/design/proposals/proposed/review-wait-posture/00_proposal.md
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - retrigger_bot_review
acceptance:
  - "confirm-fixes-workflow.md's CI check mechanism section documents a concrete, bash -n-verified bounded-poll loop (Bash run_in_background, STALE_AGE_SECONDS=900 cap, named poll interval) whose pending/success/terminal-failure predicate preserves the existing branch-rules-based exit-1 disambiguation from confirm-fixes-workflow.md:203-273 -- not a naive raw exit-code-1-means-failure mapping, which would misfire on the exact post-push race that section already exists to handle"
  - "lrh-land/SKILL.md Step 4 (Review-response) and Step 5 (Confirm-fixes), plus land-workflow.md, document the same CI-wait mechanism at the actual wait call sites, closing the original 'wait a reasonable amount of time' gap that motivated PROP-REVIEW-WAIT-POSTURE"
  - "Both files explicitly state the bot-response-wait predicate is out of scope, deferred to Stage 4 (WS-LRH-CHAIN-DEFAULTS, gated on real Stage 1 evidence) -- not silently implemented or silently dropped"
  - "src/lrh/skills/ and .claude/skills/ mirrors match exactly (diff -r) for both lrh-confirm-fixes and lrh-land; the .agents/skills/ (Codex) and .gemini/plugins/lrh/skills/ (Antigravity) render-adapted targets are verified via lrh skills install --dry-run --diff for each target rather than diff -r, since Codex/Antigravity installs are not byte-for-byte mirrors of src/lrh/skills/"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .claude/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .agents/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .agents/skills/lrh-land/SKILL.md
  - .agents/skills/lrh-land/references/land-workflow.md
  - .gemini/plugins/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md
  - .gemini/plugins/lrh/skills/lrh-land/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-land/references/land-workflow.md
---

# Specify a bounded-poll CI-wait mechanism

## Summary

Specifies the CI-wait half of `PROP-REVIEW-WAIT-POSTURE` Decision 3 —
this is a planning artifact, not yet built: a documented, syntactically-
valid, bounded background-poll mechanism for waiting on CI in
`/lrh-confirm-fixes` and `/lrh-land`, replacing today's unspecified
"attempt it first" / "wait a reasonable amount of time" prose. The
bot-response-wait predicate (the other half of Decision 3) is explicitly
out of scope — deferred to Stage 4's evidence-gated round-cap redesign.

## Problem / Context

`PROP-REVIEW-WAIT-POSTURE`'s Decision 3 already specifies a concrete,
`bash -n`-verified loop shape distinguishing pending/success/terminal-
failure via `gh pr checks`'s own documented exit codes (8/0/1). Verified
directly against the current skill files: neither
`confirm-fixes-workflow.md`'s "CI check mechanism" section nor
`lrh-land/SKILL.md`/`land-workflow.md` contain any `sleep`/`poll`/
`background`/loop construct today — the wait mechanism gap this proposal
was written to close has not actually been implemented anywhere yet,
Stage 1's retrigger removal notwithstanding.

**Scoping note, settled live with the user during this WI's own
creation:** Decision 3 has two sub-parts with different urgency.
`round-cap-gate.md`'s own "Historical risk notes" section says its
retired-mechanism lessons "remain useful if a future stage rebuilds a
persistent reviewer-wait primitive" — and `PROP-INVOCATION-AND-GATE-
RESET`'s own Non-Goals state plainly: "Does not resolve the round-cap
gate's final shape... the canonical replacement is Stage 4 scope,
informed by real post-Stage-1 evidence" (Stage 4 = `WI-LRH-CHAIN-
DEFAULTS-INCREMENT-2` plus a new Increment 3, owned by
`WS-LRH-CHAIN-DEFAULTS`, explicitly excluded from
`WS-INVOCATION-AND-GATE-RESET`'s own scope). The bot-response-wait
predicate is tied to that round-cap/no-progress-counting redesign and
should wait for it. The CI-wait predicate is not — CI waits are needed
regardless of round-cap policy, and its correctness doesn't depend on
Stage 1 dogfooding evidence about self-review round behavior. This WI is
scoped to CI-wait only for that reason.

### Prior-art check

**Duplication search — no duplicate.** No work item, proposal, or
execution record implements a bounded-poll CI-wait mechanism anywhere in
this repo. `WI-RETRIGGER-REMOVAL-STAGE1` (resolved) rescoped
`PROP-REVIEW-WAIT-POSTURE` and removed the retrigger surface but did not
touch the wait-mechanism gap itself — confirmed by grepping the current
skill files for any poll/sleep/background construct (none found).

**Demand search — demand is recorded and current.** `PROP-REVIEW-WAIT-
POSTURE` Decision 3 (proposed, this WI's own governing design) already
specifies this exact mechanism in full, `bash -n`-verified detail. No
other open work item claims this scope.

## Scope

In scope: the CI-wait predicate and its bounded-poll loop shape, in
`confirm-fixes-workflow.md`'s CI check mechanism section and
`lrh-land`'s actual wait call sites — Step 4 (Review-response) and Step 5
(Confirm-fixes), not Step 8 (Run journal, a reporting step with no wait
in it) — plus `land-workflow.md`, across all four active skill corpora
(`src/lrh/skills/`, `.claude/skills/`, `.agents/skills/`,
`.gemini/plugins/lrh/skills/`).

Out of scope: the bot-response-wait predicate; `round-cap-gate.md`'s
no-progress threshold or any round-cap policy change; any bot-retrigger
mechanism; round-state persistence/branch bookkeeping.

## Required Changes

1. Add the bounded-poll CI-wait loop (Bash `run_in_background`,
   `STALE_AGE_SECONDS=900`, named poll interval) to
   `confirm-fixes-workflow.md`'s "CI check mechanism" section,
   immediately after its existing exit-code-8 documentation. **The
   predicate must preserve the existing branch-rules-based exit-1
   disambiguation** (`confirm-fixes-workflow.md:203-273`) rather than
   mapping raw exit codes 8/0/1 straight to pending/success/failure —
   exit 1 is ambiguous (also fires when no required-check rule exists at
   all, not only on a genuine CI failure), and treating it as a
   terminal-failure signal would misfire on exactly the post-push race
   that existing section already handles correctly.
2. Add the same mechanism to `lrh-land/SKILL.md` Step 4 (Review-response)
   and Step 5 (Confirm-fixes) — the actual wait call sites, not Step 8
   (Run journal) — and `land-workflow.md`, closing the original
   unspecified-wait gap.
3. In both files, add an explicit note that the bot-response-wait
   predicate is deferred to Stage 4, not covered here — so a future
   reader does not assume this WI closed Decision 3 in full.
4. Render the change into `.claude/skills/`, `.agents/skills/`, and
   `.gemini/plugins/lrh/skills/` via `lrh skills install` for each
   target, not by hand-copying — `.agents/` and `.gemini/` are
   render-adapted output (e.g. `.agents/` adds `agents/openai.yaml` and
   translates Claude-only frontmatter), not byte-for-byte mirrors of
   `src/lrh/skills/`, so a manual copy would fight the renderer on the
   next install.

## Non-Goals

- Does not implement the bot-response-wait predicate — Stage 4 scope.
- Does not change `round-cap-gate.md`'s no-progress threshold or any
  round-cap policy.
- Does not reintroduce any bot-retrigger mechanism.
- Does not implement round-state persistence or branch bookkeeping.

## Acceptance Criteria

Consult the `acceptance:` frontmatter field, which is the authoritative
list.

## Validation

- lrh validate
- bash -n against the literal committed loop snippet in each file
- diff -r src/lrh/skills/lrh-confirm-fixes .claude/skills/lrh-confirm-fixes
- diff -r src/lrh/skills/lrh-land .claude/skills/lrh-land
- lrh skills install --dry-run --local --target codex --diff (expect no USER_MODIFIED diff for the touched skills)
- lrh skills install --dry-run --local --target antigravity --diff (expect no USER_MODIFIED diff for the touched skills)

## Risk Notes

**Scope-boundary risk.** The CI-wait/bot-response-wait split is a live
judgment call made during this WI's own creation, not something the
governing proposal itself drew this precisely. If Stage 4 later
determines the two predicates should share more implementation surface
than expected, this WI's work may need light rework to fit — acceptable
given CI-wait is needed regardless of that outcome.

**This WI's own first review round (PR #549) found two P1s in its own
design, not just wording issues** — caught before any implementation
started, which is exactly what this review step is for, but worth
flagging since both were load-bearing: (1) the original acceptance
criteria would have mapped `gh pr checks`'s exit code 1 straight to
"terminal failure," which is wrong — exit 1 is ambiguous (it also fires
when no required-check rule exists at all) and `confirm-fixes-workflow.md`
already documents the correct disambiguation; naively implementing the
original wording would have produced false failing verdicts on the exact
post-push race the mechanism is meant to handle. (2) The original text
cited `lrh-land/SKILL.md` Step 8 as a wait call site — Step 8 is actually
"Run journal," a reporting step with no wait in it; the real call sites
are Step 4 and Step 5. Both are now corrected in this file's own
acceptance criteria and Required Changes. A third finding added the
`.gemini/plugins/lrh/skills/` (Antigravity) mirror, which the original
scope omitted even though it is a tracked, actively-mapped target.

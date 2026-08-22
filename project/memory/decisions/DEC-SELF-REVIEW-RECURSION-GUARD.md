---
id: DEC-SELF-REVIEW-RECURSION-GUARD
---

# `disallowed-tools: Skill` Is the Verified, Platform-Enforced `/lrh-self-review` Recursion Guard

Status: accepted
Date: 2026-08-19

## Summary

`PROP-INVOCATION-AND-GATE-RESET` Decision 5 required a platform-enforced
recursion guard for `/lrh-self-review`, rejected assuming `disallowed-tools`
was that mechanism without verification, and left the guard itself
unimplemented — `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` (PR #560)
shipped only the advisory dispatch-prompt instruction and recorded the
platform guard as reassigned to Stage 3. This decision closes that gap:
`disallowed-tools: Skill`, added to `lrh-self-review/SKILL.md`, is empirically
verified to remove the `Skill` tool from both the invoking session and the
dispatched subagent while the skill is active, and is adopted as the primary,
enforced recursion guard. The existing advisory instruction is retained as a
secondary, defense-in-depth layer — not a substitute for the platform
mechanism.

This also amends Decision 5's "Options considered" framing, which posed
prompt-level instruction and platform mechanism as mutually exclusive and
never evaluated using both together.

## Context

Decision 5 (`project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md`,
Decision 5 heading) chose "a platform mechanism, with the
specific mechanism left to implementation" and explicitly warned: *"Do not
assume `disallowed-tools` is that mechanism... it would produce a guard that
silently does not guard,"* reasoning that the frontmatter reference describes
it as restricting *"Claude's available pool while this skill is active"* —
read as the invoking session's pool, not necessarily a dispatched
`general-purpose` `Agent` subagent's pool.

`WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` (merged as PR #560,
commit 916012d0ff251347d0ba1f66df8fbd01545922b3) removed
`disable-model-invocation` from `lrh-self-review` and the three other retained
skills, but for the recursion guard specifically shipped only an advisory
dispatch-prompt instruction ("explicit instruction not to invoke
`/lrh-self-review`... or spawn another review agent") plus a Codex-side
static `agents/openai.yaml` policy. Its own PR body recorded the Claude-side
platform guard as unresolved: *"records the unresolved Claude subagent-preload
hard guard as reassigned to Stage 3 gate-policy audit scope."* That
reassignment was never actually reflected in `WI-GATE-POLICY-CASCADE-STAGE3`'s
own acceptance criteria or scope — grepped and confirmed absent — so nothing
would have forced it to be picked up there.

### Empirical test

Before this decision, the assumption Decision 5 warned against was tested
directly rather than re-assumed either way: a throwaway skill with
`disallowed-tools: Skill` was invoked, then a `general-purpose` `Agent`
subagent was dispatched from within it and instructed to attempt a `Skill`
tool call and report the result.

- The invoking session's own `Skill` tool call was blocked while the test
  skill was active, consistent with the documented behavior.
- The dispatched subagent reported it had **no `Skill` tool available at
  all** — contradicting the specific failure mode Decision 5 worried about
  (a guard that restricts only the parent session while leaving the
  subagent's access open).

**Control test — causation confirmed, not merely correlated.** The original
test left open whether the subagent's lack of `Skill` access was *caused* by
`disallowed-tools`, or was a structural property of the `general-purpose`
agent type regardless of the parent skill's frontmatter — a gap a PR #566
review comment (Codex, P2) correctly identified as unclosed: both prior
observations were made with the flag present, with no no-flag baseline to
compare against. A no-flag control was then run: a `general-purpose` `Agent`
subagent dispatched from a plain session context, with no `disallowed-tools`
active anywhere in the call chain, was asked only to report whether a `Skill`
tool was available to it. Result: **`SKILL_TOOL_AVAILABLE`** — the tool was
directly present in its tool list. This confirms causation: a
`general-purpose` subagent has `Skill` tool access by default, and
`disallowed-tools: Skill` on the dispatching skill is what removes it. The
guard is not incidentally piggybacking on an unrelated platform restriction.

This test used a throwaway skill created and deleted within the same session,
so no file artifact of it survives in the repo — a self-review pass on this
decision's own diff flagged that the empirical claim above is otherwise
unverifiable against tracked state. As a second, independent data point: the
`/lrh-self-review` diff-mode subagent dispatched to review this exact change
(after `disallowed-tools: Skill` was already live on this skill) itself
reported having no `Skill` tool available in its dispatch context, consistent
with the original test and obtained under real operating conditions rather
than a purpose-built one. Read together with the no-flag control above (same
agent type, same dispatch pattern, only the flag differs), the two results
bracket the mechanism from both sides.

## Decision

1. `lrh-self-review/SKILL.md` carries `disallowed-tools: Skill` in its
   frontmatter (source and all installed corpora: `.claude/skills/`,
   `.agents/skills/`, and user-scope Claude/Codex installs). This is the
   primary, verified, platform-enforced recursion guard Decision 5 required.
2. The advisory dispatch-prompt instruction added by PR #560 ("explicit
   instruction not to invoke `/lrh-self-review`... or spawn another review
   agent") is retained as a secondary, defense-in-depth layer. It is
   explicitly **not** sufficient on its own — Decision 5's objection to
   advisory-only guidance for a cost-bearing loop still holds — and must not
   be cited as the enforced control for this or any other skill.
3. Decision 5's "Options considered" framing is amended: it posed
   prompt-level instruction and platform mechanism as mutually exclusive and
   never evaluated combining them. Both together, clearly labeled by which is
   primary, is the correct shape going forward wherever this pattern recurs.
4. `WI-GATE-POLICY-CASCADE-STAGE3`'s Stage 3 gate-corpus audit no longer needs
   to resolve the self-review recursion guard as an open item — this decision
   closes it ahead of that audit so Stage 3 audits a stable target rather than
   a moving one.

## Consequences

- `/lrh-self-review`'s recursion risk — a subagent reviewing content that
  references `/lrh-self-review` itself (e.g., a diff touching this skill's
  own files, as this change is) re-invoking it — is closed by an enforced
  mechanism, not a request the subagent could ignore.
- Any future skill with a similar cold-context-subagent-dispatch pattern
  should default to `disallowed-tools: Skill` plus an explicit dispatch-prompt
  instruction, not advisory instruction alone.
- `lrh-self-review/SKILL.md` Step 3's prose was updated to describe the guard
  as implemented, replacing the "explicitly reassigned Stage 3" language that
  is no longer accurate.

## Non-Goals

- Does not address the `lrh-codex-export` retained flag, which remains
  ungoverned by any work item.
- Does not implement Stage 3's gate corpus audit, policy proposal, or
  cascade — those proceed under `WI-GATE-POLICY-CASCADE-STAGE3` unchanged.
- Does not claim the empirical test generalizes to other agent types or
  skills without separate verification.

## Revisit conditions

- If a future platform change alters how `disallowed-tools` or subagent tool
  provisioning works, re-run the empirical test before relying on this
  decision's verification.
- Causation (flag-caused, not structural-to-agent-type) is now confirmed by
  the no-flag control test above, for the `general-purpose` agent type
  specifically. Applying this guard to a *different* agent type or dispatch
  pattern should still verify independently rather than assume the result
  transfers.

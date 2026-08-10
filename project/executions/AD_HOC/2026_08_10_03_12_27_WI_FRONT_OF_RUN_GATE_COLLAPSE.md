---
execution_id: 2026_08_10_03_12_27_WI_FRONT_OF_RUN_GATE_COLLAPSE
prompt_id: PROMPT(AD_HOC:WI_FRONT_OF_RUN_GATE_COLLAPSE)[2026-08-10T03:05:34+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/536
commit:
created_at: 2026-08-10T03:12:27+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Amend `PROP-INVOCATION-AND-GATE-RESET` with a fourth confirmation-fatigue
symptom and a new Decision 11, and file `WI-FRONT-OF-RUN-GATE-COLLAPSE` to
implement it under Stage 3. Motivated by a live incident: a `/lrh-execute` run
stalled for roughly two hours on a deadline because the implementation-plan gate
fired minutes after the chain-authorization gate the human had already answered.

# Result

One commit (`0389abe2`) on `xenotaur/chore/front-of-run-gate-collapse-wi`,
opened as PR #536. Three files: the proposal, the governing workstream, and the
new work item.

## What the amendment records

Background section 3 previously named three symptoms of confirmation fatigue.
The front-of-run pair — `/lrh-execute` Step 2 followed by `/lrh-implement`
Step 4 — is a fourth, and was in scope nowhere. Decision 7 collapsed the
merge/closeout pair at the back of the run and did not reach the symmetric case
at the front.

The amendment is grounded in a field-by-field derivability check rather than an
assertion of redundancy: task summary, expected file changes, and validation
commands come from the work item's own static sections; the prompt ID needs only
the WI-ID; the branch name needs `gh api user` plus the WI's `type`; readiness
warnings come from `lrh work-items readiness`. All six are obtainable before the
first gate fires. Of the four intervening steps, only the prior-art check can
yield genuinely new information, and only when the work item lacks one; the
other two are stops, not questions.

Decision 11 chose hoist-and-merge plus divergence-only gating, adopting
Decision 7's already-ratified reasoning rather than arguing the point afresh,
with the run-plan contract named as the general end-state and notification as an
independent complement.

## The finding worth carrying forward

Activating `chain_init_confirmation: skip_if_opted_in` is the intuitive fix for
this incident and is the wrong one — it would have made the incident strictly
worse. That mode is scoped to the chain gate's *conditions*
(`src/lrh/skills/_shared/chain-defaults.md:70-82`); `/lrh-implement` Step 4 is
untouched by it, and `lrh-execute/SKILL.md:179-181` explicitly preserves that
gate. Applied to the incident, skip mode would have skipped the gate the human
answered and left the one that blocked them, reaching the same stall with no
front gate at all. Recorded in Decision 11 specifically so Stage 3.5's
sequencing is not read as also addressing this.

## Three latent defects the hoist exposes

Verified against the skill text rather than inferred:

- `/lrh-execute` Step 1 runs no readiness check at all for a `WI-ID` input —
  zero occurrences of "readiness" in `SKILL.md:79-91`. Readiness is first
  evaluated at `/lrh-implement` Step 1, after the chain has been authorized.
- The prior-art warning arrives after the chain is authorized rather than while
  the human is deciding.
- The idempotence check can abort a run the human already approved.

All three are repaired as a side effect of moving the work ahead of the gate,
which is part of why (B) was chosen over a label-only patch.

## Deviation from the skill's interview step

`/lrh-work-item` Step 2 asks eight interview questions before the Step 5
confirm gate. Those were derived from the invoking request and the surrounding
session instead, and the complete work item was presented once at Step 5 with
inferred fields called out for correction. Running both would have reproduced,
inside this very change, the double-ask pattern the change exists to remove.
The Step 5 gate itself was honoured, and it carried the PR decision too, so no
second ask was needed.

# Validation

- `lrh prompt check-execution --slug wi-front-of-run-gate-collapse
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`,
  pre-existing and not in this diff).
- `lrh work-items readiness WI-FRONT-OF-RUN-GATE-COLLAPSE --format md` →
  `prompt_ready: yes`, no blocking reasons, no warnings.
- `git diff --cached --check` → clean.
- Committed content verified with `git show HEAD:<path>` rather than a clean
  `git status` — `id`, `depends_on`, and the five Decision 11 references were
  confirmed present in the commit itself.
- Prior-art searches run with `git grep` (tracked files only), not filesystem
  `grep -r`, per `AGENTS.md` § Evidence.

# Follow-up

`commit:` left empty until closeout, when the merge commit exists.

Two dispositions were made deliberately and should be revisited if the sequencing
changes:

- `depends_on: [WI-DELIBERATE-MODEL-INVOCATION]` makes the proposal's
  "Stages 1 to 3 strictly sequential" claim mechanical rather than prose, and
  blocks dispatch until Stage 2 resolves. Note that
  `lrh work-items readiness` still reports `prompt_ready: yes` — `depends_on`
  enforcement lives in `/lrh-execute` Step 1, which is the gap
  `WI-WORK-ITEM-BLOCKED-STATE-EXPRESSIVENESS` documents.
- The new work item was not added to `WS-INVOCATION-AND-GATE-RESET`'s
  `work_items:`, which stays empty so `/lrh-execute` cannot dispatch Stage 3 out
  of order. Whether it belongs there later depends on stage sequencing — consult
  that field rather than this note, which is not kept in sync with it.

One coordination point recorded in the work item's Risk Notes: this item and
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` may each want a chain-defaults profile field
for their respective gate collapses. They should agree on one schema before
either lands, since they are owned by different workstreams and would otherwise
converge only at review.

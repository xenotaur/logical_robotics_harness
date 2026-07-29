---
execution_id: 2026_07_29_01_25_34_LAND_WI_DELIBERATE_MODEL_INVOCATION_REFINE
prompt_id: PROMPT(AD_HOC:LAND_WI_DELIBERATE_MODEL_INVOCATION_REFINE)[2026-07-29T01:25:23-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/423
commit: 69bb467
created_at: 2026-07-29T01:25:34-04:00
agent: claude_app
instruction_source: "ad-hoc :land run for PR #423 (refines WI-DELIBERATE-MODEL-INVOCATION); no instruction-phase prompt file"
session_transcript: claude-app:0144f1d4-0a1a-4d6d-860b-df64ac8bc0d4
---

# Summary

Honest **backfill** record (created at closeout, not at an instruction phase)
for PR #423, landed via a Taurcode `:land` run. #423 refines the proposed
`WI-DELIBERATE-MODEL-INVOCATION` (planning-only, no execution record of its
own) directly via edit rather than through a skill that mints one, so no record
existed for the PR. Reconstructed from available PR data (`pr`, `commit`,
`status`, `agent`, session id) per the find-or-backfill rule — not a fabricated
instruction-phase artifact.

# Result

- Refined `WI-DELIBERATE-MODEL-INVOCATION`'s first Required Change to record the
  target end-state: lifecycle skills likely converge on the `lrh-proposal`
  pattern (drop `disable-model-invocation: true` for a policy-derived
  `when_to_use` field), enforcement moving from the flag to `when_to_use`
  guidance plus the deliberate-initiation contract, decided per-skill (e.g.
  `/lrh-closeout` may keep stronger guardrails), updating both
  `src/lrh/skills/` and the `.claude/skills/` mirror.
- Squash-merged as commit `69bb467`.
- Review: **clean, no findings.** Copilot's summary raised no issues; Codex
  responded "Didn't find any major issues." No fixes were needed (Steps 2-3
  skipped).
- Process note: Codex's clean-pass response arrived as a plain issue comment,
  not a review object — a poll that only checks `reviews[]` will miss it. Had
  to post an explicit `@codex review` nudge before it responded at all (~40 min
  after PR open); worth accounting for in future `:land` review-landed checks.
- The WI remains `proposed`; this PR only refines its text, it does not resolve
  it or implement the described work.

CHAIN-NOTE: cycles=0; stops=0; gates=[]; friction="Codex's clean-pass reply is a plain issue comment, not a review object; a reviews[]-only poll misses it and needs an explicit @codex review nudge before it responds"; note="fourth :land flight; clean review, no fixes needed, first fully find-or-backfill run with the record written fresh from this run's start"

# Validation

- `lrh validate` -> 0 errors, 1 warning (`WS-LRH-ASSISTANTS`, inherited from
  main, unrelated to this change).
- `lrh work-items validate` -> 0 errors (no new warnings from this PR).

# Follow-up

- Implementing `WI-DELIBERATE-MODEL-INVOCATION` should also fix the
  `:land`/`:execute` review-landed check to recognize a clean-pass Codex reply
  posted as an issue comment, not only a review object.

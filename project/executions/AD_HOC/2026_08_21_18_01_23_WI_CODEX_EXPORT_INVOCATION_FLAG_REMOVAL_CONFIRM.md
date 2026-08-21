---
execution_id: 2026_08_21_18_01_23_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL_CONFIRM)[2026-08-21T16:17:17+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_20_04_35_54_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/571
commit: 0578ac8e
agent: claude_code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/571
session_transcript: pending
created_at: 2026-08-21T18:01:23+00:00
---

# Summary

Pre-merge verification pass for PR #571 against `HEAD` `5bf848ec`,
independently re-checking round-1's fixes against the live diff rather than
trusting the review-response record's own claims.

# Result

Fresh-eyes classification of all 3 remaining unresolved threads (2 others
had already flipped `isResolved: true` on GitHub, independently reconfirmed
fixed either way):

- **Clear-satisfied, resolved:** Codex P1 "Preserve Codex explicit-invocation
  policy" — diff plainly adds the required persistent
  `src/lrh/skills/lrh-codex-export/agents/openai.yaml` requirement.
- **Clear-satisfied, resolved:** Copilot "path `lrh-codex-export/SKILL.md`
  doesn't exist" — confirmed both bare references now qualified with
  `src/lrh/skills/`.
- **Unaddressed, left open:** Codex P2 "Register the item in its parent
  workstream" — genuinely not done in the diff. The WI's Non-Goals section
  documents why (avoids a concurrent-edit collision with PR #577, which
  owns `WS-INVOCATION-AND-GATE-RESET.md` right now) and names the follow-up
  condition, but the requested change itself wasn't made. Surfaced to the
  human at the confirm gate; human confirmed the Clear-satisfied batch
  without directing further action on this one.

Thread-resolution verdict (Step 6): **not green** — one exception
(Unaddressed) remains open.

# Validation

- `lrh github threads --mode raw --state all`, filtered `isResolved == false`
  client-side
- `gh api graphql resolveReviewThread` for both Clear-satisfied threads,
  confirmed `isResolved: true` in the mutation response
- `gh pr checks 571 --required` — no required-check protection configured
  on `main` (confirmed via `gh api repos/.../rules/branches/main`, genuine
  absence not the ambiguous exit-1 case)
- `gh pr checks 571` (unfiltered) — `coverage`/`tests` `IN_PROGRESS` at
  gather time; `installed-wheel-smoke`/`lint`/`Check workflow files`
  passing

# Follow-up

Re-checking CI and REVIEW-LANDED against the post-push `HEAD` once this
record is committed (Step 8), before issuing a final verdict.

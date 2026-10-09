---
execution_id: 2026_10_06_05_29_22_WI_SKILLS_CHATGPT_EXPORT_HARDENING_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_SELFREVIEW)[2026-10-06T05:29:22+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_06_03_50_00_WI_SKILLS_CHATGPT_EXPORT_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/775
commit: b559d3622b34f54dc35083babe1d8365fe68f763
created_at: 2026-10-06T05:29:22+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/775
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

PR-mode `/lrh-self-review` substitute review signal for PR #775, from
`/lrh-confirm-fixes` Step 8, on the `_CONFIRM` HEAD
`5f42bfeec413aac2dcc9df71d3442947f2f1c385`. The bots reviewed only the first
two commits; no hosted review bot was retriggered. Substitute round 1.

# Result

Report-only. Cold-context subagent verdict: "safe to merge as-is". It
confirmed every factual claim about current behavior and that all 3 bot
threads are satisfied; validation, readiness, and CI were all green. Findings:

1. **P2: the planned `when_to_use` fold does not cover the WI's own
   motivating example.**
   - `lrh-export-claude`'s "Do not invoke proactively" guard lives only in
     its `when_to_use`. Description plus `when_to_use` is 1480 characters,
     over the 1024 limit, so Required Change 4 would still drop it with a
     notice.
   - The same fallback applies to `lrh-work-remains` (1155) and
     `lrh-config-gates` (1143).
   - **Independently re-verified** by parsing all canonical `SKILL.md`
     frontmatter (lengths include a 1-character separator). Holds.
2. P3: the frontmatter `acceptance:` list omits the body's "20 exported / 5
   skipped" baseline criterion and the "absent key does not fail" clause.
3. P3: Required Change 4 leaves the fold separator unspecified
   (`lrh-config-skills` is borderline at 1015). It also doesn't say whether
   a folded `when_to_use` is still reported by the `stripped_metadata`
   notice.
4. P3: the PR body's acceptance summary predates the round-1 narrowing to
   directories.
5. Optional: the `src/lrh/gate_staleness.py:60-69` comment about
   `skill_names()` may need updating at implementation time.

Routing: the P2 is a non-thread finding. Under the run's agreed policy (P1/P2
stops), the stop-work condition fired; the run halted before Step 6 and the
finding was surfaced to the human for direction. No-progress counter: 0
(this round surfaced findings).

# Validation

At `5f42bfee`: CI 5/5 success; `lrh validate` 0 errors; readiness
prompt-ready.

---
execution_id: 2026_09_28_06_37_21_WI_SKILLS_CHATGPT_EXPORT_IMPL_CONFIRM_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_IMPL_CONFIRM_SELFREVIEW)[2026-09-28T06:37:21+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_27_17_54_52_WI_SKILLS_CHATGPT_EXPORT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/747
commit: 97b111bbc521029455af02963f25edcb64f6a79f
created_at: 2026-09-28T06:37:21+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/747
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

PR-mode `/lrh-self-review` substitute review signal for PR #747, from
`/lrh-confirm-fixes` Step 8, on the `_CONFIRM` HEAD
`0bcc74ab279b178eb0ff49a75a7fa3de040677d5`. Codex and Copilot reviewed only
the opening commit; no hosted review bot was retriggered. Substitute round 1.

# Result

Report-only. Cold-context subagent verdict: **safe to merge as-is**, no P1/P2.
It confirmed all 7 resolved threads are fixed at HEAD, CI green, 1861 tests,
deterministic 20-bundle export with 5 manual-only skips. Six P3 findings,
handled under the run's agreed P3 policy (verify, fix the real cheap in-scope
ones in one round, defer the rest, continue):

1. **Quoted manual-only markers bypass detection** (`'true'` /
   `"false"` strings). **Independently re-verified** by probe: both
   quoted-marker skills exported in the default run with no manual-only
   notice. **Fixed** in `8d88a7d573e24e2c68e8a99a3d84eedc279ab9db`:
   non-boolean markers now fail the skill.
2. **Optional portable fields unvalidated** (`license`, `compatibility`,
   `metadata`). **Fixed** in the same commit, per the WI's "reject malformed
   frontmatter".
3. **A hidden directory in a filesystem source blocks the export**
   (`SkillSource.skill_names()` only skips `_`-prefixed names). **Deferred:**
   pre-existing installer behavior, not introduced here.
4. **Publish-time failures exit 2, undocumented.** **Fixed** in docs.
5. **Stale test count (1852) in the PR body and primary record.**
   **Deferred** to the closeout note; the primary record body stays as
   authored.
6. **Dropping `when_to_use` loses hosted auto-selection guards.**
   **Deferred:** already a listed follow-up in the primary record.

Routed to `/lrh-confirm-fixes` Step 3 as non-thread findings; all P3, none
blocking under the agreed policy. No-progress counter: 0 (this round surfaced
findings).

# Validation

At `8d88a7d5`: `scripts/format --check --diff` clean; `scripts/lint` exit 0;
`scripts/test` 1864 tests OK; `lrh validate` 0 errors;
`lrh skills export --target chatgpt --source current-repo` still exports 20
and skips 5.

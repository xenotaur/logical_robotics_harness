---
execution_id: 2026_09_27_17_58_09_WI_LRH_GITHUB_SKILL_NETWORK_GUIDANCE
prompt_id: PROMPT(WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE:WI_LRH_GITHUB_SKILL_NETWORK_GUIDANCE)[2026-09-27T15:03:29+00:00]
work_item: WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/748
commit: 010f8fea8f34828d83cbf20b0094bcd74865fa50
agent: codex_app
instruction_source: project/work_items/proposed/WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE.md
session_transcript: codex-app:01a0e002-47b5-7351-b25c-e952fb3fe109
created_at: 2026-09-27T17:58:09+00:00
---

# Summary

Implement bounded network-escalation guidance for GitHub-consuming LRH skills,
under WS-LRH-GITHUB-EXECUTION-RESILIENCE.

# Result

Added the canonical shared procedure, updated all 17 in-scope canonical
skills, regenerated Claude and Codex targets, completed the required
report-only cold-context self-review, committed the implementation, and opened
PR #748.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- Claude target drift check — passed.
- Codex target status — touched targets up to date; unrelated pre-existing
  drift/notices remain.
- `scripts/test` — 1806 tests passed.
- `git diff --check` — passed.
- Formatting/lint commands were blocked by the environment's pre-existing
  Black/Ruff version mismatch; no installation or upgrade was performed.

# Follow-up

Await PR review and follow the normal review/land workflow. Do not merge
without the separate explicit merge authorization gate.

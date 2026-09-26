---
execution_id: 2026_09_26_07_01_32_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_GUARDRAILS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_GUARDRAILS_REVIEW)[2026-09-26T06:54:38+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_02_57_59_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_GUARDRAILS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/732
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/732"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-26T07:01:32+00:00
---

# Summary

Review-response round for PR #732, which folds the desktop toolchain guardrails
into `WI-LRH-CONSOLE-DESKTOP-L0`. It ran inline from `/lrh-land` Step 4 and
covered four unresolved threads: one from `chatgpt-codex-connector` and three
from `copilot-pull-request-reviewer`. The user confirmed addressing all four.

# Result

Each claim was checked against `scripts/build`, `scripts/release-smoke`,
`src/lrh/dev/release_smoke.py`, and `STYLE.md:484-487`. All four were fixed in
`0b4b7ce5`:

1. **Codex P2, and Copilot on the same point.** The planned `desktop.yml` path
   filter now includes `scripts/desktop`, so a wrapper-only change still runs
   desktop CI.
2. **Copilot, ambiguous sdist check.** The check is pinned to an assertion in
   `src/lrh/dev/release_smoke.py`. That module is run by
   `scripts/release-smoke`, and the `installed-wheel-smoke` workflow runs it on
   every PR. Its logic gets unit coverage in
   `tests/dev_tests/release_smoke_test.py`. `artifacts_expected` and the
   validation lines were updated to match.
3. **Copilot, STYLE script contract.** The wrapper must now support `--help`,
   `--check`, and `--dry-run`, and validation exercises all three.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-DESKTOP-L0`: `prompt_ready: yes`,
  no warnings.

The change is planning text only; no code changed.

# Follow-up

Thread resolution is left to `/lrh-confirm-fixes`.

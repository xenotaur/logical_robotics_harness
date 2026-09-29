---
execution_id: 2026_09_29_06_33_02_WI_LRH_CONSOLE_DESKTOP_L0_SPLIT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_SPLIT_REVIEW)[2026-09-29T06:32:54+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/757
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/757"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-09-29T06:33:02+00:00
---

# Summary

Review-response round 1 for PR #757, the planning split of
`WI-LRH-CONSOLE-DESKTOP-L0`, run inside `/lrh-land`. The first-push hosted
reviews left 5 inline threads: 1 from Codex and 4 from Copilot. The user chose
to fix all 5.

# Result

All five are fixed in `bd8fc038`:

1. **Codex: the governing proposal was out of sync.**
   - `00_proposal.md` now lists all five L0 work items and records the
     2026-09-29 split. Items 3–5 together meet the L0b gate.
   - The intro no longer says "first two" items.
   - The workstream intro now says "its initial L0 leaves" instead of "two
     initial leaves".
2. **Copilot: DOGFOOD evidence.** Added `test_output` to `required_evidence`.
3. **Copilot: SHELL artifacts.** `artifacts_expected` now lists the files the
   deferred PR #750 test items touch: `desktop_modes_test.py`, and
   `scripts/run` and/or `desktop-toolchain.md`.
4. **Copilot: SUPERVISOR isolation.** Added a case where a separately started
   `lrh serve` stays untouched. It appears in the acceptance frontmatter, the
   `supervisor_test.rs` case list, and the body's acceptance criteria.
5. **Copilot: the protocol reference.** It now names SUPERVISOR as the Rust
   supervisor that the SHELL Tauri app drives.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness` returns `prompt_ready: yes` for SUPERVISOR,
  SHELL, and DOGFOOD.

# Follow-up

Next: confirm-fixes, which resolves the five threads, runs a substitute cold
review of the new HEAD, and re-checks CI.

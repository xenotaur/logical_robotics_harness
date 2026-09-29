---
execution_id: 2026_09_29_05_10_29_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-L0:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_CLOSEOUT_NOTE)[2026-09-29T05:10:29+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-L0
status: landed
rerun_of: 2026_09_27_18_17_35_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN
pr: https://github.com/xenotaur/logical_robotics_harness/pull/750
commit: 9eeea4422cfe3a12021b1a33b43c300a879bc896
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/750"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-29T05:10:29+00:00
---

# Summary

This is the closeout note for PR #750, PR 1 of 2 for
`WI-LRH-CONSOLE-DESKTOP-L0`. The PR delivered the desktop toolchain and
scripts infrastructure (Required Changes item 9) plus a minimal Tauri app.
The `/lrh-execute` chain ran the closeout. The primary record's body is
immutable, so the chain note lives here.

# Result

CHAIN-NOTE: `cycles=2; stops=2; gates=[execute-chain, land-chain, ci-stop x2, review-response, confirm-fixes, merge]; friction=classifier-outage,self-introduced-ci-regression; self_review_rounds=3; bot_rounds=1; note="The first push was reviewed by Codex (1 thread) and Copilot (4 review-body findings). CI stop 1: the macOS desktop job exposed a pre-existing bash 3.2 empty-array bug in scripts/validate, fixed in this PR. The round-1 fixes covered pinned rustup components, the full Linux prereqs and the wheel dist-info guard, with one finding dismissed. CI stop 2: the new xdo.h check read the real filesystem on the stock ubuntu runner, fixed with an override and a hermetic Linux-branch test. The final cold review found the PR safe. Merged with the SHA lock after 7/7 CI green."`

PR #750 merged as `9eeea4422cfe3a12021b1a33b43c300a879bc896`, using
`--match-head-commit 6401a829` after an in-session merge authorization.

Four records were landed with that commit: the primary, `_SELFREVIEW`,
`_REVIEW` and `_CONFIRM`.

`WI-LRH-CONSOLE-DESKTOP-L0` stays `proposed`. Two things are still pending:

- PR 2, the remaining L0 app work;
- the user's five Mac dogfood sessions.

The workstream and proposal are unchanged.

# Validation

- `lrh validate` was run after these closeout edits (see the closeout commit).

# Follow-up

The final cold review raised three optional items, deferred to PR 2:

- (low) `LinuxPrerequisitesTest` passes on the exit code alone. It should
  also assert that the `pkg-config --exists webkit2gtk-4.1` probe ran.
- (nit) `LRH_DESKTOP_XDO_HEADER` also applies outside tests. Rename it with a
  test prefix, or document it in `desktop-toolchain.md`.
- (nit) The expected text for the `rustup_absent` failure case (`"rustup"`)
  is weak and could pin the exact message.

Next: PR 2 of `WI-LRH-CONSOLE-DESKTOP-L0`.

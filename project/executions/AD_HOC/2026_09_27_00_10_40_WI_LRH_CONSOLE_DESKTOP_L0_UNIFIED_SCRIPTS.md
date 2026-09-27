---
execution_id: 2026_09_27_00_10_40_WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS)[2026-09-27T00:08:54+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/744
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-L0.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-27T00:10:40+00:00
---

# Summary

Ad-hoc planning update, requested by the user after a review of Rust/Tauri
development-workflow options. The chosen option ("B": desktop modes on the
existing scripts) is folded into `WI-LRH-CONSOLE-DESKTOP-L0` before
implementation.

# Result

The work item was updated with:

- a "Developer workflow placement" section comparing four options and
  recording the external facts behind the choice (rustup 1.28 install
  behavior, `tauri::test` MockRuntime, no macOS desktop WebDriver client, OS
  prerequisites, GitHub runner Rust);
- a rewrite of required change 9. It adds a single `apps/desktop/scripts/run`
  helper and `--desktop` modes on `scripts/develop`, `test`, `lint`, `format`,
  and `version`. Default runs stay Rust-free with an explicit SKIPPED line,
  and every `--desktop` mode fails when the toolchain is missing. It also
  covers no silent installs and no `sudo`, test tiers 0-3, a `desktop.yml`
  that calls the same scripts plus a weekly drift run, a desktop-toolchain
  how-to, and `tests/scripts_tests/desktop_modes_test.py`;
- matching frontmatter acceptance, `artifacts_expected`, acceptance,
  validation, and risk entries.

It also settles the PR #732 deferred nit: `--check` means no tracked-file
edits, and gitignored `target/` artifacts are allowed.

No code changed.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-DESKTOP-L0`: `prompt_ready: yes`,
  no warnings.

# Follow-up

Land after review with `/lrh-land`. Implementation remains
`/lrh-execute WI-LRH-CONSOLE-DESKTOP-L0`.

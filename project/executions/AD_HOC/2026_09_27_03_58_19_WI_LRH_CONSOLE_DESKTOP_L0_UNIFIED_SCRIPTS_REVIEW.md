---
execution_id: 2026_09_27_03_58_19_WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS_REVIEW)[2026-09-27T02:58:06+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_27_00_10_40_WI_LRH_CONSOLE_DESKTOP_L0_UNIFIED_SCRIPTS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/744
commit: 
created_at: 2026-09-27T03:58:19+00:00
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/744"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
---

# Summary

Review-response round for PR #744, which routes the L0 desktop toolchain
through the existing scripts. It ran inline from `/lrh-land` Step 4 and
covered 7 unresolved threads: one from `chatgpt-codex-connector` and six from
`copilot-pull-request-reviewer`. The user confirmed addressing all 7.

# Result

Claims were checked against `scripts/test:20-32` (unrecognized arguments are
passed to unittest as test targets) and `scripts/version:7`
(`python -m lrh.dev.versioning`). All 7 were fixed in `118dd33c`:

1. **Codex P2, dry run not preview-only.** `scripts/develop --desktop
   --dry-run` is now handled before the Python setup. It prints the `pip`
   command and the desktop setup commands, then exits 0 without running
   either.
2. **Copilot, same point.** Covered by fix 1, together with a rule that each
   script parses its own flags before any other work or argument
   passthrough.
3. **Copilot, undefined `--install-rust`.** It is defined as `scripts/develop
   --desktop --install-rust`, passed through to `run setup --install-rust`.
   It is the only path that runs the rustup installer; without it, the
   default is a refusal with a non-zero exit. Both paths get stub tests.
4. **Copilot, undefined `--all`.** Removed. `scripts/test --desktop` means the
   Python suite plus the desktop tier, and it is parsed before unittest
   passthrough.
5. **Copilot, contradictory version wording.** Plain `scripts/version tools`
   is unchanged, with no Rust probes.
6. **Copilot, strict version check.** The new strict
   `scripts/version tools --desktop` exits non-zero on a missing or
   mismatched pin, and desktop CI uses it.
7. **Copilot, incomplete test coverage** (also noted at line 325).
   `desktop_modes_test.py` now covers, for every `--desktop` mode: absent
   rustup or cargo, a pinned toolchain that is missing or mismatched, and
   `tauri-cli` missing or mismatched. It also covers the dry-run and
   `--install-rust` paths. The validation line was updated to match.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-DESKTOP-L0`: `prompt_ready: yes`,
  no warnings.

The change is planning text only.

# Follow-up

Thread resolution is left to `/lrh-confirm-fixes`.

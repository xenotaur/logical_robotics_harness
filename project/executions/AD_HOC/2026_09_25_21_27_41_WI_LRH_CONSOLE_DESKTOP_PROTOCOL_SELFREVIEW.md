---
execution_id: 2026_09_25_21_27_41_WI_LRH_CONSOLE_DESKTOP_PROTOCOL_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_PROTOCOL_SELFREVIEW)[2026-09-25T21:27:40+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/727
commit: d9f0e49e722a2b940ac62fe8e943a2c814e9315a
created_at: 2026-09-25T21:27:41+00:00
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-PROTOCOL.md"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

Diff-mode `/lrh-self-review` of the uncommitted `WI-LRH-CONSOLE-DESKTOP-PROTOCOL`
implementation. The diff was the working tree against `origin/main` at
`fa837320e0a01598353dd2822216fc1cbd75d531`. It ran from `/lrh-implement`
Step 7.5, inside a human-initiated `/lrh-execute` chain, before the PR's first
push. `rerun_of` is empty because diff-mode runs before the primary
implementation record exists.

# Result

Mode: diff. A cold-context `general-purpose` subagent received only the diff
path, the work item's requirements, and repository conventions. It reported
six findings. It ran the targeted unit and smoke suites plus its own probe
scripts, and it changed no repository files.

1. Medium: an oversized echoed control `type` after `ready` made the child
   send `failed` after `ready` and exit 1.
2. Medium-low: the reference supervisor left a child running after
   `exited_before_ready` (child closed stdout but stayed alive).
   `DesktopSupervisor.start` could also replace a failed child without
   stopping it.
3. Low-medium: the supervisor treated a mismatched-launch `ready` as stale and
   waited, contrary to the doc.
4. Low: a `project/` control-directory workspace was accepted by the child but
   rejected by the supervisor's identity check.
5. Low: the exit-code table misdescribed parent loss before `start`.
6. Low/informational: the doc lacked notes on existing Meta selector routes and
   on a stdout write blocking when the parent stops reading.

Top finding re-verified directly by the invoking session. A start request
followed by a control message whose `type` was 20,000 backslashes produced
stdout `ready L1` then `failed None`, and stderr said
`outgoing message exceeds 65536 bytes`. The finding holds.

Report-only dispatch; `--apply` was not used. Under `/lrh-implement` Step 7.5
the implementing workflow applied fixes for all six verified, in-scope
findings, and added regression tests:

- bounded echoes, and post-ready errors now stop with `stopping`/`stopped`
  reason `internal_error`;
- every failed start escalates against the owned handle, and the supervisor
  stops any previous child first;
- a mismatched startup `ready` fails with `launch_id_mismatch`;
- identity verification uses the echoed request and `project_dir`;
- doc corrections for findings 5 and 6.

After the fixes, the original repro produced a bounded `error`
(`unknown_message_type`, 748 bytes), and the server then stopped normally.

# Validation

- `python -m unittest tests.cli_tests.desktop_protocol_test tests.cli_tests.desktop_supervisor_test tests.smoke.desktop_protocol_smoke` with `-W always::ResourceWarning`: 72 tests OK, no resource warnings.
- `scripts/format --check --diff`: 261 files unchanged. `scripts/lint`: exit 0.
- `scripts/test --log`: `Ran 1770 tests in 121.892s`, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

None from this pass. The PR's first automatic review round still runs after
the push; this pass does not replace it.

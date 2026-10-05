---
execution_id: 2026_10_05_04_34_52_WI_LRH_CONSOLE_DESKTOP_DOGFOOD
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-DOGFOOD:WI_LRH_CONSOLE_DESKTOP_DOGFOOD)[2026-10-05T04:12:09+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-DOGFOOD
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/766
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-DOGFOOD.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-05T04:34:52+00:00
---

# Summary

This record covers implementing `WI-LRH-CONSOLE-DESKTOP-DOGFOOD` through
`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with `/lrh-implement` inline.
The owner ran the Mac sessions. The agent drafted the evidence record from
the owner's pasted notes, fixed the checklist doc, and filed defect work
items. The agent ran no dogfood sessions.

# Result

**Before the gate.** The owner first ran a pause-and-resume: sessions 0 to
0.3, then 1 to 4. The agent compared the notes with the work item and
reported three checks that only the owner could close: a forced startup
failure, backend crash recovery, and app crash recovery. The owner ran them
in session 5.

**Run plan.** At the chain gate the owner approved the run plan and chose
three grouped defect work items over one per defect.

**Delivered:**

- `project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`. It covers nine
  sessions, checklist steps 1 to 17, work item coverage, the embedded-versus-
  browser matrix, findings, automated validation, a recommendation (close L0;
  L1 proceeds with three adjustments; L3 stays gated), and Owner decisions.
- `docs/how-to/lrh-console-local-dogfood.md`. It adds a step 12 recipe and
  new steps 15 and 16 for crash recovery. The `kill` and `pgrep` checks are
  scoped to the owned PID and the exact `serve --desktop-protocol` argv.
- `WI-SERVE-QUIET-CLIENT-DISCONNECT`, `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`,
  and `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`, all added to the workstream's
  `work_items:` list.
- `project/design/backlog.md`: "Deferred LRH Console L0 dogfood checks".

**Divergence from the approved plan.** The backlog entry was not in the
plan's expected file list. It was added at the owner's direction ("leave
them in the backlog or work items to dogfood later"). The approved work
items, evidence, and doc changes are otherwise as planned.

**Owner decisions** (recorded in the evidence as recollections):

- The app was almost certainly opened from the Dock in sessions 1, 2, and 5.
- The owner thinks Stop, Restart, Quit, and the forced failure all ran while
  the independent `lrh serve` was up.
- Three unrun checks are waived for L0 closure: the Chrome-absent fallback,
  a forced workspace mismatch, and external-link handoff.

**Correction made in session.** The agent had told the owner that unit tests
covered the Chrome-absent fallback. They do not. The evidence and backlog
record this as a test gap.

# Validation

- `scripts/test --desktop --log` on the dogfood Mac: 1907 Python tests OK.
  Rust: 27 unit, 9 capability, and 22 supervisor tests passed.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and
  `scripts/check-workflows` all passed.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness`: all three new work items report
  `prompt_ready: yes`.
- Environment: format and lint used the `LrhLocalAgent` conda env's pinned
  tools (Black 26.3.1, Ruff 0.15.12), with `PYTHONPATH` set to this
  worktree's `src`.

# Follow-up

- Defect work items are listed in the workstream after this one:
  `WI-SERVE-QUIET-CLIENT-DISCONNECT`, `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`,
  and `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`.
- L1 work items are still to be created from the evidence recommendation.
- The waived checks are tracked in the design backlog.

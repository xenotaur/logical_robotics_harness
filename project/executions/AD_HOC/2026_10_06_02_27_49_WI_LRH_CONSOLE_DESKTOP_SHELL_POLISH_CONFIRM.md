---
execution_id: 2026_10_06_02_27_49_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH_CONFIRM)[2026-10-06T02:27:48+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_05_20_20_18_WI_LRH_CONSOLE_DESKTOP_SHELL_POLISH
pr: https://github.com/xenotaur/logical_robotics_harness/pull/771
commit: 
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/771"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-06T02:27:49+00:00
---

# Summary

This record covers `/lrh-confirm-fixes` for PR #771
(`WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`), run inline from `/lrh-land` after
review-response round 1 (`391aea6b`) and a nit follow-up (`cb875f88`).

# Result

**Threads.** The authoritative list has 3 threads. Each was verified on
`94017380` and resolved with `resolveReviewThread`:

- **Codex P2, download phantom entry.** Clear-satisfied: the main window's
  download handler calls `download_started`, with a test.
- **Copilot, menu dispatch tests.** Clear-satisfied: `history_direction` and
  `history_target`, with tests.
- **Copilot, "backend" in Server Details.** Clear-satisfied: no
  `"backend …"` message strings remain in `supervisor.rs`.

**Substitute cold review of `2a228aee..94017380`** (hosted bots reviewed
only earlier commits). Verdict: safe to push.

- It confirmed the `before_last` bookkeeping and the event order, from wry
  0.57: the navigation record happens, then `didBecomeDownload`, then
  `DownloadEvent::Requested`, then the undo.
- It found no deadlock: the main-thread callbacks take the locks in a
  single order.
- Nits applied in `cb875f88`: two tests pin the download undo after a
  reload and after a move, and the test comment no longer overclaims what
  the policy re-check refuses.
- Nits left:
  - Machine codes such as `backend_failed:` and `incompatible_backend:` in
    the Last error row stay as they are, because they are protocol codes.
  - The Python reference supervisor's wording is CLI-only.

**CI.**

- The earlier failures on `2a228aee` and `7fda1595` were all jobs cancelled
  with no runner assigned. They were not test failures.
- On `94017380`, lint, coverage, installed-wheel smoke, and the workflow
  check passed. The desktop and test jobs were still running when this
  record was written. The commit carrying this record gets its own CI run,
  and that run is the one the merge gate checks.

**Owner's manual Mac check.** Pending when this record was written. The
owner was asked to run the Back/Forward, restart, anchor-link, and Quit
checks with `apps/desktop/scripts/run launch`. The results are recorded in
the closeout note.

**Verdict:** green on threads and review. The merge waits for CI on the
final commit and for the owner's manual check.

# Validation

- `cargo test --lib`: 39 tests passed.
- `scripts/format --check --diff --desktop` passed.
- `scripts/lint --desktop` passed.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Next is the single ask for merge and closeout, once CI is green and the
manual check is reported.

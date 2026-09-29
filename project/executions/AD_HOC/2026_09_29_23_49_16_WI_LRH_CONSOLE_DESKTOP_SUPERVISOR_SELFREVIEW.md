---
execution_id: 2026_09_29_23_49_16_WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_SUPERVISOR_SELFREVIEW)[2026-09-29T23:49:16+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SUPERVISOR.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-29T23:49:16+00:00
---

# Summary

Pre-push `/lrh-self-review` of the `WI-LRH-CONSOLE-DESKTOP-SUPERVISOR` branch,
run by `/lrh-implement` Step 7.5 before the PR was opened. It covered the
diff against `origin/main` at `66a94431`.

- Mode: diff-mode.
- Reviewer: a cold-context general-purpose subagent.
- It was report-only. The invoking session applied the verified fixes.

# Result

The verdict was "needs fixes", with 1 blocking, 4 should-fix, and 7 nit
findings.

- **Blocking, re-verified directly.** The failed-start path in
  `OwnedServer::start` escalated whenever `wait_exit` returned `None`. That
  also happens for a child that died by signal and was already reaped.
  Because of this, `libc::kill(SIGTERM)` could target a recycled PID.
  - I confirmed it by reading `supervisor.rs`: `start()` had no `!exited`
    guard, and `wait_exit` returned `exit_code` (`None` after a signal).
  - The same bug made `is_running()` return true for a child killed by a
    signal.
  - Fixed in `b515a228`:
    - `wait_for_exit` now returns an exited flag.
    - `escalate()` returns early once the child has exited.
    - `SAFETY` comments now match the code.
  - Regression test:
    `a_child_killed_by_a_signal_before_ready_is_reaped_not_signalled`.
- **Should-fix (fixed):**
  - **Kill without a wait.** A kill was not followed by a wait, so Restart
    could spawn before the old exit was observed. A blocking `wait()` after
    SIGKILL now prevents that.
  - **Late exit detection.** The handshake wait did not poll the child, so an
    exit behind a leaked stdout descriptor only surfaced at the 20 s timeout.
    It now polls in 100 ms slices. Regression test:
    `an_exit_is_noticed_even_if_a_leaked_descriptor_keeps_stdout_open`.
  - **Zombie flake.** The kill-escalation test asserted "not alive" at once,
    which a zombie could flake. It now uses `wait_until_dead`.
- **Should-fix (documented):** `status()` returns the cached status while
  another operation holds the supervisor. It is now documented as "was
  running at the last check".
- **Nits:**
  - Fixed: a relative `LRH_DESKTOP_TEST_PYTHON` is now made absolute, and the
    helper is now killed and reaped if it never reports its PID.
  - Not changed:
    - "`last_error` kept while Running": incorrect, because `Starting`
      already clears it.
    - The unbounded post-ready channel: only slow growth.
    - Protocol checks on `failed`: informational.
    - The bind-then-drop port race in one test: small.
    - Widening the desktop CI paths to all of `src/lrh/**`: it would run
      macOS desktop CI on nearly every Python PR. The protocol and serve
      modules the tests drive are already covered.

# Validation

After the fixes:

- `cargo test --locked` passed three consecutive runs, with 15 integration
  and 12 unit tests each time. No stray `lrh serve` or fake processes were
  left afterward.
- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`,
  `scripts/test --desktop` (Python suite OK), `lrh validate`, and
  `scripts/check-workflows` all pass.

# Follow-up

None. The PR's first hosted review round follows the push.

---
execution_id: 2026_10_11_02_27_35_LRH_CONSOLE_DESKTOP_LOADING_CUE_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-DESKTOP-LOADING-CUE:LRH_CONSOLE_DESKTOP_LOADING_CUE_CONFIRM)[2026-10-11T02:27:35+00:00]
work_item: WI-LRH-CONSOLE-DESKTOP-LOADING-CUE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/821
commit: 781e8871bedee22bef67617c3d1c65735ee3c51d
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/821"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-11T02:27:35+00:00
---

# Summary

This record covers confirm-fixes for PR #821 (`WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`), run as part of
`/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so a
cold-context substitute review stood in for them on the review-round head.

# Result

- **Substitute review** of `e53dea51..a848d33b`:
  - **Copilot (next navigation clears the cue):** Clear-satisfied. The thread was resolved.
  - **Codex (fragment removal):** correctly declined. The HTML navigate algorithm and WebKit's
    `FrameLoader::shouldPerformFragmentNavigation` both treat a navigation as in-page only when the
    new URL has a fragment. The thread was resolved, after the reply that gives this reasoning.
  - **Copilot (owner check):** Partial.
    - Acceptance criterion 4 is met.
    - Acceptance criterion 1 is only partly met. Restart is confirmed in the app, and the View menu
      is explained from code. The sidebar case was not reproducible, and the WebKit-painting
      hypothesis is unconfirmed.
    - The review record and the PR body overstated this.
- **Owner decision:** option A, waiving the sidebar part of criterion 1. The native cue covers it
  either way.
- **Fixes in `90ab93573e5e0cd592eaf674406349a42d95806f`:**
  - **Reload:** View > Reload of a URL with a fragment, which WebKit loads in full, showed no cue.
    `LoadingCue::expect_reload` now marks the Reload navigation. A test covers it, and the
    integration tests pass the cue to `build_main_window`.
  - **Comments:** they document the main-frame assumption (iframes and server redirects would
    restart the cue; served pages use neither), and that an in-page jump during a slow load hides
    that load's cue early. That is fail-safe.
  - **Wording:** the review record and PR body now state criterion 1 as partly met under the
    owner's waiver.
- **CI:** 7/7 green on `a848d33b`. The final head is checked before the merge ask.

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and `scripts/test --desktop`
  pass (53 shell tests plus the integration suites).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- None for this PR. Whether WebKit paints during a provisional load stays an open question, waived
  by the owner.

---
execution_id: 2026_10_08_00_31_19_LRH_CONSOLE_TOKENS
prompt_id: PROMPT(WI-LRH-CONSOLE-TOKENS:LRH_CONSOLE_TOKENS)[2026-10-07T23:24:24+00:00]
work_item: WI-LRH-CONSOLE-TOKENS
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/785
commit:
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated\")"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T00:31:19+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-TOKENS` through `/lrh-execute`: the
shared LRH Console token file, the `/style` specimen, the contrast test, and the reduced-motion
fix. The owner approved the chain and run plan in this session ("Approve as stated").

# Result

- **`src/lrh/ux/static/lrh-tokens.css` (new):** every color, space, radius, font-role, shadow
  and motion token, with the `--lrh-` prefix, seeded from the Revision 2 mock.
  - Light values sit on `:root`. Dark values are guarded by `prefers-color-scheme`, and again by
    `[data-theme="dark"]`.
  - Band tokens alias the status hues, and the earlier Serve names remain as aliases.
- **`src/lrh/ux/tokens.py` (new):** reads the packaged file with `importlib.resources` and caches
  it. `pyproject.toml` ships `static/*.css`.
- **`src/lrh/serve.py`:**
  - `_base_styles` inlines the tokens, and the policy is unchanged.
  - Five pages that set no `data-theme` now set `light`, so every existing page stays light
    until `WI-LRH-CONSOLE-THEME` lands.
  - The new `/style` specimen route follows the system theme.
- **Desktop app:** the `apps/desktop/ui/lrh-tokens.css` copy is linked before `style.css`, and
  `style.css` uses tokens instead of literal colors. Error text uses the vermillion
  `status-blocked-fg`. The `.flash` highlight and its `scrollIntoView` honor
  `prefers-reduced-motion`.
- **Tests:**
  - `tests/ux_tests/tokens_test.py` (new) covers copy sync, the packaged resource, dark-block
    parity, the prefix, alias resolution, and WCAG pairs in both themes. It also checks that
    every declared status and band is contrast-checked and shown in the specimen, that only
    `/style` follows the system theme, and the desktop styles.
  - `tests/cli_tests/serve_test.py` adds the `/style` route, inlining, and the route list.

**Spec notes:**

- The contrast test found the mock's light edge color (`#7f8ba6`) at 2.91:1 on the sunken
  surface. It is now `#78849f` (3.19:1).
- The `color.plane.*` tokens are deferred because the design has no values for them yet. The
  token file and the PR say so.

**Pre-push cold review.** It found 1 must-fix item: the five unthemed Serve pages would have
turned dark on a dark-mode system. It also found 4 should-fix items: hand-listed states could
skip the checks, some pairs in use were undeclared, the specimen test was weak, and the plane
deferral needed naming. All were applied in `e4d12381`, along with one nit (a bare `assert`).

# Validation

- `scripts/format --check --diff --desktop`, `scripts/lint --desktop`, and
  `scripts/test --desktop` pass: 1968 Python tests, and the desktop tests (42, 9, and 22).
- `lrh validate`: 0 errors, 0 warnings.
- A wheel built with `python -m build` contains `lrh/ux/static/lrh-tokens.css`.
- `/style` was checked in the browser pane in light and dark mode. `/` stays light with the
  system set to dark.

# Follow-up

- `WI-LRH-CONSOLE-THEME` removes the hard-coded `data-theme` and adds `--theme`.
- The owner can check the desktop Settings window in dark mode, where native controls now follow
  `color-scheme: dark`.

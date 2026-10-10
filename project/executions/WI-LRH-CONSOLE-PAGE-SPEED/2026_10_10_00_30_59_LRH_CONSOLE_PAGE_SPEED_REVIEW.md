---
execution_id: 2026_10_10_00_30_59_LRH_CONSOLE_PAGE_SPEED_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-PAGE-SPEED:LRH_CONSOLE_PAGE_SPEED_REVIEW)[2026-10-10T00:30:59+00:00]
work_item: WI-LRH-CONSOLE-PAGE-SPEED
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/811
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/811"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-10T00:30:59+00:00
---

# Summary

This record covers review-response round 1 for PR #811 (`WI-LRH-CONSOLE-PAGE-SPEED`), run as part of
`/lrh-land` inside `/lrh-execute`. It combines the owner's check of this branch's LRH Console build
with two bot threads.

- **CI** passed 7/7 on `b04f4632`.
- **The owner's check:**
  - speed is much improved, and second visits are "lightning fast";
  - the loading pill was not seen, except possibly on the first Workbench load;
  - checking that edits appear was deferred as not urgent, since a server test covers it.
- **The owner also found a bug that predates this PR.** A registered project with no local
  checkout (LCATS) shows the served project's dependency map. `_config_for_project_selector`
  falls back to the served project. At the owner's choice, this was spun off as a separate task.

# Result

- **Codex P2, `parser.py`:** `items: [a?b]` passes libyaml but fails the pure loader, a case the
  guard missed even after 300k fuzzed inputs. I measured the options: keeping libyaml with a wider
  guard, dropping it, or dropping it and adding a background warm-up. The owner chose to drop
  libyaml.
  - `parser.py` is back to `main`, so parsing is exact by construction.
  - The scalar-kind memo and the project-state cache stay.
  - The fast-loader tests were removed.
  - Warm pages are unchanged at about 55 ms. First visits are about 2.0 to 2.7 s.
  - `WI-LRH-CONSOLE-CACHE-WARMUP` was filed for fast first visits and added after PAGE-SPEED in
    the workstream.
- **Copilot, `serve.py` `_build_snapshot`:** a cached snapshot showed its old `generated_at`, so a
  cached render differed from a fresh one. Cache hits now get the current time, alongside the
  freshly read git HEAD. The test now proves the cache hit by counting builds.

Fix commit: `54d349701e183e081ae803b7aaa0b15f49f0f72a`.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass.
- `lrh validate`: 0 errors, 0 warnings.
- Validation reports match `main` on this repo and on the broken-YAML copy.
- Timings on the owner's registry, first visit then repeat:
  - `/meta`: 2.71 s, then 0.055 s;
  - `/`: 2.04 s, then 0.052 s;
  - the project page: 0.06 s, then 0.056 s;
  - the dependency map: 0.81 s, then 0.046 s.

# Follow-up

- Confirm-fixes with a substitute cold review, since hosted bots review only the first push.
- `WI-LRH-CONSOLE-CACHE-WARMUP`, and the spun-off fix for project pages with no checkout.

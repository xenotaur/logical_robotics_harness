---
execution_id: 2026_10_10_00_13_31_LRH_CONSOLE_PAGE_SPEED
prompt_id: PROMPT(WI-LRH-CONSOLE-PAGE-SPEED:LRH_CONSOLE_PAGE_SPEED)[2026-10-09T23:45:49+00:00]
work_item: WI-LRH-CONSOLE-PAGE-SPEED
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/811
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/811"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-10T00:13:31+00:00
---

# Summary

`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` resolved to `WI-LRH-CONSOLE-PAGE-SPEED`, the first
unfinished item in the workstream's order:

- its dependency (STATUSBOARD) was resolved;
- readiness was `prompt_ready: yes` with no warnings;
- there was no prior record;
- open bot PRs #630 and #658 touch only `prompt_workflow_records.py`.

At the chain gate the owner approved the plan, including a loading indication built into the
`--interactive` script rather than a native overlay, which keeps the main window capability-free.

# Result

Profiling corrected the work item's diagnosis. Files were not parsed many times over. Of the
28,563 `safe_load` calls, 23,569 came from frontmatter lint's per-scalar type check, and the rest
were one parse per file through the pure-Python loader.

- **YAML:**
  - `parser.safe_load_fast` uses libyaml when available.
  - Text that the two loaders could disagree on always takes the pure loader, and any error is
    re-parsed with the pure loader, so messages are byte-identical.
  - The disagreeing text covers tabs, a bare `!`, `|#` headers, `\r`, NEL, BOM, and Unicode line
    separators. It was found by fuzzing after the pre-push review caught the tab case.
- **Lint:** the scalar-kind check is memoized.
- **Cache:** `core_state.ProjectStateCache` is keyed by a `project/` fingerprint (path, size,
  mtime in ns, inode; symlinked directories followed). `lrh serve` caches core state, loaded
  projects, and dependency-map snapshots, and reads a snapshot's git HEAD fresh on each request.
- **Loading:** `--interactive` pages dim and show a "Loading…" status after 300 ms on same-origin
  navigations.
- **Timings, warm** (owner's registry, `main` to branch): about 2.5 s to about 55 ms on every
  page. First requests are about 3x faster. `validate_project` dropped from 2.6 s to about 0.5 s.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass.
- `lrh validate`: 0 errors, 0 warnings.
- Validation reports match `main` exactly, on this repo and on a copy with broken YAML.
- 300k fuzzed inputs agree between the two loaders under the guard.
- The loading cue was checked in the browser pane: it appears after 300 ms, dims the page, and
  clears on `pageshow`.

# Follow-up

- An owner check of navigation speed in this branch's LRH Console build.
- Known limit: a same-size edit within one filesystem timestamp tick is not detected until the
  next change. This is documented in `docs/reference/cli/serve.md`.

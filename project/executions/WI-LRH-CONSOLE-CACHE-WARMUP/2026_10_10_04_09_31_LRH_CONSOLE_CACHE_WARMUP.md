---
execution_id: 2026_10_10_04_09_31_LRH_CONSOLE_CACHE_WARMUP
prompt_id: PROMPT(WI-LRH-CONSOLE-CACHE-WARMUP:LRH_CONSOLE_CACHE_WARMUP)[2026-10-10T02:41:27+00:00]
work_item: WI-LRH-CONSOLE-CACHE-WARMUP
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/817
commit: 3cff4c292ce3792cfeaaceb45c18af745d901dc4
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/817"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-10T04:09:31+00:00
---

# Summary

`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` resolved to `WI-LRH-CONSOLE-CACHE-WARMUP`, the first
unfinished item in the workstream's order:

- its dependency (PAGE-SPEED) was resolved;
- readiness was `prompt_ready: yes`;
- there was no prior record.

At the chain gate the owner approved the plan. It also covered filing
`WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`, because in the app the page-script pill never showed, even
on sidebar clicks, and carrying the owner's pending edit check into this item's validation notes.

# Result

- **Single-flight `ProjectStateCache`:**
  - concurrent misses on one key and fingerprint share one build;
  - a waiter on a failed build builds for itself;
  - waiters fall back to their own build after 60 s.
- **Warm-up:** `warm_caches` and `start_cache_warmup` fill, in order:
  1. `/meta`'s projects;
  2. the served project;
  3. every project's loaded control files and dependency-map views, deduplicated.

  Warm-up runs on one daemon thread and writes one stderr line.
- **Start order:**
  - foreground mode starts warm-up after the `listening on` line;
  - desktop mode starts it after `ready`, through a new `on_ready` hook in `desktop_protocol`.
    This file was not in the planned list. The hook was needed for the "never delays ready"
    criterion, after the pre-push review found the first version starting warm-up before the
    self-check.
- **Shared root lookup:** `/meta`'s registered-root lookup was extracted into
  `_registered_project_root`. Warm-up's first version had found no registered projects.
- **Pre-push cold review:** found no single-flight correctness bugs. It did find six gaps, all
  fixed in `4e668038`:
  - the warm-up missed the loaded-project entry;
  - desktop warm-up started before `ready`;
  - the single-flight tests did not block;
  - waiters had no timeout;
  - snapshot warm-up made a git call per view;
  - the project count included duplicates.
- **Timings** (owner's registry):
  - after warm-up, which takes about 7 s: about 50 to 80 ms on every page;
  - 3 s after start: 0.3 to 1.5 s;
  - a request at second 0 shares warm-up's builds, so it takes about the same as a cold load
    (2.4 s for `/meta`).

# Validation

- `scripts/format --check --diff`, `scripts/lint`, `scripts/test` (2203 tests), and
  `tests/smoke/desktop_protocol_smoke.py` pass.
- One full-suite run on a heavily loaded machine reported one error. It did not reproduce on a
  rerun, or in six repeated runs of the new threaded test modules.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- An owner check of first-visit speed in this branch's LRH Console build, plus the carried-over
  edit check.
- `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`.

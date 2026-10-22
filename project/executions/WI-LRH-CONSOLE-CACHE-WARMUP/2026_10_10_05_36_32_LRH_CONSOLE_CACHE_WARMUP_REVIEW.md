---
execution_id: 2026_10_10_05_36_32_LRH_CONSOLE_CACHE_WARMUP_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-CACHE-WARMUP:LRH_CONSOLE_CACHE_WARMUP_REVIEW)[2026-10-10T05:36:32+00:00]
work_item: WI-LRH-CONSOLE-CACHE-WARMUP
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/817
commit: 3cff4c292ce3792cfeaaceb45c18af745d901dc4
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/817"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-10T05:36:32+00:00
---

# Summary

This record covers review-response round 1 for PR #817 (`WI-LRH-CONSOLE-CACHE-WARMUP`), run as part
of `/lrh-land` inside `/lrh-execute`. It combines the owner's check of this branch's LRH Console
build with four bot threads.

- **CI** passed 7/7 on `a55211b5`.
- **The owner's check**, run after Server > Restart:
  - startup lands on the Statusboard, with a first load of about 2 to 3 s;
  - first clicks after that "feel instant".
- **Copilot** left 3 threads and **Codex** left 1 P2 thread. All were valid, and the owner approved
  all four fixes.

# Result

- **Copilot, `core_state.py` fallback:** a waiter's successful fallback build, after the owner
  failed or the 60 s wait ran out, was returned but never stored. It is now published through a
  shared `_store`, unless an entry with the same fingerprint already exists. A test checks that
  the next caller hits the cache.
- **Copilot, `serve.py` de-duplication:** roots are now de-duplicated on the `project/` directory
  they resolve to (`_control_dir_key`), so a nested `project_dir` reached two ways is warmed and
  counted once.
- **Copilot, `serve.py` silent view failures:**
  - `warm_caches` returns `WarmupResult(projects, failures)`;
  - `start_cache_warmup` logs each skipped item and adds ", N item(s) failed" to the summary line;
  - a test covers this with a broken view.
- **Codex P2, cache capacity:**
  - `ProjectStateCache.reserve(n)` grows capacity and never shrinks it;
  - before warming anything, warm-up plans its roots and views and reserves twice its entry count,
    so later entries never evict `/meta`'s on large registries.
- **Docs:** `docs/reference/cli/serve.md` describes the failure lines and the capacity sizing.

Fix commit: `583a9e40f67a1c9cb83d4802a4cf1a87ab8e2d13`.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, `scripts/test` (2206 tests), and
  `tests/smoke/desktop_protocol_smoke.py` pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Confirm-fixes with a substitute cold review, since hosted bots review only the first push.

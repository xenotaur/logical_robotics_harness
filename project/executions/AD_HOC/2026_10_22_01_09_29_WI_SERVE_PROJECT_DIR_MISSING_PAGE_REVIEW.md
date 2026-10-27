---
execution_id: 2026_10_22_01_09_29_WI_SERVE_PROJECT_DIR_MISSING_PAGE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE_REVIEW)[2026-10-15T05:38:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_13_06_18_05_WI_SERVE_PROJECT_DIR_MISSING_PAGE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/841
commit: a94f15d4e783d52c7e95e79105c74b47e31a8ba6
created_at: 2026-10-22T01:09:29+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/841
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Review-response round 1 for PR 841, run inline from `/lrh-land` Step 4. It
addresses the three first-push bot threads on the new work item
`WI-SERVE-PROJECT-DIR-MISSING-PAGE` and resolves a merge conflict with
`main`.

# Result

The fix is commit `412b00e8b830c1900d596f278d0ddd20e7b6d77d`. The merge commit is `084c847f`.

1. **Same finding from two reviewers.** chatgpt-codex-connector (P2,
   `PRRT_kwDOR7l1D86ru7LI`) and copilot-pull-request-reviewer
   (`PRRT_kwDOR7l1D86ru7xc`) both said `lrh project init --project-root
   <repo>` cannot fix a record with a custom `project_dir`.
   - **Verified:** `src/lrh/project/bootstrap.py` `build_plan` writes the
     packaged templates at fixed `project/...` paths under the repo.
   - **Fixed:** the next actions now depend on the directory. A default
     `<repo>/project` gets init and repoint. A custom `project_dir` gets
     repoint, or init followed by `lrh meta set <name> --project-dir
     project`, and never init alone.
   - Updated to match: Problem/Context, Required Changes 1-2, the tests (now
     covering unset, explicit `project`, and non-default `control`), both
     acceptance lists, and Risk Notes.
2. **Validation order.** copilot-pull-request-reviewer
   (`PRRT_kwDOR7l1D86ru7x2`) asked for `scripts/version tools` as the first
   Validation command.
   - **Verified:** `AGENTS.md:168`.
   - **Fixed:** added as the first bullet.
3. **Merge conflict with `main`.** I ran the app's `sync_with_base_branch`
   (base `main`). The only conflict was in `WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
   `work_items:`. I kept `main`'s five new entries and then this PR's
   `WI-SERVE-PROJECT-DIR-MISSING-PAGE`.

# Validation

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`. Black was
26.3.1 and Ruff 0.15.12.

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2362 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- Readiness: prompt-ready.

# Follow-up

- `/lrh-land` Step 5 (confirm-fixes) resolves the three threads.

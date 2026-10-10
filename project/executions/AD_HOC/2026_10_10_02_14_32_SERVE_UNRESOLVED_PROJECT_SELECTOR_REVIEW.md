---
execution_id: 2026_10_10_02_14_32_SERVE_UNRESOLVED_PROJECT_SELECTOR_REVIEW
prompt_id: PROMPT(AD_HOC:SERVE_UNRESOLVED_PROJECT_SELECTOR_REVIEW)[2026-10-10T02:09:01+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_01_17_08_SERVE_UNRESOLVED_PROJECT_SELECTOR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/813
commit: d9f5b1bd2c829e40b366421fecf4a2c83cd3a42a
created_at: 2026-10-10T02:14:32+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/813
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Review-response round 1 for PR 813, run inline from `/lrh-land` Step 4. It
addresses the two first-push bot threads: Copilot on `df65c5bb` and Codex on
`48a62924`.

# Result

Fix commit `775275e69d94a52d41cdf8e5bbd9dbaa02596d43`.

1. **copilot-pull-request-reviewer (high), `PRRT_kwDOR7l1D86q_i4F`.** The
   `main` fallback still applied to every `MetaRegistryError`. **Fixed.**
   - Workspace resolution and registry inspection are now split.
   - `main` falls back only when no Meta workspace exists, or when
     `_registry_has_no_match` confirms the registry reads cleanly with no
     matching record.
   - An ambiguous selector or an unreadable registry returns 404, carrying
     the registry's message.
   - New test: `test_main_does_not_fall_back_when_the_registry_cannot_decide`
     covers an ambiguous `main` (HTML and API) and a malformed record.
2. **chatgpt-codex-connector (P2), `PRRT_kwDOR7l1D86q_jTN`.** A record that
   omits `project_dir` was reported as `no_local_checkout`. **Fixed.**
   - When the repo path resolves and the record has no `project_dir`, the
     project path defaults to `<repo>/project`. This matches serve's
     `_registered_project_control_root`.
   - An explicit but invalid `project_dir` (absolute, or escaping the repo)
     still gets no default.
   - New test: `test_project_routes_default_a_record_without_project_dir`.
3. `docs/reference/cli/serve.md` "Project selectors" now reflects both
   behaviors.

No threads were skipped.

# Validation

Run in the `LrhLocalAgent` env with `PYTHONPATH=src`. Versions: Black 26.3.1,
Ruff 0.15.12.

- `scripts/format --check --diff`: 295 files unchanged.
- `scripts/lint`: passed.
- `scripts/test`: 2188 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `/lrh-land` Step 5 (confirm-fixes) resolves the two threads.

---
execution_id: 2026_09_26_08_19_25_WI_TEST_OUTPUT_SUPPRESSION_AUDIT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TEST_OUTPUT_SUPPRESSION_AUDIT_REVIEW)[2026-09-26T08:19:06+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_08_10_29_WI_TEST_OUTPUT_SUPPRESSION_AUDIT_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/736
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/736
session_transcript: claude-app:42f65eea-a5d0-4b14-b12d-fdac79928916
created_at: 2026-09-26T08:19:25+00:00
---

# Summary

Second review-response round on PR #736: a fresh `lrh request review_response`
call after the first round's push surfaced 2 new Codex comments (the first
round's 2 Copilot comments had gone outdated once their anchor lines moved,
not resolved).

# Result

1. **Restrict suppression to noisy call sites** (`r4110663753`, Codex,
   P2) — fixed. `ReleaseSmokeRunTest`'s class-level `setUp`/`addCleanup`
   wrapped an entire test method's lifecycle in `suppress_output()`, not
   just the one noisy `run_release_smoke(...)` call, contradicting this
   PR's own STYLE.md principle (preserve deliberate debugging prints;
   suppress at the call site, per test). Removed the class-level wrap;
   wrapped each of the 8 individual `run_release_smoke(...)` call sites
   in its own `with testing_support.suppress_output():` block. Verified
   the 3 tests in this class that assert on printed content
   (`mock.patch("builtins.print")`) still pass -- that mechanism is
   independent of the `sys.stdout`/`sys.stderr` redirection
   `suppress_output()` performs.
2. **Remaining in-process warning** (`r4110663748`, Codex, P2) —
   skipped. Real finding (`datetime.datetime.utcnow()` in
   `src/lrh/guardrails/models.py` is deprecated on Python 3.12+ and would
   emit a warning there), but out of scope for this PR: pre-existing,
   unrelated production code untouched by this PR's diff (confirmed via
   `git diff origin/main -- src/lrh/guardrails/models.py`, empty), and
   this project's CI and local dev both pin Python 3.11 (confirmed via
   `.github/workflows/*.yml` and `scripts/version tools`), where
   `utcnow()` does not warn. Flagged separately as a follow-up task
   rather than folded into this PR.

No comments were skipped without rationale.

# Validation

- `scripts/format --check --diff` — clean after one `scripts/format`
  auto-fix pass (263 files, pinned tool versions: ruff 0.15.12, black
  26.3.1).
- `scripts/lint` — clean (ruff, black, test framework guardrails).
- `scripts/test tests.dev_tests.release_smoke_test -v` — 28/28 OK.
- `scripts/test` (full suite) — 1806 tests, OK, zero unexpected output.
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

`datetime.datetime.utcnow()` deprecation in `src/lrh/guardrails/models.py`
flagged as a separate follow-up task (out of this PR's scope).

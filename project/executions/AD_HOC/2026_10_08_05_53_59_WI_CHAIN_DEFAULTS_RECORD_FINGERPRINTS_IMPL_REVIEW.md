---
execution_id: 2026_10_08_05_53_59_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_REVIEW)[2026-10-07T23:02:43+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_07_16_28_36_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/783
commit: 
created_at: 2026-10-08T05:53:59+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/783
session_transcript: pending
---

# Summary

Review-response round 1 on PR #783 (the `WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS`
implementation), run inline from `/lrh-land` Step 4 within `/lrh-execute`.
There were 6 open threads: 4 from Copilot, and a P1 and a P2 from Codex. All
were accepted and fixed in commit `1a4aa5d8`. Two of the threads duplicated
each other.

# Result

- **Codex P1 `r4209472029`: the approved preview and the applied re-stamp were
  not bound together.** Fixed.
  - `RestampPlan.digest` is a SHA-256 over the stale files, every
    fingerprint entry (name, comparison, hash), and the previous and new
    commit. It deliberately excludes `confirmed_at`.
  - `--dry-run` prints `plan_digest`.
  - `restamp --expect-digest` refuses with exit 2 and writes nothing on a
    mismatch.
  - Every re-stamp site in `_shared/chain-defaults.md` and `land-workflow.md`
    (kept in sync), `/lrh-config-gates` Step 3b, and the CLI docs now use
    the `--dry-run` then `--expect-digest` pair.
- **Copilot `r4209428245`: a failed staleness check was downgraded to
  display-only.** Fixed. `plan_restamp` now refuses when the check fails;
  only the null/absent first-encounter case proceeds without a stale-files
  payload.
- **Copilot `r4209428413` and Codex P2 `r4209472048`: a `read_bytes`
  `OSError` escaped as a traceback.** Fixed. `plan_fingerprints` converts it
  to `GateStalenessError`, so the CLI exits 2.
- **Copilot `r4209428318`: a same-second re-stamp of the same `HEAD`
  produced an identical stamp.** Fixed. `plan_restamp` refuses when the new
  stamp equals the profile's current canonical stamp.
- **Copilot `r4209428539`: the profile-write-failure test did not simulate a
  failure.** Fixed by adding
  `test_profile_replace_failure_after_store_write_fails_closed`. It injects
  an `os.replace` failure on the profile only, then asserts:
  - a clean error is raised;
  - the store was written;
  - the old profile and consent are intact;
  - user-scope targets stay fail-closed.

  The existing git-checkout test is kept, since it models a declined push.

Other new tests:
- digest mismatch refuses, and a matching digest applies (the time is
  excluded from the digest);
- a failed staleness check refuses;
- an unreadable target refuses;
- an identical stamp refuses;
- the CLI exits 2 on an `--expect-digest` mismatch.

The CLI happy-path test now goes through `--dry-run`, then `--expect-digest`.

The PR body was updated for the digest flow.

# Validation

Run with the LRH conda env:
- `scripts/format` and `scripts/lint`: clean.
- `scripts/test`: OK.
- `lrh validate`: 0 errors, plus 1 warning that predates this work.
- `lrh skills check`: up to date for both skills on all three targets.

# Follow-up

- Confirm-fixes must resolve the 6 threads against `1a4aa5d8`.

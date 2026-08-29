---
execution_id: 2026_08_29_05_24_37_WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_CONFIRM)[2026-08-29T05:24:28+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_28_20_30_16_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/648
commit: 60d0597a
created_at: 2026-08-29T05:24:37+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/648
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

`/lrh-confirm-fixes` pre-merge verification pass for PR #648
(`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT` filing).

# Result

1 review thread (Codex P1, automatic first-push), classified real and
substantive — a genuine gap in the WI's own scope, not a wording nit:
the WI's original Required Change #2 assumed a `git show`-based
comparison would work for any resolved installed-target path, but the
documented default (user-scope) install lives entirely outside any git
working tree (`installer.py`'s `_default_skills_dir` resolves under
`Path.home()`), so no git history exists there to diff against
`confirmed_commit` regardless of which path is watched.

Verified directly against `installer.py` before fixing. Split Required
Change #2 into two explicit cases (project-local git-tracked target vs.
user-scope/untracked target requiring a persisted content fingerprint
instead), added an explicit fail-closed requirement, and added a Risk
Notes warning that a fixture committing the installed path would hide
this exact gap — which the WI's own originally-prescribed fixture
would have done.

Thread resolved via GraphQL `resolveReviewThread` after posting a
reply with the fix commit and verification.

Thread-resolution verdict (Step 6): **green** — 0 unresolved threads.

# Validation

- `lrh validate`: 0 errors, 0 warnings
- CI on commit `60d0597a`: `coverage`, `installed-wheel-smoke`, `lint`,
  `Check workflow files`, `tests` — all pass

# Follow-up

- None outstanding for this PR. The implementation itself
  (`src/lrh/gate_staleness.py` changes) is not started — this PR only
  files/refines the planning artifact.

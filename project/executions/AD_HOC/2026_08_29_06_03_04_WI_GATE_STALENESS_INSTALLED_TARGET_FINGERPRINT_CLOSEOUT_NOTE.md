---
execution_id: 2026_08_29_06_03_04_WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_CLOSEOUT_NOTE)[2026-08-29T06:02:59+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_28_20_30_16_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/648
commit: 7b5c8a409d67953435d9cda3cfb707ea603f8df0
created_at: 2026-08-29T06:03:04+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/648
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

CHAIN-NOTE record for `/lrh-land`'s Step 7 closeout of PR #648
(`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT` filing). The primary
record's body is immutable per the Found-or-Backfill Matrix, so this
CHAIN-NOTE is recorded here instead.

# Result

One `/lrh-confirm-fixes` round ran on PR #648: 1 real Codex P1 finding
from the automatic first-push bot review. The finding was substantive,
not cosmetic — it caught a genuine gap in the WI's own Required
Changes: the WI as originally drafted assumed a `git show`-based
comparison would work for any resolved installed-target path, but the
documented default (user-scope) install lives entirely outside any git
working tree. Verified directly against `installer.py`'s
`_default_skills_dir` before fixing. Split the requirement into two
cases (project-local git-tracked vs. user-scope/untracked, the latter
requiring a persisted content fingerprint) and added an explicit
fail-closed requirement. No self-review substitution needed — the
bot's auto-review surfaced the finding on the reviewed round.

CHAIN-NOTE:

```text
cycles=1; stops=0; gates=[merge]; friction=none; self_review_rounds=0; bot_rounds=1; note="review caught a real scope gap in the WI's own Required Changes -- git-based comparison assumed a git-tracked target, but the default user-scope install has no git history at all"
```

# Validation

- `lrh validate`: 0 errors, 0 warnings (post-closeout)
- PR #648: `MERGED`, commit `7b5c8a409d67953435d9cda3cfb707ea603f8df0`
- All 5 CI checks passed on the final pushed commit (`b83dca75`) prior
  to merge

# Follow-up

- The actual implementation (`src/lrh/gate_staleness.py` changes this
  WI describes) has not started — this PR only filed and refined the
  planning artifact.
- 5 of PR #512's 6 original review threads are now resolved; the P1
  thread this WI directly answers remains open on PR #512 itself
  (intentionally — it stays open until the implementation, not just
  the filing, lands).

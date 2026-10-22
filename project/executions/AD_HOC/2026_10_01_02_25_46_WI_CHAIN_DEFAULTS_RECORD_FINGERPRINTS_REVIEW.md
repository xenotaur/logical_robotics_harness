---
execution_id: 2026_10_01_02_25_46_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW)[2026-10-01T02:22:39+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_30_21_42_33_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/753
commit: 6aec589a9b9a942cc1f8812ca9e28282e12d848b
created_at: 2026-10-01T02:25:46+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/753
session_transcript: claude-app:708f8a5c-20da-4910-bafb-fdecde18e51e
---

# Summary

Review-response round 3 on PR #753, run inline from `/lrh-land` Step 5.

Re-verification of round 2 found a new P2. The run's stop-work condition
fired: "a reviewer finding that isn't Clear-satisfied on re-verification."
The run stopped and reported. The user explicitly lifted the stop for this
one round and chose the fix: bind the fingerprint store to its stamp.

The fix is in commit `36ac404d`.

# Result

**P2: the fail-closed claim in Risk Notes was false for fingerprint-only
client repos.** Fixed.

The problem:
- In a client repo with only a user-scope install, every target is
  fingerprint-kind (`src/lrh/gate_staleness.py:429`), and staleness is
  `any(...)` over those targets (`:623`).
- So a store written before (or without) the matching committed profile
  made the repo read fresh while its old consent stayed valid. That covered
  three cases: a failed profile write, a declined `main` push, and a branch
  still carrying the old profile.

The fix:
- The WI now requires the store to record `confirmed_commit` alongside the
  hashes.
- `check_gate_staleness` accepts the store only when that value equals the
  `confirmed_commit` it checks against. A mismatch, or an old-format bare
  map, fails every fingerprint-kind target closed, with a distinct reason.
- `restamp` writes the same stamp to the store and the profile.

Other WI updates:
- The Risk Notes "Partial failure" and "Declined `main` push" bullets were
  corrected.
- A "Shared store, branch-local profile" note was added.
- New acceptance criteria were added, and the worktree criterion was
  amended.
- New stamp-binding tests were added, using a fingerprint-only fixture.

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings.
- `scripts/test`: OK.
- `scripts/lint` and `scripts/format --check --diff` were not run because
  of local tool-version pins (ruff 0.15.12 required vs 0.15.0 installed;
  black 26.3.1 required vs 25.11.0 installed). This PR changes Markdown only.

# Follow-up

- Confirm-fixes must re-verify `36ac404d` before writing the `_CONFIRM`
  record and making the merge ask.

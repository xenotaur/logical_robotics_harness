---
execution_id: 2026_10_07_16_28_36_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL
prompt_id: PROMPT(WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL)[2026-10-07T16:00:15+00:00]
work_item: WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/783
commit: 53b839a564a73f0b80ec24f0d0f5d6710baf2566
created_at: 2026-10-07T16:28:36+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS.md
session_transcript: claude-app:708f8a5c-20da-4910-bafb-fdecde18e51e
---

# Summary

Implemented `WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS` through
`/lrh-execute WS-INVOCATION-AND-GATE-RESET`, which selected it as the first
ready WI in list order. The work adds `lrh chain-defaults restamp`, which
re-stamps `confirmed_commit`/`confirmed_at` and records user-scope
installed-target fingerprints bound to that same stamp, as one act.

The branch and slug carry an `-impl` suffix so they don't collide with the
planning PR's branch (#753). The user approved that at the Step 2 gate, along
with a run-scoped `merge_pr` override and a P3 policy.

# Result

**`src/lrh/gate_staleness.py`**
- The fingerprint store moves to `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`
  (`fingerprint_store_path`).
- The store is now a `FingerprintStore` holding
  `{confirmed_commit, confirmed_at, fingerprints}`.
- `canonical_confirmed_at` normalizes values to one form. It rejects
  timezone-less or fractional-second values, which resolves the P3 deferred
  from the planning PR.
- `plan_fingerprints` produces new/unchanged/changed/removed entries and
  refuses on any unresolved or missing target, which fixes the old `{}` bug.
- `record_fingerprints` is now stamp-bound and replaces the whole map.
- `check_gate_staleness(confirmed_at=...)` accepts the store only on an
  exact stamp match, comparing `confirmed_commit` as a full SHA.

**`src/lrh/chain_defaults_status.py`**
- New `plan_restamp`, `apply_restamp` and the restamp formatters.
- `apply_restamp` rewrites only the two stamp lines, and refuses before
  writing anything if those lines are malformed.
- `compute_status` passes `confirmed_at` through.

**`src/lrh/cli/main.py`**
- New `restamp` subcommand (`--dry-run`, `--format`).
- `check-staleness` gains `--confirmed-at`.

**Skill text**
- `_shared/chain-defaults.md` and `land-workflow.md` (kept in sync): every
  re-stamp site now uses `restamp`, the staleness snippet passes
  `--confirmed-at`, and both sanctioned re-stamp points are named.
- `lrh-config-gates/SKILL.md`: new Step 3b re-confirm, a fingerprint summary
  in Step 2, a widened Step 5, and the PR-branch and `main` fast-forward
  handling.

**Docs and rendered skills**
- `docs/reference/cli/chain-defaults.md` is updated.
- Rendered skill copies are regenerated for claude, codex and antigravity.

**Tests**
- New tests in `tests/gate_staleness_test.py` and
  `tests/chain_defaults_status_test.py`.
- New file `tests/cli_tests/chain_defaults_test.py`.

The diff-mode self-review found 1 P2 and 4 P3s. All were verified and fixed
before the first push; see the `_SELFREVIEW` record.

# Validation

Run with the LRH conda env (Python 3.11.15, ruff 0.15.12, black 26.3.1).

- `scripts/format` (after auto-format) and `scripts/lint`: clean.
- `scripts/test`: OK.
- `lrh validate`: 0 errors, plus 1 warning that predates this change.
- `lrh chain-defaults restamp --project-root . --dry-run`: "nothing to
  fingerprint", which is correct for the harness repo.
- `lrh chain-defaults status --format json`: runs cleanly.
- `lrh skills check --target claude|codex|antigravity --local`: both skills
  up to date.

# Follow-up

- After merge, this repo's chain-defaults will read stale once, because this
  PR deliberately edits `GATE-DEFINITION` regions.
- Still deferred, as Non-Goals: the `DEC-GATE-POLICY-CASCADE` Decision 4
  amendment, gate-text snapshots, and marker-scoped fingerprinting.

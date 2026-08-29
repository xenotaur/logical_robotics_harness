---
execution_id: 2026_08_29_07_48_38_WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_GATE_STALENESS_INSTALLED_TARGET_FINGERPRINT_IMPL_REVIEW)[2026-08-29T07:47:57+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_29_06_10_00_FIX_GATE_STALENESS_INSTALLED_TARGET
pr: https://github.com/xenotaur/logical_robotics_harness/pull/649
commit:
created_at: 2026-08-29T07:48:38+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/649
session_transcript: pending
---

# Summary

`/lrh-review-response` pass on PR #649's automatic first-push review
(Copilot + Codex), addressing the 8 comments it surfaced (2 duplicate
pairs).

# Result

- **Copilot** (`discussion_r3885912138`/`r3885912170`, duplicate):
  `zip(canonical_names, DEFAULT_WATCHED_FILES)` silently truncates on a
  length mismatch. Valid, fixed: `resolve_watch_targets`'s self-check
  branch now raises `GateStalenessError` up front if the lengths differ.
- **Copilot** (`discussion_r3885912180`): bare `assert` for runtime
  validation is unsafe under `python -O`. Valid, fixed: replaced both
  asserts in `check_target_staleness` with explicit `GateStalenessError`
  raises.
- **Copilot** (`discussion_r3885912187`): fingerprint persistence wrote
  without explicit encoding and non-atomically. Valid, fixed:
  `record_fingerprints` now writes UTF-8 to a temp file in the same
  directory, then `os.replace`s it into place.
- **Copilot** (`discussion_r3885912198`/`r3885912209`, duplicate):
  `WatchTarget.kind` was a free-form `str`. Valid, fixed: typed as
  `typing.Literal["git", "fingerprint", "unresolved"]`.
- **Copilot** (`discussion_r3885912219`): no test asserted
  `record_fingerprints` raises on a missing target file. Valid, fixed:
  added `test_record_fingerprints_raises_on_missing_target_file`,
  asserting the canonical name appears in the exception message.
- **Codex P1** (`discussion_r3885914683`): `CANONICAL_SKILL_NAMES`
  included `_shared/chain-defaults.md`, but `installer.py`'s own
  `skill_names()` unconditionally excludes `_`-prefixed directories from
  every real install -- so that file never exists at any installed
  target. This made every project-local installed-target check fail
  closed permanently (via `strict_absence`), and made
  `record_fingerprints` raise on its very first entry, before recording
  anything at all -- a real correctness bug, independently re-verified
  by reading `installer.py`'s `SkillSource.skill_names` directly before
  fixing. Fixed: added `INSTALLED_CANONICAL_SKILL_NAMES` (the same list
  minus any `_`-prefixed top segment), used by default whenever
  resolving against an actual installed target; the harness's own
  self-check is unaffected (unchanged `CANONICAL_SKILL_NAMES`/
  `DEFAULT_WATCHED_FILES` pairing). Added two regression tests:
  `_shared/chain-defaults.md` is never in a resolved installed-target
  watch set, and `record_fingerprints` succeeds against a fixture
  matching what the real installer actually produces.
- **Codex P1** (`discussion_r3885914685`): `record_fingerprints` has no
  production caller anywhere in this repo, so a real user-scope install
  always fails closed. Valid concern, **not fixed in this PR** --
  feasibility check fails: no `skip_if_opted_in` consent-grant call site
  exists anywhere in this repo yet to wire it into (no `lrh
  chain-defaults grant`/`confirm` CLI command), and wiring one is outside
  this WI's own stated `artifacts_expected` scope
  (`src/lrh/gate_staleness.py` + `tests/gate_staleness_test.py` only).
  Already tracked as a Follow-up in both the primary execution record and
  the diff-mode self-review record; fail-closed is the safe interim
  behavior, not a regression from before this PR (which was actively
  wrong for installed targets, not merely not-yet-usable).

# Validation

- `python3 -m unittest tests.gate_staleness_test tests.chain_defaults_status_test -v`: 40/40 pass
- `scripts/format --check --diff`, `scripts/lint`: clean
- `lrh validate`: 0 errors (1 pre-existing, unrelated warning on the WI
  file's own frontmatter)

# Follow-up

- Wire `record_fingerprints` into a real `skip_if_opted_in`
  consent-grant call site once one exists in this repo (per Codex's
  second P1 above and the primary record's own Follow-up).

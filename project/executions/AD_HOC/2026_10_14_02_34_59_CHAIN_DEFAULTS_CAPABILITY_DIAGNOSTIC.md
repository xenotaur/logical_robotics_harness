---
execution_id: 2026_10_14_02_34_59_CHAIN_DEFAULTS_CAPABILITY_DIAGNOSTIC
prompt_id: PROMPT(AD_HOC:CHAIN_DEFAULTS_CAPABILITY_DIAGNOSTIC)[2026-10-14T01:59:07+00:00]
work_item: AD_HOC
status: landed
agent: claude_app
instruction_source: ad-hoc task via /lrh-implement (chain-defaults CLI/skill capability-mismatch diagnostic; handoff from an LCATS /lrh-land session)
session_transcript: claude-app:be3e3683-be69-4c9d-b790-4aeee0e23183
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/844
commit: 9958ad603c0d61e7c280de67f8d5fb24a76e647e
created_at: 2026-10-14T02:34:59+00:00
---

# Summary

Make `lrh chain-defaults` diagnostics distinguish a missing fingerprint baseline, a real content change, a baseline/stamp mismatch, and a CLI older than the installed skills. Root cause of the originating report: the PATH `lrh` was an older build without `restamp` (already on main via PR #753) while the installed skills named it; the old text made "no baseline recorded" read like "files changed". The install itself was repaired by the user (`scripts/develop` re-install); this PR is the software side.

# Result

- `FileStaleness.category` + `next step:` text; `category` in status/check-staleness/restamp JSON; `cli` provenance block in status JSON; unknown-subcommand hint; CLI/skill preflight docs outside all `GATE-DEFINITION` regions; mirrors regenerated for claude, codex and antigravity.
- `restamp` plan digest unchanged (test pins this).
- Diff-mode self-review: two P3 test-quality findings, both fixed (see the `_SELFREVIEW` record).
- No LCATS state, consent, or shared install was touched.

- Round 2 (LCATS follow-up, same PR): `coverage` block (watched vs. unwatched installations; `verification_scope`) in `status` and `restamp` output, excluded from the plan digest; docs now distinguish "configured targets verified" from "all installations verified"; `cli.legacy_distributions` plus a status warning for leftover `logical-robotics-harness` metadata, with a how-to section that warns `pip uninstall logical-robotics-harness` can delete the shared `bin/lrh`.

# Validation

`scripts/format --check`, `scripts/lint`, `scripts/test` (2336 tests OK after round 2), `lrh validate` (0 errors, 0 warnings).

# Follow-up

- Human decision, outside this PR: whether to apply a restamp for the paused LCATS landing (preview with `lrh chain-defaults restamp --dry-run`, apply with `--expect-digest`).
- Stale `logical-robotics-harness 0.2.3.dev173` editable distribution remains in the base env; `python -m pip uninstall logical-robotics-harness` removes it (not done).
- Envs `LrhSessionErgonomics` (stale), `conda-env-contributor-setup` and `wi-gate-staleness-impl` (broken `lrh`) still need re-install if used.

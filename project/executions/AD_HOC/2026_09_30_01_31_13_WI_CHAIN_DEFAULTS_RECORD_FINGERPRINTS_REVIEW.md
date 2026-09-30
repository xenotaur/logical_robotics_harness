---
execution_id: 2026_09_30_01_31_13_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW)[2026-09-29T23:59:40+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_28_08_01_48_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/753
commit: 
created_at: 2026-09-30T01:31:13+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/753
session_transcript: pending
---

# Summary

Review-response round 1 on PR #753 (the planning PR that creates
`WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS`), run inline from `/lrh-land`
Step 4. There were 7 open threads: 5 from Copilot and 2 from Codex (P1, P2).
All 7 were accepted and fixed in commit `e68dcca9`. The P1 fix meant a
redesign, which the user chose explicitly after a grounded re-analysis.

# Result

- **Copilot `r4119862381`: no-op vs fail-closed.** Fixed. "Nothing to do"
  now requires every target to have resolved successfully, and any
  unresolved target refuses first.
- **Copilot `r4119862433`: missing test artifacts.** Fixed.
  `artifacts_expected` now lists `tests/chain_defaults_status_test.py` and
  `tests/cli_tests/chain_defaults_test.py`.
- **Copilot `r4119862466`: rendered targets.** Fixed. Added the `.agents`
  and `.gemini` copies of `lrh-config-gates` and `lrh-land`, a
  regeneration step, and `lrh skills check` for the claude, codex, and
  antigravity targets.
- **Copilot `r4119862507`: `git grep` evidence.** Fixed. The primary
  record and the WI now cite `git grep -n "record_fingerprints(" -- src`.
- **Copilot `r4119862552`: canonical test runner.** Fixed. The primary
  record now cites `scripts/test tests/gate_staleness_test.py` (31 tests,
  OK).
- **Codex P1 `r4119865008`: changed fingerprints bypass the stale path.**
  Accepted. The WI was redesigned (option C′, chosen by the user):
  - Fingerprints are recorded only inside a `confirmed_commit` re-stamp,
    through a new `lrh chain-defaults restamp`. Every existing re-stamp
    site in `_shared/chain-defaults.md` and `land-workflow.md` uses it.
  - `/lrh-config-gates` gains a separately confirmed re-confirm step that
    shows the stale-files list, and is named as a second sanctioned
    re-stamp point.
  - The consent grant stays its own question.

  Grounding for the decision:
  - Git and fingerprint baselines must be the same moment:
    `src/lrh/gate_staleness.py:475-476` and `:528`.
  - The canonical stale path is `_shared/chain-defaults.md:254-300`.
  - Consent is bound to the whole-file blob hash:
    `DEC-GATE-POLICY-CASCADE.md:56-57` and `_shared/chain-defaults.md:59-62`.
    Because of that, a re-stamp invalidating consent is ratified behaviour,
    not a bug. Changing it is recorded as a Non-Goal that needs its own
    proposal.
  - The earlier "regrant loop" rationale in the WI was wrong: a re-stamp
    costs one regrant per gate change. It has been removed.
- **Codex P2 `r4119865016`: removals when no targets remain.** Fixed. When
  stored entries exist but no fingerprint targets remain, an empty map is
  now written, so the previewed `removed` entries actually go away.

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings.
- `scripts/test`: OK.
- `scripts/lint` and `scripts/format --check --diff` did not run because of
  local tool-version pins, not code problems:
  - ruff: `0.15.12` required, `0.15.0` installed;
  - black: `26.3.1` required, `25.11.0` installed.

  This PR changes only Markdown, and PR CI `lint` passed on the prior head.

# Follow-up

- Confirm-fixes (`/lrh-land` Step 5) must resolve the 7 threads against
  `e68dcca9`.
- Deferred by design: a `DEC-GATE-POLICY-CASCADE` Decision 4 amendment to
  stop re-stamps from invalidating consent; gate-text snapshots;
  marker-scoped fingerprinting.

---
execution_id: 2026_08_21_16_36_33_FIX_STALE_REVIEW_PURGE_DOCS
prompt_id: PROMPT(AD_HOC:FIX_STALE_REVIEW_PURGE_DOCS)[2026-08-21T16:33:35+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/585
commit: c003c7785c30cda971d7e53b452edc03ed8b1fa3
created_at: 2026-08-21T16:36:33+00:00
agent: claude_app
instruction_source: ad_hoc
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

Ad hoc fix, not tied to a work item: `lrh secrets review`'s `--help`
epilog and module docstring still claimed "purge is not yet implemented"
after `WI-SECRETS-PURGE` shipped in PR #584. Caught by the user's own
real-world dogfooding of `lrh secrets scan` -> `lrh secrets review`
against a live repo (Taurcode) immediately after this session's
`WS-SECRETS-COMMAND` closeout — they ran `lrh secrets review --help`
post-refresh and the stale claim was still visible.

# Result

- `src/lrh/cli/main.py`: `review`'s `--help` epilog rewritten from "a
  future lrh secrets purge command will accept, never the draft (purge
  is not yet implemented -- see WI-SECRETS-PURGE)" to "the file lrh
  secrets purge accepts via its --replacements flag, never the draft".
- `src/lrh/secrets/review.py`: module docstring's equivalent claim
  ("`purge` does not exist in this repo yet - see `WI-SECRETS-PURGE`.
  The enforcement mechanism `purge` will use...") updated to present
  tense, dropping the now-false "does not exist" claim and "will use"
  future tense.
- No test asserted the stale text directly (`grep` confirmed), so no
  test changes were needed; spot-checked `lrh secrets review --help`
  directly to confirm the fix.
- The rest of the user's dogfood run was assessed and confirmed
  correct, not a bug: `review` intentionally has no `--project-root`
  (it only reads `--out-dir`, never touches the source repo); the 4
  flagged "secrets" were gitleaks false positives on conda package-pin
  strings in `environment.yml` -- exactly what the review gate exists
  to catch via `decision: ignore`; the missing-`--decisions`-file error
  was a clean rejection, no traceback.

# Validation

- `scripts/format --check --diff` — clean
- `scripts/lint` — all checks passed
- `PYTHONPATH="$(pwd)/src" python -m unittest tests.secrets_tests.review_test
  tests.cli_tests.secrets_test` — 44/44 OK
- `PYTHONPATH="$(pwd)/src" scripts/test` — full suite, OK
- `lrh validate` — 0 errors, 0 warnings
- `lrh secrets review --help` — spot-checked directly, confirmed the
  stale text is gone

# Follow-up

- None — this closes the documentation gap the user's dogfooding
  surfaced; no further round expected unless review finds something
  else.

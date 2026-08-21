---
execution_id: 2026_08_21_06_56_15_WI_SECRETS_PURGE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SECRETS_PURGE_REVIEW)[2026-08-21T06:56:03+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_21_06_37_20_WI_SECRETS_PURGE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/584
commit: 9bb90d921b8ae1a065e43b95a130a0fbda5108e3
created_at: 2026-08-21T06:56:15+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/584
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

Addressed 4 open review comments on PR #584 (`WI-SECRETS-PURGE`), run via
`/lrh-execute`'s inlined `/lrh-land` Step 4 (`/lrh-review-response`).
`rerun_of` resolved to the primary `WI-SECRETS-PURGE` execution record
directly (only one prior record for this WI existed at dispatch time).
Also fixed a real CI failure (unrelated to any bot comment) between the
first push and this round: the pre-push self-review's own fix (moving
`check_filter_repo_available()` before the dry-run early return, per the
WI's own "--dry-run: validate ... binaries present" requirement) made a
subprocess-based CLI test that asserted dry-run always exits 0 fail on
CI runners without `git-filter-repo` installed; fixed by
`skipUnless`-gating that test, then superseded by this round's fix #4
below (mocking the availability boundary in-process instead, per
`chatgpt-codex-connector`'s suggestion, which is strictly better: it
keeps full CI coverage of the CLI dry-run path everywhere, not just on
machines with the binary installed).

# Result

Fixed all 4 comments — all valid, genuine defects, not style nitpicks:

1. **`copilot` — reject blank/comment/malformed lines in the reviewed
   replacements file** (`discussion_r3827918919`): `load_stripped_replacements()`
   passed every line after the marker through verbatim, so a blank or
   `#`-comment line in `--replacements` would be treated as a literal
   "secret" by `secrets_from_replacements()` and reach `git-filter-repo`
   as a bogus replace-text entry. Fixed: blank/comment lines are now
   dropped, and any remaining line not shaped like `<secret>==><placeholder>`
   raises `PurgeInputError` before any clone happens.
2. **`chatgpt-codex-connector` P1 — pass every ref in a single `--refs`
   flag** (`discussion_r3827923262`): the previous code emitted one
   `--refs <ref>` pair per ref (`--refs main --refs dev`); `git-filter-repo`
   defines `--refs` as `nargs='+'`, so a repeated flag overwrites rather
   than accumulates -- only the last ref in `--refs-file` was ever
   actually rewritten. A silent, severe correctness bug: with multiple
   refs, the tool would report success while leaving the secret present
   on every ref but the last. Fixed: `--refs` is now passed once,
   followed by the complete ref list.
3. **`chatgpt-codex-connector` P2 — resolve a relative local `--source`
   before printing the push command** (`discussion_r3827923266`):
   `git -C <mirror_dir> push --force <source> <ref>` resolves a relative
   `<source>` against `mirror_dir`, not the caller's original cwd -- a
   relative local path (e.g. `--source .`) produced a push command that
   silently pushed back into the mirror itself. Fixed: added
   `resolve_local_source()`, which resolves an existing local filesystem
   path to absolute and leaves URLs/ssh-style remotes untouched; wired
   into `run_purge()` before the mirror clone and the printed command.
4. **`chatgpt-codex-connector` P2 — stub the external binary in the
   unit dry-run test** (`discussion_r3827923271`): the same CI failure
   already fixed once this round via `skipUnless` -- rewrote the test to
   mock `check_filter_repo_available()` in-process instead (matching the
   existing `test_lrh_secrets_purge_delegates_to_secrets_purge_module`
   pattern), keeping the unit suite hermetic per `AGENTS.md`'s testing
   policy while preserving CI coverage of this path everywhere, not just
   where the real binary happens to be installed.

Nothing was skipped -- all 4 comments passed presence/validity/feasibility
and were fixed. Added 5 new regression tests: blank/comment-line
dropping, malformed-entry rejection, single-`--refs`-flag-with-all-refs,
and relative-vs-URL `resolve_local_source()` behavior (2 tests).

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 (confirmed
  correct, no reinstall needed this round)
- `scripts/format --check --diff` — clean
- `scripts/lint` — all checks passed
- `PYTHONPATH="$(pwd)/src" python -m unittest tests.secrets_tests.purge_test
  tests.cli_tests.secrets_test tests.smoke.secrets_purge_smoke` — 45/45
  OK (including the real `git-filter-repo` smoke test)
- `PYTHONPATH="$(pwd)/src" scripts/test` — full suite, OK
- `lrh validate` — 0 errors, 0 warnings
- `gh api graphql resolveReviewThread` — 4/4 mutations returned
  `isResolved: true`

# Follow-up

- None specific to this round; proceeds to `/lrh-confirm-fixes` next
  (CI stable-read check against this commit, thread-resolution verdict).

---
execution_id: 2026_08_20_22_24_16_WI_SECRETS_REVIEW_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SECRETS_REVIEW_REVIEW)[2026-08-20T22:17:26+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_20_19_02_00_WI_SECRETS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/578
commit: 
created_at: 2026-08-20T22:24:16+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/578
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

Addressed 8 open review comments on PR #578 (`WI-SECRETS-REVIEW`), run
via `/lrh-execute`'s inlined `/lrh-land` Step 4 (`/lrh-review-response`).
`rerun_of` resolved to the primary `WI-SECRETS-REVIEW` execution record
via the sibling-elimination provenance check — `WI_SECRETS_REVIEW`'s own
slug ends in the reserved `_REVIEW` suffix, but the pre-push
`_SELFREVIEW` sibling record proved it primary (its own base slug,
stripped of `_SELFREVIEW`, matches `WI_SECRETS_REVIEW` exactly).

# Result

Fixed all 8 comments — all valid, mostly real robustness/correctness
gaps, two doc-accuracy fixes:

1. **`chatgpt-codex-connector` P1 — reject a missing findings report**
   (`discussion_r3824540755`): a nonexistent `findings.json` was treated
   identically to an existing-but-empty one, letting `--check`/`--apply`
   falsely pass with zero scan evidence loaded. Fixed: `load_findings()`
   now raises a new `ReviewInputError` when `findings.json` is missing
   entirely (an existing, 0-byte file is still a legitimate clean scan
   and is unaffected).
2. **`chatgpt-codex-connector` P1 — invalidate stale reviewed output on a
   failed apply** (`discussion_r3824540761`): a leftover
   `replacements.reviewed.txt` from an earlier successful `--apply`
   survived a later failed `--apply` in the same `--out-dir`. Fixed:
   added `invalidate_stale_reviewed()`, called from the CLI's undecided
   `--apply` failure path before reporting the error.
3. **`chatgpt-codex-connector` P2 — require a rationale before considering
   a finding decided** (`discussion_r3824540764`): `decision: keep` with
   no/empty `reason` counted as fully decided. Fixed: `Decision.is_decided()`
   now requires both a valid `decision` value and a non-empty (post-strip)
   `reason`; `undecided()`/`kept()`/`format_text()` all use it.
4. **`copilot` — future-tense the `purge`-doesn't-exist-yet claims**
   (`discussion_r3824554717`, `discussion_r3824554944`): both the module
   docstring and the `--help` epilog described `lrh secrets purge` as
   already existing and enforcing the marker line. Reworded to future
   tense, citing `WI-SECRETS-PURGE` as not yet implemented.
5. **`copilot` — clean error handling for malformed decisions input**
   (`discussion_r3824554770`): `load_decisions()` could raise a raw
   `AttributeError`/`yaml.YAMLError` that would bubble as a stack trace.
   Fixed: validates the parsed YAML is a mapping and each entry is a
   mapping, raising `ReviewInputError` with a clear message otherwise.
6. **`copilot` — validate `--out-dir` and turn parse failures into clean
   exits** (`discussion_r3824554843`): `load_findings()` now checks
   `out_dir.is_dir()` first and catches `json.JSONDecodeError`, both
   raising `ReviewInputError`; the CLI dispatch catches it and exits `2`
   with a clean `error: ...` message instead of a stack trace (covers
   this comment together with #1 and #5, since all three needed the same
   `ReviewInputError` mechanism).
7. **`copilot` — fallback error message should mention `review` too**
   (`discussion_r3824554895`): `secrets requires a subcommand` still only
   suggested `scan`. Fixed to suggest both.
8. **`copilot` — same future-tense fix as #4, in `--help`'s epilog**
   (`discussion_r3824554944`): fixed together with #4.

Nothing was skipped — all 8 comments passed presence/validity/feasibility
and were fixed. Added 13 new tests across both test files covering every
fix (missing/malformed findings and decisions inputs, `--out-dir`
validation, reason-required decisions, stale-file invalidation, the
updated fallback message).

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 (reinstalled again
  after another concurrent session reverted them mid-round — same
  recurring shared-environment issue this session's own memory already
  documents)
- `scripts/format --check --diff` — clean, 203 files unchanged
- `scripts/lint` — all checks passed (one line-length fix needed and
  applied)
- `PYTHONPATH="$(pwd)/src" scripts/test` — 1135 tests, OK
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- None specific to this round; proceeds to `/lrh-confirm-fixes` next.

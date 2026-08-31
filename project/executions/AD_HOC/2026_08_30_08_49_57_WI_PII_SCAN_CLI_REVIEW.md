---
execution_id: 2026_08_30_08_49_57_WI_PII_SCAN_CLI_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PII_SCAN_CLI_REVIEW)[2026-08-30T08:41:53+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_29_17_13_27_WI_PII_SCAN_CLI
pr: https://github.com/xenotaur/logical_robotics_harness/pull/654
commit: 7905ae10
created_at: 2026-08-30T08:49:57+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/654
session_transcript: "claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c"
---

# Summary

Addressed the first round of automatic review comments on PR #654
(`chatgpt-codex-connector` P1+2xP2, `copilot-pull-request-reviewer`, 4
findings total) for the `WI-PII-SCAN-CLI` implementation.

Note on `rerun_of`: linked to the implementation primary record
(`pr: #654`), not the same-slug creation record under `AD_HOC`
(`pr: #596`) — same slug collision pattern as this WI's sibling records.

# Result

All four comments passed presence/validity/feasibility triage and were
fixed:

1. **P1 — Reject a missing explicit config file.** `config.load_config`
   silently fell back to built-in defaults when an explicit `--config`
   path didn't exist, which could produce a falsely-clean audit if the
   user's custom rules (or `content_scan_scope: "all-text"`) were never
   actually applied. Fixed: an explicit `config_path` that doesn't exist
   now raises `PiiConfigError`; only the auto-discovered-at-project-root
   case still falls back silently.
2. **P2 — Include finding details in the text report.** `ScanResult`
   discarded the filtered findings before formatting, so the default
   `--format text` output only ever printed a count. Fixed: `ScanResult`
   now carries `findings`, and `format_text` delegates to the existing
   `output.render_text_summary` for per-finding detail (path, rule,
   severity/confidence, commit) instead of reinventing it.
3/4. **P2 + copilot — Handle `Layer1BlobReadError`/`OSError` at the CLI
   boundary.** The CLI dispatch only caught `PiiConfigError`; a
   `Layer1BlobReadError` (unexpected `git rev-parse` failure) or an
   `OSError` (e.g. `--out-dir` unwritable) would surface as a raw
   traceback. Fixed: both are now caught alongside the existing
   `Layer2ContentReadError`/`CalledProcessError` handling, reporting a
   clean `error: ...` message and exit code 2.

Added/updated tests for all four:
`test_missing_explicit_config_path_raises_pii_config_error`,
`test_format_text_includes_disclosure_counts_and_finding_details`,
`test_lrh_pii_scan_reports_layer1_blob_read_error_cleanly`,
`test_lrh_pii_scan_reports_os_error_cleanly`,
`test_lrh_pii_scan_reports_missing_explicit_config_cleanly`. Manually
re-verified the text-report fix against this real repo: `lrh pii scan
--project-root . --out-dir <dir>` now prints per-finding detail lines,
not just a count.

# Validation

- `tests.pii_tests.config_test` + `tests.pii_tests.scan_test` +
  `tests.cli_tests.pii_test` — 30/30 pass (5 new/changed since the
  self-review round).
- Full suite: `python -m unittest discover -s tests -p '*_test.py'` —
  1537 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 2 pre-existing unrelated warnings.
- Manual re-run of `lrh pii scan` against this real repo, confirming the
  text-report fix.

# Follow-up

- None beyond the standard `/lrh-confirm-fixes` pass before merge.

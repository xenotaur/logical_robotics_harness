---
execution_id: 2026_08_28_08_02_08_WI_PII_SCAN_LAYER2_CONTENT
prompt_id: PROMPT(WI-PII-SCAN-LAYER2-CONTENT:WI_PII_SCAN_LAYER2_CONTENT)[2026-08-28T06:49:23+00:00]
work_item: WI-PII-SCAN-LAYER2-CONTENT
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/646
commit: pending
created_at: 2026-08-28T08:02:08+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-PII-SCAN-LAYER2-CONTENT.md
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Implement `lrh pii scan`'s Layer 2 scoped content-pattern detector:
`src/lrh/pii/layer2.py`, plus a `content_scan_scope` (`"flagged"`
default, `"all-text"` opt-in) extension to `src/lrh/pii/config.py`'s
`.lrh-pii.toml` loader. Depends on `WI-PII-SCAN-RULE-TAXONOMY` (shared
regex rule taxonomy) and `WI-PII-SCAN-LAYER1-ENUMERATOR` (path
enumeration, per-commit content-fetch enumeration, Layer 1 flagged-path
set), both already resolved.

# Result

Implemented `content_findings_for_paths(project_root, flagged_paths,
all_paths, config)`, which selects the target path set per
`config.content_scan_scope` (`flagged_paths` by default, `all_paths`
under `"all-text"`), requests every historical commit touching those
paths from `lrh.pii.enumerate.enumerate_commits_for_paths` (not just
current working-tree content — this is what makes the "PII added then
later removed" scenario catchable under `"all-text"`), fetches each
commit's content via `git show <commit>:<path>`, extracts scannable
text (PDF via `lrh.conversations.pdf_import.extract_pdf_text`, plain
text via UTF-8 decode, everything else skipped as a disclosed gap), and
runs the shared rule engine
(`lrh.conversations.sensitivity.scan_text_for_sensitive_findings`) over
each extracted text, reusing the taxonomy from
`WI-PII-SCAN-RULE-TAXONOMY` rather than re-implementing it.

Extended `PiiConfig` with `content_scan_scope: str = "flagged"`,
validated in `load_config` against the two allowed values
(`PiiConfigError` on anything else), following the same validation
pattern already used for `useDefault`/list fields in that module.

Ran a diff-mode `/lrh-self-review` pass before the first push (see
`project/executions/AD_HOC/2026_08_28_07_32_36_WI_PII_SCAN_LAYER2_CONTENT_SELFREVIEW.md`):
a cold-context subagent independently verified the scope branching, the
PDF/text/skip decision, exception-safety of the git-show and decode
paths, and config validation consistency, and deliberately tried (and
failed) to break the modify-after-add detection with scenarios beyond
the existing tests. No findings.

# Validation

- `tests/pii_tests/layer2_test.py` (6 tests, new) and
  `tests/pii_tests/config_test.py` (2 new tests for `content_scan_scope`)
  — 17/17 pass, covering: flagged-scope content match; ordinary-file
  match caught only under `"all-text"`; PII added in a commit after the
  initial benign add, still detected under `"all-text"` even though
  current working-tree content is clean; PDF content via
  `pdf_import`; binary content skipped without error; empty
  flagged-path set scans nothing under the default scope.
- Full suite: `PYTHONPATH=<worktree>/src python3 -m unittest discover -s
  tests -p '*_test.py'` — 1438 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean on touched
  files (one pre-existing lint error in an untouched file,
  `tests/scripts_tests/scripts_log_redirection_test.py`, confirmed not
  introduced by this diff).
- `lrh validate` — 0 errors, 0 warnings.
- Diff-mode self-review — clean, see linked `_SELFREVIEW` record above.

# Follow-up

- None beyond the standard post-merge steps: `/lrh-review-response` for
  any reviewer findings, `/lrh-confirm-fixes` before merge, then
  `/lrh-closeout` to land this record and resolve
  `WI-PII-SCAN-LAYER2-CONTENT`.
- `WI-PII-SCAN-ALLOWLIST-OUTPUT` and `WI-PII-SCAN-CLI` remain the last
  two `WS-PII-SCAN` work items once this merges.

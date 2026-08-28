---
execution_id: 2026_08_28_16_53_30_WI_PII_SCAN_LAYER2_CONTENT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PII_SCAN_LAYER2_CONTENT_REVIEW)[2026-08-28T08:05:49+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_28_08_02_08_WI_PII_SCAN_LAYER2_CONTENT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/646
commit: 3c7891db
created_at: 2026-08-28T16:53:30+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/646
session_transcript: "claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c"
---

# Summary

Addressed the first round of automatic review comments on PR #646
(`chatgpt-codex-connector`, 2 findings, both P2) for the
`WI-PII-SCAN-LAYER2-CONTENT` implementation.

Note on `rerun_of`: linked to the implementation primary record
(`pr: #646`), not the same-slug creation record under `AD_HOC`
(`pr: #596`) — same slug collision pattern documented for this WI's
sibling records (`WI-PII-SCAN-LAYER1-ENUMERATOR`, `WI-PII-SCAN-RULE-TAXONOMY`).

# Result

Both comments passed presence/validity/feasibility triage and were fixed
in `src/lrh/pii/layer2.py`:

1. **Deduplicate renamed histories before scanning.** Requesting both
   sides of a rename in `all_paths`/`flagged_paths` made
   `enumerate_commits_for_paths` report the same `(commit, path)` pair
   twice (verified empirically against a scratch repo: querying both
   `a.txt` and `b.txt` for a renamed file returned the add-commit entry
   under both queries). `content_findings_for_paths` now deduplicates
   `path_commits` via `dict.fromkeys` (frozen-dataclass equality) before
   scanning, matching `enumerate.py`'s own dedup convention.
2. **Surface unexpected blob-read failures.** `_read_content_at_commit`
   previously treated every non-zero `git show` exit as "path absent at
   this commit" and returned `None`. It now inspects `git`'s own stderr:
   only the expected "does not exist in" / "exists on disk, but not in"
   messages are treated as an ordinary absent-path skip; any other
   failure raises the new `Layer2ContentReadError` instead of being
   silently swallowed.

Added `tests/pii_tests/layer2_test.py::ReadContentAtCommitTest` (2 new
tests: expected-deletion returns `None`; an unexpected `git show` failure,
via a mocked `subprocess.run` result, raises `Layer2ContentReadError`) and
`ContentFindingsForPathsTest::test_renamed_file_content_is_not_double_counted`
(asserts the correct post-dedup count of 2, not the pre-fix 3 — the add
commit and the rename commit are two genuinely distinct historical
revisions, so full dedup collapses only the literal duplicate, not both
findings).

# Validation

- `tests.pii_tests.layer2_test` + `tests.pii_tests.config_test` — 20/20
  pass (8 new/changed since the self-review round).
- Full suite: `python -m unittest discover -s tests -p '*_test.py'` —
  1441 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- None beyond the standard `/lrh-confirm-fixes` pass before merge.

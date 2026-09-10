---
execution_id: 2026_08_29_15_59_43_WI_PII_SCAN_ALLOWLIST_OUTPUT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PII_SCAN_ALLOWLIST_OUTPUT_REVIEW)[2026-08-29T15:59:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_29_08_28_16_WI_PII_SCAN_ALLOWLIST_OUTPUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/650
commit: a5404d88f2ff7795fceb344a31ff02a61e91aa36
created_at: 2026-08-29T15:59:43+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/650
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Addressed the first round of automatic review comments on PR #650
(`chatgpt-codex-connector` P1+P2, `copilot-pull-request-reviewer`, 3
findings total) for the `WI-PII-SCAN-ALLOWLIST-OUTPUT` implementation.

Note on `rerun_of`: linked to the implementation primary record
(`pr: #650`), not the same-slug creation record under `AD_HOC`
(`pr: #596`) — same slug collision pattern as this WI's sibling records.

# Result

All three comments passed presence/validity/feasibility triage and were
fixed in `src/lrh/pii/output.py`:

1. **Compute working-tree presence from current content** (P1,
   `chatgpt-codex-connector`). Verified the concern against the source
   before fixing: `still_in_working_tree = (commit == HEAD)` is neither
   necessary (an unrelated later commit moving `HEAD` doesn't mean the
   flagged file changed) nor sufficient (as originally worded) as a
   presence check. Fixed by comparing `HEAD`'s blob SHA for the path
   against the finding's own commit's blob SHA — byte-identical means
   still present, a disclosed conservative check (a file that changed
   elsewhere while keeping the same flagged value reports as absent).
2. **Emit the documented `matched_layer` values** (P2,
   `chatgpt-codex-connector`). Read `PROP-LRH-PII-SCAN` Decision 7
   directly (`project/design/proposals/proposed/lrh-pii-scan/00_proposal.md:110`)
   before accepting: it explicitly specifies `matched_layer:
   "path"|"content"`, not `"layer1"`/`"layer2"` as implemented. Fixed by
   changing the two constants' values (symbolic constants throughout, no
   other code needed to change).
3. **Distinguish unexpected git failures in `_blob_sha`**
   (`copilot-pull-request-reviewer`). Mirrors `layer2.py`'s existing
   `Layer2ContentReadError` precedent — added `Layer1BlobReadError`,
   raised for any `git rev-parse` failure whose stderr doesn't match the
   expected missing-path markers.

Added 5 new tests: `test_still_in_working_tree_true_when_unrelated_commit_moved_head`,
`test_still_in_working_tree_false_when_content_later_changed`,
`test_matched_layer_values_match_the_documented_contract`, and a new
`BlobShaTest` class (2 tests) for the missing-path-vs-unexpected-failure
distinction.

# Validation

- `tests.pii_tests.output_test`, `tests.pii_tests.allowlist_test`,
  `tests.pii_tests.layer2_test` — 34/34 pass.
- Full suite: `python -m unittest discover -s tests -p '*_test.py'` —
  1507 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean.
- `lrh validate` — 0 errors (1 pre-existing unrelated warning).

# Follow-up

- None beyond the standard `/lrh-confirm-fixes` pass before merge.

---
execution_id: 2026_08_29_08_28_16_WI_PII_SCAN_ALLOWLIST_OUTPUT
prompt_id: PROMPT(WI-PII-SCAN-ALLOWLIST-OUTPUT:WI_PII_SCAN_ALLOWLIST_OUTPUT)[2026-08-29T07:45:26+00:00]
work_item: WI-PII-SCAN-ALLOWLIST-OUTPUT
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/650
commit: a5404d88f2ff7795fceb344a31ff02a61e91aa36
created_at: 2026-08-29T08:28:16+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-PII-SCAN-ALLOWLIST-OUTPUT.md
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Implemented `WI-PII-SCAN-ALLOWLIST-OUTPUT`: the `.lrh-pii-allowlist`
content-bound allowlist mechanism and unified `pii_findings.json`/text-
summary output for `lrh pii scan`, per `PROP-LRH-PII-SCAN` Decisions 6
and 7 (both revised during PR #591 review).

# Result

- `src/lrh/pii/allowlist.py` (new): `.lrh-pii-allowlist` auto-discovery,
  `gitleaksignore`-style parsing; `compute_fingerprint(path, rule_id,
  content_digest)` = `sha256(path + rule_id + content_digest)`.
- `src/lrh/pii/output.py` (new): `build_findings` assembles Layer 1 +
  Layer 2 findings into the revised schema (`path, rule_id, category,
  severity, confidence, commit, content_digest, still_in_working_tree,
  matched_layer`); `filter_allowlisted` drops allowlisted entries;
  `render_json`/`render_text_summary` produce the two output formats,
  the text summary always ending in a fixed disclosure block (no OCR, no
  ML/NLP classification, heuristic only).
- `src/lrh/pii/layer2.py`: added a `content_digest` field to
  `Layer2Finding` (sha256 of the matched substring only, sliced from the
  already-decoded scan text via the underlying match offsets — the raw
  substring is never stored or returned, only its digest). Required so
  the allowlist fingerprint can distinguish one flagged value from
  another at the same path/rule, per Decision 6's content-binding
  requirement.
- `tests/pii_tests/allowlist_test.py` (new, 8 tests) and
  `tests/pii_tests/output_test.py` (new, 11 tests), including the WI's
  required fixture (`test_content_change_at_allowlisted_path_and_rule_produces_a_fresh_finding`):
  a content change at an allowlisted path/rule produces a fresh,
  non-suppressed finding.

**Self-review finding (found and fixed before push):** diff-mode
`/lrh-self-review` found that `build_findings` grouped Layer 1's
per-commit results by their *historical* path name (what
`enumerate_commits_for_paths` reports at each commit) but looked them up
by the finding's *current* path — silently dropping every commit reached
only under a pre-rename name. Independently reproduced against a scratch
repo (add `notes.txt` → rename to `passport.pdf`: only the rename commit
survived, the add commit vanished from output entirely) before accepting
the finding. Fixed by querying `enumerate_commits_for_paths` once per
Layer 1 finding (not batched across all findings and re-grouped by
historical name afterward), and using the historical path name for the
blob-SHA lookup, not the current/canonical name. Added a regression test
(`test_layer1_finding_keeps_pre_rename_commits_not_only_post_rename`).

# Validation

- `tests.pii_tests.allowlist_test`, `tests.pii_tests.output_test`,
  `tests.pii_tests.layer2_test` — 29/29 pass.
- Full suite: `python -m unittest discover -s tests -p '*_test.py'` —
  1502 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean.
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`, not touched by
  this change).
- Diff-mode `/lrh-self-review` (cold-context subagent): 1 finding,
  independently re-verified by direct reproduction, fixed.

# Follow-up

- None beyond the standard review-response/confirm-fixes/merge/closeout
  chain for PR #650.

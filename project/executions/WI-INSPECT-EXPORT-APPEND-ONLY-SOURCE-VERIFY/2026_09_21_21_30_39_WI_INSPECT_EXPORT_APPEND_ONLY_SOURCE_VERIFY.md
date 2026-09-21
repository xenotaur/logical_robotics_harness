---
execution_id: 2026_09_21_21_30_39_WI_INSPECT_EXPORT_APPEND_ONLY_SOURCE_VERIFY
prompt_id: PROMPT(WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY:WI_INSPECT_EXPORT_APPEND_ONLY_SOURCE_VERIFY)[2026-09-21T19:26:47+00:00]
work_item: WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/692
commit: 
created_at: 2026-09-21T21:30:39+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Implement `WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY` through
`/lrh-execute`: record how many source bytes an export hashed, and let
`inspect-export --source` verify that recorded prefix so a live, append-only
transcript that grew after export is reported as valid instead of `mismatch`.
Covers both the Claude and Antigravity exporters.

# Result

- `export_manifest.py`: optional `source_byte_count` (non-negative int),
  emitted only when set, parsed when present or absent; `schema_version` stays 1.
- `claude_export.py` and `antigravity_export.py`: set
  `source_byte_count=len(raw_bytes)` from the same bytes that produce
  `source_sha256`. Codex is unchanged.
- `export_inspector.py`: when the source is longer than the recorded count, the
  first N bytes are hashed. Equal to `source_sha256` is the new status
  `match_source_grew` (valid, exit 0, "grew by N bytes" line in text output,
  `expected_byte_count`/`actual_byte_count` in JSON); a different prefix, a
  shorter source, or a grown source with no recorded count is `mismatch`. When
  a prefix is compared, the reported `actual` hash is that prefix's hash.
- `docs/reference/cli/conversation.md`: documents the field, the status, the
  append-only assumption, and the exit code.
- Tests (all `unittest.TestCase`): manifest optional/round-trip/rejection;
  inspector unchanged, appended, altered-earlier-byte, shorter, no-count,
  CLI text and JSON; end-to-end grown-source verification for both exporters.

Required change 8 finding: the Antigravity exporter's `--conversation-id`
discovery reads only the top-level `logs/transcript.jsonl` (falling back to
`transcript_full.jsonl`) and never reads `chunks/`. Whether `transcript.jsonl`
aggregates chunks on rollover was not tested; only a single-chunk conversation
was available. Not fixed here (out of scope). The exporter's CLI path near
`antigravity_export.py:417` reads the file a second time only to derive an
output filename; the manifest count comes from the converter's own read.

Predecessor evidence: the Claude and Antigravity growth behaviour and the
export-time prefix (45,952 bytes for the tested Antigravity export) are
recorded in the batch record for PR #682.

# Validation

- `PYTHONPATH=src scripts/test` — 1646 tests OK. Run with anaconda Python and
  Homebrew bash 5. With macOS system bash 3.2, `scripts/validate` and
  `scripts/format` (no args) fail on an empty-array `set -u` error, which made
  `scripts_log_redirection_test` fail there; unrelated to this change.
- `scripts/lint` and `scripts/format --check --diff` — clean.
- `lrh validate` — 0 errors, 0 warnings.
- Pre-push cold-context self-review (`_SELFREVIEW` record): no correctness
  issues.

# Follow-up

- `src/lrh/skills/lrh-antigravity-export/SKILL.md:82` still says to confirm
  `Source hash: match` (and its installed copies). No work item covers it; the
  Claude skill's equivalent is covered by
  `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`.
- Chunk rollover for long Antigravity conversations remains untested.
- Proceed to `/lrh-land` for PR #692.

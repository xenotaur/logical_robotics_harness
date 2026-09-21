---
execution_id: 2026_09_20_20_06_58_WI_CLAUDE_EXPORT_LIVE_SESSION_BATCH
prompt_id: PROMPT(AD_HOC:WI_CLAUDE_EXPORT_LIVE_SESSION_BATCH)[2026-09-20T20:03:32+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/682
commit: eab347c4804dbf2dce80d10591fff3c024c65679
created_at: 2026-09-20T20:06:58+00:00
agent: claude_app
instruction_source: ad-hoc — capture the live-session export fixes as work items in one draft PR
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Design-capture batch: three proposed work items recording the fixes found while
dogfooding `/lrh-export-claude` for the first time. This is a draft PR opened
only to capture the design; it is not submitted for review and nothing is
implemented.

# Result

Added three work items under `project/work_items/proposed/`, all
`prompt_ready: yes`:

- `WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY` — optional manifest
  `source_byte_count` and prefix verification, with a new valid
  `match_source_grew` status in `inspect-export`.
- `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER` — a
  `current-claude-session-id` resolver, `export-claude-session --current`, a
  project-scoped `--latest` (with `--all-projects`), and a `Source transcript:`
  output line.
- `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` — the skill defaults to the
  current session, a typed invocation counts as explicit, and Step 5 accepts
  `match_source_grew`. Depends on the other two.

Antigravity investigation (read-only, sizes and hashes only, no conversation
content read): a live conversation's `transcript.jsonl` (44,262 bytes) and
`transcript_full.jsonl` (52,222 bytes) each grew by roughly 1-2 KB after two
more messages, and the original bytes still hashed exactly to the baseline
digests, so the logs are append-only and a whole-file hash goes stale. The
first work item was amended to cover both the Claude and Antigravity
exporters.

Stage 2 round trip (CLI from this session, scratch export at mode 0600,
deleted afterwards; only metadata was printed): `export-antigravity-session
--conversation-id` read `transcript.jsonl` and recorded source sha256
`33a16920…`. `inspect-export --source` immediately afterwards reported
`Valid: yes`, `Source hash: match`. After one more message in the
conversation it reported `Valid: no`, `Source hash: mismatch` (whole-file hash
`667c253b…`, file 46,462 bytes). A review finding pointed out that the
44,262-byte baseline prefix did not by itself cover the export-time bytes, so
a read-only search over prefix lengths of the live file was run: exactly one
length, 45,952 bytes (ending on a line boundary), hashes to the export's
recorded `33a16920…`. The export-time bytes are therefore an exact prefix of
the file as it later grew, which shows prefix verification with a recorded
`source_byte_count` would have reported `match_source_grew`. Because the
exporter did not record the byte count, that length had to be recovered by
search. The inspector's exit code was not captured. Only `transcript.jsonl`
was tested end to end. Not tested: chunk rollover on a long conversation.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing warning from another session's
  closeout note (not introduced here).
- No code changed, so no test run applies.

# Follow-up

- Keep PR #682 as a draft until the user decides to submit it.
- Then land this record via `lrh prompt update-execution` at closeout.

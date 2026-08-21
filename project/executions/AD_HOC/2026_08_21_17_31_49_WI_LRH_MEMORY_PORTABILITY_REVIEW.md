---
execution_id: 2026_08_21_17_31_49_WI_LRH_MEMORY_PORTABILITY_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_PORTABILITY_REVIEW)[2026-08-21T17:31:11+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_21_17_21_02_WI_LRH_MEMORY_PORTABILITY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/589
commit: 9d524c99a70b8d4f6978dcb56278c5d6ee501ade
created_at: 2026-08-21T17:31:49+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/589
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Round 1 review-response for PR #589, addressing three
`chatgpt-codex-connector` findings (1 P1, 2 P2) on the initial push.

# Result

All three triaged as present, valid, and feasible:

1. **P1 -- resolve fresh destination slugs before deriving project
   paths.** `_resolve_memory_dir`'s literal-slug branch required
   `<claude_projects_root>/<value>/memory` to already exist, so the
   normal "fresh destination corpus" case for `--to` fell through to
   `project_slug_for_path()`, treating the bare slug string as a
   relative filesystem path from the current working directory and
   silently writing into a wrongly-derived corpus. Fixed: any value with
   no path separators is now unconditionally treated as a literal slug,
   regardless of whether its corpus already exists.
2. **P2 -- reject malformed bundle records instead of crashing.** A
   JSONL line decoding to a list/scalar, or an object with an
   incorrectly-typed field, previously reached unconditional `.get()`
   calls and raised uncaught `AttributeError`/`TypeError`. Fixed by
   validating each record is a dict before use, and catching
   `TypeError`/`AttributeError` around the write call as a clean
   `ImportEntry` error. Also caught, while fixing this, that a string
   `applies_to` didn't crash at all -- `tuple("not-a-list")` silently
   splits it into one bogus entry per character -- so added an explicit
   type check rejecting it rather than writing corrupted metadata.
3. **P2 -- run import validation during dry runs.** `--dry-run`
   previously marked every parsed record error-free unconditionally,
   before any real validation ran, so an invalid type or cross-agent
   conflict a real import would reject was reported as `would write`.
   Fixed by giving `_write_memory_into_dir` a real `dry_run` mode that
   runs every validation/conflict check without touching the
   filesystem.

All three independently re-verified against the actual code before
fixing (not accepted from the bot report alone).

Pushed directly: `git push` to the open PR branch.

# Validation

`lrh validate` (0 errors/warnings), full `scripts/test` suite (1243
tests, all pass). Format/lint checked against a minimal override config
(this machine's installed `black`/`ruff` versions had drifted from the
pinned versions since the earlier `WI-LRH-MEMORY-ARCHIVE-SIDE` session;
verified against real rules, not `--isolated`) -- both clean on the 4
changed files. Added 4 new regression tests (fresh-slug transfer,
malformed-bundle-records, dry-run-runs-real-validation) plus updated the
existing literal-slug test to no longer pre-create the destination.

# Follow-up

- Loop back to confirm-fixes for a fresh verdict against this new
  `HEAD`.

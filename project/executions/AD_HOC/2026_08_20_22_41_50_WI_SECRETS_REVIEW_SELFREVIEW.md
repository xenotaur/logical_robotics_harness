---
execution_id: 2026_08_20_22_41_50_WI_SECRETS_REVIEW_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SECRETS_REVIEW_SELFREVIEW)[2026-08-20T22:41:42+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_20_19_02_00_WI_SECRETS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/578
commit: 8fc01390340962bbdf21f85261dd50fcb66bea5e
created_at: 2026-08-20T22:41:50+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/578
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

PR-mode substitute review signal for PR #578, dispatched from
`/lrh-confirm-fixes` Step 8 after a bounded ~5-minute wait produced no
automatic reviewer response matching the `_CONFIRM` commit (`8fc01390`).
`rerun_of` resolved via the same sibling-elimination provenance check.
No-progress cap: round 1 of substitute review for this confirm-fixes
gate, well under the 3-round threshold.

# Result

Dispatched a cold-context `general-purpose` subagent (PR-mode prompt) in
a fresh worktree against PR #578 at HEAD `8fc01390`. It verified most of
the round-1 review fixes hold up (marker line, `0600` permissions,
`--check`/`--apply` mutual exclusivity, future-tense docs, keep/ignore
filtering, missing-vs-empty `findings.json` distinction), but found and
reproduced a real, genuine gap: `invalidate_stale_reviewed()` (added to
fix `discussion_r3824540761`, "stale reviewed output on failed apply")
only fires on the *undecided-findings* failure path inside `if
args.apply:` — it never runs if `--apply` instead fails via
`ReviewInputError` (raised by `build_report()`, before that block is
reached). A stale, marker-bearing `replacements.reviewed.txt` from an
earlier successful `--apply` survives untouched if a later `--apply` in
the same `--out-dir` fails due to a missing/malformed `findings.json` or
decisions file — a partial fix, not the complete fix the round-1 record
claimed.

**Independent re-verification (Step 4, mandatory):** reproduced directly
myself, not just accepted the subagent's claim: wrote a valid
`findings.json`/`decisions.yaml`, ran `--apply` successfully (reviewed
file created, `0600`, marker present), corrupted `decisions.yaml` to an
invalid shape, re-ran `--apply` (`ReviewInputError`, exit 2 as designed),
and confirmed the stale reviewed file was still present afterward,
unmodified. Confirmed real.

This is a genuine new finding, not a GitHub thread (self-review sourced)
- routed back to `/lrh-confirm-fixes` Step 3's taxonomy as
Clear-satisfied-eligible pending a fix, presented at a confirm gate
before editing.

# Validation

- Direct reproduction (see Result) — confirmed the gap exists on `HEAD`
  `8fc01390`

# Follow-up

- Fix needs to move (or duplicate) the `invalidate_stale_reviewed()` call
  so it also runs on the `ReviewInputError` path when `--apply` was
  requested, then push as a further round and re-run `/lrh-confirm-fixes`
  from the top for a fresh verdict.

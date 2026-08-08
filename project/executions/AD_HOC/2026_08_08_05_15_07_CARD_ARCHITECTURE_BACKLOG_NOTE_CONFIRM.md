---
execution_id: 2026_08_08_05_15_07_CARD_ARCHITECTURE_BACKLOG_NOTE_CONFIRM
prompt_id: PROMPT(AD_HOC:CARD_ARCHITECTURE_BACKLOG_NOTE_CONFIRM)[2026-08-08T05:09:46+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/517
commit: 5093f49
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/517
session_transcript: pending
created_at: 2026-08-08T05:15:07+00:00
---

# Summary

Confirm-fixes verification pass for PR #517 (design-backlog entry
recording a card-architecture reuse assessment between prosoc and LRH).
Backfill record — no primary execution record exists, since the PR was
opened via plain git/gh rather than `/lrh-implement`.

# Result

Fresh-eyes verification against commit `5093f49` found 3 unresolved
threads, all bot-authored, all `isOutdated: true` (a follow-up fix commit
shifted the diff lines) but `isResolved: false` — per this project's
guidance, outdated is not resolved, so all three were verified against
the current diff, not skipped:

1. Codex (P2) — the note originally claimed Claude/Codex/Antigravity
   harness differentiation was "already shipped." On `main`,
   `SkillTarget` only has `CLAUDE`/`CODEX`
   (`src/lrh/skills/installer.py:21-23`); Antigravity is tracked as
   `status: proposed` in `WI-SKILLS-ANTIGRAVITY-TARGET.md`. Fixed: the
   note now states Claude/Codex are shipped and Antigravity is proposed,
   not shipped.
2. Copilot — a citation pointed at `snapshot_cli.py:652-656`
   (`summarize_directory()`) for a claim about opaque frontmatter/body
   parsing, but the actual behavior described lives in `summarize_file()`.
   Fixed: citation corrected to `snapshot_cli.py:571-587`.
3. Copilot — the `installer.py:24-32` citation didn't cover
   `SkillTarget`'s actual definition (starts at line 21) or the renderer
   classes. Fixed: citation widened to `installer.py:21-23` for the enum
   plus `:172`/`:181` for `ClaudeSkillRenderer`/`CodexSkillRenderer`.

All three classified Clear-satisfied against the current diff (not
self-attested — read against `gh pr diff` fresh). Presented at the batch
confirm gate; human approved; all three resolved via `resolveReviewThread`
GraphQL mutation, each confirmed `isResolved: true` in the mutation
response.

Thread-resolution verdict: **green** — every thread resolved, no
exceptions surfaced (no Unaddressed/Partial/Ambiguous/Problematic
threads this round).

# Validation

- `lrh github threads --mode raw --state all` on `5093f49` — 3 threads,
  all `isResolved: false` pre-resolution (despite `isOutdated: true`);
  all 3 resolved via `resolveReviewThread`, each mutation response
  confirmed `isResolved: true`.
- `gh pr checks` (unfiltered — confirmed via
  `gh api repos/xenotaur/logical_robotics_harness/rules/branches/main`
  that no `required_status_checks` rule exists on this repo, count 0,
  same as the documented PR #399 precedent) at time of this record: 3/5
  checks pass (`installed-wheel-smoke`, `lint`, `Check workflow files`),
  2 pending (`coverage`, `tests` still `IN_PROGRESS`) — re-checked at
  Step 8 against the post-push `HEAD`.
- `lrh validate` — run before this record's commit.

# Follow-up

None beyond what this PR itself adds to `project/design/backlog.md`.
Step 8 re-checks CI and REVIEW-LANDED against the post-push `HEAD`
(this record's own commit) before the final merge-readiness verdict.

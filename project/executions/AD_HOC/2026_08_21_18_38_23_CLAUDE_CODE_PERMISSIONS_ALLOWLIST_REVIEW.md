---
execution_id: 2026_08_21_18_38_23_CLAUDE_CODE_PERMISSIONS_ALLOWLIST_REVIEW
prompt_id: PROMPT(AD_HOC:CLAUDE_CODE_PERMISSIONS_ALLOWLIST_REVIEW)[2026-08-21T18:19:58+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/557
commit: 4d0cd98c
created_at: 2026-08-21T18:38:23+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/557
session_transcript: claude-app:17bd90a6-1e4a-4b7b-8883-fc13d0d8a192
---

# Summary

Addressed all 7 open review comments on PR #557 (4 from
chatgpt-codex-connector, all P1; 3 from copilot-pull-request-reviewer)
against `.claude/settings.json` and its companion doc.

# Result

All 7 comments were valid and fixed, none skipped:

- Narrowed `Bash(gh api *)` to the two exact read-only forms actually
  used (`gh api user`, `gh api user --jq .login`) — the wildcard let a
  caller mutate via `-X PUT/POST/DELETE`, including merging a PR without
  matching the `gh pr merge` deny rule (Codex P1).
- Added deny patterns covering force-push in flag-first, flag-last, and
  flag-middle argument orders, plus `--force-with-lease`/
  `--force-if-includes` — the prior deny only matched `--force`/`-f`
  immediately after `git push` (Codex P1 + Copilot, same finding).
- Added deny patterns for `find`'s mutating actions (`-delete`, `-exec`,
  `-execdir`, `-ok`, `-okdir`, `-fprint`, `-fprintf`) — `find *` was
  allowing worktree-destructive invocations under a "read-only" label
  (Codex P1).
- Removed `gh pr merge` from the deny list entirely — `permissions.deny`
  is an unconditional block with no "always prompt" mode, so it was
  silently breaking this repo's own agent-executes-merge-with-live-
  authorization path (`DEC-AGENT-EXECUTED-MERGE-GATE`) (Codex P1).
- Recategorized `git fetch` out of "read-only" in the doc — it writes
  local remote-tracking refs even though it never touches the working
  tree (Copilot).
- Replaced the undefined "Git Safety Protocol" proper noun with a
  descriptive statement, citing `AGENTS.md`'s actual merge-authority
  section for the one claim it supports (Copilot).

Pushed directly to the open PR branch (`xenotaur/chore/claude-code-permissions-allowlist`)
as commit `4d0cd98c`.

# Validation

- `python3 -c "import json; json.load(open('.claude/settings.json'))"` — valid JSON
- `scripts/version tools`
- `scripts/format --check --diff` — 196 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 1086 tests, OK; release smoke passed
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-SESSION-ARCHIVE-SYNC` has no actionable leaf)

# Follow-up

- `session_transcript` uses the in-session host id, confirmed via
  `$CLAUDE_CODE_HOST_SESSION_ID` (same session that authored the original
  PR and ran this review-response round — no window change occurred).
- The doc's "Known residual gap" note (bundled short-flag force-push
  forms, e.g. `-uf`) is a deliberate, disclosed limitation of the simple
  wildcard-based permission matcher, not something this round attempted
  to close — flagged for awareness if it ever needs closing later.
- Next: run `/lrh-confirm-fixes` against this PR to verify the fixes
  against the current diff and resolve the review threads before merge.

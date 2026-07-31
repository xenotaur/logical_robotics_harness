---
execution_id: 2026_07_31_04_42_07_WI_REVIEW_ROUND_ESCALATION_GATE_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_REVIEW_ROUND_ESCALATION_GATE_IMPL_REVIEW)[2026-07-31T04:41:39-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_31_04_19_55_WI_REVIEW_ROUND_ESCALATION_GATE_IMPL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/445
commit: eac6284537435bd252fed48f5965263b7a5eeac7
created_at: 2026-07-31T04:42:07-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/445
session_transcript: claude-app:b1f7a963-e611-4bcd-9d8c-a6a80d633a47
---

# Summary

Address PR #445's fifth review round: 2 P2 findings from Codex on the
round-state branch mechanics, plus an unrelated but critical
self-discovered fix to the Copilot retrigger command itself.

# Result

Both Codex findings valid and fixed:

- **"Clean up stale round-state worktrees before adding":** an
  invocation interrupted between `git worktree add` and
  `git worktree remove` leaves the branch registered as checked out,
  which then blocks the very recovery invocation meant to resolve it.
  Fixed by pruning and force-removing any stale registered worktree for
  `round-state` before every add.
- **"Restore the reviewed branch when bootstrap push fails":** the
  bootstrap sequence used `git checkout --orphan` directly in the main
  checkout with an `&&` chain; a failure partway (e.g. a transient push
  error) would skip the final `git checkout -` and strand the session on
  the orphan branch with its working tree wiped. Fixed by moving
  bootstrap into a throwaway worktree too, matching the read/write path,
  so a failure at any step can never touch the PR branch's own checkout.

**Separately, a critical, unrelated discovery surfaced via a parallel
memory-system investigation:** the actual root cause of the two
`copilot-swe-agent[bot]` concurrent-push incidents earlier in this WI's
history (on PR #444 and this PR) is now known. `gh pr comment --body
"@copilot review"` — the exact retrigger command this skill has used
throughout Step 8, including in every version of the round-cap-gate work
this session — does not invoke Copilot's review bot at all. A bare
`@copilot` mention anywhere in a PR comment body invokes GitHub's
Copilot *coding agent*, which treats "review" as free text, not a
reserved keyword, and — per a GitHub default change dated 2026-03-24 —
pushes commits directly to the PR branch in response. Both "mysterious"
concurrent pushes earlier in this session were this skill's own retrigger
command misfiring, not third-party interference. Fixed the command
everywhere it appears (`SKILL.md`'s retrigger step, `round-cap-gate.md`'s
"What round means" definition) to use `gh pr edit <pr-url> --add-reviewer
@copilot` instead — verified against `gh pr edit --help`, which
documents this exact special-value syntax for requesting Copilot's
review-only product.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this file.
- `scripts/format --check --diff`, `scripts/lint`: clean.
- `scripts/test`: 808 tests, OK.
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`: no differences.
- `gh pr edit --help` confirms `--add-reviewer @copilot` is the
  documented special-value syntax for a Copilot review request.
- `grep -rn '"@copilot review"'` across `src/lrh/`, `.claude/`, and
  `REVIEWS.md` confirms no other occurrences remain.
- Pushed directly to the open PR branch.

# Follow-up

- `/lrh-confirm-fixes` should run next to verify and resolve these
  threads, and this round's own retrigger should use the corrected
  command to confirm it actually reaches Copilot's review bot.
- `session_transcript: pending` should be updated once resolvable.

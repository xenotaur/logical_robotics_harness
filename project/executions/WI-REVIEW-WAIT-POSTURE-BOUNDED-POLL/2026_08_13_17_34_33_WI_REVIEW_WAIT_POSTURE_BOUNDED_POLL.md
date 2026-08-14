---
execution_id: 2026_08_13_17_34_33_WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL
prompt_id: PROMPT(WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL:WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL)[2026-08-13T15:57:14+00:00]
work_item: WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/552
commit: ec40e9d757a87ca761a4d65464ff1fc4587a6ebd
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL.md
session_transcript: claude-app:529191fc-e38a-4928-baf0-3196753dda62
created_at: 2026-08-13T17:34:33+00:00
---

# Summary

Implemented `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL`: the bounded
background-poll CI-wait mechanism specified by `PROP-REVIEW-WAIT-POSTURE`
Decision 3 (CI-wait half only).

# Result

**Scoping correction made before implementing (Step 4 confirm-plan
gate).** The WI's Required Change 2 cited `lrh-land/SKILL.md` Step 4 and
Step 5 as CI-wait call sites. Reading the actual current file content
directly showed both are bot-response-wait sites instead (Step 4's
`lastPush`-vs-now timing note; the "Re-run REVIEW-LANDED... sufficient
time to run" passage near Step 5/6) — the bot-response predicate this WI
explicitly scopes out. Implemented the mechanism once, canonically, in
`confirm-fixes-workflow.md` (the file `/lrh-land` Step 5 actually
inherits from by inlining `/lrh-confirm-fixes/SKILL.md` wholesale) rather
than writing a CI predicate into a bot-wait site.

**Additional stale-citation catch.** The WI's acceptance criteria cited
"reusing `round-cap-gate.md`'s existing `STALE_AGE_SECONDS=900`
constant" — verified directly that this constant no longer exists in
that file (removed when Stage 1 rewrote it to the self-review-substitute
mechanism). Defined `STALE_AGE_SECONDS=900` fresh in
`confirm-fixes-workflow.md`, disclosed honestly in the prose as a new
definition matching prior precedent, not a false claim of reuse.

**Implementation:**
1. Added the bounded-poll loop (three-way pending/success/terminal-
   failure branching via `check_ci_predicate`'s exit status, reusing the
   existing branch-rules exit-1 disambiguation rather than a naive raw
   exit-code mapping) to `confirm-fixes-workflow.md`, immediately after
   "Why CI is checked twice."
2. Cross-referenced it from `lrh-confirm-fixes/SKILL.md` Step 8.
3. Added an explicit note in `land-workflow.md`'s "Interim Invocation
   Pattern" section that Step 5 inherits the mechanism via inlining, and
   that Step 4's own wait is a different, out-of-scope predicate.
4. Mirrored to `.claude/skills/`, `.agents/skills/`,
   `.gemini/plugins/lrh/skills/` via `lrh skills install --local --target
   all --source current-repo --force`, not hand-copied.

**Proactive self-review (Step 7.5) found one real gap, fixed before
push:** the acceptance criterion's literal text asked for documentation
to land in `lrh-land/SKILL.md` itself at Step 4 and Step 5, not only in
`land-workflow.md`. Added matching pointer notes directly to `SKILL.md`
Step 4 (bot-wait, out of scope, deferred to Stage 4) and Step 5 (CI-wait
inherited via inlining), independently re-verified the finding via `git
diff main -- src/lrh/skills/lrh-land/SKILL.md` (confirmed zero hunks
before the fix), then re-ran `lrh skills install` and re-validated
before committing.

**Unrelated propagation drift deliberately excluded from this PR.**
`lrh skills install --target all` also picked up `.agents/skills/lrh-
work-remains/` and `.gemini/plugins/lrh/skills/lrh-work-remains/` —
mirror gaps from an unrelated, already-merged PR, incidental to running
`--target all` in this checkout. Left untracked/unstaged; not this WI's
scope.

# Validation

- `PYTHONPATH="$(pwd)/src" lrh validate`: 0 errors, 1 pre-existing
  unrelated warning (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`)
- `bash -n` against the new loop snippet in isolation (extracted alone,
  not concatenated with unrelated blocks in the same file — a naive
  concatenation can spuriously pass even if one block alone is broken):
  clean
- `diff -r src/lrh/skills/lrh-confirm-fixes .claude/skills/lrh-confirm-fixes`
  and `diff -r src/lrh/skills/lrh-land .claude/skills/lrh-land`: both
  exit 0, no differences
- `lrh skills install --dry-run --local --target codex --diff
  --source current-repo` and `--target antigravity --diff`: both report
  "up to date" for `lrh-confirm-fixes` and `lrh-land`, no `USER_MODIFIED`
- No `scripts/format`/`scripts/lint`/`scripts/test` — this PR touches
  only markdown, no Python source
- Proactive self-review (Step 7.5, diff-mode, cold-context subagent):
  found the `lrh-land/SKILL.md` gap above; independently re-verified
  before fixing; re-validated clean after

# Follow-up

- None beyond what the governing proposal's own Implementation Plan
  already lists (bot-response-wait predicate remains Stage 4 scope).
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after this session ends.

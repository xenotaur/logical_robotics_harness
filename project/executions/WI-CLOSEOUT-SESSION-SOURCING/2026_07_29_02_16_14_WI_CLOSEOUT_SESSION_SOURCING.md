---
execution_id: 2026_07_29_02_16_14_WI_CLOSEOUT_SESSION_SOURCING
prompt_id: PROMPT(WI-CLOSEOUT-SESSION-SOURCING:WI_CLOSEOUT_SESSION_SOURCING)[2026-07-29T02:09:21-04:00]
work_item: WI-CLOSEOUT-SESSION-SOURCING
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/431
commit: b3d89347666b41afafafd887ee3a698131aba6ec
created_at: 2026-07-29T02:16:14-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLOSEOUT-SESSION-SOURCING.md
session_transcript: claude-app:f1e9c968-f61d-4618-979c-29f8b08bfb0c
---

# Summary

Implement WI-CLOSEOUT-SESSION-SOURCING: make the `/lrh-closeout` skill's Step 3
backend-aware and host-id-first, closing the two review threads deferred during
PRs #409 (host-id sourcing) and #411 (`none` sentinel). Markdown-only skill
change; no Python.

# Result

Rewrote Step 3 in `SKILL.md` and the session-transcript section of
`references/closeout-workflow.md`, in both `src/lrh/skills/` and
`.claude/skills/` mirrors, to resolve in order:

1. `$CLAUDE_CODE_HOST_SESSION_ID` (host id, `local_` stripped →
   `claude-app:<host-uuid-stem>`) **with a confirm step**;
2. `list_sessions` matched by PR number (cross-session);
3. View > Copy URL paste (authoritative over the env var on divergence);
4. `none` (terminal) vs `pending` (to-do) sentinels, kept distinct.

Removed the child-id JSONL auto-detection (the #409 bug). Also aligned the
Reference-Knowledge bullet, the Step 8 reminder, and the frontmatter example
for consistency.

**Env-var-drift enhancement (found live this run):** the confirm step exists
because `$CLAUDE_CODE_HOST_SESSION_ID` reflects the *current window* and the
host id rotates on resume/continue. While planning this PR the env var had
drifted from the id used earlier in the session (`f1e9c968` vs `4c3d03d6`),
demonstrating the exact failure the confirm step guards. Included beyond the
WI's literal criteria at the user's explicit direction; still a superset of
every acceptance criterion.

Branch used an `-impl` suffix to avoid colliding with the already-merged
`/lrh-work-item` branch name (PR #419).

# Validation

- `scripts/format --check` — clean
- `scripts/lint` — clean
- `scripts/test` — 808 tests, OK
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS`)
- `diff -r src/lrh/skills/lrh-closeout .claude/skills/lrh-closeout` — exit 0

# Follow-up

- WI stays `proposed` until this PR merges and closeout resolves it.
- The closeout at the end of this PR's own chain is the first live run of the
  rewritten Step 3 (host-id sourcing + drift confirm).

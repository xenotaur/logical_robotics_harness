---
execution_id: 2026_11_06_23_53_51_CLAUDE_PLUGIN_NEW_SESSION_CLOSEOUT
prompt_id: PROMPT(AD_HOC:CLAUDE_PLUGIN_NEW_SESSION_CLOSEOUT)[2026-11-06T23:53:51+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/862
commit: e780d91a8fde69c02231f74c820edfe4d8484ac6
created_at: 2026-11-06T23:53:51+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/862
session_transcript: claude-app:b45207bd-f56d-4b2d-a182-23126acc88a6
---

# Summary

`/lrh-land` closeout record for PR #862, a docs-only follow-up to PR #861.
It adds to `docs/how-to/use-lrh-with-agent-assistants.md` §5 that a cloud
session got account plugins when it was created, so a session created
before the plugin was enabled needs replacing with a new one, since
`/reload-plugins` is refused in cloud sessions. It also names
desktop-started cloud sessions alongside claude.ai/code. PR #862 had no
primary execution record, because it was opened at the human's "Let's go
ahead with the docs pr" rather than through `/lrh-implement`. This is the
backfill record, and it carries the CHAIN-NOTE.

# Result

PR #862 merged as `e780d91a` via `lrh vcs merge ... --merge
--match-head-commit 2cefe795`, after the human's "Approve merge" reply to
the merge-and-closeout summary. `gh pr view` confirmed `MERGED`.

Closeout lands three records, with no work item, workstream or proposal
linked:
- this record;
- the `_CONFIRM` record;
- the PR-mode `_SELFREVIEW` record, which ships in this commit on `main` so
  the merge's SHA lock stayed on the reviewed head.

CHAIN-NOTE: `cycles=1; stops=0; gates=[chain-init, merge]; friction=none; self_review_rounds=1; note="Docs-only follow-up, the first run under the new stored stop condition (halt only on blocking or unverifiable findings, b4cd0dbe). Hosted review (Codex, Copilot) ran on open and was clean. The substitute self-review of the _CONFIRM head found four non-blocking wording points and no blocking ones, so the run went straight to the merge gate. Compare PR #861, which took three rounds under the stricter condition. Evidence came from a desktop-started cloud session for xenotaur/taurworks, created 2026-09-21: it had account skills but no plugins, while a new session had lrh at once."`

## Non-blocking notes from the self-review (not fixed)

1. One observation is stated as a rule. The old session predates every
   plugin on the account, and possibly predates plugin sync into cloud
   sessions altogether. So "created before plugin sync existed" fits the
   evidence as well as "plugins arrive at creation". The advice to start
   a new session holds either way. "In one test" would state the sample
   size.
2. "Got the plugin as claude.ai had synced it when the session was
   created" implies a version snapshot; only presence was observed.
3. "Same repository and environment": the new session's environment type
   wasn't recorded.
4. "No in-place refresh" is verified only for `/reload-plugins`. Anthropic
   says plugin toggles can reach running cloud Cowork sessions; whether a
   background path reaches a running Claude Code cloud session is
   untested.

# Validation

- CI passed on both heads (`eb062d98`, `2cefe795`).
- Locally on the doc commit: `scripts/format --check --diff`,
  `scripts/lint`, `lrh validate` (0 errors), `pytest tests/packaging_tests`
  (57 passed).
- Merge verified with `gh pr view` (state `MERGED`, merge commit
  `e780d91a`).
- `lrh validate` and `lrh sessions closeout-sync` ran before this closeout
  commit.

# Follow-up

- Optional: soften notes 1–3 the next time these docs change.
- To separate the two explanations in note 1, check a cloud session created
  after 2026-10-26 but before the `lrh` plugin was enabled, if one exists,
  or test whether a newly enabled plugin reaches an existing post-sync
  session.

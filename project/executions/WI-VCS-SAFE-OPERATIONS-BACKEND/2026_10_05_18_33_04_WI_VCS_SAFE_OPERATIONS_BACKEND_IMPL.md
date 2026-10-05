---
execution_id: 2026_10_05_18_33_04_WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL
prompt_id: PROMPT(WI-VCS-SAFE-OPERATIONS-BACKEND:WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL)[2026-10-05T17:44:14+00:00]
work_item: WI-VCS-SAFE-OPERATIONS-BACKEND
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/769
commit: 
created_at: 2026-10-05T18:33:04+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-VCS-SAFE-OPERATIONS-BACKEND.md
session_transcript: claude-app:a4f7b764-fb7e-424a-b0c1-6042007869d3
---

# Summary

Implementation of `WI-VCS-SAFE-OPERATIONS-BACKEND`, run through
`/lrh-execute`: audit LRH's git/`gh` mutation operations, add a
backend-neutral VCS interface with a GitHub implementation, implement the
SHA-locked merge as `lrh vcs merge`, and wire `/lrh-land` and
`/lrh-confirm-fixes` to present it.

# Result

Run-scoped decisions agreed at the `/lrh-execute` Step 2 chain gate: the
agent runs the merge (explicit override of the WI's own
`forbidden_actions: merge_pr`, for this run only); a P3-only substitute
review gets one verified fix round, then a delta review, then remaining P3s
are deferred; the branch and primary slug carry an `-impl` suffix because the
planning branch `xenotaur/feat/wi-vcs-safe-operations-backend` still exists
and would collide record slugs across the two PRs; and the WI is amended to
restore `add_cli_command` and name `lrh vcs merge` as the invocation surface.

Delivered, against the WI's acceptance criteria:
1. **Audit:** `project/audits/2026-09-28-vcs-mutation-operations-audit.md`
   (path as the WI names it; written 2026-10-05) inventories the operations
   with file:line citations, denial evidence E1 to E7, and dispositions.
2. **Backend design:** `src/lrh/vcs/` (`VcsBackend` protocol,
   `merge_pull_request_locked`, `GitHubBackend`, registry) and
   `docs/reference/vcs-backend.md`, which also documents how to add a backend.
   Only the merge action has code; the other actions are planned vocabulary.
3. **Wiring:** `/lrh-land` Step 6 and `/lrh-confirm-fixes` Step 8, plus the
   two lifecycle-diagram references, now present `lrh vcs merge`. `AGENTS.md`
   updated to match. `.claude/skills` is byte-identical; `.agents/skills` was
   rendered for just the three edited skills and its diff matches the source
   diff exactly.
4. **Observable errors:** subprocess and read failures surface as `VcsError`
   with the original message; a failed merge call also reports the PR's state
   read back afterwards; the merge is issued at most once.
5. **Pre-launch boundary:** stated in `docs/reference/vcs-backend.md` (Error
   scope), `docs/reference/cli/vcs.md`, and `/lrh-land` Step 6.
6. **Validation:** see below.

Not done, deliberately: the tracked `.gemini` Antigravity mirror (already
broadly stale; separate target-wide refresh), any permission-setting change,
and any claim that this bypasses the permission classifier. The audit shows
the same merge shape was denied once and allowed later.

Consequences to carry forward: `/lrh-land` Half A is inside a
`GATE-DEFINITION` region, so the chain-defaults profile is now stale for the
next run; the re-stamp is deferred to closeout rather than committed here.

# Validation

Run from the `LRH` conda env (pinned `ruff 0.15.12`, `black 26.3.1`):
- `scripts/format --check --diff` and `scripts/lint`: clean.
- `scripts/test`: 1949 tests, OK (after the self-review fixes).
- `lrh validate`: 0 errors, 0 warnings.
- `diff -r` of the three edited skills against `.claude/skills`: identical;
  `lrh skills check --target claude --local`: up to date; codex check: the
  three edited skills up to date (pre-existing `argument-hint` notes and a
  modified `lrh-antigravity-export` are unrelated).
- Diff-mode self-review before the first push: no P1; findings fixed or
  deliberately left, see the `_SELFREVIEW` record.
- Not exercised against a real PR: `lrh vcs merge` is covered by unit tests
  with a fake backend and a mocked `gh`. Its first real use is intended to be
  the merge of this PR.

# Follow-up

- Closeout: resolve this WI with a `resolution:` supplied by the user, and
  update the originating backlog entry in `project/design/backlog.md`.
- Offer the chain-defaults re-stamp (and the separate skip-consent re-grant)
  at closeout.
- Refresh the stale `.gemini` Antigravity mirror as its own change.
- `session_transcript` is already the durable pointer, not `pending`.

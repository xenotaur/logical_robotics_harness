---
execution_id: 2026_08_09_15_10_38_INVOCATION_AND_GATE_RESET
prompt_id: PROMPT(AD_HOC:INVOCATION_AND_GATE_RESET)[2026-08-09T15:06:33+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/535
commit: 98b128ed733a7b125a68f7d5d8db1308e6b62fd6
created_at: 2026-08-09T15:10:38+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Capture `PROP-INVOCATION-AND-GATE-RESET` — the design produced by a `/lrh-design`
session addressing three simultaneous operational failures: uncontrolled GitHub
review-bot spend, `disable-model-invocation` blocking legitimate skill
invocation, and confirmation fatigue from repeated near-no-op gates.

# Result

Created `project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md`
(533 lines), committed as `9e4ef0b1` on branch
`claude/self-review-command-prefs-68c9f9`.

The proposal records ten design decisions across a seven-stage program:
provisional-then-canonical sequencing (Decision 1); unconditional retrigger
removal with a provisional loop cap retained (Decision 2); fleet-wide
`disable-model-invocation` removal including chain runners (Decision 3);
report-only `/lrh-self-review` diff-mode (Decision 4); a platform-enforced
recursion guard (Decision 5); a three-artifact governance spine of audit +
proposal + DEC record (Decision 6); single-ask merge+closeout with closeout
still post-merge (Decision 7); late activation of the chain-defaults mechanism
(Decision 8); semantic redesign of the staleness watch list (Decision 9); and a
two-workstream ownership split (Decision 10).

Findings established during the design session and carried into the proposal:

- **The chain-defaults mechanism is dormant for three independent reasons**, each
  sufficient alone — shipped mode is `always_confirm`;
  `lrh.chainDefaults.skipConsentHash` is unset; and the stored `confirmed_commit`
  (`e4a1a34`) is already stale against its own Decision 5 watch list. The repeated
  condition-asking is a built mechanism that has never been in a firing state.
- **The staleness watch list is wrong in both directions** — it is file-granular
  (a typo fix invalidates consent identically to a gate redesign) *and* omits the
  three gate-bearing skills `/lrh-land` inlines (`/lrh-confirm-fixes`,
  `/lrh-review-response`, `/lrh-closeout`), verified by inspection.
- **Committing closeout content pre-merge is structurally impossible**, ruling out
  one candidate design: execution records cite the *merge* commit, which does not
  exist pre-merge, and pushing to the PR branch would break the
  `--match-head-commit` SHA lock by design.
- **Amendment authority is internal, not an override.**
  `DEC-DELIBERATE-CHAIN-INITIATION`'s own first Revisit condition ("chains
  frequently need mid-run human intervention") is met and was never actioned.
- **Consent is per-clone, not per-worktree** — corrected an earlier claim in the
  same session; `git config --local` in a worktree writes to the shared common
  `.git/config`.

Incidental repair: `lrh prompt check-execution` failed with exit 3
(`fatal: bad object refs/remotes/origin/main (1)`). Root cause was a stray
cloud-sync artifact ref file, `.git/refs/remotes/origin/main (1)`, holding
`fc8aa96` — verified an already-merged ancestor of `origin/main`, and already
ignored by git as a broken-name ref. Removed; the idempotence check then
returned exit 0 clean. No commits or reachable refs were affected.

# Validation

- `lrh prompt check-execution --slug invocation-and-gate-reset --work-item AD_HOC`
  → exit 0, "No prior execution record found for this slug" (after the stray-ref
  repair above).
- `lrh validate` → 0 errors, 1 warning. The warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)
  is pre-existing and unrelated to this change.
- `git diff --cached --check` → clean, no trailing whitespace.
- Commit content verified from the object store
  (`git show HEAD:<path>`), not the working tree: 533 lines.

# Follow-up

No PR opened. Opening one triggers this repository's automatic bot review, which
is the exact spend `PROP-INVOCATION-AND-GATE-RESET` Stage 1 exists to stop, so the
push/PR decision was deferred to the author rather than taken by default.

Deferred to the author (proposal's own Open Questions section):

1. Whether `/lrh-confirm-fixes` retains a user-requested retrigger escape hatch.
2. The provisional no-progress round-cap threshold.
3. Whether Taurcode's `:land`/`:execute` prompts fall in the Stage 3 cascade.
4. Stage 5b triage capacity across currently-open PRs.
5. `PROP-REVIEW-WAIT-POSTURE` (PR #522) disposition — rescope is the design's
   recommendation.

Follow-on artifacts offered, not created: `/lrh-workstream` for
`WS-INVOCATION-AND-GATE-RESET` (owning Stages 1, 2, 3, 3.5, 5, 6, 7), and an
Increment 3 work item under the existing `WS-LRH-CHAIN-DEFAULTS` (owning Stage 4
alongside `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`).

Also outstanding on this branch: 17 uncommitted files from the earlier
blast-radius exploration (retrigger removal and flag removal), deliberately left
uncommitted pending the review/revert/keep/tweak pass that Stage 1 and Stage 2
formalize.

Note: the `/lrh-proposal` skill's own commit-message template
(`Add design proposal <PROP-ID>: <title>`) does not satisfy `STYLE.md`'s
Conventional Commits requirement; `chore(design):` was used instead, matching
`STYLE.md`'s "planning artifacts" mapping to `chore`.

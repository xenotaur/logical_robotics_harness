# Tempspace migration burndown

Live checklist tracking each repository's move from Google-Drive-adjacent
`~/Workspace/` into `~/Tempspace/Projects/` (see `plan.md` and `README.md`
for the why and the repo-lane/session-lane procedure). Not a design
artifact — an operational status list, updated as each repo's move
progresses. Add a row here before moving a new repo; update its columns as
each step completes rather than leaving the row stale.

Repo-lane steps, per `README.md`'s "Repository lane" and `plan.md`'s
Sequence: move + symlink → mint canonical bucket (start one session from
the new physical path) → snapshot (`snapshot_state.sh`) → pre-migration
audit (`audit_buckets.py`) → memory migration (`migrate_memory.py`) →
acceptance test → post-migration re-audit (`audit_buckets.py` again,
expecting zero orphans and zero splits). Worktree repair (`git worktree
repair`, run from the new physical path) is an extra step for any repo
with linked worktrees.

Two audit points from `plan.md`'s Sequence are distinct steps, not one:
`audit_buckets.py` run *before* migration (plan.md step 1, establishes
current state) and re-run *after* (plan.md step 7, "expect zero orphans
and zero splits"). Both get their own column below so a row can't read as
fully done while either is actually skipped.

**"Insurance memory snapshot" is a separate, optional activity from the
in-sequence "Pre-migration audit" step** — do not conflate the two.
Several repos below had their memory corpus snapshotted as a standalone
precaution before any physical move was even scheduled (see "Memory
snapshots already taken" below); that's legitimately independent of, and
can predate, every other column in the same row, including "Physical move
+ symlink" itself — the memory corpus being snapshotted lives in the
*old* bucket regardless of whether the repo directory has moved yet. The
formal step-3 snapshot (`snapshot_state.sh`, run as part of the
in-sequence procedure right before "Pre-migration audit") is a distinct,
later action even when this column already reads "done."

| Repo | Physical move + symlink | Worktree repair | Canonical bucket minted | Insurance memory snapshot | Pre-migration audit | Memory migrated | Acceptance test | Post-migration re-audit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LogicalRoboticsHarness (LRH) | done | n/a checked at move time | done | done — formal in-sequence snapshot, migration fully complete | done | done | done | done — 0 orphans, 0 splits | Original incident repo; full history in `findings.md`. |
| LCATS | done | n/a checked at move time | done | done — formal in-sequence snapshot, migration fully complete | done | done | done | done — 0 orphans, 0 splits | Original incident repo; full history in `findings.md`. |
| ProsocialRobotics (`prosocial`) | done (2026-08-21) | done (2026-08-21) — 4 linked worktrees repaired, `prunable` cleared | not yet | not yet | not yet | not yet | not yet | not yet | Move predates this checklist; worktree repair was the gap found and fixed. No `Workstreams`-style sibling symlink added — no evidence `ProsocialRobotics/` ever had one (unlike LRH/LCATS). |
| Taurworks (`taurworks`) | done (2026-08-21) | done (2026-08-21) — 1 linked worktree (`intelligent-einstein-81d3f9`) repaired, `prunable` cleared | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | `taurworks-safety` (a stale second clone of the same GitHub repo, found alongside during survey) was investigated and deleted separately by the user — not part of this migration. `Archive/` and `.taurworks/` siblings deliberately left in place (not git-tracked, no evidence they need to travel with the repo). |
| Taurcode (`taurcode`) | not started | n/a — no worktrees found | not started | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Blocked on the user closing out the active Taurcode session (Claude) and a paused Codex session — do not move while either is live. Taurcode PR #82 (skills-resync work) landed separately and is unrelated to this move. |
| Velumin (`velumin`) | done (2026-08-21) | done (2026-08-21) — 1 linked worktree (`velumin-project-status-816cb8`) repaired, `prunable` cleared | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Moved while several Codex sessions were paused (not active) — paused Codex sessions are not path-keyed the way Claude Code sessions are, so resuming them later does not itself trigger the classic bucket-split failure this migration exists to prevent; the Claude-side memory-migration steps above should still happen once those sessions are next revisited. Velumin PR #7 already merged. |
| ReplicationVector (`replication_vector`) | done (2026-08-21) | n/a — no worktrees found | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Confirmed clean, no worktrees, `main`, no open PRs, no live session of any kind at move time — lowest-risk move of the batch. |

## Memory snapshots already taken (insurance, independent of move status)

Per-repo memory corpora were snapshotted to
`~/.local/share/claude-session-rescue/` as insurance before any closeout
work, ahead of the physical moves above — these remain valid regardless
of when each repo's move actually happens:

- `20260819-taurcode-velumin-rv-memory-snapshot-2/` — Taurcode, Velumin,
  ReplicationVector memory corpora (26 + 23 + 1 files).
- `20260819-taurworks-memory-snapshot/` — Taurworks memory corpus (45
  files).

## How to update this file

When a repo's row changes state, edit the relevant cell(s) directly —
don't append a running log. If a step surfaces a gap (like Prosocial's
missing worktree repair), note it in the Notes column rather than only in
chat, so the fix is discoverable later without replaying the conversation.

# Tempspace migration burndown

Live checklist tracking each repository's move from Google-Drive-adjacent
`~/Workspace/` into `~/Tempspace/Projects/` (see `plan.md` and `README.md`
for the why and the repo-lane/session-lane procedure). Not a design
artifact — an operational status list, updated as each repo's move
progresses. Add a row here before moving a new repo; update its columns as
each step completes rather than leaving the row stale.

Repo-lane steps, per `README.md`'s "Repository lane": move + symlink →
mint canonical bucket (start one session from the new physical path) →
memory migration (`migrate_memory.py`) → acceptance test → re-audit
(`audit_buckets.py`). Worktree repair (`git worktree repair`, run from the
new physical path) is an extra step for any repo with linked worktrees.

| Repo | Physical move + symlink | Worktree repair | Canonical bucket minted | Memory migrated | Acceptance test | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| LogicalRoboticsHarness (LRH) | done | n/a checked at move time | done | done | done | Original incident repo; full history in `findings.md`. |
| LCATS | done | n/a checked at move time | done | done | done | Original incident repo; full history in `findings.md`. |
| ProsocialRobotics (`prosocial`) | done (2026-08-21) | done (2026-08-21) — 4 linked worktrees repaired, `prunable` cleared | not yet | not yet | not yet | Move predates this checklist; worktree repair was the gap found and fixed. No `Workstreams`-style sibling symlink added — no evidence `ProsocialRobotics/` ever had one (unlike LRH/LCATS). |
| Taurworks (`taurworks`) | done (2026-08-21) | done (2026-08-21) — 1 linked worktree (`intelligent-einstein-81d3f9`) repaired, `prunable` cleared | not yet | not yet | not yet | `taurworks-safety` (a stale second clone of the same GitHub repo, found alongside during survey) was investigated and deleted separately by the user — not part of this migration. `Archive/` and `.taurworks/` siblings deliberately left in place (not git-tracked, no evidence they need to travel with the repo). |
| Taurcode (`taurcode`) | not started | n/a — no worktrees found | not started | not started | not started | Blocked on the user closing out the active Taurcode session (Claude) and a paused Codex session — do not move while either is live. Skills-resync work (PR #82) landed separately and is unrelated to this move. |
| Velumin (`velumin`) | not started | not started | not started | not started | not started | Confirmed session-free and clean as of 2026-08-19/20 survey (1 linked worktree `velumin-project-status-816cb8`, its own PR #7 already merged). Ready to move whenever. |
| ReplicationVector (`replication_vector`) | not started | not started | not started | not started | not started | Confirmed clean, no worktrees, `main`, no open PRs. Ready to move whenever. |

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

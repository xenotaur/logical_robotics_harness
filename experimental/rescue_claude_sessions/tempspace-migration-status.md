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

**Scope note: this checklist's columns cover only the plain
`<Project>/<repo_name>` path — the "human workspace" this repo's move
migrates memory into — not any `<Project>/Workspaces/<Agent>/<Task>/<repo_name>/`
clone.** Each such clone is a genuinely separate Claude Code bucket in
practice, confirmed empirically: LRH's own real, on-disk buckets include
both `-Users-centaur-Workspace-LogicalRoboticsHarness-logical-robotics-harness`
(the old symlinked path) and
`-Users-centaur-Tempspace-Projects-LogicalRoboticsHarness-logical-robotics-harness`
(the new real path) as two separately-populated buckets — Claude Code's
actual bucketing does not collapse a symlinked path and its target into
one bucket. **Caution:** `lrh`'s own `project_slug_for_path`
(`src/lrh/prompt_workflow_sessions.py:565-582`) does *not* reliably
predict this — it calls `.expanduser().resolve()` before slugging, so
feeding it the *old* symlinked path returns the *new* bucket's slug, not
the old bucket's real, distinct name confirmed above. This is a genuine
discrepancy between that helper and Claude Code's observed behavior, not
just a documentation nuance — flagged separately for a fix, since any
`lrh` command relying on it to resolve a symlinked path would silently
target the wrong bucket. (The sibling `bucketlib.slugify` in this same
`experimental/` directory does *not* call `.resolve()` — plain
character substitution on the given string — and matches the observed
real behavior; `project_slug_for_path` is the outlier.)

**This scope boundary is narrow to this one document, not a claim that
`Workspaces/*` clones are intended to start without memory access.**
They should have it — that they currently don't is a real, known gap,
not a design choice: `git worktree`'s own documented purpose is
isolating working directories/branches to avoid contention (see
[git-scm.com/docs/git-worktree](https://git-scm.com/docs/git-worktree),
"a git repository can support multiple working trees, allowing you to
check out more than one branch at a time" — nothing about isolating
information or memory access), so nothing about wanting per-clone git
isolation implies wanting per-clone memory isolation. Closing that gap
is being explored in a separate, in-progress investigation (not yet a
tracked artifact in this repo as of this writing) into a possible
hub-and-spoke consolidation model; the only mechanism actually shipped
today is the adopted, operator-initiated `lrh memory transfer` command
(`project/design/proposals/adopted/lrh-memory-command/00_proposal.md`),
which requires an explicit per-invocation `--from`/`--to` — automatic
propagation on bucket creation is an explicitly deferred, not-yet-built
idea in that same proposal, not scheduled work. Do not treat a
`Workspaces/*` clone's absence from this table's migration columns as
evidence the gap has been decided against, and do not assume a hub is
already being built just because an investigation is underway.

| Repo | Physical move + symlink | Worktree repair | Canonical bucket minted | Insurance memory snapshot | Pre-migration audit | Memory migrated | Acceptance test | Post-migration re-audit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LogicalRoboticsHarness (LRH) | done | n/a checked at move time | done | done — formal in-sequence snapshot, migration fully complete | done | done | done | done — 0 orphans, 0 splits | Original incident repo; full history in `findings.md`. |
| LCATS | done | n/a checked at move time | done | done — formal in-sequence snapshot, migration fully complete | done | done | done | done — 0 orphans, 0 splits | Original incident repo; full history in `findings.md`. |
| ProsocialRobotics (`prosocial`) | done (2026-08-21) | done (2026-08-21) — 4 linked worktrees repaired, `prunable` cleared | not yet | not yet | not yet | not yet | not yet | not yet | Move predates this checklist; worktree repair was the gap found and fixed. No `Workstreams`-style sibling symlink added — no evidence `ProsocialRobotics/` ever had one (unlike LRH/LCATS). |
| Taurworks (`taurworks`) | done (2026-08-21) | done (2026-08-21) — 1 linked worktree (`intelligent-einstein-81d3f9`) repaired, `prunable` cleared | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | `taurworks-safety` (a stale second clone of the same GitHub repo, found alongside during survey) was investigated and deleted separately by the user — not part of this migration. `Archive/` and `.taurworks/` siblings deliberately left in place (not git-tracked, no evidence they need to travel with the repo). |
| Taurcode (`taurcode`) | not started | n/a — no worktrees found | not started | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Blocked on the user closing out the active Taurcode session (Claude) and a paused Codex session — do not move while either is live. Taurcode PR #82 (skills-resync work) landed separately and is unrelated to this move. |
| Velumin (`velumin`) | done (2026-08-21) | done (2026-08-21) — 1 linked worktree (`velumin-project-status-816cb8`) repaired, `prunable` cleared | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Moved while several Codex sessions were paused (not active) — paused Codex sessions are not path-keyed the way Claude Code sessions are, so resuming them safely doesn't depend on this row's remaining columns. That is unrelated to when this row's own repo-lane steps (bucket, audit, memory migration, acceptance test) should run: per `README.md`'s repo lane, complete those promptly, on their own schedule — not deferred until the Codex sessions are next revisited — so any ordinary Claude session starting from the new path in the meantime doesn't see an empty corpus (`README.md:21-24`). Separately, per `findings.md:9-11,91-94`, Codex can write memory files directly into Claude's memory area, which can make an existing snapshot stale — re-snapshot immediately before running the repo-lane memory migration rather than relying solely on the 2026-08-19 insurance copy. Velumin PR #7 already merged. |
| ReplicationVector (`replication_vector`) | done (2026-08-21) | n/a — no worktrees found | not yet | done (2026-08-19) — see snapshot list below; a standalone insurance copy, not the in-sequence step | not yet | not yet | not yet | not yet | Confirmed clean, no worktrees, `main`, no open PRs at move time — lowest-risk move of the batch. Update (2026-08-22): no longer session-free — separate `Workspaces/Claude/ControlPlane/replication_vector` and `Workspaces/Codex/ControlPlane/replication_vector` clones now exist with active sessions (see scope note above: those clones' lack of memory access is a real, known gap under separate investigation, out of *this document's* scope, not out of scope for the project). This row's own remaining columns still refer only to the plain path above. |

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

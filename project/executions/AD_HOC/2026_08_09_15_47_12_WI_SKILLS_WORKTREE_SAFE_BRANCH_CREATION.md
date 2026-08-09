---
execution_id: 2026_08_09_15_47_12_WI_SKILLS_WORKTREE_SAFE_BRANCH_CREATION
prompt_id: PROMPT(AD_HOC:WI_SKILLS_WORKTREE_SAFE_BRANCH_CREATION)[2026-08-09T15:45:25+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T15:47:12+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` to fix the branch-creation step
in the eight skills that hard-code `git checkout main && git pull`.

# Result

Created `project/work_items/proposed/WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION.md`,
committed as `9d71ca69` on branch `claude/self-review-command-prefs-68c9f9`
alongside `PROP-INVOCATION-AND-GATE-RESET`, per the author's request to assemble
the planning artifacts for review as a whole.

Four defects documented, none guarded in any of the eight skills:

1. **Worktree lock.** `git checkout main` fails when another worktree holds the
   default branch. Verified live: `main` was checked out in
   `.claude/worktrees/lrh-pypi-installability-status-a4c549` with 10+ worktrees
   active, so all eight skills would fail at their branch step when invoked from
   any other worktree.
2. **Dirty-tree carry-over.** `git checkout` brings working-tree modifications
   onto the new branch. Zero of eight check `git status --porcelain` first. The
   two skills mentioning "uncommitted" (`lrh-work-item`, `lrh-readiness`) were
   inspected: both references concern not leaving edits uncommitted *later*,
   neither is a pre-checkout guard.
3. **Hard-coded `main`.** LRH installs into client repositories that may use
   `master` or `trunk`.
4. **Silent stale base.** With `&&`, a failed `git pull` after a successful
   checkout leaves the branch on a stale default with no signal.

The fix already exists in-repo twice and never propagated: `/lrh-land`
`SKILL.md:400-405` branches from `origin/main` to dodge the worktree lock, and
`round-cap-gate.md` documents hardened default-branch resolution including the
`pipefail` trap. This is the restatement-drift pattern already tracked in
`project/design/backlog.md`.

`related_workstreams` left empty deliberately: `WS-SKILLS` is the conceptual
home but is `resolved` (attaching would reopen a closed workstream), and
`WS-SKILLS-TARGET-AWARE-INSTALL` covers Codex install targets, not branch
mechanics.

Branch hygiene performed in the same run, at the author's direction: the 17
uncommitted blast-radius exploration files that had been sharing this branch's
working tree were moved to their own branch
(`claude/wip-retrigger-and-flag-removal-exploration`, commit `a92159f0`,
+301/-2007 matching the original diff exactly), leaving this branch as planning
artifacts only. A patch backup was taken to the session scratchpad before the
switch, and overlap between the carried modifications and the branch's own
commits was verified empty beforehand.

# Validation

- `lrh prompt check-execution --slug wi-skills-worktree-safe-branch-creation
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning. The warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)
  is pre-existing and unrelated.
- `lrh work-items readiness WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` →
  `prompt_ready: yes`, confirming the `## Validation` section parsed as bullets
  rather than a fenced block.
- `git diff --cached --check` → clean.
- Post-switch verification: exploration branch carried all 17 files and committed
  them; planning branch returned to a clean tree with its 2 commits intact.

# Follow-up

No PR opened, consistent with the author's plan to assemble the proposal,
workstream, and work items and review them as a whole, and with the standing
constraint that opening a PR triggers automatic bot review.

Notable while running this skill: `/lrh-work-item` Step 6 is itself one of the
eight sites this work item fixes. Its `git checkout main && git pull` would have
failed in this environment, so the branch step was deviated from deliberately
rather than executed. The skill diagnosed its own defect during use.

Second instance of a skill-template defect found this session: `/lrh-work-item`
Step 9 and `/lrh-proposal` Step 9 both specify commit messages
(`Add work item <ID>: <title>`) that do not satisfy `STYLE.md`'s Conventional
Commits requirement. `chore(work-item):` was used instead. Worth folding into
this work item or a sibling.

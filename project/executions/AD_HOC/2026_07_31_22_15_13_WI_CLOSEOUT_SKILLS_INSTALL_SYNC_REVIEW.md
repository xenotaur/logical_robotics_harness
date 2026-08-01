---
execution_id: 2026_07_31_22_15_13_WI_CLOSEOUT_SKILLS_INSTALL_SYNC_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SKILLS_INSTALL_SYNC_REVIEW)[2026-07-31T21:56:12-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_31_21_38_13_WI_CLOSEOUT_SKILLS_INSTALL_SYNC
pr: https://github.com/xenotaur/logical_robotics_harness/pull/454
commit: 2a56851
created_at: 2026-07-31T22:15:13-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/454
session_transcript: claude-app:20d16dd9-a465-4d31-b39f-280db14488ef
---

# Summary

Addressed 2 open review comments on PR #454
(`WI-CLOSEOUT-SKILLS-INSTALL-SYNC`): a grammar nit from
`copilot-pull-request-reviewer` and a P1 substantive finding from
`chatgpt-codex-connector` that the work item's proposed non-force
`lrh skills install` step cannot actually refresh a stale skill. A
follow-up Copilot review of the fix commit raised 3 more findings (as a
summary body, 0 new inline comments); 1 was valid and fixed, 2 were
checked against this skill's own documented conventions and found false.

# Result

- Comment 1 (copilot-pull-request-reviewer, grammar): "found 6 diverged"
  read as ungrammatical. Fixed to "found 6 that had diverged" in
  `## Problem / Context`.
- Comment 2 (chatgpt-codex-connector, P1): confirmed valid —
  `_skill_differs_from_package` in `src/lrh/skills/installer.py`
  classifies any installed skill whose bytes differ from the current
  package as `USER_MODIFIED` and skips it, including a stale unmodified
  copy of the previous package revision. A plain non-force
  `lrh skills install` run after a skill-touching merge would therefore
  skip exactly the skills it's meant to fix — confirmed retroactively
  against the 6 skills found stale in the creation record's session, none
  of which would have been refreshed by a non-force run. Rescoped the
  work item's Scope, Required Changes, Non-Goals, Acceptance Criteria,
  Validation, and frontmatter `acceptance`/`artifacts_expected` from
  "blanket non-force install" to "targeted refresh of exactly the skill
  names the merged PR's diff touched," adding a Required Changes item for
  a new `installer.py` capability (force-install a named subset) with
  accompanying unit test coverage.
- Both fixes applied directly to
  `project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md`
  (planning-artifact text only — no code changed, since this PR only
  creates the work item, not its implementation).
- Pushed as commit `ce5558a`.

**Follow-up round** — a second Copilot review (bound to commit
`3443565`, triggered by re-requesting Copilot review) raised 3 findings
as suppressed/summary comments (0 new inline threads):
- "`status: in_progress` is an outlier vs. other `_REVIEW` records" —
  **checked and found false**: all 98 other `_REVIEW` records under
  `project/executions/AD_HOC/` show `status: landed` only because
  `/lrh-closeout` has already landed them; a freshly created,
  not-yet-closed-out record is supposed to be `in_progress` per this
  skill's own Step 7 (`--status in_progress`). Not changed.
- "`session_transcript: pending` should be a concrete value like other
  records" — the literal value this skill's Step 7 instructs
  (`session_transcript: pending`), so the finding's stated premise is
  wrong, but the underlying suggestion is a genuine improvement:
  `$CLAUDE_CODE_HOST_SESSION_ID` is available and stable for this session
  (already used to populate the sibling creation record), so filled in
  `session_transcript: claude-app:20d16dd9-a465-4d31-b39f-280db14488ef`
  here too for consistency, and dropped the now-stale "update later"
  follow-up note.
- "`lrh-create-skill` is not the only skill documenting `lrh skills
  install`" — **confirmed valid**: `lrh-implement`'s reference doc
  (`references/lrh-implement-workflow.md`) has its own `### lrh skills
  install` section, and `_shared/lifecycle-chain.md`'s table also
  mentions it (in `lrh-create-skill`'s own row). Reworded the WI's
  `## Problem / Context` claim from "the only skill that documents..." to
  precisely state that `lrh-create-skill` is the only skill whose *own
  execution steps* direct the agent to run it, and dropped the brittle
  line-number citations per the review's secondary point.
- Pushed as commit `2a56851`.
- Fixed the `commit:` frontmatter field itself (was one commit stale) —
  pushed as commit `e8c49ea`.

**Third round** — retriggered both reviewers against `e8c49ea`; Copilot
`APPROVED` (🟢 ready to approve, 2 more suppressed comments), Codex
posted a clean summary review plus 4 new inline threads (all substantive,
none previously seen):
- P2 "Filter changed paths to actual skill directories" — **confirmed
  valid**: a changed-path prefix match on `src/lrh/skills/` also matches
  non-skill files directly under it (e.g. `installer.py`, a module, not a
  skill tree); passing that name to `_copy_skill` raises
  `NotADirectoryError`. Added an explicit filter-against-`_skill_names()`
  requirement to Required Changes item 1, with new test coverage
  specified for a diff containing `src/lrh/skills/installer.py` itself.
- P2 "Strip the `local_` prefix from the transcript pointer" — **confirmed
  valid against `project/executions/README.md:65`** (the review's own
  cited `AGENTS.md:L107-L109` did not actually contain this rule — checked
  and it doesn't; the real source is the README's `session_transcript`
  values table, which does). Both this record's and the creation record's
  `session_transcript` had the un-stripped `local_` prefix
  (`claude-app:local_20d16dd9-...`); fixed both to
  `claude-app:20d16dd9-a465-4d31-b39f-280db14488ef`.
- P1 "Require confirmation before destructive skill refresh" —
  **confirmed valid**: the WI's Risk Notes only required an after-the-fact
  report of the targeted-refresh mutation, not pre-action disclosure —
  meaning a skill touched by the merge that also happened to carry
  genuine local edits could be silently, irreversibly overwritten.
  Rewrote Required Changes item 2 and Risk Notes to require the planned
  refresh (which names, added/modified vs. removed) be included in
  `/lrh-closeout`'s own Step 2 plan and approved at its Step 4 confirm
  gate *before* any file under `~/.claude/skills/` is written.
- P2 "Handle removed and renamed skills explicitly" — **confirmed
  valid**: the original scope only discussed "touched" skills generically;
  a skill the merge deleted or renamed has no current package source to
  refresh from, so path-prefix detection alone would leave the obsolete
  `~/.claude/skills/<old-name>` stale with no signal. Added an explicit
  added/modified-vs-removed split to Required Changes item 2, a
  corresponding Non-Goal (no automatic uninstall — report as an anomaly
  instead), and matching Acceptance Criteria.
- Copilot's 2 suppressed comments on this round were metadata-consistency
  notes already superseded by the fixes above (transcript field, commit
  field) — no separate action needed.
- All 4 fixes applied to
  `project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md`
  (Required Changes, Non-Goals, Acceptance Criteria, Validation, Risk
  Notes, and frontmatter `acceptance`).
- Pushed as commit `551c36c`.

**Fourth round** — retriggered both reviewers against `551c36c`; Copilot
`APPROVED` again (1 minor wording nit), Codex posted a clean summary
review plus 2 new inline threads (both P1, both self-consistent with
round 3's own just-written text):
- "Add a bootstrap install for the new closeout step" — **confirmed
  valid, and important**: the globally installed `lrh-closeout` skill is
  what actually runs in a session; it only gains the new step once
  refreshed, but refreshing it is exactly what the new step does — so it
  cannot bootstrap its own first activation on this WI's own
  implementation PR. Added Required Changes item 5, a matching Acceptance
  Criterion, a Validation entry, and a Risk Note requiring the
  implementation PR's own closeout to include an explicit manual refresh
  of `lrh-closeout` itself.
- "Preserve removed names before package filtering" — **confirmed valid,
  a real bug in round 3's own text**: round 3 filtered the touched-name
  set against `_skill_names()` (package membership) *before* the
  added/modified-vs-removed split, which discards a removed skill's name
  before it can ever be classified removed — making the removed-skill
  handling round 3 just added unreachable. Rewrote Required Changes item
  2 to sequence this correctly: derive candidates by *structural* path
  shape first (excludes non-skill files like `installer.py` without
  relying on package membership), then partition by package membership
  second (added/modified vs. removed/renamed).
- Copilot's 1 suppressed comment ("`~force` reads like a pseudo-flag that
  doesn't exist") was resolved as a side effect of the item-2 rewrite
  above, which dropped that phrasing entirely.
- All fixes applied to the same WI file (Required Changes, Acceptance
  Criteria, Validation, Risk Notes, frontmatter `acceptance`).
- Pushed as commit `cabe863`.

**Fifth round** — retriggered both reviewers against `cabe863`; Copilot
`APPROVED` cleanly (0 comments). Codex's summary review was clean, but 1
new inline thread remained (the round-4 bootstrap thread persisted
non-outdated, since it isn't line-anchored — not a new finding, already
addressed) plus 1 genuinely new P1 thread:
- "Use a force-capable targeted command for bootstrap" — **confirmed
  valid, a bug in round 4's own fix**: round 4's Required Changes item 5
  told the bootstrap step to run "a manual, one-time `lrh skills install`
  (or equivalent targeted refresh)" — but plain non-force
  `lrh skills install` is exactly the command whose `USER_MODIFIED`
  misclassification this entire WI exists to fix, and the installed
  `lrh-closeout` copy at bootstrap time necessarily differs from the
  just-merged package (that's the premise of needing a bootstrap at
  all). Reworded item 5 to require the targeted-refresh capability
  itself, scoped to `lrh-closeout` alone, and explicitly rule out both
  the plain command and a blanket `--force`. Also clarified that the
  Python-level function is importable immediately post-merge (no
  install-order problem for the code itself, only for the rendered
  `~/.claude/skills/*.md` content). Matching Acceptance Criterion,
  Validation entry, and Risk Note updated to match.

# Validation

- `scripts/version tools`: ruff 0.15.12, black 26.3.1, pylint 2.16.2,
  pyright not installed (pre-existing environment gap, unrelated to this
  change)
- `scripts/format --check --diff`: all 179 files unchanged
- `scripts/lint`: all checks passed
- `scripts/test`: OK
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- Next: `/lrh-confirm-fixes` against PR #454 to verify these fixes and
  resolve the review threads before merge.

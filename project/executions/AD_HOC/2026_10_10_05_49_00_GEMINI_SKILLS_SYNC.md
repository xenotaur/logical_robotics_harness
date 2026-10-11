---
execution_id: 2026_10_10_05_49_00_GEMINI_SKILLS_SYNC
prompt_id: PROMPT(AD_HOC:GEMINI_SKILLS_SYNC)[2026-10-10T05:33:22+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/819
commit:
created_at: 2026-10-10T05:49:00+00:00
agent: claude_app
instruction_source: ad-hoc — regenerate stale .gemini/plugins/lrh/skills Antigravity install target from src/lrh/skills and pin it with a renderer-equality regression test
session_transcript: pending
---

# Summary

Regenerated the committed Antigravity install target
`.gemini/plugins/lrh/skills/` from canonical `src/lrh/skills/`. Added a
regression test that pins the committed tree to the Antigravity renderer
output.

# Result

- **Diff review.** Ran
  `lrh skills install --local --target antigravity --source current-repo --diff`
  and reviewed every difference before overwriting.
  - 14 skills reported local modifications: closeout, create-skill,
    doc-organize, doc-work, land, pr-triage, proposal, readiness,
    review-response, self-review, session-id-claude, work-item, work-remains
    and workstream.
  - Every difference was plain staleness: content present in `src` but never
    regenerated into `.gemini`. Examples: the "Restricted network recovery"
    sections, the frontmatter scalar-quoting guidance, `lrh vcs merge`
    wording, the `GATE-DEFINITION` markers, and self-review's log-hygiene
    section.
  - The only installed-only lines were older wording from `src`. No
    Antigravity-specific edits were found, and `.gemini` held no skills or
    files beyond what `src` has.
- **Decision (user):** keep `.gemini/plugins/lrh/` committed.
- **Regeneration.** Ran the same command with `--force`, after a dry-run.
  That updated the 14 stale skills and added `lrh-antigravity-export`.
  `plugin.json` was unchanged.
- **Regression test.** Added
  `tests/packaging_tests/skills_gemini_sync_test.py`. It asserts:
  - the committed skill set equals the `src` skill set;
  - each skill equals `installer._renderer_for_target(SkillTarget.ANTIGRAVITY).render(name, files)`
    file-by-file, with no extra or missing files;
  - symlinks are rejected, as the installer rejects them;
  - `plugin.json` equals the installer manifest.

  The test failed when one stale file was restored or `lrh-antigravity-export`
  was removed. It passed after regeneration.
- **Rebase.** Rebased onto `origin/main` (10 newer commits, including `.gemini`
  updates). A dry-run regeneration then reported everything up to date.
- **Prior art.** No existing work item or test covered `.gemini` sync. The
  `.claude`/`.agents` mirrors are pinned only by
  `skills_vcs_merge_wiring_test.py`. PR #807 had regenerated only
  `lrh-confirm-fixes`.

# Validation

- Ran in the per-worktree conda env `LrhGeminiSkillsSync`
  (`scripts/conda-worktree-env`). It provides Python 3.11.17 and ruff 0.15.12,
  with the editable `lrh` bound to this worktree.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: OK.
- `lrh validate`: 0 errors, 0 warnings.
- The diff-mode `/lrh-self-review` ran before push. See the
  `GEMINI_SKILLS_SYNC_SELFREVIEW` record.

# Follow-up

- `lrh skills install --diff` is not read-only: it installed the missing
  `lrh-antigravity-export` while reporting diffs. This was spun off as a
  separate task.

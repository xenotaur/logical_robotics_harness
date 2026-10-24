---
execution_id: 2026_10_23_05_40_34_SKILLS_MIRROR_WORDING_POLISH
prompt_id: PROMPT(AD_HOC:SKILLS_MIRROR_WORDING_POLISH)[2026-10-22T18:02:51+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/854
commit:
created_at: 2026-10-23T05:40:34+00:00
agent: claude_app
instruction_source: ad-hoc — wording polish for skill mirror regeneration guidance, the follow-up recorded in the PR 831 closeout note
session_transcript: pending
---

# Summary

This PR fixes the two optional wording issues recorded in PR #831's
closeout note (`2026_10_15_05_38_31_SKILLS_MIRROR_SYNC_TEST_CLOSEOUT_NOTE`,
Follow-up). Both came from #831's second PR-mode self-review.

# Result

- **`lrh-create-skill` Step 6.** "Regenerate only the affected skill" had no
  clear referent.
  - A new skill cannot trigger the "local modifications — skipped" warning.
    The Step 6 existence check rules out target directories, and the
    non-forced install then installs the skill (`installer.py:930-948`).
  - The text now says any such warning names a *different* item: another
    skill, or the Antigravity `plugin.json` (`installer.py:665`). That item
    is already out of sync, either on the base branch or through an
    uncommitted working-tree edit.
  - The reader is told to leave the item alone, not to add `--force`, and
    to report it separately (or revert their own stray edit).
- **`lrh-review-response` `canonical-validation.md` and `CONTRIBUTING.md`.**
  The pointer to the scratch-source recipe said "edited skills", but the
  recipe shows one `<name>`. Both now say to copy each edited skill into the
  same scratch directory, one `cp -R` per skill.
- **Regeneration.** Both skills were regenerated into `.claude`, `.agents` and
  `.gemini` from a scratch source holding both. The `--force --diff` preview
  listed only those skills.
- **Self-review.** The diff-mode `/lrh-self-review` found two minor precision
  issues in the new text: the referent could be `plugin.json`, and drift
  could come from the working tree. Both were fixed in `37aaa861`. See
  `2026_10_23_05_39_54_SKILLS_MIRROR_WORDING_POLISH_SELFREVIEW`.

**Approval.** The user requested the fix ("Please fix the wording polishes")
and approved the Step 4 plan.

# Validation

All runs used conda env `LrhGeminiSkillsSync` with `PYTHONPATH=$PWD/src`
(ruff 0.15.12, black 26.3.1), branched from `origin/main` `8d06df4a`.

- `scripts/format --check --diff`: clean.
- `scripts/lint`: exit 0.
- `scripts/test`: 2368 tests, OK.
- `lrh validate`: 0 errors.
- `lrh skills install --local --target all --source current-repo --dry-run`:
  all up to date.

# Follow-up

None.

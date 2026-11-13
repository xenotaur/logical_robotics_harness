---
execution_id: 2026_10_24_21_14_41_SKILLS_MIRROR_WORDING_POLISH_REVIEW
prompt_id: PROMPT(AD_HOC:SKILLS_MIRROR_WORDING_POLISH_REVIEW)[2026-10-24T21:10:44+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_23_05_40_34_SKILLS_MIRROR_WORDING_POLISH
pr: https://github.com/xenotaur/logical_robotics_harness/pull/854
commit:
created_at: 2026-10-24T21:14:41+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/854
session_transcript: pending
---

# Summary

Review-response round for PR #854, run inline from `/lrh-land`.

There were no GitHub review threads: Copilot recommended approval, and Codex
found nothing. Instead, the run halted under its stop-work condition after
the PR-mode self-review at `b1387bab` (record
`2026_10_23_06_10_43_SKILLS_MIRROR_WORDING_POLISH_CONFIRM_SELFREVIEW`) found
one low-severity wording defect. The user approved this fix round ("Go
ahead").

# Result

Fixed in `ffef098d`, pushed directly.

1. **Low (self-review finding 1).** In `lrh-create-skill` Step 6, the claim
   "the new skill cannot trigger this warning" was too absolute.
   - *Why it was wrong:* Step 6's existence check lets the user choose to
     overwrite or extend an existing skill, and `src` can be edited again
     after installing (for example, by a Step 7 frontmatter fix). In both
     cases the warning names the user's own skill, and the text wrongly said
     to leave it alone.
   - *The fix:* the paragraph now branches on which item the warning names.
     - **Your own skill:** the claim is scoped to a first install of a
       brand-new skill. The two exceptions are named, with "regenerate just
       that skill with the scratch-source recipe" as the remedy.
     - **Anything else** (another skill, or `plugin.json`): leave it alone,
       no repo-wide `--force`, and revert or report it.
   - This restores the coverage the old "regenerate only the affected skill"
     sentence had, without its ambiguity.
2. **Nit 2.** The loose "it" in "Report it … until it is" is now explicit
   ("report the out-of-sync item … until that item is back in sync").
3. **Nit 3.** CONTRIBUTING's several-skills note now sits in the sentence
   that introduces the recipe, ahead of the code block.

`lrh-create-skill` was regenerated into `.claude`, `.agents` and `.gemini`
from a one-skill scratch source. The `--force --diff` preview listed only
that skill.

# Validation

Run in conda env `LrhGeminiSkillsSync` with `PYTHONPATH=$PWD/src`:

- `scripts/format --check --diff`: clean.
- `scripts/lint`: exit 0.
- `scripts/test`: 2368 tests, OK.
- `lrh validate`: 0 errors.
- `lrh skills install --local --target all --source current-repo --dry-run`:
  all up to date.

# Follow-up

Re-run confirm-fixes and the PR-mode self-review before the merge gate.

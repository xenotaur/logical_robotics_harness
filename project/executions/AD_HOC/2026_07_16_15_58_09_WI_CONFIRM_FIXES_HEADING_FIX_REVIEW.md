---
execution_id: 2026_07_16_15_58_09_WI_CONFIRM_FIXES_HEADING_FIX_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CONFIRM_FIXES_HEADING_FIX_REVIEW)[2026-07-16T15:40:03-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/395
commit: 
created_at: 2026-07-16T15:58:09-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/395
session_transcript: pending
---

# Summary

Address 2 open review comments on PR #395 (`WI-SKILLS-LRH-CONFIRM-FIXES`
heading fix) via `/lrh-review-response`.

# Result

Both comments passed presence/validity/feasibility triage and were fixed:

1. **copilot-pull-request-reviewer** — `## Problem / Context` (the heading
   just applied in this same PR, copied from the documented canonical
   convention) does not feed `parsed.problem`:
   `work_item_prompt_core._parse_sections()` keys sections by exact
   lowercased heading text, and `parse_work_item_markdown()` looks up
   `sections.get("problem", "")` — a section titled "Problem / Context"
   never matches the key `"problem"`. Verified empirically: `parsed.problem`
   was empty, so `build_work_item_prompt_data()`'s
   `objective = parsed.problem or parsed.summary or parsed.title` was
   silently falling back to Summary instead of the richer Problem content.
   Fixed by renaming the heading to `## Problem` in this WI. Verified after
   the fix: `parsed.problem` is non-empty and the objective now equals it.
2. **copilot-pull-request-reviewer** — `## Required Changes` used a numbered
   list (`1.`, `2.`, ...) with wrapped continuation lines.
   `work_item_prompt_core._extract_bullets()` only recognizes lines starting
   with `- ` as bullet starts; a numbered list falls through entirely, so
   `build_work_item_prompt_data()` fell back to `_normalized_lines()`, which
   splits every physical line (including wrapped continuations) into its own
   fragment. Verified empirically: the 9-item numbered list was producing 26
   garbled fragments. Fixed by converting to `- `-bulleted items with
   indented continuation lines, which `_extract_bullets()` merges correctly.
   Verified after the fix: exactly 9 clean bullets, matching the original
   items.

Both fixes verified by directly calling `parse_work_item_markdown()`,
`evaluate_prompt_readiness()`, and `build_work_item_prompt_data()` against
the file — not just visual inspection. `is_ready: True` after both fixes.

No original execution record was found to link via `rerun_of` — this fix was
authored directly (not via `/lrh-implement`), so there is no primary `WI-*`
execution record for this branch.

**Follow-up finding, flagged as a background task (not fixed here):** the
`## Problem / Context` vs. `"problem"`-key mismatch is not unique to this WI
— `work-item-body-guide.md` documents `## Problem / Context` as the
canonical heading, but the parser only recognizes `## Problem`. Every WI
following the documented convention has this same silent gap, including the
already-merged `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE.md`. This PR's fix is a
local rename on one file, which now makes that one WI's heading diverge from
the documented guide — fixing the guide/parser mismatch at the source is a
separate, broader task (spawned as a background task, `task_f66dd66c`,
titled "Fix Problem/Context heading vs parser key mismatch").

# Validation

```
scripts/version tools  — lrh 0.2.5.dev83, Ruff 0.15.12, Black 25.11.0 confirmed
scripts/format --check --diff  — skipped: no Python files changed (markdown-only control-plane edit)
scripts/lint  — skipped: no Python files changed
scripts/test  — skipped: no Python files changed
lrh validate  — 0 errors, 0 warnings
parse_work_item_markdown() + evaluate_prompt_readiness() + build_work_item_prompt_data() (direct parser check)  — is_ready: True, parsed.problem non-empty, objective uses problem, required_changes = 9 clean bullets
```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after the
  session ends.
- Pick up the spawned background task once PR #395 merges: fix the
  `## Problem / Context` heading vs. `"problem"`-key mismatch at the source
  (parser or guide), and check `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE.md` for
  the same latent defect.
- No unresolved comments remain on PR #395 as of this record.

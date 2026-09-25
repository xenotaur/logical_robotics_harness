---
execution_id: 2026_09_22_06_22_38_WI_EXPORT_CLAUDE_SKILL_CURRENT_SESSION_DEFAULT_FORCE_EXCEPTION
prompt_id: PROMPT(AD_HOC:WI_EXPORT_CLAUDE_SKILL_CURRENT_SESSION_DEFAULT_FORCE_EXCEPTION)[2026-09-22T06:19:31+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_22_05_28_56_WI_EXPORT_CLAUDE_SKILL_CURRENT_SESSION_DEFAULT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/703
commit: 34f05fa01e93dbdbec533a7483d6947ac3b1a210
created_at: 2026-09-22T06:22:38+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/703
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Human-directed design refinement on `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`,
folded into the same open PR (#703) before merge, not a bot review response.
Discussed in-session: `km9-g`'s underlying concern (typed invocation skips
confirmation even for a durable, potentially sensitive write) has a narrow,
real edge in the `--force` case specifically — overwriting an existing prior
export is a different kind of consequence than target selection, per
Nielsen Norman Group's guidance that confirmation should be reserved for
actions with serious, hard-to-undo consequences, distinct from routine
target selection.

# Result

Step 3 of `src/lrh/skills/lrh-export-claude/SKILL.md` (and its three
installs) gained a check evaluated before the typed/model-initiated split:
if the invocation includes `--force`, always wait for confirmation before
Step 4, regardless of typed/model status, stating that an existing file at
the destination would be overwritten. `--force` is currently the only entry
in this list.

Two designs were considered and discussed with the user before
implementing:

1. **Dynamic**: compute the exact default destination path (duplicating the
   exporter's `<archive_root>/claude/exports/<YYYY>/<MM>/<safe_sid>.md`
   formula, `claude_export.py:488-498`) and do a read-only existence check,
   asking only when `--force` would actually overwrite something.
2. **Static** (chosen): treat `--force`'s mere presence as dangerous,
   without predicting whether it would have an effect.

The static design was chosen deliberately: the dynamic design duplicates
exporter logic inside skill prose, the exact defect class that produced two
of the five findings in this PR's first review round (stale `--latest`
scoping, missing `--current` route). A static check has no state to drift
out of sync; its only cost is occasionally asking when `--force` would have
been a no-op, which is the safe direction to be imprecise in.

Also clarified in Step 3's text, per the same discussion: a user-typed
invocation is explicit "regardless of what flags accompany it or how the
message is phrased" — an explicit example was added ("Yes, please execute
`/lrh-export-claude`" counts the same as a bare invocation) to record that
the typed/model-initiated classification was never meant to depend on
message phrasing or the presence of ordinary (non-dangerous) flags.

Reply already posted on the deferred `km9-g` review thread
(https://github.com/xenotaur/logical_robotics_harness/pull/703#discussion_r4068775134)
stays accurate: this change narrows the residual risk that thread named,
without reversing the underlying typed-invocation design it objected to.

# Validation

- `scripts/format --check --diff` and `scripts/lint` — clean.
- `PYTHONPATH=src scripts/test` — 1682 tests OK (anaconda Python, Homebrew
  bash 5).
- `lrh skills install --dry-run --local --target <claude|codex|antigravity>`
  — `lrh-export-claude` absent from every list on all three targets.
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Step 8: CI on the post-record head, REVIEW-LANDED (automatic response or
  a substitute `/lrh-self-review` pass — this is new content since the last
  review round, so a fresh signal is needed before merge), then the merge
  gate, naming `km9-g` again in the merge summary.
- At closeout, land all of this PR's records with `lrh prompt
  update-execution --status landed --pr --commit`.

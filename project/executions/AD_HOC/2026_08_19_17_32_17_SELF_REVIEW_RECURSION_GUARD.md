---
execution_id: 2026_08_19_17_32_17_SELF_REVIEW_RECURSION_GUARD
prompt_id: PROMPT(AD_HOC:SELF_REVIEW_RECURSION_GUARD)[2026-08-19T17:22:42+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/566
commit: 3202bf3f
agent: claude_code
instruction_source: user request, in-conversation design carried forward from PROP-INVOCATION-AND-GATE-RESET Decision 5
session_transcript: claude-app:local_dd7df709-1e50-4e78-a5bf-802d06e31d50
created_at: 2026-08-19T17:32:17+00:00
---

# Summary

Closed a gap `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` (PR #560) left
open: `/lrh-self-review`'s Claude-side recursion guard was advisory-only,
with the platform-enforced mechanism recorded as "reassigned to Stage 3" —
a reassignment `WI-GATE-POLICY-CASCADE-STAGE3` never actually tracked in its
own scope, so it was at risk of being silently dropped a second time. Added
`disallowed-tools: Skill` to `lrh-self-review/SKILL.md` as the primary,
platform-enforced guard, verified empirically (in an earlier session, via a
throwaway test skill) rather than assumed, per `PROP-INVOCATION-AND-GATE-RESET`
Decision 5's own warning against exactly that assumption. Recorded the
amendment as `DEC-SELF-REVIEW-RECURSION-GUARD`.

# Result

- `disallowed-tools: Skill` added to `lrh-self-review/SKILL.md` in all three
  mirrors (`.claude/skills/`, `.agents/skills/`, `src/lrh/skills/`) and
  propagated to repo-local and user-scope Claude/Codex installs via
  `lrh skills install`.
- Existing advisory dispatch-prompt instruction retained as an explicitly
  labeled secondary, defense-in-depth layer, not a substitute for the
  platform mechanism.
- `DEC-SELF-REVIEW-RECURSION-GUARD` written, cited from `decision_log.md`
  and from `lrh-self-review/SKILL.md` Step 3, and cross-linked into
  `PROP-INVOCATION-AND-GATE-RESET` (Decision 5 amendment note plus
  `related_design`/`implemented_by` frontmatter updates). Also corrected a
  stale `proposed/` path reference for the now-`resolved`
  `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE`, found while editing the
  same frontmatter block.
- Diff-mode `/lrh-self-review` ran before this PR's first push (see
  `2026_08_19_17_31_07_SELF_REVIEW_RECURSION_GUARD_SELFREVIEW.md`); one
  genuine internal-consistency defect found and fixed (a miscounted
  instruction reference), independently re-verified directly against the
  file. The subagent also confirmed it had no `Skill` tool available in its
  own dispatch context — a real-world data point now cited in the decision
  record alongside the original throwaway-skill test.
- Opened as PR #566, landing separately and ahead of
  `WI-GATE-POLICY-CASCADE-STAGE3` so that Stage 3's gate-corpus audit works
  against a stable target rather than a moving one.

# Validation

- `PYTHONPATH=src PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH python -m lrh.cli.main validate` — 0 errors, 0 warnings
- `git diff --check`
- `scripts/format --check --diff`
- `scripts/lint`
- `lrh skills install --target claude --local --source current-repo --force`
- `lrh skills install --target codex --local --source current-repo --force`
- `lrh skills install --target claude --scope user --source current-repo --force`
- `lrh skills install --target codex --scope user --source current-repo --force`
- Diff-mode `/lrh-self-review` (see linked `_SELFREVIEW` record)

# Follow-up

- `lrh-codex-export`'s retained `disable-model-invocation` flag remains
  ungoverned by any work item — separate, deliberately out of scope here.
- `WI-GATE-POLICY-CASCADE-STAGE3`'s Stage 3 gate-corpus audit no longer
  needs to resolve the self-review recursion guard as an open item.
- Closeout (resolve into `resolved/`, land this and the linked selfreview
  record) happens after PR #566 merges, pending explicit merge
  authorization.

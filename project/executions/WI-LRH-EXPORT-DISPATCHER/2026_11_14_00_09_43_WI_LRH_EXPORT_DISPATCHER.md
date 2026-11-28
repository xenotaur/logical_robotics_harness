---
execution_id: 2026_11_14_00_09_43_WI_LRH_EXPORT_DISPATCHER
prompt_id: PROMPT(WI-LRH-EXPORT-DISPATCHER:WI_LRH_EXPORT_DISPATCHER)[2026-11-13T21:37:48+00:00]
work_item: WI-LRH-EXPORT-DISPATCHER
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/874
commit:
created_at: 2026-11-14T00:09:43+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-EXPORT-DISPATCHER.md
session_transcript: pending
---

# Summary

Ran `/lrh-execute WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`. It resolved to
`WI-LRH-EXPORT-DISPATCHER`, the first ready item in list order: every
earlier item was resolved, including `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`
from PR #797. The run added `/lrh-export`, the delegating dispatcher over
`lrh-export-<vendor>` described in `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`
Decision 2.

# Result

- Added `src/lrh/skills/lrh-export/SKILL.md` and `agents/openai.yaml`, with
  `allow_implicit_invocation: false`.
- **Vendor order:**
  1. an explicit first argument (`claude`, `codex` or `antigravity`);
  2. the single environment signal set (`CLAUDE_CODE_SESSION_ID`,
     `CODEX_THREAD_ID` or `ANTIGRAVITY_CONVERSATION_ID`);
  3. otherwise ask, including when several signals are set.
- **Missing variant:** stops with "Nothing was exported", with no fallback
  to a stub.
- **Gates:** the dispatcher adds no write step, archive default or gate of
  its own; the variant's gate applies in full. All three variants are
  gated, the Antigravity one since #870, so the work item's "surface an
  ungated variant" condition did not arise.
- **Typed-invocation rule (user-approved design choice at the chain
  gate):**
  - A user-typed `/lrh-export` counts as a typed invocation of the selected
    variant, and satisfies Codex's "explicitly requested" condition.
  - A proactive or chained `/lrh-export` counts as model-initiated, and an
    unclear one as ambiguous; both wait.
  - `--force` (Claude and Antigravity only) always waits.
- **Proactive use:** `when_to_use` limits the skill to explicit export
  requests.
- **Rendering:** rendered to `.claude/skills`, `.agents/skills` and
  `.gemini/plugins/lrh/skills` one skill at a time, without `--force`. The
  committed `plugins/lrh` tree was regenerated.
- `CLAUDE.md` lists `/lrh-export`. The portability test's `AFFECTED_SKILLS`
  now includes `lrh-export`.
- **Before implementation:** the chain-defaults profile was re-stamped on
  `main` (`21bcfbca`). The user re-confirmed the stored conditions after
  being shown the stale gate change from #872 (`lrh-closeout` Step 4).
- **Commit:** `bad30bc2`.

# Validation

- `scripts/version tools`: OK.
- `lrh validate`: 0 errors, 0 warnings.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: passes.
- `scripts/test --log`: passes. After the wording-only self-review fixes,
  the packaging, exporter and installer tests (244) pass, including the
  plugin drift test.
- `lrh skills check --target claude --local` and `lrh skills status
  --target codex|antigravity --local --source current-repo`: up to date.
- `diff -r src/lrh/skills/lrh-export .claude/skills/lrh-export`: identical.

# Follow-up

- `WI-EXPORT-SESSION-ID-DOCS` is now unblocked. Its scope includes both
  dispatchers' docs, and it can also fix two stale lines:
  - `lrh-session-id/SKILL.md:58`, which still says "once it ships";
  - `lrh-session-id-claude/SKILL.md:47`, which still says "a future
    dispatcher".
- Dogfood the "both signals set" case (proposal Open Question 3) when
  possible.

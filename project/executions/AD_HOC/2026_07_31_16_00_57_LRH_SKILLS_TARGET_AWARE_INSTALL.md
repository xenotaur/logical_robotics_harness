---
execution_id: 2026_07_31_16_00_57_LRH_SKILLS_TARGET_AWARE_INSTALL
prompt_id: PROMPT(AD_HOC:LRH_SKILLS_TARGET_AWARE_INSTALL)[2026-07-31T15:57:53-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/449
commit: da69c926ed66e4406850249f6fae3e41380395c3
created_at: 2026-07-31T16:00:57-04:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
session_transcript: claude-app:7989b360-bab9-4b9f-a77e-c320c71a1219
---

# Summary

Reviewed an externally-provided design session document ("Target-Aware
Agent Skills Installation") proposing to extend `lrh skills install` from
a Claude-only installer into a target-aware installer supporting Claude
and Codex as first-class local install targets, with ChatGPT deferred to
a later export path. Assessed feasibility against the current repo state
(`src/lrh/skills/installer.py`, `src/lrh/cli/main.py`) and against
independently verified external facts (Codex CLI's `.agents/skills/`
discovery mechanism, ChatGPT Skills' 2026-07-09 GA), then ran
`/lrh-proposal` to capture the design as `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`
with four refinements folded in from the feasibility review.

# Result

Created `project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
(`status: proposed`, `implementation_status: not_started`). The proposal:

- Adopts the source design's four-dimension model (source/scope/target/mode),
  target directories, canonical-vs-installed-copy separation, conflict
  handling, and staged delivery intent.
- Corrects the Codex metadata design (Decision 2): the source design proposed
  a nested `metadata.lrh.targets.codex.*` frontmatter key, but Codex's real
  extension point is the sibling file `agents/openai.yaml` — verified via
  external research before the proposal was drafted, not assumed.
- Names the real cost of "copy where safe" (Decision 4): all 14 shipped
  `src/lrh/skills/*/SKILL.md` skills reference Claude Code and/or `/lrh-*`
  slash invocation directly in body prose, not just frontmatter, so a naive
  Codex-target copy ships Claude-flavored instructions unadapted — scoped as
  an explicit interim-caveat plus separate follow-on work, not left implicit.
- Flags a repo-config parsing risk (Decision 5) against a documented prior
  bug in `_parse_simple_yaml` (`src/lrh/control/validator.py:568`), which
  strips quotes from scalars but not list elements — directly relevant since
  the proposed `agent_skills.yaml` config is list-valued.
- Reconciles a scope mismatch in the source design's Implementation Plan
  between its 7-stage plan and its separate "Recommended First Work Item"
  section, adopting the latter's scope as the authoritative first work item.

Opened PR #449 (documentation-only; no CLI or installer code changes).

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`,
  not touched by this PR).
- Prior-art check run per `references/prior-art-check.md`: no in-repo
  duplication found; no open work item, proposal, or backlog entry already
  requests this capability.
- Idempotence check: searched `project/executions/AD_HOC/` for a prior
  record matching this slug before minting the prompt ID — none found.

# Follow-up

- Run `/lrh-work-item` to file `WI-SKILLS-TARGET-AWARE-INSTALL` (first
  implementation slice, per the proposal's Implementation Plan).
- Given the proposal's medium/large multi-stage scope, consider
  `/lrh-workstream` to govern staged delivery across the remaining stages
  (source abstraction, repo config, render adapters, status/check commands,
  body-prose neutralization, deferred ChatGPT export).
- `/lrh-review-response` and `/lrh-confirm-fixes` on PR #449 as review
  rounds come in; `/lrh-closeout` after merge to land this record.

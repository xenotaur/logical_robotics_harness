---
execution_id: 2026_08_29_07_58_49_WI_SKILLS_LRH_CONFIG_SKILLS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_CONFIG_SKILLS_REVIEW)[2026-08-29T07:58:43+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/638
commit: bca085b20e4ee721765e893add83137b35f3bfae
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/638
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-29T07:58:49+00:00
---

# Summary

`/lrh-review-response` round for PR #638, inlined from `/lrh-land` Step 4.

# Result

4 findings, all present, valid, and feasible (2 from
`copilot-pull-request-reviewer`, 2 from `chatgpt-codex-connector`, P2 each):

1. **(copilot)** A `git grep` command was written as an inline code span
   split across two lines -- invalid Markdown, renders inconsistently.
   Fixed: moved into a fenced ` ```bash ` block.
2. **(copilot)** Acceptance bullet 2 called all 4 fields (including
   `install.overwrite`) "configurable," contradicting bullet 4's "never
   offered as a settable field." Fixed: reworded bullet 2 to distinguish
   `sources`/`targets`/`scope` (resolved effective value + provenance,
   editable) from `install.overwrite` (raw configured value or "not
   set," display-only).
3. **(codex, P2)** "Define the missing overwrite default" -- verified
   directly against `src/lrh/skills/installer.py`: `AgentSkillsConfig`
   and `AgentSkillsInstallPlan` (lines 93-104) carry no `overwrite`
   field at all, and `_validate_config_install_policy` (lines 411-423)
   only validates and discards the value -- the WI's Required Change #1
   could not literally "reuse" `load_agent_skills_config`/
   `resolve_agent_skills_install_plan` for this field, since neither
   function exposes it, and the schema documents no conventional default
   for it either (only source/target/scope have documented defaults).
   Fixed: Required Change #1 now specifies reading `install.overwrite`'s
   raw value directly from the parsed config instead, with "not set" as
   the only fallback, and explicitly forbids extending `installer.py`'s
   data model (would violate this WI's own Non-Goals against touching
   `lrh skills install`'s internal loading logic).
4. **(codex, P2)** "Resolve whether overwrite is editable" -- Acceptance
   bullet 4 said `install.overwrite` "is never offered as a settable
   field" while Required Change #2 said the skill should "permit its
   non-destructive values" -- directly contradictory. Fixed: made
   `install.overwrite` strictly read-only/display-only throughout the WI
   (Scope, Required Changes, Non-Goals, Acceptance Criteria body all
   updated to match) -- a human who wants to set it edits
   `project/agent_skills.yaml` by hand, same as `closeout_with_merge`'s
   precedent in `/lrh-config-gates`.

All 4 fixed directly in `project/work_items/proposed/WI-SKILLS-LRH-CONFIG-SKILLS.md`
(frontmatter `acceptance`, and the Scope, Required Changes, Non-Goals,
and Acceptance Criteria body sections, kept consistent with each other).

# Validation

- `lrh validate`: 0 errors, 80 pre-existing warnings unrelated to this
  file (`FRONTMATTER_LINT_UNSAFE_SCALAR` on already-resolved WIs/
  workstreams elsewhere in the repo -- confirmed none reference this
  file).
- Identity verified before triage: `gh pr view` `headRefOid` matched
  local `HEAD` (`602925a7...`) exactly.
- Findings 3 and 4 verified directly by reading
  `src/lrh/skills/installer.py:93-104,411-423` before fixing, not
  accepted on the bot's citation alone.
- Re-checked every remaining `install.overwrite` mention in the file
  after fixing (via `grep -n "overwrite"`) to confirm no contradictory
  wording survived in Scope, Non-Goals, or the Acceptance Criteria body.

# Follow-up

None deferred -- all 4 findings fixed in this round.

---
execution_id: 2026_09_22_06_25_10_WI_SKILLS_PLANNING_ID_PROPOSAL
prompt_id: PROMPT(AD_HOC:WI_SKILLS_PLANNING_ID_PROPOSAL)[2026-09-22T06:23:14+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/707
commit: 
created_at: 2026-09-22T06:25:10+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-PLANNING-ID-PROPOSAL.md
session_transcript: claude-app:61a2a7f9-ccdb-45b9-b6de-d9930280fb0c
---

# Summary

Investigated why `/lrh-work-item` started demanding a `WI-*` ID from Codex
sessions when Claude sessions had been proposing one unprompted. Grounded
the diagnosis directly against the repo (hashes, `git blame`, sibling-skill
comparison) rather than trusting a prior agent's citation-based analysis,
then designed and scoped a fix: created work item
`WI-SKILLS-PLANNING-ID-PROPOSAL`, which formalizes Claude's observed
propose-then-confirm behavior as a deterministic mechanism across
`lrh-work-item`, `lrh-proposal`, and `lrh-workstream`, instead of relying
on prose instruction-following.

# Result

- Disproved the initial "stale install / regenerated skill" hypothesis: the
  ID-required wording is byte-identical across canonical source and both
  global installs (`~/.agents/skills`, `~/.claude/skills`), and has been
  present since the skill's first commit (`5f85fcb9`, 2026-06-23) - not a
  recent regression.
- Established the actual mechanism: Claude has been deviating from the
  written "ask for one" instruction by proposing an ID anyway; Codex
  followed the contract as written. Confirmed the same pattern exists
  identically in the two sibling skills (`lrh-proposal`, `lrh-workstream`).
- Evaluated four options for formalizing the propose-then-confirm behavior
  (prose-only, deterministic CLI collision check, full auto-allocation, do
  nothing / rely on post-write validate), grounded in repo state
  (`file:line` citations) and Anthropic's own Claude Code skills docs (the
  `argument-hint` frontmatter field is only an autocomplete hint, never a
  platform-enforced requirement - the "required" framing is entirely
  LRH-authored). Recommended the deterministic-CLI-check option, reusing
  the architecture `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` /
  `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT` already validated for a sibling
  problem (prompt-slug idempotence).
- Created `project/work_items/proposed/WI-SKILLS-PLANNING-ID-PROPOSAL.md`
  scoping that fix, including a prior-art check against the active
  `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` item (related architecture, different
  check - not a duplicate, but flagged as a file-overlap coordination risk
  since both touch the same three `SKILL.md` files).
- Opened PR #707: https://github.com/xenotaur/logical_robotics_harness/pull/707

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- Candidate ID `WI-SKILLS-PLANNING-ID-PROPOSAL` collision-checked against
  local `project/work_items/` buckets and open PRs before use (none found).

# Follow-up

- This PR creates the planning artifact only; no implementation yet. The
  work item's own scope (CLI check command(s), skill edits, tests) is the
  follow-up, to be picked up via `/lrh-implement` or `/lrh-execute
  WI-SKILLS-PLANNING-ID-PROPOSAL`.
- Coordinate branch/PR sequencing with `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`
  (active) before implementation starts, since both touch the same three
  `SKILL.md` files in different sections - see the work item's Risk Notes.
- No workstream was attached (`related_workstreams: []`) - no clean fit was
  found; flagged to the user as inferred rather than confirmed.

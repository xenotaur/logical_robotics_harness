---
execution_id: 2026_09_20_02_09_36_ADOPT_PROP_LRH_CLAUDE_CONVERSATION_EXPORTER
prompt_id: PROMPT(AD_HOC:ADOPT_PROP_LRH_CLAUDE_CONVERSATION_EXPORTER)[2026-09-20T02:05:05+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/678
commit: 8a3563735c0244df920ea5c064e524aaa8d9e8f4
created_at: 2026-09-20T02:09:36+00:00
agent: claude_app
instruction_source: ad-hoc — adopt PROP-LRH-CLAUDE-CONVERSATION-EXPORTER
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Adopt `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` now that all three of its
tranches have shipped: the core API (PR #664), the CLI subcommand
(PR #666), and the `/lrh-export-claude` skill (PR #669). Found by
`/lrh-work-remains`: the proposal was still `status: proposed`, because
`/lrh-closeout` only offers adoption when a governing workstream closes
and these work items had no workstream. This also corrects an earlier
statement of mine, in the PR #666 and #669 closeout previews, that the
proposal was already adopted; that was unverified and wrong.

# Result

- Moved `project/design/proposals/proposed/lrh-claude-conversation-exporter/`
  to `project/design/proposals/adopted/lrh-claude-conversation-exporter/`
  (whole directory; it contains only `00_proposal.md`).
- Frontmatter per `/lrh-closeout`'s Proposal Adoption Protocol, matching
  the adopted antigravity sibling: `status: adopted`,
  `implementation_status: implemented`, `implemented_by:`
  `WI-CLAUDE-CONVERSATION-EXPORT-API`, `-CLI`, `-SKILL`, and
  `updated_on: 2026-09-20`. `WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP`
  is deliberately not listed: it resolved one of the proposal's open
  questions but did not implement the proposal.
- Updated the old path in the three resolved work items'
  `related_design` frontmatter and in `backlog.md:97`, so no structural
  reference points at a missing path. The antigravity precedent left its
  resolved work items' links dangling; updating them was chosen
  deliberately and approved by the user. Execution records that mention
  the old path are immutable history and were left untouched.
- The proposal body is unchanged. Some sentences are now stale
  ("has not shipped"), as with the adopted antigravity sibling.

Pre-push diff-mode self-review found no blockers or majors and
spot-checked that the shipped code matches the proposal, so
`implemented` is accurate. See
`project/executions/AD_HOC/2026_09_20_02_08_43_ADOPT_PROP_LRH_CLAUDE_CONVERSATION_EXPORTER_SELFREVIEW.md`.

Protocol order followed: branch created first, then idempotence check
and prompt-ID mint, then edits; the run plan was presented and approved
before any of it.

Publication: pushed directly, PR opened at
https://github.com/xenotaur/logical_robotics_harness/pull/678.

# Validation

- `PYTHONPATH=src scripts/test` — `Ran 1605 tests`, `OK`, exit 0.
- `scripts/lint` and `scripts/format --check --diff` — clean, exit 0
  (black 26.3.1, ruff 0.15.12, matching the pins).
- `lrh validate` — 0 errors, 0 warnings.
- Grep for the old path outside `project/executions/`: no matches.

# Follow-up

- `project/design/proposals/README.md` lists the already-adopted
  antigravity proposal as `proposed/` and never listed the Claude
  proposal. Pre-existing drift, out of scope here.
- Continue with `/lrh-land` for PR #678.

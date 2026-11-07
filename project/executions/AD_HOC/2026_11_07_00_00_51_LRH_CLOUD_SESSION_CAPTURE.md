---
execution_id: 2026_11_07_00_00_51_LRH_CLOUD_SESSION_CAPTURE
prompt_id: PROMPT(AD_HOC:LRH_CLOUD_SESSION_CAPTURE)[2026-11-06T23:42:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/863
commit:
created_at: 2026-11-07T00:00:51+00:00
agent: claude-code
instruction_source: project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
session_transcript: pending
---

# Summary

Investigated why `/lrh:lrh-export-claude` needed manual recovery and three
permission round trips in a Claude Code cloud session on `xenotaur/taurworks`
(2026-11-06). Captured the result as three kinds of planning artifact:

- an evidence audit;
- the design proposal `PROP-LRH-CLOUD-SESSION-CAPTURE`;
- six companion work items.

The user confirmed the proposal and all six work items before anything was
written, and chose a single PR for the set. That's why one execution record
covers the whole set, instead of one per `/lrh-proposal` and
`/lrh-work-item` run.

# Result

- `project/audits/2026-11-06-cloud-session-export-audit.md`: findings for
  each investigation question, cited to repo files, `lrh conversation ...
  --help` output, and Claude Code docs fetched 2026-11-06.
- `project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md`
  (`PROP-LRH-CLOUD-SESSION-CAPTURE`): six decisions, the non-goals, an
  implementation plan, and open questions.
- `project/work_items/proposed/`, six items:
  - `WI-CLOUD-SESSION-PROBE`
  - `WI-LRH-CLI-RESOLUTION-REFERENCE`
  - `WI-EXPORT-ALLOWLIST-READY`
  - `WI-EXPORT-REFRESH-AND-STALENESS`
  - `WI-PLUGIN-BUNDLED-CLI` (depends on the probe)
  - `WI-EXPORT-CLAUDE-CLOUD-BRANCH` (depends on the probe)
- PR: https://github.com/xenotaur/logical_robotics_harness/pull/863

No code, skill, or documentation behavior changed.

# Validation

- `lrh validate`: 0 errors, 0 warnings, after the proposal and again after
  the work items.
- `lrh work-items readiness <ID>`: `prompt_ready: yes` for all six.
- `lrh prompt check-execution --slug <slug> --work-item AD_HOC`: no prior
  record for `lrh-cloud-session-capture` or any of the six WI slugs.

# Follow-up

- Start with `WI-CLOUD-SESSION-PROBE`. It decides whether
  `WI-PLUGIN-BUNDLED-CLI` goes ahead and confirms the environment-variable
  facts behind `WI-EXPORT-CLAUDE-CLOUD-BRANCH`.
- The proposal's open questions are unresolved:
  - the bundled launcher's name;
  - whether to bundle PyYAML;
  - a `claude-cloud:` pointer;
  - whether `closeout-sync` should skip mirroring in cloud sessions;
  - an `import-claude-export` command;
  - Codex Cloud export;
  - whether to group the six items under a workstream.
- Coordinate with `WI-EXPORT-SKILL-FAMILY-RENAME` (skill paths) and
  `WI-CLOSEOUT-EXPORT-SCOPE` (the closeout Step 8 offer).
- `session_transcript: pending`: update to this session's `claude-app:`
  pointer at closeout.

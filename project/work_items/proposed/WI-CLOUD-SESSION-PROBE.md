---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLOUD-SESSION-PROBE
title: "Probe a Claude Code cloud session for the facts PROP-LRH-CLOUD-SESSION-CAPTURE depends on"
type: investigation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
  - project/audits/2026-11-06-cloud-session-export-audit.md
depends_on: []
blocked_by: []
expected_actions:
  - create_report
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - print_transcript_text
  - commit_transcript_export
  - modify_user_settings
acceptance:
  - "An execution record states, from commands run in a real claude.ai/code cloud session, whether a synced plugin's bin/ directory is on the Bash tool's PATH"
  - "The record states the python3 version and whether PyYAML imports in the default image"
  - "The record states which of CLAUDE_CODE_REMOTE, CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_HOST_SESSION_ID and CLAUDE_CODE_REMOTE_SESSION_ID are set, reporting presence and ID format only, never transcript content"
  - "The record states whether an exact Bash(lrh conversation ...) allow rule in the session repository's .claude/settings.json ran the command without a classifier denial in auto mode"
  - "The audit's open-questions section and the proposal's Open Questions are updated with the answers, and lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - "project/executions/WI-CLOUD-SESSION-PROBE/<timestamp>_WI_CLOUD_SESSION_PROBE.md"
  - project/audits/2026-11-06-cloud-session-export-audit.md
  - project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
---

# WI-CLOUD-SESSION-PROBE: Probe a cloud session for the facts the proposal depends on

## Summary

Run a real Claude Code cloud session and record four facts that
`PROP-LRH-CLOUD-SESSION-CAPTURE` relies on but Claude Code's documentation
doesn't settle:

- whether a synced plugin's `bin/` is on PATH;
- the Python and PyYAML runtime in the default image;
- which session-ID environment variables are set;
- whether an exact allow rule bypasses the auto-mode classifier.

## Problem / Context

The proposal's Decision 1 (bundle the CLI in the plugin) depends on plugin
`bin/` working for an account-synced plugin in a cloud session. The plugin
reference documents `bin/`, but not cloud behavior. Decisions 3 and 4
assume behavior that is documented in general but has never been checked in
a cloud session. `project/audits/2026-11-06-cloud-session-export-audit.md`
lists these as open questions. A probe is cheap, and it stops two
deliverables from being built on assumptions. The repo already has a
precedent: the `lrh-cloud-probe` plugin probe recorded in
`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`.

### Duplication search
- In-repo: Related: `project/work_items/resolved/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md`. Its dogfood covered skill loading only, not `bin/`, environment variables, or permissions.
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE — this item is that proposal's first implementation step
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Run one or more claude.ai/code cloud sessions, with the probe plugin
  enabled, on a test repository.
- Record the answers as an execution record, and fold them into the audit
  and the proposal's Open Questions.

## Required Changes

1. Build a minimal throwaway probe plugin, or extend the existing
   `lrh-cloud-probe`, with a `bin/lrh-probe` script that prints its own path
   and exits. Enable it on claude.ai and start a fresh cloud session. Plugins
   reach a session only when it is created.
2. In that session, run:
   - `command -v lrh-probe`;
   - `python3 --version`;
   - `python3 -c "import yaml"`;
   - for each of the four variables, a check that prints only set or unset,
     plus each ID's prefix or format.
3. On a single-repo cloud session whose repository's `.claude/settings.json`
   allows `Bash(lrh conversation current-claude-session-id *)`, with `lrh`
   installed by setup script, run that command in auto mode. Record whether
   it was denied.
4. Write the execution record under `project/executions/WI-CLOUD-SESSION-PROBE/`.
5. Update the audit's open-questions section and the proposal's
   `## Open Questions` with the answers.

## Non-Goals

- Do not implement the bundled CLI, the cloud branch, or any skill change.
- Do not run `export-claude-session` or record any transcript content.
  Environment variables are reported as present or absent, plus ID format,
  only.
- Do not change claude.ai account or environment settings beyond what the
  probe needs, and record anything that was changed.

## Acceptance Criteria

- The execution record answers each of the four questions with the command
  run and what it showed, or says plainly that a question couldn't be
  answered, and why.
- The audit and the proposal's Open Questions reflect the answers.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`

## Risk Notes

- A single session is one observation. Record the date, the account type
  (personal or org), and the environment's network level, so a later
  regression can be compared.
- If `bin/` isn't on PATH, Decision 1 falls back to the setup-script route,
  and `WI-PLUGIN-BUNDLED-CLI` should be abandoned or rescoped.

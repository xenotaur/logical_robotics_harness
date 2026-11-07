---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-CLAUDE-CLOUD-BRANCH
title: "Report cloud status from current-claude-session-id and add a cloud-session branch with delivery to lrh-export-claude"
type: deliverable
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
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
depends_on:
  - WI-CLOUD-SESSION-PROBE
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
  - commit_transcript_export
  - skills_install_force
acceptance:
  - "lrh conversation current-claude-session-id --format json adds cloud_session (true only when CLAUDE_CODE_REMOTE == 'true') and remote_session_id (CLAUDE_CODE_REMOTE_SESSION_ID or null), stays metadata-only, and existing fields and --field values are unchanged; unit tests cover set, unset and non-'true' values"
  - "lrh-export-claude reads cloud status only from that JSON output, never from the environment directly"
  - "When cloud_session is true, the skill still exports to the archive, and its Step 3 statement and Step 6 report say plainly that the archive copy is lost when the session ends"
  - "When cloud_session is true and the session offers a file-delivery tool (checked at run time, never assumed), the skill copies the export to a deliverable location with mode 600 and offers it; when no such tool exists, it says so and doesn't improvise"
  - "The cloud report includes the one-line 'chmod 600 <file>' to run after download, and the local re-verify command 'lrh conversation inspect-export <file>'"
  - "Existing gates are unchanged: --force always waits, model-initiated exports wait, no transcript text is printed, and nothing is committed; lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass; rendered copies are regenerated without --force"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_session.py
  - tests/conversations_tests/claude_session_test.py
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - docs/reference/cli/conversation.md
  - docs/how-to/use-lrh-with-agent-assistants.md
  - plugins/lrh/skills/lrh-export-claude/SKILL.md
---

# WI-EXPORT-CLAUDE-CLOUD-BRANCH: Cloud detection in the CLI and a cloud branch in the export skill

## Summary

Have `current-claude-session-id` report whether the session is a cloud
session, from the documented `CLAUDE_CODE_REMOTE`, along with the cloud
session ID. Give `lrh-export-claude` a cloud branch: it says the archive
copy is temporary, offers delivery when the session can deliver files, and
tells the user how to restore 0600 after download.

## Problem / Context

In a cloud session the default archive lives in a VM that is discarded when
the session ends. Claude Code documents git as the only persistence, and
exports must never be committed (audit §1.3). The taurworks agent
improvised a scratchpad copy and a download, and the download lost the
file's 0600 mode. `CLAUDE_CODE_REMOTE=true` is the documented cloud signal,
and `CLAUDE_CODE_REMOTE_SESSION_ID` carries the `cse_`-prefixed ID; LRH
reads neither today (`claude_session.py:14,55-56`). No way to download a
file from a cloud session is documented, so delivery has to be a run-time
capability check. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decisions 4 and 5. This
item depends on `WI-CLOUD-SESSION-PROBE` to confirm which variables are
actually set.

### Duplication search
- In-repo: Related: `src/lrh/conversations/claude_session.py` (the resolver this extends).
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found. Adjacent: WI-LRH-EXPORT-DISPATCHER may later reuse `cloud_session`.
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decisions 4 and 5)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Two metadata-only fields on `current-claude-session-id`.
- A cloud branch in `lrh-export-claude`: an ephemeral-archive notice,
  conditional delivery, and the chmod and re-verify guidance.

## Required Changes

1. In `src/lrh/conversations/claude_session.py`, add `cloud_session` and
   `remote_session_id` to the resolved identity and the JSON output. Keep
   the text output and `--field` choices backward compatible. Add tests.
2. In `src/lrh/skills/lrh-export-claude/SKILL.md`, add the cloud branch:
   - **Steps 1 and 3:** record `cloud_session` from the JSON, and add the
     ephemeral-archive note to what is stated before writing.
   - **New delivery step, after Step 5:** if a file-delivery tool is
     available, copy the verified export with mode 600 and offer it.
   - **Step 6 report:** add the delivered path (if any), the
     `chmod 600 <file>` line, and the local `inspect-export` re-verify
     command.
3. Document the new fields in `docs/reference/cli/conversation.md`, and the
   cloud behavior in `docs/how-to/use-lrh-with-agent-assistants.md` §5.
4. Regenerate rendered copies and the plugin tree.

## Non-Goals

- Do not define a `claude-cloud:` `session_transcript:` pointer. That is an
  open question in the proposal.
- Do not add an `import-claude-export` command.
- Do not change the default archive root, or skip the archive write in the
  cloud.
- Do not read Claude Code's internal storage directly.

## Acceptance Criteria

- The new JSON fields work as specified, with tests for each variable state.
- The skill branches on the CLI output only, states that the archive is
  ephemeral, delivers only when a tool exists, and gives the chmod and
  re-verify guidance.
- All existing gates and privacy rules are unchanged.
- `lrh validate`, `scripts/test`, `scripts/lint` and
  `scripts/format --check --diff` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills check --target claude --local`

## Risk Notes

- The delivery tool and the session's displayable directories are harness
  capabilities, not documented contracts. The skill text must describe them
  as conditional.
- If the probe finds `CLAUDE_CODE_SESSION_ID` unset in some cloud sessions,
  the current-session route already fails clearly. Don't add a `--latest`
  fallback.

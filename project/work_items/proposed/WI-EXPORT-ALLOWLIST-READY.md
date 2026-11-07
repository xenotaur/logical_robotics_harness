---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-ALLOWLIST-READY
title: "Make the Claude export commands matchable by exact allow rules: CLI-owned 0700 directories, no subshell, and a published settings snippet"
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
depends_on: []
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
  - skills_install_force
  - write_settings_without_confirmation
acceptance:
  - "export-claude-session creates any missing output and archive parent directories with mode 0700, regardless of the process umask, and leaves existing directories' modes unchanged; a unit test covers a permissive umask (022)"
  - "The export file is still created 0600 from the first write, with the existing os.open(..., 0o600) behavior unchanged"
  - "lrh-export-claude Step 4 runs plain 'lrh conversation export-claude-session ...' commands with no '( umask 077 ... )' subshell"
  - "Documentation publishes a client-repo .claude/settings.json snippet that allows exactly lrh conversation current-claude-session-id *, lrh conversation export-claude-session * and lrh conversation inspect-export *, plus an ask rule that matches --force, and states that multi-repo cloud sessions don't read project settings and that plugins can't grant permissions"
  - "The documented snippet states that its rules match the command word lrh, and that a differently named bundled launcher (WI-PLUGIN-BUNDLED-CLI) needs the same rules under its own name; if that launcher has already shipped under another name, the snippet includes those rules"
  - "If /lrh-config-skills, or a sibling skill, offers to write the snippet, it shows the exact diff and writes only after explicit confirmation; otherwise the item documents the snippet only"
  - "lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass, and rendered skill copies are regenerated without --force"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - tests/conversations_tests/claude_export_test.py
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - docs/how-to/use-lrh-with-agent-assistants.md
  - docs/reference/cli/conversation.md
  - plugins/lrh/skills/lrh-export-claude/SKILL.md
---

# WI-EXPORT-ALLOWLIST-READY: Make the export commands matchable by exact allow rules

## Summary

Let a client repository pre-approve LRH's Claude export commands with
narrow allow rules, so auto mode's classifier never has to judge them. The
CLI creates its own directories as 0700, so the skill can drop the
`( umask 077 … )` subshell. A settings snippet is published as well.

## Problem / Context

In the taurworks cloud session, auto mode denied running the LRH CLI against
the session's Claude data until the user authorized it by hand. Claude Code
documents that allow rules skip the classifier, and that cloud sessions read
the repository's `.claude/settings.json` in single-repo sessions (audit
§1.2). But the skill wraps the export in a multi-line `( umask 077 … )`
subshell, which an exact `Bash(lrh conversation export-claude-session *)`
rule is not documented to match. The wrapper exists only for directory
modes: the file is already opened 0600 (`claude_export.py:180`), but
`out.parent.mkdir(parents=True, exist_ok=True)` (`claude_export.py:144`)
follows the umask. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 3.

### Duplication search
- In-repo: No existing implementation found. This repo's own `.claude/settings.json` allows other `lrh` subcommands, but not `lrh conversation`.
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 3)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Directory-mode hardening in the Claude exporter.
- Remove the subshell from `lrh-export-claude`.
- Publish the allow/ask settings snippet.

## Required Changes

1. In `src/lrh/conversations/claude_export.py`, create missing parent
   directories with mode 0700. Use a helper that creates each missing level
   with an explicit mode and chmods only the directories it created, so a
   permissive umask can't widen them. Add tests in
   `tests/conversations_tests/claude_export_test.py`.
2. In `src/lrh/skills/lrh-export-claude/SKILL.md` Step 4, replace the
   subshell blocks with plain commands. Note that the CLI now owns the file
   and directory modes.
3. Document the settings snippet in
   `docs/how-to/use-lrh-with-agent-assistants.md` §5 (and, if it fits there,
   `docs/reference/cli/conversation.md`), with its limits stated. Exact
   Bash rules match the command word, so say that the rules cover `lrh`
   only. If `WI-PLUGIN-BUNDLED-CLI` has already shipped a launcher under
   another name, add the same rules for that name. If it hasn't, that item
   owns adding them.
4. Optional, decided at implementation time: have `/lrh-config-skills`
   offer to add the snippet, behind a confirm gate that shows the exact
   diff.
5. Regenerate rendered skill copies and the plugin tree.

## Non-Goals

- Do not change the Codex or Antigravity exporters or skills.
- Do not add `autoMode` configuration. It isn't read from project settings.
- Do not write any settings file without explicit confirmation.

## Acceptance Criteria

- New directories are 0700 under umask 022, as shown by a test, and the file
  stays 0600.
- Step 4 has no subshell.
- The snippet and its limits are documented, including which command names
  it covers.
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

- Changing directory creation affects the shared archive layout. Only newly
  created directories should change; existing directories must not be
  chmodded.
- An allow rule for `export-claude-session *` also allows `--out` anywhere.
  The skill's own gates still govern `--force` and exports the model starts
  on its own, and the `ask` rule adds a harness-level checkpoint for
  `--force`.
- Whether an exact rule actually suppresses the classifier in the cloud is a
  `WI-CLOUD-SESSION-PROBE` question. If it doesn't, the CLI change is still
  worth keeping, but revisit the docs claim.

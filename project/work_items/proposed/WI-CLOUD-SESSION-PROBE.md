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
  - "An execution record states, from commands run in a real claude.ai/code cloud session, whether ${CLAUDE_PLUGIN_ROOT} in a synced plugin's SKILL.md text is substituted with the plugin's path, whether the same placeholder in a references/ file reaches Claude as literal text, and whether python3 -I runs a script under the plugin's scripts/ by that path; the probe plugin has no top-level bin/, which claude.ai won't install"
  - "The record states, in auto mode, whether a plugin skill's allowed-tools rule written with ${CLAUDE_PLUGIN_ROOT} ran the probe script without a permission prompt or classifier review, for both the quoted and unquoted path forms, with a control skill that has no allowed-tools; if the control also runs without review, the result is recorded as inconclusive; it also states whether the grant still applied to a model-initiated run of skill A made after a confirming reply"
  - "The record states the python3 version and whether PyYAML imports in the default image"
  - "The record states which of CLAUDE_CODE_REMOTE, CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_HOST_SESSION_ID and CLAUDE_CODE_REMOTE_SESSION_ID are set, reporting presence and ID format only, never transcript content"
  - "The record states, for one lrh conversation command, whether auto mode denied it without an allow rule (the control) and whether it ran without a denial once an exact Bash(lrh conversation ...) allow rule for it was in the session repository's .claude/settings.json; if the control isn't denied, the record says the allow-rule result is inconclusive rather than a pass"
  - "The record states whether teleporting the cloud session (claude --teleport) from a clean local checkout writes a local transcript under ~/.claude/projects/, which session id it carries, whether current-claude-session-id run inside the teleported session resolves it, and whether the cloud session had been compacted (and so is documented to lose compacted messages), without reading or printing transcript content"
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

Run a real Claude Code cloud session and record six facts that
`PROP-LRH-CLOUD-SESSION-CAPTURE` relies on but Claude Code's documentation
doesn't settle:

- whether `${CLAUDE_PLUGIN_ROOT}` is substituted in a synced plugin's
  SKILL.md text, and left literal in a `references/` file, and whether a
  script under the plugin's `scripts/` runs by that path;
- whether the skill's own `allowed-tools` rule for that script avoids a
  prompt and classifier review in auto mode, for a skill inside a synced
  plugin, and whether the grant survives a confirming reply;
- the Python and PyYAML runtime in the default image;
- which session-ID environment variables are set;
- whether an exact allow rule bypasses the auto-mode classifier;
- whether teleporting the session writes a complete local transcript, which
  would let the export run locally and skip the download.

## Problem / Context

The proposal's Decision 1 bundles the CLI under the plugin's `scripts/`,
and skills call it as `${CLAUDE_PLUGIN_ROOT}/scripts/…`. A top-level `bin/`
is ruled out because claude.ai won't install a plugin that has one (audit
§1.1). Claude Code documents substituting `${CLAUDE_PLUGIN_ROOT}` in skill
content. A 2026-10-26 probe saw it resolve once in a synced cloud plugin,
but cloud behavior for synced plugins isn't documented. Decisions 3 and 4
assume behavior that is documented in general but has never been checked in
a cloud session. `project/audits/2026-11-06-cloud-session-export-audit.md`
lists these as open questions. A probe is cheap, and it stops two
deliverables from being built on assumptions. The repo already has a
precedent: the `lrh-cloud-probe` plugin probe recorded in
`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`.

### Duplication search
- In-repo: Related: `project/work_items/resolved/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md`. Its probe saw `${CLAUDE_PLUGIN_ROOT}` resolve, but didn't run a bundled script, check environment variables, or test permissions.
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
   `lrh-cloud-probe`, with no top-level `bin/`:
   - a `scripts/lrh_probe.py` that prints its own resolved path and exits;
   - skill A, whose SKILL.md runs
     `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_probe.py --probe`
     unquoted, with frontmatter
     `allowed-tools: Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_probe.py --probe)`;
   - skill B, the same with the path double-quoted in both the command and
     the rule;
   - skill C, the same command with no `allowed-tools`, as the control;
   - in skill A, a `references/path.md` file that holds the line
     `${CLAUDE_PLUGIN_ROOT}/scripts/lrh_probe.py`, which the skill asks
     Claude to read and quote back exactly.

   The rules name the exact command line, `--probe` included, with no
   wildcard. A `*` "matches any text, including spaces", and a trailing
   ` *` matches the bare command only when it is the rule's only wildcard
   (`permissions.md`). An exact rule keeps the probe from reporting a
   false "no match", or a match broader than intended.

   Enable it on claude.ai and start a fresh cloud session. Plugins reach a
   session only when it is created.
2. In that session, in auto mode, run skills A, B and C. Record:
   - the exact command line each skill produced, which shows whether
     `${CLAUDE_PLUGIN_ROOT}` was substituted, plus the script's output and
     exit status;
   - for each, whether the call ran with no prompt and no classifier
     review, was reviewed and allowed, or was denied. If C also ran with no
     review, the `allowed-tools` result is inconclusive, not a pass;
   - a confirm-then-run turn. Ask Claude to propose running skill A and
     wait for a yes. After replying "yes", record whether the script ran
     with no review. The docs say the grant clears at the user's next
     message, which is what `lrh-export-claude`'s confirmation gates rely
     on;
   - the text Claude quoted from `references/path.md`: a literal
     `${CLAUDE_PLUGIN_ROOT}` confirms that supporting files aren't
     substituted;
   - `ls -l` of the installed script, to see whether file modes survived
     sync. This is informational, since skills run the file through
     `python3`.
   - `python3 --version`;
   - `python3 -I -c "import yaml"`, in isolated mode like the bundled
     launcher, so a PyYAML present only in user site-packages doesn't
     pass;
   - for each of the four variables, a check that prints only set or unset,
     plus each ID's prefix or format.
3. Test an allow rule against a control, on single-repo cloud sessions in
   auto mode, with `lrh` installed by setup script:
   1. **Control.** With no LRH allow rule in the repository's
      `.claude/settings.json`, run
      `lrh conversation export-claude-session --current --out <scratchpad>/probe.md`.
      The CLI requires a session selector, so without `--current` it exits
      2 and writes nothing, and the test would show nothing. This is the
      same kind of action the taurworks session was denied: the CLI
      reading the session's own Claude data. Record whether the classifier
      denied it.
   2. **With the rule.** In a fresh session on a branch whose
      `.claude/settings.json` allows
      `Bash(lrh conversation export-claude-session *)`, run the same
      command. Record whether it was denied.
   3. If the command ran in either case, record its exit status and
      `probe.md`'s size, then delete `probe.md` without opening or
      printing it. A run that exits non-zero, or writes no file, counts as
      inconclusive, not as a pass.

   If the control isn't denied, record the allow-rule result as
   inconclusive, not as a pass. `current-claude-session-id` alone isn't a
   useful test: it reads environment variables and globs for the
   transcript path without opening the file
   (`claude_session.py:47-118`), so it may never be denied.
4. From a clean local checkout of the session's repository, with the cloud
   session's branch pushed, run `claude --teleport <session-id>`. Then
   record:
   - whether a new `*.jsonl` file appears under `~/.claude/projects/`, by
     name and size only;
   - its session ID;
   - whether `lrh conversation current-claude-session-id`, run through the
     Bash tool *inside the teleported Claude Code session*, resolves it. A
     plain local shell can't test this: the command needs
     `CLAUDE_CODE_SESSION_ID`, which only a Claude Code session sets
     (`claude_session.py:63-69`);
   - whether the cloud session had been compacted before the teleport.

   Don't open or print the transcript. Completeness isn't measured
   directly, since that would need the content. Record compaction status
   instead: Claude Code documents that compacted messages aren't copied by
   teleport, so a compacted session's local transcript is known to be
   incomplete.
5. Write the execution record under `project/executions/WI-CLOUD-SESSION-PROBE/`.
6. Update the audit's open-questions section and the proposal's
   `## Open Questions` with the answers.

## Non-Goals

- Do not implement the bundled CLI, the cloud branch, or any skill change.
- Do not record any transcript content. The only export run is the
  allow-rule test in step 3: written to the scratchpad, never opened,
  printed or committed, and deleted afterwards. Environment variables are
  reported as present or absent, plus ID format, only.
- Do not change claude.ai account or environment settings beyond what the
  probe needs, and record anything that was changed.

## Acceptance Criteria

- The execution record answers each of the six questions with the command
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
- If `${CLAUDE_PLUGIN_ROOT}` isn't substituted, or the script doesn't run,
  Decision 1 falls back to the setup-script route, and
  `WI-PLUGIN-BUNDLED-CLI` should be abandoned or rescoped.

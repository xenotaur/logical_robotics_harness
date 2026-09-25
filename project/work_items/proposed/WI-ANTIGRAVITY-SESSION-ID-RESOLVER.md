---
resolution: null
blocked_reason: null
blocked: false
id: WI-ANTIGRAVITY-SESSION-ID-RESOLVER
title: "Add an Antigravity current-conversation resolver CLI and the lrh-session-id-antigravity skill"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
related_design:
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
  - project/work_items/resolved/WI-CODEX-SESSION-ID-RESOLVER.md
  - project/work_items/resolved/WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER.md
depends_on:
  - WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - print_transcript_text
  - export_transcript_content
  - skills_install_force
acceptance:
  - "An lrh conversation subcommand, current-antigravity-conversation-id unless the investigation chose another name, reports the current Antigravity conversation ID and its session_transcript pointer in the format and with the fallback behavior the investigation appendix specified, without reading or printing transcript content"
  - "The resolver is implemented in src/lrh/conversations/antigravity_session.py with hermetic unit tests that cover the resolved, ambiguous and unresolvable cases"
  - "src/lrh/skills/lrh-session-id-antigravity/SKILL.md, modelled on lrh-session-id-codex, wraps the resolver, reports pending when the current conversation cannot be determined, and is installed to all three targets without --force"
  - "docs/reference/cli/conversation.md documents the new subcommand, the pointer format is added wherever the codex-app and claude-app formats are documented, and CLAUDE.md lists /lrh-session-id-antigravity"
  - "lrh sessions report (build_session_report in src/lrh/prompt_workflow_sessions.py) recognizes the new Antigravity pointer scheme instead of classifying it as unsupported, with tests covering it"
  - "If the investigation recommended deferring, this item is abandoned with that reason instead of implemented"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/antigravity_session.py
  - tests/conversations_tests/antigravity_session_test.py
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-session-id-antigravity/SKILL.md
  - src/lrh/skills/lrh-session-id-antigravity/agents/openai.yaml
  - .claude/skills/lrh-session-id-antigravity/
  - .agents/skills/lrh-session-id-antigravity/
  - .gemini/plugins/lrh/skills/lrh-session-id-antigravity/
  - docs/reference/cli/conversation.md
  - PROMPTS.md
  - project/executions/README.md
  - CLAUDE.md
---

# WI-ANTIGRAVITY-SESSION-ID-RESOLVER: Add the Antigravity session-ID resolver and skill

## Summary

Add a metadata-only resolver for the current Antigravity conversation. It is a
`lrh conversation` subcommand plus the `lrh-session-id-antigravity` skill, and
together they complete the session-ID family defined by
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`. The ID source, pointer format and
fallback behavior all come from `WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION`.

## Problem / Context

Claude and Codex each have a resolver CLI (`current-claude-session-id`,
`current-codex-thread-id`) and a session-ID skill. Antigravity has neither, so
Antigravity-run execution records cannot carry a `session_transcript:`
pointer. What is available depends on what the investigation finds, which is
why this item depends on it. Scope this item from the investigation's
appendix, not from assumptions.

Per the proposal's Decision 4, the CLI name uses Antigravity's own term,
"conversation": `current-antigravity-conversation-id`. The investigation may
choose another name.

### Duplication search
- In-repo: Related: `src/lrh/conversations/codex_session.py` and
  `claude_session.py` (resolver precedents to mirror);
  `src/lrh/conversations/antigravity_export.py` (existing `--conversation-id`
  and `--latest` discovery to reuse rather than duplicate).
- Sibling repos: None identified.
- External libraries: Whatever the investigation identifies.
- Recommendation: Proceed after the investigation lands.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 5.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Add the resolver module, the CLI subcommand and tests.
- Add the skill, installed to all three targets.
- Document the subcommand and the pointer format, and add the skill to
  `CLAUDE.md`.

## Required Changes

1. Add `src/lrh/conversations/antigravity_session.py`:
   - mirror `codex_session.py` and `claude_session.py` in shape and in
     metadata-only output;
   - reuse `antigravity_export.py`'s brain-directory discovery;
   - never read transcript content.
2. Register the subcommand under `lrh conversation` in `src/lrh/cli/main.py`.
3. Add hermetic tests in
   `tests/conversations_tests/antigravity_session_test.py` covering these
   cases: resolved, ambiguous, unresolvable, and a missing brain directory.
4. Create `src/lrh/skills/lrh-session-id-antigravity/` (`SKILL.md` and
   `agents/openai.yaml`), modelled on `lrh-session-id-codex`, including its
   safety rules. Install it to all three targets, one skill at a time.
5. Document the pointer format and the subcommand in:
   - `PROMPTS.md`
   - `project/executions/README.md`
   - `docs/reference/cli/conversation.md`
6. Add `/lrh-session-id-antigravity` to `CLAUDE.md`.
7. Update `build_session_report` in `src/lrh/prompt_workflow_sessions.py`.
   Today it handles only the `claude-app` and `codex-app` schemes and reports
   every other pointer as `unsupported`.
   - Recognize the new Antigravity scheme and classify it on the evidence
     available, the way the other two schemes are classified.
   - Add tests for it alongside the existing session-report tests.

## Non-Goals

- Does not change `export-antigravity-session` or `lrh-export-antigravity`.
- Does not add the `/lrh-session-id` dispatcher. That is
  `WI-LRH-SESSION-ID-DISPATCHER`.
- Does not change `/lrh-closeout`'s pointer handling beyond documenting the
  new format.

## Acceptance Criteria

- The resolver subcommand reports the current conversation ID and pointer as
  the investigation specified, without reading transcript content.
- The module is covered by hermetic tests for the resolved, ambiguous and
  unresolvable cases.
- `lrh-session-id-antigravity` wraps the resolver, reports `pending` when the
  conversation is unresolved, and is installed to all three targets.
- The CLI reference, the pointer-format docs and `CLAUDE.md` are updated.
- `lrh sessions report` recognizes Antigravity pointers rather than reporting
  them as unsupported.
- If the investigation deferred this work, this item is abandoned with that
  reason.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh conversation current-antigravity-conversation-id --help`
- `lrh skills check --target claude --local`
- `lrh skills status --target antigravity --local`

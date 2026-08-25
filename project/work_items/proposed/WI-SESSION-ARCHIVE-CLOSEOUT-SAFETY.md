---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-CLOSEOUT-SAFETY
title: Harden session archive closeout sync and refresh generated skill targets
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
  - WS-SESSION-ARCHIVE-SYNC
related_design:
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
depends_on:
  - WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - commit_raw_transcripts
  - change_session_transcript_schema
  - implement_encrypted_off_machine_archive
acceptance:
  - lrh sessions sync and closeout-sync reject archive roots inside the project checkout before writing raw transcript bytes
  - closeout-triggered session archive sync has a preflight path or equivalent sequencing so predictable archive-root failures occur before confirmed control-plane edits
  - Canonical skill references document the complete lrh sessions schedule option set and use the current sessions heading cross-reference
  - Claude, Codex, and Antigravity local target skill copies are regenerated or checked from canonical src/lrh/skills sources
  - Focused tests cover unsafe archive roots, closeout preflight behavior, and the documented schedule option surface
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/sessions_workflow.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
  - tests/cli_tests/sessions_test.py
  - docs/reference/cli/sessions.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-closeout/references/closeout-workflow.md
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
  - .claude/skills/
  - .agents/skills/
  - .gemini/plugins/lrh/
---

# Harden session archive closeout sync and refresh generated skill targets

## Summary

Harden `lrh sessions sync` and `lrh sessions closeout-sync` so raw transcript archive writes cannot target the project checkout, then update canonical session/skill documentation and regenerate target skill copies for Claude, Codex, and Antigravity.

## Problem / Context

PR #624 exposed that the generated Gemini/Antigravity skill copies were stale relative to canonical `src/lrh/skills`, but the deeper review findings point back to canonical source and runtime behavior. Current closeout instructions run `lrh sessions closeout-sync --project-root .`, while the sync implementation resolves an archive root and writes raw transcript bytes under that root; without an explicit outside-checkout guard, a misconfigured `--archive-root` or `LRH_SESSION_ARCHIVE_ROOT` could place private transcript bodies inside tracked repository state. The same review also found canonical documentation drift: the closeout workflow cross-reference still names the old sessions heading, and the skill command synopsis omits supported `schedule` options that the CLI accepts.

### Duplication search

- In-repo: Related prior work exists but does not duplicate this fix. `WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC` delivered closeout-triggered sync and scheduling, while `WI-SKILLS-ANTIGRAVITY-TARGET` delivered generated Antigravity target support. Neither adds an archive-root-outside-checkout guard or the closeout preflight sequencing described here.
- Sibling repos: None identified for this LRH-side runtime and canonical-skill fix.
- External libraries: None identified. The implementation should use existing `pathlib`/CLI/test patterns.
- Recommendation: Proceed as a focused hardening follow-up to `WS-SESSION-ARCHIVE-SYNC`.

### Demand search

- Work items: No proposed LRH work item found for closeout archive-root safety. `WI-TAURCODE-PROMPT-AND-SKILL-SYNC` is related only as sibling-repo skill synchronization and explicitly does not change LRH.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` remains the governing design for private local transcript archive behavior.
- Backlog: Related archive-root-location and generated-skill drift concerns exist, but no matching narrow item covers this safety/documentation fix.
- Recommendation: No closeout action now; link this item to `WS-SESSION-ARCHIVE-SYNC`.

## Scope

- Harden LRH session archive root validation for `sync` and `closeout-sync`.
- Add a closeout preflight path or equivalent sequencing so predictable archive failures happen before control-plane edits.
- Correct canonical CLI/skill documentation for `lrh sessions` command references.
- Regenerate or verify local Claude, Codex, and Antigravity generated skill targets from canonical `src/lrh/skills`.
- Preserve the existing private local archive model and `session_transcript` grammar.

## Required Changes

1. Add a helper in `src/lrh/prompt_workflow_sessions.py` or `src/lrh/sessions_workflow.py` that resolves archive roots and rejects any root equal to, nested under, or symlink-resolving into the selected `--project-root`.
2. Apply that guard before any raw transcript mirroring, export metadata persistence, or dry-run destination reporting in `lrh sessions sync` and `lrh sessions closeout-sync`.
3. Add `lrh sessions closeout-sync --preflight` or an equivalent explicit preflight path that checks archive-root safety and expected writeability without copying transcript bodies or updating `project/sessions/index.jsonl`.
4. Update `src/lrh/skills/lrh-closeout/SKILL.md` so closeout shows the archive-sync command at the gate, runs preflight before confirmed control-plane edits, runs the real sync after edits and before validation, and reports failures without leaving predictable partial closeout state.
5. Update `src/lrh/skills/lrh-closeout/references/closeout-workflow.md` to reference the current `lrh sessions` heading.
6. Update `src/lrh/skills/lrh-implement/references/execution-session-reference.md` so the `lrh sessions schedule` synopsis includes the complete supported option set, including `--claude-projects-root`, `--exports-dir`, `--archive-root`, `--label`, and `--output`.
7. Add focused tests for unsafe archive roots, preflight behavior, and the schedule option synopsis/CLI surface.
8. Regenerate or verify local target skill copies from canonical source for Claude, Codex, and Antigravity, including `.gemini/plugins/lrh/plugin.json` where applicable.

## Non-Goals

- Do not choose or redesign the long-term encrypted/off-machine archive storage policy.
- Do not change the `session_transcript` schema or execution-record grammar.
- Do not commit raw transcript files, raw JSONL fixtures from real sessions, or private archive contents.
- Do not hand-edit generated `.gemini`, `.agents`, or `.claude` skill copies without reconciling canonical `src/lrh/skills` source.
- Do not alter unrelated session archive report, discover, or link behavior except where needed to share archive-root validation.

## Acceptance Criteria

- `lrh sessions sync` and `lrh sessions closeout-sync` reject archive roots inside the project checkout before writing raw transcript bytes.
- Closeout-triggered session archive sync has a preflight path or equivalent sequencing so predictable archive-root failures occur before confirmed control-plane edits.
- Canonical skill references document the complete `lrh sessions schedule` option set and use the current sessions heading cross-reference.
- Claude, Codex, and Antigravity local target skill copies are regenerated or checked from canonical `src/lrh/skills` sources.
- Focused tests cover unsafe archive roots, closeout preflight behavior, and the documented schedule option surface.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills check --target claude --local --source current-repo`
- `lrh skills check --target codex --local --source current-repo`
- `lrh skills check --target antigravity --local --source current-repo`
- `python -m unittest tests.cli_tests.sessions_test tests.assist_tests.prompt_workflow_sessions_test`

## Risk Notes

- Archive-root validation must handle non-existing paths and symlinked path components without accidentally allowing a repo-local private archive.
- Preflight cannot prevent every later I/O failure, but it should catch deterministic misconfiguration before control-plane edits are made.
- Target skill copies are generated outputs; hand edits can hide canonical drift unless the implementation verifies them against `src/lrh/skills`.
- The fix should not make normal private defaults unusable for users whose archive root is outside the checkout.

---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ID-CODEX-SKILL-RENAME
title: "Rename lrh-codex-session to lrh-session-id-codex, with a deprecated stub"
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
depends_on:
  - WI-EXPORT-SKILLS-LIVE-SESSION-WORDING
blocked_by: []
expected_actions:
  - run_tests
  - create_file
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - rename_cli_subcommands
  - rewrite_adopted_or_resolved_documents
  - skills_install_force
  - export_transcript_content
acceptance:
  - "src/lrh/skills/lrh-session-id-codex/ (SKILL.md and agents/openai.yaml) exists with the full content of lrh-codex-session, with the frontmatter name and self-references updated and behavior otherwise unchanged"
  - "src/lrh/skills/lrh-codex-session/SKILL.md is a deprecated stub: disable-model-invocation is true, the description names /lrh-session-id-codex, and the body hands off with the same arguments"
  - "Every current skill, doc and proposed work item that names /lrh-codex-session, including the Codex export skill (src/lrh/skills/lrh-codex-export/SKILL.md, or lrh-export-codex/SKILL.md if WI-EXPORT-SKILL-FAMILY-RENAME landed first, plus its three installed copies) and WI-SKILLS-LRH-CLAUDE-SESSION's template reference, uses /lrh-session-id-codex; adopted and resolved documents are unchanged"
  - "All three install targets contain lrh-session-id-codex and the stub, installed skill by skill without --force, and CLAUDE.md lists /lrh-session-id-codex"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
  - "On the Antigravity target, where AntigravitySkillRenderer strips disable-model-invocation with no equivalent, each stub's description tells the model not to select it and names the replacement; the implementer also checks whether Antigravity supports an invocation-control field and, if so, maps disable-model-invocation onto it in the renderer"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-session-id-codex/SKILL.md
  - src/lrh/skills/lrh-session-id-codex/agents/openai.yaml
  - src/lrh/skills/lrh-codex-session/SKILL.md
  - .claude/skills/lrh-session-id-codex/
  - .agents/skills/lrh-session-id-codex/
  - .gemini/plugins/lrh/skills/lrh-session-id-codex/
  - src/lrh/skills/lrh-codex-export/SKILL.md (or src/lrh/skills/lrh-export-codex/SKILL.md, whichever exists)
  - CLAUDE.md
  - docs/conversations/codex_export.md
  - docs/reference/cli/conversation.md
---

# WI-SESSION-ID-CODEX-SKILL-RENAME: Rename lrh-codex-session to lrh-session-id-codex

## Summary

Rename the metadata-only Codex session-pointer skill from `lrh-codex-session`
to `lrh-session-id-codex`, following `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`
Decisions 1 and 3. Keep `lrh-codex-session` as a deprecated stub.

## Problem / Context

`lrh-codex-session` (`WI-CODEX-SESSION-ID-RESOLVER`, PR #611) is the only
session-ID skill that has shipped. Its name puts the vendor first and does
not share a prefix with the planned `/lrh-session-id` dispatcher. The Claude
equivalent, `WI-SKILLS-LRH-CLAUDE-SESSION`, is retargeted to
`lrh-session-id-claude` in the same workstream, so renaming this skill keeps
the family consistent.

Live references to the old name, found by grep on 2026-09-24:
- `src/lrh/skills/lrh-codex-export/SKILL.md`, which becomes
  `lrh-export-codex` if `WI-EXPORT-SKILL-FAMILY-RENAME` lands first;
- `CLAUDE.md`;
- `docs/conversations/codex_export.md`;
- `docs/reference/cli/conversation.md`;
- `project/work_items/proposed/WI-SKILLS-LRH-CLAUDE-SESSION.md`, which uses it
  as a template.

The installer facts in `WI-EXPORT-SKILL-FAMILY-RENAME` apply here too: the
installer never deletes skills, and `--force` overwrites every
locally-modified skill in the target.

### Duplication search
- In-repo: Related: `src/lrh/skills/lrh-codex-session/`, the skill being
  renamed.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found beyond this workstream.
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decisions 1 and 3.
- Backlog: No matching entries.
- Recommendation: No action.

This item depends on `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`, because it
edits the Codex export skill (its `/lrh-codex-session` reference), which is
one of the files the wording fix edits. That keeps a single edit order for
the export skill files.

## Scope

- Create `lrh-session-id-codex`, with the same behavior as before.
- Replace `lrh-codex-session` with a deprecated stub.
- Install both to all three targets.
- Update current references to the old name.

## Required Changes

1. Copy `src/lrh/skills/lrh-codex-session/` (`SKILL.md`,
   `agents/openai.yaml`) to `src/lrh/skills/lrh-session-id-codex/`. Update
   `name:`, headings and usage examples. Change nothing else.
2. Replace `src/lrh/skills/lrh-codex-session/SKILL.md` with a deprecated
   stub:
   - set `disable-model-invocation: true`;
   - write a description of the form "Deprecated: use
     /lrh-session-id-codex";
   - in the body, hand off to the replacement with the same arguments.
3. Install the new skill and the stub to `.claude/skills/`, `.agents/skills/`
   and `.gemini/plugins/lrh/skills/`, one skill at a time. Do not use
   `--force`.
4. Update `/lrh-codex-session` to `/lrh-session-id-codex` in:
   - the Codex export skill, under whichever name it currently has;
   - `CLAUDE.md`;
   - `docs/conversations/codex_export.md`;
   - `docs/reference/cli/conversation.md`;
   - `WI-SKILLS-LRH-CLAUDE-SESSION`.

   Leave adopted and resolved documents and execution records unchanged.

### Stub protection on the Antigravity target

`disable-model-invocation: true` protects a stub differently on each target:

- **Claude:** honored as written.
- **Codex:** the Codex renderer turns it into
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- **Antigravity:** `AntigravitySkillRenderer`
  (`src/lrh/skills/installer.py`) strips the key and writes nothing in its
  place.

For the Antigravity target:

1. Make each stub's `description` tell the model not to select it and
   name the replacement.
2. Check whether Antigravity supports any invocation-control field. If it
   does, map `disable-model-invocation` onto it in the renderer.

See `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 3.

## Non-Goals

- Does not rename the `lrh conversation current-codex-thread-id` CLI.
- Does not change the `codex-app:<id>` pointer format or resolver behavior.
- Does not add the Claude or Antigravity session-ID skills, or the
  dispatcher.

## Acceptance Criteria

- `lrh-session-id-codex` exists with `lrh-codex-session`'s behavior unchanged,
  apart from the name and self-references.
- `lrh-codex-session` is a deprecated stub with
  `disable-model-invocation: true` that hands off to the new name.
- Every current reference to `/lrh-codex-session` uses the new name.
- All three targets contain the new skill and the stub, and `CLAUDE.md` lists
  `/lrh-session-id-codex`.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills check --target claude --local`
- `lrh skills status --target codex --local`
- `lrh skills status --target antigravity --local`

## Risk Notes

- This item and `WI-EXPORT-SKILL-FAMILY-RENAME` edit each other's skills.
  This item updates `/lrh-codex-session` references in the Codex export
  skill; that one updates `/lrh-codex-export` references in this skill.
  - Whichever lands second must rebase onto the other, and edit the other
    skill under its current name.
  - Before finishing, re-run
    `grep -rln 'lrh-codex-session\|lrh-codex-export' src/lrh/skills` so no
    skill is left routing through a deprecated stub.

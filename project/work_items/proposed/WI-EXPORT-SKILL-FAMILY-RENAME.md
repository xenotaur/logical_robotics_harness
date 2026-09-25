---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-SKILL-FAMILY-RENAME
title: "Rename lrh-codex-export and lrh-antigravity-export to lrh-export-codex and lrh-export-antigravity, with deprecated stubs"
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
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
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
  - rename_export_artifact_prefix
  - rewrite_adopted_or_resolved_documents
  - skills_install_force
acceptance:
  - "src/lrh/skills/lrh-export-codex/ and src/lrh/skills/lrh-export-antigravity/ exist with the full content of the old skills, with the frontmatter name and self-references updated and behavior otherwise unchanged"
  - "src/lrh/skills/lrh-codex-export/SKILL.md and src/lrh/skills/lrh-antigravity-export/SKILL.md are deprecated stubs: disable-model-invocation is true, the description names the replacement, and the body tells the agent to run the replacement with the same arguments"
  - "All three install targets (.claude/skills, .agents/skills, .gemini/plugins/lrh/skills) contain both new skills and both stubs, installed skill by skill without lrh skills install --force, and lrh-export-antigravity is present in .gemini/plugins/lrh/skills"
  - "CLAUDE.md lists /lrh-export-codex and /lrh-export-antigravity; current docs and proposed work items that name the old skills use the new names; adopted and resolved documents are unchanged"
  - "Other skills' references to /lrh-codex-export (src/lrh/skills/lrh-codex-session/SKILL.md, or lrh-session-id-codex/SKILL.md if WI-SESSION-ID-CODEX-SKILL-RENAME landed first) use /lrh-export-codex, including their three installed copies, so no skill routes through a deprecated stub"
  - "The lrh-codex-export-<timestamp> export-directory prefix in src/lrh/conversations/codex_archive.py, its tests and experimental/rescue_codex_exports is unchanged"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
  - "On the Antigravity target, where AntigravitySkillRenderer strips disable-model-invocation with no equivalent, each stub's description tells the model not to select it and names the replacement; the implementer also checks whether Antigravity supports an invocation-control field and, if so, maps disable-model-invocation onto it in the renderer"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-export-codex/SKILL.md
  - src/lrh/skills/lrh-export-codex/agents/openai.yaml
  - src/lrh/skills/lrh-export-antigravity/SKILL.md
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
  - .claude/skills/lrh-export-codex/
  - .claude/skills/lrh-export-antigravity/
  - .agents/skills/lrh-export-codex/
  - .agents/skills/lrh-export-antigravity/
  - .gemini/plugins/lrh/skills/lrh-export-codex/
  - .gemini/plugins/lrh/skills/lrh-export-antigravity/
  - src/lrh/skills/lrh-codex-session/SKILL.md (or src/lrh/skills/lrh-session-id-codex/SKILL.md, whichever exists)
  - CLAUDE.md
  - docs/conversations/README.md
  - docs/conversations/codex_export.md
  - docs/conversations/conversation-capture-options.md
  - docs/reference/cli/conversation.md
---

# WI-EXPORT-SKILL-FAMILY-RENAME: Rename the Codex and Antigravity export skills to the lrh-export-<vendor> scheme

## Summary

Rename `lrh-codex-export` to `lrh-export-codex` and `lrh-antigravity-export`
to `lrh-export-antigravity`, following Decision 1 of
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`. Keep each old name as a
deprecated stub (Decision 3). In the same change, install the Antigravity
exporter to the Antigravity target, where it is currently missing
(Decision 6).

## Problem / Context

The three export skills use two naming shapes. `lrh-export-claude` puts the
verb first; `lrh-codex-export` and `lrh-antigravity-export` put the vendor
first. `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 9 deferred this rename
to the design of the `/lrh-export` dispatcher, and that design is now
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`.

Facts the implementer needs:

- **The installer never deletes skills.** `src/lrh/skills/installer.py` only
  overwrites the skills it is installing and never removes a folder whose
  source is gone. That is why the old names must become stubs rather than be
  deleted: downstream installs would otherwise keep a stale full copy.
- **The Antigravity target is out of date.** A dry run of
  `lrh skills install --target antigravity --local --source current-repo`
  reports "would install: lrh-antigravity-export", so that target has never
  received the exporter.
- **Do not use `--force`.** The same dry run reports local modifications to
  nine other skills in `.gemini/plugins/lrh/skills/`, and `--force` would
  overwrite all of them. Install skill by skill instead: use
  `installer._copy_skill_from_source` with a `SkillSource` from
  `installer.resolve_skill_source(...)`.
- **Do not rename the artifact prefix.** `lrh-codex-export-<timestamp>...` is
  also the name prefix of export artifact folders, in
  `src/lrh/conversations/codex_archive.py`,
  `tests/conversations_tests/codex_archive_test.py` and
  `experimental/rescue_codex_exports/`. It is a data-format name, not a skill
  name, and must not change.
- **Wait for the wording fix.** `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING` edits
  these same skill files. This item depends on it so the two do not collide.

### Duplication search
- In-repo: Related: `src/lrh/skills/lrh-codex-export/`,
  `src/lrh/skills/lrh-antigravity-export/` (the skills being renamed). No
  existing rename or stub mechanism.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found beyond this workstream.
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 9, and
  `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decisions 1, 3 and 6.
- Backlog: "Generalize conversation export manifests beyond Codex before
  `/lrh-export`" (its Naming paragraph).
- Recommendation: No action. `WI-EXPORT-SESSION-ID-DOCS` resolves that
  backlog entry.

## Scope

- Create the two renamed skills, with the same behavior as before.
- Replace the two old skill folders with deprecated stubs.
- Install the renamed skills and stubs to all three targets.
- Update `CLAUDE.md`, current docs, and proposed work items that name the old
  skills.

## Required Changes

1. Copy `src/lrh/skills/lrh-codex-export/` (including `agents/openai.yaml`)
   to `src/lrh/skills/lrh-export-codex/`, and
   `src/lrh/skills/lrh-antigravity-export/` to
   `src/lrh/skills/lrh-export-antigravity/`. Update `name:`, headings, and
   usage examples (`/lrh-codex-export ...` becomes `/lrh-export-codex ...`).
   Change nothing else.
2. Replace each old `SKILL.md` with a deprecated stub:
   - keep the old `name:`;
   - set `disable-model-invocation: true`;
   - write a description of the form "Deprecated: use /lrh-export-<vendor>";
   - in the body, tell the agent to run the replacement skill's steps with the
     same arguments and add no behavior of its own;
   - delete the old `agents/openai.yaml`, or reduce it to the same stub.
3. Install `lrh-export-codex`, `lrh-export-antigravity` and both stubs to
   `.claude/skills/`, `.agents/skills/` and `.gemini/plugins/lrh/skills/`,
   one skill at a time. Do not use `--force`.
4. In `CLAUDE.md` `## Skills`:
   - replace the `/lrh-codex-export` and `/lrh-antigravity-export` entries
     with the new names;
   - do not list the stubs, or list them only as deprecated.
5. Update the old names to the new ones in:
   - other skills that reference them. Today only
     `src/lrh/skills/lrh-codex-session/SKILL.md` refers to
     `/lrh-codex-export` (lines 50, 62, 113). It is
     `lrh-session-id-codex/SKILL.md` if
     `WI-SESSION-ID-CODEX-SKILL-RENAME` landed first. Update it and re-install
     its three copies. Re-run
     `grep -rln 'lrh-codex-export\|lrh-antigravity-export' src/lrh/skills`
     before finishing, to catch any new references.
   - `docs/conversations/README.md`
   - `docs/conversations/codex_export.md`
   - `docs/conversations/conversation-capture-options.md`
   - `docs/reference/cli/conversation.md`
   - skill-name references in `experimental/save_codex_threads/plan.md` and
     `experimental/rescue_codex_exports/README.md`
   - proposed work items that name them (for example
     `WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`,
     `WI-CODEX-EXPORT-RESCUE-CANONICAL-DEST`,
     `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`)

   Leave these unchanged:
   - `adopted` and `resolved` documents
   - execution records
   - the `lrh-codex-export-<timestamp>` artifact prefix

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

- Does not rename any `lrh conversation` CLI subcommand.
- Does not change export behavior, archive paths or confirm gates. The
  Antigravity confirm gate is `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`.
- Does not rename `lrh-codex-session`. That is
  `WI-SESSION-ID-CODEX-SKILL-RENAME`.
- Does not remove the stubs. That is a later follow-up.
- Does not add `/lrh-export`. That is `WI-LRH-EXPORT-DISPATCHER`.

## Acceptance Criteria

- `lrh-export-codex` and `lrh-export-antigravity` exist with the old skills'
  behavior unchanged, apart from the name and self-references.
- `lrh-codex-export` and `lrh-antigravity-export` are deprecated stubs with
  `disable-model-invocation: true` that hand off to the new names.
- All three install targets contain the new skills and the stubs.
  `lrh-export-antigravity` is present in `.gemini/plugins/lrh/skills/`. No
  `--force` install was used.
- `CLAUDE.md`, current docs and proposed work items use the new names.
  Adopted and resolved documents are unchanged.
- The `lrh-codex-export-<timestamp>` artifact prefix is unchanged.
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
- `diff -r src/lrh/skills/lrh-export-codex .claude/skills/lrh-export-codex`

## Risk Notes

- This item and `WI-SESSION-ID-CODEX-SKILL-RENAME` edit each other's skills
  (see Required Change 5). Whichever lands second must rebase onto the other,
  and edit the other skill under its current name.
- A stub accidentally left model-invocable would compete with the new name
  for automatic triggering. `disable-model-invocation: true` is required.
- A blanket search-and-replace would also rewrite the
  `lrh-codex-export-<timestamp>` artifact prefix and break
  `codex_archive.py`. Replace skill-name references one by one.

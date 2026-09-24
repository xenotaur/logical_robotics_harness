---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CHATGPT-EXPORT
title: 'Export canonical LRH skills as ChatGPT-uploadable bundles'
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
  - write_docs
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - publish_package
  - implement_openai_api_skill_sync
  - implement_openai_plugin_distribution
acceptance:
  - '`lrh skills export --target chatgpt --out <dir>` exports canonical skills as ChatGPT-uploadable ZIP bundles'
  - 'Each exported ZIP contains exactly one top-level skill directory with a valid SKILL.md and preserves applicable references, scripts, and assets'
  - 'ChatGPT rendering removes unsupported agent-specific metadata without modifying canonical skill sources or local Claude, Codex, or Antigravity installs'
  - 'Repeated export from identical source content produces deterministic bundle bytes'
  - 'Automated tests cover package and filesystem sources, skill selection, rendering, deterministic ZIP output, invalid source content, and symlink/path-safety behavior'
  - 'ChatGPT usage documentation covers upload, @-invocation, automatic selection, updates, and capability limitations'
  - 'At least one instruction-centric LRH skill is manually dogfooded successfully in ChatGPT online'
  - 'scripts/test and lrh validate complete successfully'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - src/lrh/skills/installer.py
  - src/lrh/cli/main.py
  - tests/skills_exporter_test.py
  - tests/cli_tests/skills_test.py
  - docs/reference/cli/skills.md
  - docs/how-to/use-lrh-with-agent-assistants.md
---

## Summary

Add `lrh skills export --target chatgpt` so LRH can render canonical package
or repository skills into deterministic, ChatGPT-uploadable Agent Skill ZIP
bundles without introducing a separate ChatGPT-specific source of truth.

## Problem / Context

LRH already supports one canonical skill source rendered or installed for
Claude, Codex, and Antigravity. The adopted target-aware skills proposal
reserved ChatGPT as a later hosted export target rather than a filesystem
install target, but deferred implementation because the ChatGPT upload
contract was not sufficiently documented at the time.

That external dependency is now resolved: ChatGPT supports uploaded Agent
Skills and explicit `@skill-name` selection. The missing LRH boundary is
therefore packaging and validation, not another local installation mechanism.
Relevant current OpenAI documentation includes:

- https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- https://developers.openai.com/api/docs/guides/tools-skills

The implementation must preserve the distinction between **workflow knowledge**
and **runtime capability**. Exporting a skill that references `git`, `gh`,
shell commands, or LRH CLI operations does not imply ChatGPT online has those
capabilities; export should preserve such semantics and report compatibility
limitations rather than mechanically rewriting the workflow.

### Duplication search

- In-repo: No ChatGPT skill-export implementation exists. Related
  infrastructure already exists in `src/lrh/skills/installer.py`, including
  canonical `SkillSource` handling and target renderer abstractions. The
  adopted target-aware proposal explicitly reserves ChatGPT export as a
  deferred stage.
- Sibling repos: No matching implementation found in LCATS or Prosoc.
- External libraries/services: ChatGPT provides the hosted skill upload
  mechanism; LRH should package for that mechanism rather than implement its
  own hosting service.
- Recommendation: Proceed by extending the existing LRH skills architecture
  with a hosted-export boundary.

### Demand search

- Work items: No existing `WI-SKILLS-CHATGPT-EXPORT` or equivalent
  implementation item found.
- Proposals: `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` explicitly identifies
  future `lrh skills export --target chatgpt`.
- Backlog: No separate ChatGPT skill-export backlog item found.
- Recommendation: Treat this work item as realization of the adopted
  proposal's deferred ChatGPT-export stage; do not create a parallel proposal.

## Scope

- Add a hosted-export operation under the existing `lrh skills` command
  family.
- Reuse canonical package, current-repo, explicit-path, and repository-config
  skill source resolution where applicable.
- Render portable ChatGPT-compatible skill trees without altering canonical
  sources.
- Package each selected skill as an independently uploadable deterministic
  ZIP.
- Add focused validation, tests, and user documentation.
- Dogfood the exported artifact in ChatGPT online.

## Required Changes

1. Add an `export` subcommand to the existing `lrh skills` CLI:
   - `lrh skills export --target chatgpt --out <directory>`;
   - reuse existing `--source` semantics;
   - optionally support repeatable `--skill <name>` selection;
   - when no skill selector is supplied, export all public skills from the
     selected source;
   - do not expose `--local` or `--scope` on export because hosted
     artifacts have no local install scope.

2. Create `src/lrh/skills/exporter.py` to own hosted skill packaging rather
   than extending filesystem-install behavior inside the installer:
   - resolve canonical skill files from the existing `SkillSource`
     abstraction;
   - render target-compatible output;
   - validate bundle shape;
   - write one deterministic ZIP per skill;
   - return structured export results suitable for CLI formatting and tests.

3. Add a ChatGPT renderer compatible with the existing `SkillRenderer`
   abstraction:
   - preserve portable Agent Skills fields, `SKILL.md` body content,
     references, scripts, and assets;
   - remove Claude-, Codex-, or Antigravity-specific frontmatter or generated
     metadata that is not part of the portable ChatGPT bundle;
   - do not modify the canonical source tree;
   - do not generate Codex `agents/openai.yaml` solely for ChatGPT.

4. Package each skill as exactly one top-level directory:

   ```text
   <skill-name>/
     SKILL.md
     references/
     scripts/
     assets/
   ```

   Only directories/files actually present in the canonical source need be
   included.

5. Make ZIP generation deterministic:
   - sort archive paths;
   - normalize path separators;
   - use stable ZIP timestamps and metadata;
   - ensure two exports of unchanged source produce byte-identical archives.

6. Validate export content before writing:
   - require `SKILL.md`;
   - reject malformed frontmatter;
   - enforce safe relative paths;
   - never follow source symlinks;
   - reject duplicate or escaping archive paths;
   - check documented ChatGPT upload size/file-count constraints where
     practical.

7. Add non-blocking compatibility reporting for skills that visibly depend on
   capabilities not guaranteed in ChatGPT online, such as:
   - local `git`;
   - `gh`;
   - arbitrary shell commands;
   - direct LRH CLI invocation.

   The exporter must not attempt heuristic rewriting of these procedures.

8. Extend automated tests:
   - package-resource source;
   - explicit filesystem source;
   - one-skill and all-skill export;
   - portable metadata rendering;
   - preservation of nested reference/script/asset files;
   - deterministic byte output;
   - malformed `SKILL.md`;
   - symlink and path-traversal handling;
   - CLI argument and reporting behavior.

9. Update user-facing documentation:
   - add ChatGPT Online to `docs/how-to/use-lrh-with-agent-assistants.md`;
   - document `lrh skills export --target chatgpt`;
   - document ChatGPT upload;
   - document explicit `@skill-name` invocation and automatic activation;
   - explain that skill instructions do not grant unavailable tools;
   - document re-export/re-upload when canonical skills change;
   - update `docs/reference/cli/skills.md`.

10. Dogfood at least one instruction-centric skill such as `lrh-design`,
    `lrh-proposal`, or `lrh-work-item` in ChatGPT online and record the
    result as implementation evidence.

## Non-Goals

- Do not add `chatgpt` to `lrh skills install --target`; ChatGPT online is
  a hosted export target, not a filesystem destination.
- Do not upload skills automatically to a ChatGPT account.
- Do not add OpenAI API credentials or `/v1/skills` publishing in this item.
- Do not assume API-hosted skills synchronize into a user's ChatGPT Skills
  catalog.
- Do not build or publish an OpenAI plugin containing the LRH skill suite.
- Do not implement an LRH-hosted skill registry or marketplace.
- Do not mechanically rewrite shell- or repository-dependent skill workflows
  into ChatGPT-specific tool calls.
- Do not modify Claude, Codex, or Antigravity installation behavior except
  where shared abstractions require narrow, behavior-preserving refactoring.

## Acceptance Criteria

- `lrh skills export --target chatgpt --out <dir>` exports selected
  canonical skills as ChatGPT-uploadable ZIPs.
- Each ZIP has one correctly named top-level skill directory and one valid
  `SKILL.md`.
- Nested portable skill content is preserved.
- Agent-specific metadata inappropriate for ChatGPT export is omitted without
  changing canonical source files.
- Identical inputs generate byte-identical ZIP files.
- Unsafe symlinks and escaping archive paths are rejected rather than followed.
- Capability-dependent skills produce an informative compatibility notice
  without having their workflow text silently rewritten.
- Tests cover source resolution, rendering, packaging, determinism, invalid
  input, safety cases, and CLI behavior.
- Documentation explains export, upload, `@` invocation, automatic
  activation, updating, and capability boundaries.
- At least one exported instruction-centric LRH skill is successfully uploaded
  and exercised in ChatGPT online.
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `lrh validate` complete successfully.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills export --target chatgpt --source current-repo --out <temporary-directory>`
- Repeat the same export and verify the generated archives are byte-identical
- Inspect one generated archive and verify it contains exactly one top-level
  skill directory with `SKILL.md`
- Manually upload at least one exported skill to ChatGPT online and exercise it
  through explicit `@` invocation

## Risk Notes

- ChatGPT's hosted skill surface can evolve independently of the local Agent
  Skills implementations used by Claude, Codex, and Antigravity; keep hosted
  packaging behind a renderer/export boundary.
- A successfully uploaded skill can still be unable to complete workflows
  requiring unavailable local tools. Treat this as a capability constraint,
  not an export failure.
- Deterministic ZIP output requires normalizing archive metadata in addition to
  sorting file names.
- Exported artifacts are generated outputs and must not become a fourth
  authoritative copy of LRH skill source.
- Automatic upload/publishing would introduce credentials, account identity,
  and remote lifecycle semantics; deliberately defer those until manual
  export/upload has been dogfooded.

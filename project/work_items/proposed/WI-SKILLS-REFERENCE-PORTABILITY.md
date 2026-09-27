---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-REFERENCE-PORTABILITY
title: Make LRH skill references portable across independent client repositories
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - require_client_docs_tree
  - create_full_lrh_docs_distribution_system
  - modify_cli_runtime_behavior
acceptance:
  - "The affected LRH skills no longer require LRH-owned documentation paths to exist relative to an independent client repository in order to follow their operational workflow."
  - "The source skill corpus and all maintained rendered targets agree on the portable reference behavior."
  - "A minimal third-party repository fixture with no general docs/ directory can exercise the affected skill guidance without treating an absent optional LRH reference as a runtime failure."
  - "The portable guidance identifies CLI help or explicit runtime capability checks as the operational authority where a reference document is unavailable."
  - "lrh validate and the canonical formatting, lint, and test commands pass with 0 validation errors."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - src/lrh/skills/lrh-codex-session/SKILL.md
  - src/lrh/skills/lrh-config-skills/SKILL.md
  - src/lrh/skills/lrh-doc-audit/SKILL.md
  - .claude/skills/lrh-codex-export/SKILL.md
  - .claude/skills/lrh-codex-session/SKILL.md
  - .claude/skills/lrh-config-skills/SKILL.md
  - .claude/skills/lrh-doc-audit/SKILL.md
  - .agents/skills/lrh-codex-export/SKILL.md
  - .agents/skills/lrh-codex-session/SKILL.md
  - .agents/skills/lrh-config-skills/SKILL.md
  - .agents/skills/lrh-doc-audit/SKILL.md
  - tests/
---

# WI-SKILLS-REFERENCE-PORTABILITY: Make LRH skill references portable across independent client repositories

## Summary

Make LRH-distributed skills usable in independent client repositories whose control plane does not contain LRH's maintainer-owned `docs/` tree. Operational skill guidance must remain usable when an LRH reference document is absent, while retaining clear pointers to authoritative LRH documentation when it is available.

## Problem / Context

The installed `lrh-codex-export` skill directed an agent in the Replication Vector repository to read `docs/reference/cli/conversation.md`, but that LRH-owned path does not exist in the client repository. The export still completed through the `lrh conversation` CLI, so the missing file was an informational portability failure rather than evidence of a CLI failure. The same assumption appears in related installed skills, including `lrh-codex-session`, `lrh-config-skills`, and `lrh-doc-audit`. The adopted skill architecture treats skills as distributable into independent projects (`project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`), so client-relative references to maintainer-only documentation are an ownership and packaging mismatch that should be corrected before the pattern spreads.

### Duplication search

- In-repo: Related but non-duplicating guidance exists in `src/lrh/skills/lrh-execute/SKILL.md` and `src/lrh/skills/lrh-review-response/SKILL.md`, which resolve installed sibling skills rather than assuming the LRH source tree; affected direct documentation references are inventoried in `src/lrh/skills/lrh-codex-export/SKILL.md`, `src/lrh/skills/lrh-codex-session/SKILL.md`, `src/lrh/skills/lrh-config-skills/SKILL.md`, and `src/lrh/skills/lrh-doc-audit/SKILL.md`.
- Sibling repos: Replication Vector was the observed client fixture; no other sibling implementation of a portable LRH reference resolver was identified.
- External libraries: None identified; this is a skill packaging and instruction-boundary problem, not a missing library capability.
- Recommendation: Proceed with the bounded skill-guidance and fixture change.

### Demand search

- Work items: `WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` is adjacent client-portability work but addresses branch creation rather than documentation references. `WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP` addresses LRH-owned documentation completeness, not client portability.
- Proposals: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md` and `project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md` establish related skill packaging conventions, but neither resolves this missing-client-documents failure mode.
- Backlog: Existing conversation-export entries reference `docs/reference/cli/conversation.md` as LRH documentation; no matching entry proposes portable resolution from independent client repositories.
- Recommendation: Offer to link the implementation back to the adjacent skill-packaging and conversation-export design history; do not close the documentation-parity work item because it has a different outcome.

## Scope

- Audit and update the affected LRH skill instructions and their maintained rendered targets so LRH-owned documentation is not treated as a required client-relative file.
- Use installed/package-owned references where available, and use CLI self-description or explicit runtime capability checks for operational behavior that must work in a standalone client repository.
- Add a minimal third-party repository fixture or hermetic test that has no general `docs/` directory and verifies that absent optional LRH documentation does not block the affected workflow.
- Preserve optional links to LRH-owned documentation for maintainers and contributors working in the LRH repository.

## Required Changes

1. Update the canonical source skill guidance for `lrh-codex-export`, `lrh-codex-session`, `lrh-config-skills`, and `lrh-doc-audit` to distinguish package/LRH-maintainer references from client-local files and to define the behavior when optional references are absent.
2. Render or synchronize the corresponding `.claude/skills/` and `.agents/skills/` copies using the existing LRH skill-install conventions; do not hand-edit generated targets unless the repository convention requires it.
3. Add a focused hermetic fixture or test covering an independent repository with a `project/` control directory but no general `docs/` tree, including the observed Codex export reference case.
4. Ensure the portable instructions use CLI `--help` or explicit runtime capability checks as the operational fallback and do not require a new documentation-distribution system.
5. Document the ownership, optional-reference, and version-compatibility boundary in the affected skill guidance or its smallest appropriate shared reference.
6. Validate source/rendered skill parity and run the canonical repository validation commands.

## Non-Goals

- Do not require every client repository to add an LRH-owned `docs/` tree.
- Do not vendor the complete LRH documentation corpus into every client repository.
- Do not change `lrh` CLI runtime behavior or command semantics.
- Do not create a general-purpose documentation package or remote documentation resolver.
- Do not remove maintainer-facing LRH documentation links when they remain useful and clearly identified as optional or LRH-repository-local.
- Do not modify unrelated skill portability issues outside the discovered reference-path class unless the same shared mechanism requires it.

## Acceptance Criteria

- The affected skills can be installed and interpreted in a third-party repository that has no general `docs/` directory without a missing-file instruction blocking their operational path.
- Each affected reference either resolves to an installed/package-owned asset, is explicitly optional and LRH-repository-local, or is replaced for operational purposes by CLI help/runtime capability checks.
- A hermetic third-party fixture covers the missing `docs/reference/cli/conversation.md` case and passes without reading private transcript contents or requiring network access.
- Canonical and rendered skill copies are synchronized and the repository's skill checks report no drift.
- `lrh validate` reports 0 errors, and the canonical formatting, lint, and test commands pass.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills check --target claude --local`
- `lrh skills check --target codex --local`
- `lrh skills status --target codex --local`
- The focused third-party fixture/test command documented by the implementation

## Risk Notes

- Moving operational authority from prose references to CLI help may expose version skew if the installed CLI is older than the skill; the implementation should state the required capability or fail with a clear diagnostic.
- Treating missing references as silently optional could hide a genuinely required contract; each affected skill must distinguish informational maintainer documentation from runtime prerequisites.
- Updating canonical and rendered skill variants independently could recreate drift; the existing source-to-target installation/check mechanism should remain authoritative.
- A fixture that only checks file existence would miss instruction-level failures, so the test should exercise the relevant path without requiring private transcript data or network access.

## Related Workstream and Designs

- Workstream: `project/workstreams/resolved/WS-SKILLS.md`
- Design: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Design: `project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md`
- Related documentation: `docs/reference/cli/conversation.md`

---
resolution: null
blocked_reason: null
blocked: false
id: WI-TAURSCRIPTS-REPOSITORY-CONTRACT
title: "Document Taurscripts repository contract"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-TAURSCRIPTS-MAINTAINABILITY
related_design:
  - project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_floc_tests
  - implement_drq_tests
  - implement_installer
  - add_generated_staging_tree
acceptance:
  - "Taurscripts source, installed, documentation, test, and future staging boundaries are documented."
  - "Every current tracked top-level path is classified, including the existing bin/ and man/ trees."
  - "Criteria for moving a command into tools/<name>/ are documented."
  - "The documentation receives human review and lrh validate passes with 0 errors."
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - "Taurscripts repository contract documentation"
  - "Tracked-file classification and inventory"
  - "Documented tools/<name>/ graduation criteria"
---

## Summary

Document Taurscripts’ repository contract by defining its source, installation, documentation, testing, and future staging boundaries, and by classifying the repository’s current tracked files.

## Problem / Context

Taurscripts currently consists primarily of executable and support files under `bin/` plus a manual page under `man/`, without a documented source/install boundary, test layout, or criteria for introducing per-tool development directories. The hybrid-layout proposal calls for this contract to be documented before adding tests, an installer, or optional staging output.

The target repository currently has no existing Taurscripts repository-contract work item, test tree, installer, or equivalent layout document. This work item is the first implementation slice of `WS-TAURSCRIPTS-MAINTAINABILITY`.

### Duplication search

- In-repo: Related planning artifacts exist in `project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md` and `project/workstreams/proposed/WS-TAURSCRIPTS-MAINTAINABILITY.md`; no existing repository-contract work item was found.
- Sibling repos: The target repository is `https://github.com/xenotaur/taurscripts`; no separate sibling implementation was identified.
- External libraries: No external library is needed for repository-contract documentation.
- Recommendation: Proceed.

### Demand search

- Work items: No matching Taurscripts work item found. `WI-META-TESTS-LAYOUT-AUDIT` concerns LRH’s own test layout and is unrelated.
- Proposals: `PROP-TAURSCRIPTS-HYBRID-LAYOUT` requests this implementation sequence.
- Backlog: No separate matching Taurscripts repository-contract entry found.
- Recommendation: Link this item to `WS-TAURSCRIPTS-MAINTAINABILITY` and the existing proposal.

## Scope

- Document the current Taurscripts source and installation contract.
- Classify current tracked files and identify which remain directly under `bin/`.
- Define when a command should graduate into `tools/<name>/`.
- Record boundaries for tests, documentation, installation, and optional staging.

## Required Changes

1. Add repository documentation to Taurscripts describing:
   - the relationship between repository source files and the installed `~/bin` tree;
   - the roles of `bin/`, `man/`, future tests, documentation, and optional staging output;
   - the initial installation assumptions.
2. Produce a tracked-file inventory that classifies current content and records which commands remain flat in `bin/`.
3. Document criteria for moving a command into `tools/<name>/`, including testing, fixtures, documentation, dependency, or multi-file complexity.
4. Explicitly defer implementation of `floc` tests, `drq` tests, the installation manifest, the installer, and generated staging output to later work items.
5. Link the resulting documentation and evidence to `WS-TAURSCRIPTS-MAINTAINABILITY`.

## Non-Goals

- Do not implement `floc` or `drq` tests.
- Do not implement the manifest-driven installer.
- Do not add generated `build/bin` output.
- Do not move existing commands or files unless required to place the documentation artifact.
- Do not modify LRH runtime code or CI configuration.
- Do not merge or publish changes.

## Acceptance Criteria

- Taurscripts source, installed, documentation, test, and future staging boundaries are documented.
- Every current tracked top-level path is classified, including the existing `bin/` and `man/` trees.
- Criteria for moving a command into `tools/<name>/` are documented.
- The documentation receives human review.
- `lrh validate` reports 0 errors.

## Validation

- `git -C "$TAURSCRIPTS_REPO" diff --check` (with `TAURSCRIPTS_REPO` set to the local Taurscripts checkout)
- `git -C "$TAURSCRIPTS_REPO" ls-files` (with `TAURSCRIPTS_REPO` set to the local Taurscripts checkout)
- `lrh validate` (run from the LRH checkout)

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-TAURSCRIPTS-MAINTAINABILITY.md`
- Design proposal: `project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md`
- Target repository: `https://github.com/xenotaur/taurscripts`

## Risk Notes

- An incomplete inventory could cause later installer work to omit shell libraries, dotfiles, or nested configuration.
- Over-classifying commands as “complex” could introduce unnecessary directory churn; migration criteria should remain evidence-based.
- The documentation must preserve the existing `~/bin` installation contract while leaving room for later tooling.

## Dependencies / Order

This is the first implementation work item in `WS-TAURSCRIPTS-MAINTAINABILITY`. It should land before the `floc` and `drq` testing work items and before the manifest-driven installer, because those later items depend on an agreed source/install boundary.

## Open Questions

- The initial installer’s destination-prefix decision remains deferred to the installer work item.
- Whether ShellCheck is mandatory or optional remains deferred to the testing work item.

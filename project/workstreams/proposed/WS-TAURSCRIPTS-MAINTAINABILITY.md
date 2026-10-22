---
id: WS-TAURSCRIPTS-MAINTAINABILITY
kind: planning_node
title: "Taurscripts Maintainability and Installation Workflow"
status: proposed
stage: designed
origin: design_review
summary: "Coordinate the transition of Taurscripts from a flat personal bin collection into a documented, tested, and explicitly installable hybrid repository layout."
related_focus: []
related_roadmap: []
related_design:
  - "project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md"
  - "https://github.com/xenotaur/taurscripts"
work_items: []
execution_records: []
evidence: []
exit_criteria:
  - "The Taurscripts repository documents the distinction between source files, installed files, tests, documentation, and optional staging output."
  - "The floc and drq commands have repeatable tests covering their supported behavior and important failure cases."
  - "A manifest-driven installer supports a dry-run and installs the selected Taurscripts files into a temporary or user-selected home directory."
  - "The repository records which tools remain flat in bin/ and which tools have graduated to per-tool development directories."
  - "The adopted layout proposal and implementation evidence are linked before the workstream is closed."
---

## Purpose

This workstream coordinates the design, implementation, and validation needed to make Taurscripts maintainable as it grows beyond a small personal `~/bin` collection. It preserves `bin/` as the user-facing installation tree while creating room for tests, fixtures, documentation, dependency notes, and selective per-tool development areas.

The workstream exists now because commands such as `drq` and `floc` have enough behavior to require repeatable testing and documentation, while the repository does not yet have an explicit installer, test runner, or source/install boundary.

## Scope

- Document the Taurscripts repository layout and installation contract.
- Add tests and documentation for `floc` and `drq`.
- Add a manifest-driven installer with a safe dry-run mode.
- Define criteria for moving a command into `tools/<name>/`.
- Evaluate, but do not assume, a future generated staging tree.

## Prior Art Check

### Duplication search

- In-repo: No existing Taurscripts maintainability workstream or equivalent installation-layout artifact found.
- Sibling repos: No additional sibling implementation was identified beyond the Taurscripts target repository.
- External libraries: GNU Stow and chezmoi were considered as broader deployment patterns; neither is required for the initial workstream.
- Recommendation: Proceed.

### Demand search

- Work items: None found.
- Proposals: None found.
- Backlog: No matching Taurscripts maintainability or installation-layout entry found.
- Recommendation: No action.

## Work Items

The work items will be created as the workstream is planned. The initial candidate sequence is:

- Document the repository contract and classify current files.
- Add `floc` tests, fixtures, and command documentation.
- Add `drq` tests, fixtures, dependency notes, and documentation updates.
- Add an installation manifest and `scripts/install --dry-run`.
- Add temporary-home installation validation.
- Evaluate selective migration of complex commands into `tools/<name>/`.
- Evaluate whether a generated staging tree is justified.

## Exit Criteria

- The repository layout and installation contract are documented.
- `floc` and `drq` have repeatable tests with evidence of passing runs.
- The installer can show its changes without modifying the destination.
- Installation into an isolated temporary home has been validated.
- The final decision about per-tool directories and optional staging is recorded.
- The implementation work and evidence are linked to the adopted design proposal.

## Non-Goals

- Does not rewrite every existing Taurscripts command.
- Does not create a general-purpose dotfile management system.
- Does not require a package-manager release.
- Does not make generated `bin/` output authoritative before the installer and tests justify it.
- Does not broaden the scope to unrelated shell configuration cleanup.

## Relationship to Design

- Design proposal: `project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md`
- Target repository: `https://github.com/xenotaur/taurscripts`
- Existing Taurscripts installation assumptions: `~/bin` is sourced and added to `PATH` by the repository's shell configuration.

## Open Questions

- Whether the installer should initially target only `$HOME` or support arbitrary prefixes.
- Whether ShellCheck should be mandatory or optional for contributors.
- Which commands, beyond `floc` and `drq`, should graduate into per-tool directories.

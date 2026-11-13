---
id: PROP-TAURSCRIPTS-HYBRID-LAYOUT
type: design_proposal
title: "Taurscripts Hybrid Source and Installation Layout"
status: proposed
created_on: 2026-10-21
updated_on: 2026-10-21
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - "https://github.com/xenotaur/taurscripts"
  - "project/workstreams/proposed/WS-TAURSCRIPTS-MAINTAINABILITY.md"
---

## Summary

Taurscripts will use a hybrid repository layout that preserves `bin/` as the stable user-facing installation tree while providing per-tool development areas for commands that need substantial tests, fixtures, documentation, or multiple implementation files. Installation will be made explicit through a manifest-driven workflow before any generated `bin/` output is introduced.

## Background / Motivation

Taurscripts exists to maintain the contents of a Unix or macOS `~/bin` directory. Its current repository layout reflects that purpose: commands, shell libraries, dotfiles, and terminal configuration are kept under `bin/`, and shell startup files reference that installed location directly.

The repository now contains tools with different levels of complexity. Small commands can remain directly usable from `bin/`, while commands such as `drq` and `floc` need tests, fixtures, documentation, and dependency descriptions. A single flat tree does not provide a natural home for those materials, but replacing `bin/` with generated output would add build and installation complexity prematurely.

This proposal records a durable repository structure so later work can improve testing and installation without changing the meaning of the user-facing `~/bin` tree.

## Prior Art Check

### Duplication search

- In-repo: No existing Taurscripts layout proposal or workstream found.
- Sibling repos: `logical_robotics_harness` is the planning repository; no sibling implementation of this Taurscripts layout was identified.
- External libraries: GNU Stow and chezmoi provide broader dotfile deployment models, but no external library is required for the proposed manifest-driven installer.
- Recommendation: Proceed.

### Demand search

- Work items: None found.
- Proposals: None found.
- Backlog: No matching Taurscripts layout or installation entry found.
- Recommendation: No action.

## Design Decisions

### Decision 1: Preserve `bin/` as the stable installation tree

Options considered:

- Keep every source file directly under `bin/`.
- Make `bin/` disposable generated output.
- Keep `bin/` as the user-facing tree and add per-tool development areas selectively.

**Chosen: hybrid layout.**

`bin/` remains the place whose contents correspond to the files installed into `~/bin`. This preserves the repository's existing purpose and avoids breaking shell startup references.

### Decision 2: Add per-tool development areas only when needed

Complex tools may receive directories such as:

```text
tools/floc/
tools/drq/
```

These directories may contain tests, fixtures, README files, dependency notes, and eventually multiple implementation files. Small commands remain in `bin/` until their development needs justify migration.

### Decision 3: Introduce an explicit installation manifest

Installation will use an explicit manifest rather than copying every file below `bin/`. The manifest will distinguish commands, shell libraries, dotfiles, nested configuration, and manual pages.

A dry-run installer will be added before generated build output. It will target `$HOME` initially because the current shell configuration refers directly to `~/bin`.

### Decision 4: Defer generated staging output

A disposable `build/` tree may be added later if platform variants, packaging, or installation validation require it. Generated output will not be introduced as the primary source of truth while the repository remains a small interpreted-script collection.

### Decision 5: Add tests and documentation as first-class repository content

The repository will add a test command and per-tool tests for substantial utilities. Mature commands will receive manual pages or equivalent command documentation. Shell syntax and optional ShellCheck validation will be part of the repository checks.

## Non-Goals

- Does not turn Taurscripts into a general-purpose dotfile manager.
- Does not require every existing command to move into a `tools/` directory.
- Does not make `build/` generated output mandatory immediately.
- Does not define a package-manager formula for Homebrew, Debian, or another distribution.
- Does not promise support for shells other than those documented by each command.
- Does not replace the existing `~/bin` installation model.

## Implementation Plan

Implementation is coordinated by `WS-TAURSCRIPTS-MAINTAINABILITY` in the same reviewable planning change.

The expected sequence is:

1. Add repository documentation describing source, test, installation, and staging boundaries.
2. Add tests for `floc` and `drq`.
3. Add an explicit installation manifest and dry-run installer.
4. Add per-tool development directories for commands whose testing or documentation needs justify them.
5. Evaluate whether staged `build/bin` output is needed.
6. Close the workstream after the selected structure, tests, installer, and documentation are validated.

## Cross-References

- Workstream: `project/workstreams/proposed/WS-TAURSCRIPTS-MAINTAINABILITY.md`
- Target repository: `https://github.com/xenotaur/taurscripts`

## Open Questions

- Should the initial installer support only `$HOME` as its destination, or should it support an arbitrary installation prefix from the beginning?
- Should the first test runner use only Bash and standard Unix tools, or should ShellCheck be a required dependency?

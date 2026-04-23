# Logical Robotics Harness

An agentic harness for AI-assisted development developed for Logical Robotics.
The Logical Robotics Harness (LRH) is a reusable agentic harness for AI-assisted development.
LRH uses a literate development paradigm in which structured documentation is used to guide an
agentic development workflow based on explicitly collecting evidence of status and progress.

The core idea of LRH is to decouple the client's project state from the agentic harness code:

- the **harness** (`src/lrh/`) provides reusable orchestration, parsing, validation, evidence, status,
  and tool integration logic
- the **client project repository** contains its own `project/` directory describing its
  principles, goal, roadmap, focus, work items, actions, guardrails, evidence, and status
- **maintainer operational scripts** live in `scripts/`, including maintainer-only AI helpers in `scripts/aiprog/`

LRH is in its early stages, but the goal of this project is to point it at a target repository,
load that repository's `project/` control plane, iterate with a human to define a project roadmap,
and then help orchestrate work to achieve that roadmap in a structured and inspectable way.

## Current status

This repository now has a working control-plane baseline (`lrh validate`) and assist CLI entrypoints
(`lrh request`, `lrh snapshot`, `lrh survey`). Current planning emphasis is on packaging/runtime hardening for assist templates so installed-package usage does not depend on repository-relative paths.

## Planned top-level structure

```text
logical_robotics_harness/
  README.md
  AGENTS.md
  pyproject.toml
  src/
    lrh/
  tests/
  scripts/
    aiprog/
  project/
```

## Intended first implementation slice

The first useful workflow should be:

```bash
lrh validate
```

run inside this repository, where LRH validates its own `project/` directory.

For top-level CLI discovery, both of these are supported:

```bash
lrh --help
lrh help
```

## Design summary

The control model for a project is:

- **Intent Plane**: Principles → Project Goal → Roadmap
- **Execution Plane**: Current Focus → Work Items → Actions
- **Truth Plane**: Evidence → Status
- **Consequences Plane**: Guardrails (Safety, Cost, Optics, Approvals)

These should exist as:

1. human-readable Markdown files with YAML frontmatter
2. structured runtime objects inside `src/lrh/`

### Action lifecycle

Execution should follow this lifecycle:

**Work Item → Action Proposal → Guardrail Review → Action Decision → Execution → Evidence → Status**

This keeps execution explicit while separating consequence checks from intent and truth.

### Work-item status buckets

Work items are organized under `project/work_items/proposed/`, `active/`, `resolved/`, and `abandoned/`.
The YAML frontmatter `status` is authoritative, and directory bucket is derived for human readability.
`blocked` is modeled as secondary metadata on `active` items, not as a top-level lifecycle status.


## Near-term priorities

- package-owned template location and package-resource loading for assist workflows
- packaging/build/install hardening with installed-package smoke checks
- canonical survey command surface: `lrh survey <root> [--tests-root ...] [--format md|json] [--out ...]`
- package-owned survey implementation at `src/lrh/assist/sourcetree_surveyor.py` with legacy wrapper at `scripts/aiprog/sourcetree_surveyor.py`
- `--format json` now emits a stable survey contract (`schema_version: 1.0`) with source-tree inventory facts for follow-on audit/context workflows
- Meta CLI MVP now includes `lrh meta init`, `lrh meta register`, `lrh meta list`, and `lrh meta where` for setup, registry write/read, and active workspace inspection
- `lrh meta register` now applies deterministic Phase 1 metadata inference for URL/path locators (prefers repository identity over generic tails like `/project`) while remaining offline and override-friendly
- Meta workspace behavior now follows a three-mode model for `lrh meta`: `hybrid` (default), `local`, and `global`; hybrid uses a local/shareable catalog root with global/XDG config/state/cache/private paths
- Workspace-configured paths are persisted as normalized absolute paths, and `lrh meta where` is the primary visibility/diagnostics surface for resolved workspace context

See `project/design/architecture.md`, `project/design/repository_spec.md`, `project/roadmap/phase_02_runtime_and_workspace.md`, `project/work_items/active/WI-META-CLI-MVP.md`, and the `project/` directory for the current seed design.

# Logical Robotics Harness

An agentic harness for AI-assisted development developed for Logical Robotics. 
The Logical Robotics Harness (LRH) is a reusable agentic harness for AI-assisted development.
LRH uses a literate development paradigm in which structured documentation is used to guide a
an agentic development workflow based on explicitly collecting evidence of status and progress.

The core idea of LRH is to decouple the client's project state from the agentic harness code:

- the **harness** (`lrh/`) provides reusable orchestration, parsing, validation, evidence, status,
  and tool integration logic
- the **client project repository** contains its own `project/` directory describing its
  principles, goal, roadmap, focus, work items, evidence, and status

LRH is in its early stages, but the goal of this project is to point it at a target repository,
load that repository's `project/` control plane, iterate with a human to define a project roadmap,
and then help orchestrate work to achieve that roadmap in a structured and inspectable way.

## Current status

This repository is in bootstrap mode. The immediate goal is to define the repository structure, 
the `project/` schema, and the first implementation slice for `lrh validate`.

## Planned top-level structure

```text
logical_robotics_harness/
  README.md
  AGENTS.md
  pyproject.toml
  docs/
  lrh/
  tests/
  project/
```

## Intended first implementation slice

The first useful workflow should be:

```bash
lrh validate
```

run inside this repository, where LRH validates its own `project/` directory.

## Design summary

The control stack for a project is:

**Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status**

These should exist as:

1. human-readable Markdown files with YAML frontmatter
2. structured runtime objects inside `lrh/`

## Near-term priorities

- define the `project/` repository convention
- implement the core control-model classes
- implement parsing/loading/resolution
- add a validation CLI

See `docs/architecture.md`, `docs/repository_spec.md`, and the `project/` directory for the current seed design.

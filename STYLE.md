# LRH Style Guide

This document defines the coding, packaging, and contribution conventions for the Logical Robotics Harness (LRH) project.

Its purpose is to make the codebase easier to read, review, maintain, and extend, while keeping pull requests narrow and low-noise.

## Order of Precedence

When there is any ambiguity or conflict, use the following order of precedence:

1. Project-specific LRH conventions in this document
2. Passing unit tests
3. Ruff lint compliance
4. Black formatting compliance
5. Google Python Style Guide
6. PEP 8 for issues not otherwise covered

The project-specific conventions in this document take precedence over more general style guidance.

## General Principles

Code in LRH should favor:

- clarity over cleverness
- explicitness over implicitness
- small, reviewable changes over broad rewrites
- consistency across the repository
- minimal semantic diffs

Contributors should avoid introducing unnecessary churn in files that are otherwise unrelated to the task at hand.

## Change Scope and Pull Request Discipline

Changes should be narrowly scoped to the task being performed.

Do not modify code that is unrelated to the change at hand merely to “clean it up,” “modernize it,” or “make it prettier.” This is especially important for AI-assisted edits.

Examples of changes that should generally be avoided unless they are directly required by the task:

- reformatting unrelated files
- changing imports in unrelated modules
- renaming unrelated variables or functions
- rewriting working code for stylistic reasons alone
- moving code between files without task-specific justification

If a file must be touched for a real reason, keep unrelated edits in that file to an absolute minimum.

When a change would benefit from broader cleanup, that cleanup should usually be proposed as a separate follow-up change.

## Python Version and Environment

LRH should use a clearly documented Python version and a reproducible development setup.

Project tooling should work from the documented project root. Development dependencies should be installable in a standard way, preferably via `pyproject.toml`.

## Imports

### Core Import Policy

LRH prefers importing modules and submodules rather than importing individual members into the local namespace.

Preferred:

```python
from logical_robotics_harness import planner
from logical_robotics_harness.utils import file_ops
```

Then refer to members through the imported module:

```python
planner.make_plan(...)
file_ops.atomic_write(...)
```

Generally disallowed:

```python
from logical_robotics_harness.planner import make_plan
from logical_robotics_harness.utils.file_ops import atomic_write
```

The goal is to keep symbol origins explicit and reduce namespace ambiguity.

### Relative Imports

Dot-relative imports such as the following are not allowed by default:

```python
from . import planner
from ..utils import file_ops
```

If a dot-relative import is truly necessary, it must be accompanied by a brief explanatory comment documenting why it is required.

This should be treated as an exception, not a normal practice.

### Import Grouping and Layout

Imports should follow standard grouping:

1. standard library imports
2. third-party imports
3. local package imports

Imports should normally appear at the top of the file.

Prefer one import per line unless a grouped import is clearly more readable and remains compliant with tooling.

### Allowed Common Exceptions

Common widely accepted alias imports are allowed where they improve readability, for example:

```python
import numpy as np
import pandas as pd
```

These should remain conventional and unsurprising.

## Naming and Readability

Use descriptive names. Avoid cryptic abbreviations unless they are standard in the domain.

Names should make code easier to understand without requiring the reader to inspect distant context.

Public names, internal helper names, test names, and script names should all favor clarity and consistency.

## Docstrings and Comments

Use docstrings for public modules, classes, and functions where helpful.

Comments should explain:

- why something is done
- assumptions
- constraints
- non-obvious behavior
- documented exceptions to normal project rules

Comments should not restate obvious code.

A special case where comments are expected is when using an exception to a normal project convention, such as a necessary dot-relative import.

## Testing

All substantive code changes should be covered by tests where practical.

At minimum:

- existing unit tests must pass
- new behavior should include tests when feasible
- bug fixes should include regression tests when feasible

LRH prefers predictable, automatable tests that can be run from the command line through the project’s scripts.

The canonical project test entry point should be:

```bash
scripts/test
```

If additional arguments or modes are supported, they should be documented in the scripts documentation.

## Linting

LRH uses Ruff for linting.

Code merged into the repository should pass Ruff lint checks.

The canonical project lint entry point should be:

```bash
scripts/lint
```

Lint fixes should generally be limited to code relevant to the task, unless the work is explicitly a lint cleanup change.

## Formatting

LRH uses Black for formatting.

The canonical project formatting entry point should be:

```bash
scripts/format
```

Formatting-only changes should normally be kept separate from semantic code changes when practical.

Do not perform opportunistic formatting of unrelated files.

## Tool Responsibilities

The intended division of labor is:

- tests verify correctness
- Ruff verifies lint and code-quality rules
- Black enforces formatting

Avoid overlapping or conflicting tool configurations when possible.

## Packaging and Project Structure

LRH should maintain a clear package structure and a reproducible installation path for development.

Where practical:

- package metadata and tool configuration should live in `pyproject.toml`
- development and test dependencies should be documented and installable
- scripts should provide stable entry points for common developer tasks

If the repository adopts CI workflows, they should use the same commands developers are expected to run locally.

## Scripts

The `scripts/` directory provides the standard developer entry points for common tasks.

At minimum, contributors should be able to run:

```bash
scripts/test
scripts/lint
scripts/format
```

These scripts should remain simple, reliable wrappers around the project’s canonical tooling.

They should be preferred over ad hoc local command variants when contributing to the repository.

## Continuous Integration

CI should enforce the same standards expected locally.

At minimum, CI should check:

- unit tests
- Ruff linting
- Black formatting checks

CI configuration should prefer explicit versions and reproducible commands to reduce local-versus-CI drift.

## AI-Assisted Contributions

AI tools such as Codex, ChatGPT, or similar systems may be used to help generate or edit code, but their output must follow this style guide.

AI-assisted changes must follow these additional rules:

- do not modify code unrelated to the task
- do not create broad cleanup diffs unless explicitly asked
- do not rewrite working code unnecessarily
- do not introduce speculative refactors without justification
- prefer small, reviewable changes
- preserve existing behavior unless the task requires changing it
- when uncertain, report the issue rather than guessing

AI-generated pull requests should be especially careful to minimize noise.

## Review Guidance

Reviewers should evaluate changes in this order:

1. Is the change in scope?
2. Does it preserve or improve correctness?
3. Do tests pass?
4. Does it follow LRH conventions?
5. Does it pass lint and formatting?
6. Is the diff readable and appropriately narrow?

A change may be technically correct but still require revision if it creates unnecessary review noise.

## Exceptions

Exceptions to this guide are allowed when justified by technical constraints, packaging realities, testing requirements, or other concrete reasons.

Exceptions should be:

- rare
- documented
- minimal
- local to the relevant code

Do not treat exceptions as precedent unless they are later incorporated into this document.

## Practical Developer Workflow

Before submitting changes, contributors should normally:

```bash
scripts/test
scripts/lint
scripts/format
```

If formatting changes are produced, review them to ensure they are limited to files relevant to the task.

Before opening a PR, contributors should confirm that:

- the change is scoped correctly
- tests pass
- lint passes
- formatting passes
- unrelated code was not modified unnecessarily

## Summary

In LRH, we value:

- explicit module-oriented imports
- passing tests
- lint cleanliness
- consistent formatting
- small, low-noise diffs
- disciplined, reviewable pull requests

When in doubt, prefer the change that is clearer, narrower, and easier to review.

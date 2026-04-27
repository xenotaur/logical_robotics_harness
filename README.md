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

For package version reporting, both of these are supported (resolved via installed package metadata):

```bash
lrh --version
lrh version
```

## Developer sandbox helper

Use `scripts/sandbox` when you want to test LRH CLI behavior without touching your real
home directory, config, state, or cache paths. This is a developer-behavior sandbox only;
it is **not** an OS/container security sandbox.

Interactive usage:

```bash
scripts/sandbox
lrh meta init --mode hybrid
lrh meta where
```

Non-interactive passthrough usage (preferred for CI/agents):

```bash
scripts/sandbox --cleanup -- python -m lrh.cli.main meta init --mode hybrid
scripts/sandbox --cleanup -- python -m lrh.cli.main meta where
```

## Testing tiers

Use the standard script entry points:

```bash
scripts/test     # fast unit/regression suite
scripts/smoke    # heavyweight build/install/package smoke checks
```

Unit tests are expected to stay fast, deterministic, and hermetic; smoke coverage is where install/build/package behavior should run.

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
- setuptools-scm-backed dynamic versioning via package metadata
- canonical survey command surface: `lrh survey <root> [--tests-root ...] [--format md|json] [--out ...]`
- package-owned survey implementation at `src/lrh/assist/sourcetree_surveyor.py`
- `--format json` now emits a stable survey contract (`schema_version: 1.0`) with source-tree inventory facts for follow-on audit/context workflows
- Meta CLI MVP now includes `lrh meta init`, `lrh meta register`, `lrh meta list`, `lrh meta where`, and `lrh meta inspect` for setup, registry write/read, active workspace inspection, and truth-first single-record inspection
- `lrh meta where` is the primary workspace diagnostics command and reports resolved mode/source plus config/catalog/projects/state/cache paths (including local vs global/private scope distinctions)
- integration tests now cover the full `lrh meta init -> list -> register -> list` flow across `local`, `global`, and `hybrid` workspace modes using isolated HOME/XDG roots
- `lrh meta register` now applies deterministic Phase 1 metadata inference for URL/path locators (prefers repository identity over generic tails like `/project`) while remaining offline and override-friendly
- `lrh meta` locator model is split intentionally: `repo_locator` is the repository/ref locator, while `project_dir` is the relative path from that locator to the LRH project-control directory
- for GitHub tree URLs (for example `.../tree/main/project`), `meta register` now derives default registry/short/display names from the repository slug and, by default, normalizes stored `repo_locator` to `.../tree/<ref>` while storing `project_dir` as the tail path identity; when an explicit `--project-dir` override is provided, that normalization is intentionally skipped
- example normalization: `lrh meta register https://github.com/xenotaur/taurworks/tree/master/project` is stored as `repo_locator: https://github.com/xenotaur/taurworks/tree/master` plus `project_dir: project`
- `setup_state` semantics are now truth-first: local-path locators are checked as `lrh_project_present` vs `not_set_up`; remote URL locators are not treated as `not_set_up` by default and remain `not_checked` unless explicit remote probing is implemented
- Meta workspace behavior now follows a three-mode model for `lrh meta`: `hybrid` (default), `local`, and `global`; hybrid uses a local/shareable catalog root with global/XDG config/state/cache/private paths
- Workspace-configured paths are persisted as normalized absolute paths, and `lrh meta where` is the primary visibility/diagnostics surface for resolved workspace context
- `lrh meta register` and `lrh meta list` operate against the same resolved workspace context (`projects_dir`) used by `lrh meta where`, across hybrid/local/global modes
- `lrh meta init` now defaults to `hybrid`; in hybrid mode, an optional positional directory (or `--workspace-root`) sets the catalog/workspace root

See `project/design/architecture.md`, `project/design/repository_spec.md`, `project/roadmap/phase_02_runtime_and_workspace.md`, `project/work_items/active/WI-META-CLI-MVP.md`, and the `project/` directory for the current seed design.

## Prompt workflow guidance

For meaningful prompt-driven changes, LRH provides lightweight prompt traceability guidance in `PROMPTS.md`.

Helper scripts:

- `scripts/prompts/label-prompt`
- `scripts/prompts/record-execution`
- `scripts/version` (plus `tools`, `verify`, `tag`, `push` subcommands for release workflow checks)

Execution records are stored under `project/executions/` and may be grouped by work item or `AD_HOC`.

## Release workflow

LRH package versions are derived from Git tags via `setuptools-scm` (`pyproject.toml` has `dynamic = ["version"]`).
Release tags should use:

```text
vMAJOR.MINOR.PATCH
```

Minimal release flow:

```bash
scripts/version tools
scripts/version verify vX.Y.Z
scripts/version tag vX.Y.Z
scripts/version push vX.Y.Z
python -m build
```

- `setuptools-scm` resolves a release tag like `v1.2.3` to package version `1.2.3`; untagged builds may include additional local version metadata.
- `scripts/version verify` validates release preconditions (clean tree, lint, format check, tests).
- `scripts/version tag` verifies release preconditions before creating a new tag; if the requested tag already exists at `HEAD`, it returns without re-running verification.
- `scripts/version push` pushes the tag to `origin` and is idempotent when local/remote tags already match.
- `python -m build` builds sdist/wheel using the version resolved by `setuptools-scm` from the current tag context.

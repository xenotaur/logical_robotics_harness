# Logical Robotics Harness

A structured harness for evidence-backed, AI-assisted development workflows.
The Logical Robotics Harness (LRH) is reusable project-control tooling for human-guided assist workflows.
LRH uses a literate development paradigm in which structured documentation is used to guide
work based on explicitly collecting evidence of status and progress.

The core idea of LRH is to decouple the client's project state from the reusable harness code:

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

Design proposal lifecycle buckets can be previewed and applied with:

```bash
lrh design organize
lrh design organize --apply
```

Proposal frontmatter `status` is authoritative; path buckets under
`project/design/proposals/` are derived for human readability, while
proposal-set relative paths are preserved within those buckets.

## User installation

Once LRH is published on PyPI, the preferred normal installation path for the
standalone CLI is:

```bash
pipx install lrh
```

`pipx` keeps the `lrh` command in an isolated application environment while making
the command available on your shell path. Use this path when you primarily want to
run the LRH CLI against a repository.

Use `pip install lrh` when LRH needs to be available inside an existing Python
environment, such as library use, CI jobs, development environments, or tools that
intentionally manage their own virtual environment:

```bash
pip install lrh
```

The default `lrh` distribution is the safe-default CLI/toolkit package: it does not
include LRH's autonomous execution package or autonomous-loop commands. This is a
packaging boundary, not an OS/container sandbox guarantee. Future agentic install
forms such as `pipx install "lrh[agentic]"` should only be used once the `agentic`
extra and any backing `lrh-agentic` package actually exist.

## Command-line Completion

LRH supports optional shell completion via `argcomplete` for the existing `argparse` CLI.

Install the completion extra first:

```bash
pip install -e ".[completion]"
```

### Enable (bash)

```bash
eval "$(register-python-argcomplete lrh)"
```

### macOS note

Use these checks when troubleshooting:

```bash
echo "$BASH_VERSION"
which bash
echo "$SHELL"
```

- `echo "$BASH_VERSION"` reports the version of the shell you are running right now.
- `which bash` reports which `bash` binary a *new* `bash` command would resolve from `PATH`.
- On macOS, `/bin/bash` is often 3.2 and too old for first-class global bash completion workflows; contributors who prefer bash completion can use Homebrew bash and launch that shell session before evaluating argcomplete registration.

### Enable (zsh)

If your `argcomplete` version supports zsh registration, use:

```bash
eval "$(register-python-argcomplete --shell zsh lrh)"
```

### fish and PowerShell (best-effort notes)

LRH currently documents and validates `argcomplete` setup primarily for bash/zsh. fish and PowerShell users can still run LRH normally, but completion behavior may depend on shell-specific wrappers outside this repository and is not currently guaranteed by LRH tests.

### Expected completion behavior

```text
lrh s<TAB>       # snapshot, survey
lrh ver<TAB>     # version
lrh request <TAB>
lrh request codex_prompt_from_work_item WI-<TAB>
```

Work-item completion discovers IDs from both flat and nested layouts under
`project/work_items/` (for example `project/work_items/*.md` and
`project/work_items/**/*.md`). For each candidate file it prefers frontmatter
`id`, then falls back to a `WI-*` H1 heading, then to a `WI-*` filename stem.

### Troubleshooting

- Confirm completion dependencies are installed: `pip install -e ".[completion]"`.
- Confirm shell registration was evaluated in your current shell session.
- On macOS, confirm your running shell is not `/bin/bash` 3.2 when expecting bash completion behavior.
- Project-aware completions (for example work-item IDs) may return no matches when you are outside an LRH project root because `lrh request` completions currently discover projects from the current repository context.
- If no work items are found, run `lrh work-items organize --dry-run` to inspect/repair legacy layouts.


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

## Reconciled local, CI, and agent validation workflow

For any given commit, LRH expects `scripts/format`, `scripts/lint`, and `scripts/test` to produce the same outcome across local development, GitHub Actions, Codex Cloud, Claude Code, and comparable coding-agent environments.

### Canonical setup

```bash
scripts/develop
```

`scripts/develop` is the canonical setup entrypoint for the constrained editable development install.
This applies equally to local virtualenv/Conda setups and to agent environments that bootstrap from repository scripts.

### Canonical local validation

```bash
scripts/version tools
scripts/check-workflows
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

If `scripts/version tools` reports `lrh unknown` for package metadata or the CLI, treat its install hint as a setup diagnostic: run `scripts/develop` from the repository root, then rerun `scripts/version tools` before continuing validation.

### Repair workflow (when checks fail)

```bash
scripts/format
scripts/lint --fix
scripts/lint
scripts/format --check --diff
scripts/test
lrh validate
```

After mutating commands (for example `scripts/format` or `scripts/lint --fix`), inspect the resulting changes before committing:

```bash
git diff
```

When editing GitHub Actions workflows, run:

```bash
scripts/check-workflows
```

This validates workflow YAML syntax locally and is also run by Meta CI. Deeper GitHub Actions semantic linting (for example `actionlint`) is intentionally deferred. For reusable setup, debugging, and hardening guidance across heterogeneous repositories, see the [CI setup and debugging playbook](docs/project-setup/ci.md).

### Agent workflow rules

- Agents should use project scripts (`scripts/format`, `scripts/lint`, `scripts/test`) as the source of truth, not direct `black`/`ruff` command substitutions.
- Direct `black`/`ruff` invocations are diagnostics only and must not replace script-based validation evidence.
- Agents should not manually rewrap code to satisfy Black; run the formatter and review the output.
- Agents should not claim “pre-existing drift” or “cannot reproduce” without command evidence.

### Debug evidence checklist

When behavior differs across environments, collect and share:

```bash
git rev-parse HEAD
git status --short
scripts/version tools
scripts/check-workflows
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

### Environment notes

- **Local (venv/Conda):** install dev dependencies with constraints and run script entry points from repository root.
- **GitHub Actions:** should run the same script entry points so CI status maps directly to local checks.
- **Codex Cloud:** use repository scripts for validation and include command output in change summaries.
- **Claude Code and comparable agents:** follow the same script-first workflow and provide concrete command evidence for any reproducibility claims.

CI usage:

- pull-request and main-branch fast validation includes `scripts/test`, `scripts/format --check --diff`, `scripts/lint`, and `lrh validate`
- pull-request and main-branch coverage feedback runs `scripts/coverage --html`
- smoke validation runs `scripts/smoke` in the dedicated **Smoke validation** workflow (manual dispatch, weekly schedule, and tag pushes matching `v*`, including semantic-version release tags such as `v1.2.3`)
- release-tag validation runs in the dedicated **Release tag validation** workflow on pushed tags matching `v*.*.*`; those release-tag pushes also trigger **Smoke validation**. It runs `scripts/version verify "$TAG_UNDER_TEST"`, runs `scripts/release-smoke "$TAG_UNDER_TEST"`, and uploads build/smoke artifacts for audit trails


## Codex Cloud environment reconciliation

Codex Cloud can occasionally reuse cached environments with stale tool versions.
When this happens, script-based validation correctly fails version gates (for example Black or Ruff required-version checks), but formatter debugging should not start until setup is reconciled.

### Required setup sequence

Run this during Codex environment setup/bootstrap (not routinely during ordinary task-phase validation):

```bash
python -m pip install --upgrade pip
scripts/develop
```

### Required task-phase validation sequence

Start by verifying tool versions:

```bash
scripts/version tools
```

If Black/Ruff versions match repository expectations, run:

```bash
scripts/format --check --diff
scripts/lint
scripts/test
```

If versions are missing/mismatched, report a setup/cache mismatch and stop formatter debugging until setup/cache is reconciled.
If canonical validation fails with missing-install/import errors (for example `ModuleNotFoundError: lrh`), report a setup/bootstrap mismatch instead of a code regression.

### Common mismatch symptoms

- Black required-version failures
- Ruff required-version failures

### Resolution steps

1. Ensure your setup flow includes `scripts/develop` (canonical environment setup).
2. Re-run setup and then `scripts/version tools`.
3. If mismatches persist in Codex Cloud, reset the Codex Cloud environment cache.
4. Re-run validation commands only after setup/version checks succeed.

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

To conservatively repair legacy flat work-item files and normalize bucket placement, use:

```bash
lrh work-items organize --project-root . --dry-run
lrh work-items organize --project-root . --check
lrh work-items organize --project-root . --apply
lrh work-items validate --project-root .
lrh validate
```

`lrh work-items organize` defaults to preview behavior (non-mutating unless `--apply` is provided),
adds missing frontmatter only when a work-item ID can be inferred reliably, and defaults ambiguous
status inference to `proposed` with warnings. This command repairs organization/frontmatter but does
not replace full project validation (`lrh validate`).

`lrh work-items validate` is read-only and reports work-item hygiene diagnostics
(malformed/missing frontmatter, ID/status issues, duplicates, bucket mismatches,
and consistency warnings). Flat legacy files under `project/work_items/*.md` are
reported as warnings for compatibility, not errors.

### Workstream status buckets

Workstreams are organized under `project/workstreams/proposed/`, `active/`, `resolved/`, and
`abandoned/`. Workstream frontmatter `status` is authoritative; bucket placement is a human-facing
navigation projection.

To preview or explicitly repair status-bucket drift without rewriting workstream metadata, use:

```bash
lrh workstreams organize --project-root . --dry-run
lrh workstreams organize --project-root . --check
lrh workstreams organize --project-root . --apply
lrh validate
```

`lrh workstreams organize` defaults to preview behavior (non-mutating unless `--apply` is provided),
reports invalid workstream metadata and destination conflicts instead of guessing, and does not edit
workstream frontmatter, IDs, stages, relationships, or content.


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

## Open design proposals

Longer-form design proposals — proposed but not yet adopted into
the canonical design documents above — live under
`project/design/proposals/`. Each proposal set has its own
subdirectory, an umbrella `00_proposal.md`, and one or more
sub-proposals or appendices.

Currently open:

- `project/design/proposals/proposed/workstream-execution-framework/` —
  proposes adding a typed `workstream` artifact between focus and
  work_items, with a six-layer execution stack (control plane →
  templates → orchestration → agent runtime →
  observability+evidence → MCP bridges) and a Pass-B worked-example
  appendix walking `WS-LCATS-CORPORA-ANALYSIS` end-to-end. Status:
  `proposed`. See `project/design/proposals/README.md` for the
  proposals area conventions.

## Prompt workflow guidance

For meaningful prompt-driven changes, LRH provides lightweight prompt traceability guidance in `PROMPTS.md`.

Helper scripts:

- `scripts/prompts/label-prompt`
- `scripts/prompts/record-execution`
- Installed CLI: `lrh prompt check-execution`
- Installed CLI: `lrh match executions <prompt-file>`
- Installed CLI: `lrh search executions <query>`
- `scripts/version` (plus `tools`, `verify`, `tag`, `push` subcommands for release workflow checks)

Execution records are stored under `project/executions/` and may be grouped by
work item or `AD_HOC`. They provide a lightweight, reviewable audit trail for
meaningful prompt-driven work: which prompt ran, what status it reached, and
what evidence or follow-up notes were captured.

Use the prompt lookup commands by role:

```bash
lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .
lrh match executions prompts/my_prompt.md --project-root .
lrh search executions "PROMPT_EXECUTION_SEARCH" --project-root .
lrh search executions "release smoke" --project-root .
lrh search executions "AD_HOC" --project-root .
lrh search executions "PROMPT(" --status landed --work-item AD_HOC --project-root .
```

Use `lrh prompt check-execution --prompt-id <PROMPT_ID>` before prompt-driven
work to apply authoritative exact soft idempotence checks in human and agent
workflows. If you have a prompt file rather than a copied ID, use
`lrh match executions <prompt-file>` for exact prompt ID extraction and matching.
Use `lrh search executions <query>` for exploratory local substring search over
execution-record frontmatter and body text during discovery, auditing, and
debugging. Exploratory search is useful context, but exact `prompt_id` matching
remains authoritative for rerun and soft-idempotence decisions.

A practical recent-prompt dogfooding flow is:

1. copy the full `PROMPT(...)` identifier into `PROMPT_ID`;
2. run `lrh prompt check-execution --prompt-id "$PROMPT_ID" --project-root .`;
3. if working from a saved prompt file, run `lrh match executions <file>` as a
   convenience check that extracts and exactly looks up prompt IDs;
4. use `lrh search executions "<distinctive prompt text>" --project-root .` only
   for surrounding context, such as finding related failed attempts, validation
   notes, or prior `AD_HOC` records.

For deeper design context, see
`project/design/proposals/adopted/prompt-execution-search-and-match/`.

## Release workflow

LRH releases are validated with the repository release scripts and published
from version tags using the staged, publish-last workflow documented in
`docs/release.md`.

See [`docs/release.md`](docs/release.md) for the canonical maintainer release
runbook, including local readiness checks, installed-wheel smoke testing,
TestPyPI rehearsal, PyPI Trusted Publisher setup, tag-push publishing,
post-release verification, failure recovery notes, and release evidence.


## Assist request catalog

Use the request catalog to discover supported assist request names before rendering a prompt:

```bash
# List canonical request names grouped by category.
lrh request list

# Limit the list to one category.
lrh request list --category review

# Show canonical metadata, legacy names, template source, and usage notes.
lrh request describe prompt-from-work-item
lrh request describe codex_prompt_from_work_item
```

Canonical flat names such as `prompt-from-work-item` are preferred for new usage. Legacy template names remain supported and can be inspected with `lrh request describe <legacy-name>`. The request names `list` and `describe` are reserved for catalog discovery commands, so avoid using those names for request-template overrides.

## GitHub review helpers

LRH includes a GitHub CLI integration for PR comment/thread inspection and assist request generation for review responses.

### `lrh github` commands

```bash
# Read PR issue/review comments.
lrh github comments https://github.com/owner/repo/pull/123
lrh github comments owner/repo 123

# Read review threads in human-readable mode or deterministic JSON.
lrh github threads https://github.com/owner/repo/pull/123 --state all --mode review
lrh github threads owner/repo 123 --state unresolved --mode raw

# Shortcut for unresolved review threads only.
lrh github unresolved https://github.com/owner/repo/pull/123
lrh github unresolved owner/repo 123
```

Notes:

- `comments` uses REST comments endpoints.
- `threads` and `unresolved` use GraphQL review threads.
- `unresolved` is equivalent to `threads --state unresolved`.
- `--mode review` (default) renders a readable review view; `--mode raw` emits deterministic JSON.
- `--show-pr` is on by default; use `--no-show-pr` to hide PR header lines.

### `lrh request review_response`

Use the assist template to generate a review-response drafting prompt from unresolved review threads:

```bash
# Use a PR URL.
lrh request review_response https://github.com/owner/repo/pull/123

# Force full prompt emission even when unresolved threads are empty.
lrh request review_response --force https://github.com/owner/repo/pull/123

# Save the generated prompt to a file for later use.
lrh request review_response https://github.com/owner/repo/pull/123 > /tmp/review_response_prompt.md

# Feed the generated prompt directly into a file-backed workflow.
lrh request review_response https://github.com/owner/repo/pull/123 | tee /tmp/review_response_prompt.md
```

This command emits the full prompt when unresolved threads exist. If there are no unresolved threads, it prints a concise "Nothing to resolve" success message by default; pass --force to emit the full prompt anyway.
### Project bootstrap templates

Start with diagnostics before scaffolding:

```bash
lrh project doctor --project-root /path/to/repo
```

Use package-owned bootstrap templates to initialize LRH-compatible scaffolding in any repository:

```bash
lrh project init --profile minimal
lrh project init --profile prompt-workflow
lrh project init --profile full
```

Safety controls:

- `--project-root <path>` target repo root
- `--dry-run` preview files without writing
- `--check` exit non-zero when files are missing/outdated
- `--force` allow overwriting existing files

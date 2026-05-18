# CI Setup and Debugging Playbook

## Purpose

Use this playbook when setting up, assessing, repairing, or hardening continuous integration for LRH or another repository. It is meant for humans and agents working together: preserve each repository's conventions, make validation reproducible, and require evidence before declaring CI healthy, flaky, or unreproducible.

This is a how-to guide, not a universal workflow template. Prefer small repository-specific improvements over forcing every project onto one package manager, runtime, container, or generated CI file.

## 1. Discover the project family

Start by naming the project family, because good CI follows the repository's shape:

- **Python package/tool**: `pyproject.toml`, installable package, console scripts, wheel/sdist checks.
- **Python script/tool collection**: scripts without package metadata, often shell entrypoints plus lightweight tests.
- **Unix command/tool repository**: shell, POSIX utilities, Make targets, CLI smoke tests, platform assumptions.
- **Rust/Cargo**: `Cargo.toml`, workspace layout, `cargo fmt`, `cargo clippy`, `cargo test`.
- **Rust/WASM/WebGPU**: Rust plus browser, GPU, shader, WASM-pack, or headless-render constraints.
- **JavaScript/TypeScript**: `package.json`, package-manager lockfile, build/lint/test scripts.
- **Game or simulation**: engine version, assets, deterministic seeds, headless test mode, screenshot or replay evidence.
- **Documentation/static site**: Markdown checks, link checks, site build, publish preview.
- **Mixed repository**: more than one family; CI should make each validation lane explicit.

If the family is mixed, avoid hiding everything behind one opaque command. Use clear job and step names so reviewers can see which stack failed.

## 2. Inventory existing commands and policy files

Before editing workflows, inspect the repository's source of truth:

- `README.md` and docs indexes for setup, validation, and release guidance.
- `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, `REVIEWS.md`, or equivalent agent/review policy files.
- `scripts/`, `bin/`, `tools/`, `Makefile`, `justfile`, or other command wrappers.
- `pyproject.toml`, `requirements*.txt`, `constraints*.txt`, `tox.ini`, `noxfile.py`, or package metadata.
- `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, and workspace manifests.
- `package.json`, lockfiles, and package-manager configuration.
- Existing `.github/workflows/*.yml` and `.github/workflows/*.yaml` files.

Record the canonical commands you find. If the repository already has wrapper scripts, CI should usually call those scripts rather than raw tool commands.

## 3. Define canonical command categories

Every CI setup should make these command categories explicit, even if some are intentionally not applicable:

| Category | Purpose | LRH example |
| --- | --- | --- |
| Setup/bootstrap | Install the repository's development environment. | `scripts/develop` |
| Tool/version report | Show runtime and tool versions before validation. | `scripts/version tools` |
| Workflow YAML check | Catch malformed workflow files early. | `scripts/check-workflows` |
| Format check | Verify formatting without mutating files. | `scripts/format --check --diff` |
| Format fix | Apply formatter changes locally, then review the diff. | `scripts/format` |
| Lint check | Run static checks without broad rewrites. | `scripts/lint` |
| Lint fix | Apply safe lint fixes locally, then rerun checks. | `scripts/lint --fix` |
| Tests | Run the normal deterministic test suite. | `scripts/test` |
| Coverage | Produce coverage evidence when meaningful. | `scripts/coverage --html` |

For another repository, replace the LRH examples with that repository's own commands. If no canonical command exists, add the smallest wrapper that gives humans and CI the same entrypoint.

## 4. Separate setup phase from validation phase

Do not debug format, lint, or test failures until setup is known to be correct.

**Setup/bootstrap phase** installs dependencies, prepares toolchains, restores caches, and may use network access. In LRH, Codex Cloud and similar environments should run `scripts/develop` during environment setup/bootstrap, not as a routine task-phase validation step.

**Validation phase** should be repeatable and evidence-producing. Start with tool versions, then run checks:

```bash
scripts/version tools
scripts/check-workflows
scripts/format --check --diff
scripts/lint
scripts/test
```

If tool versions are missing or mismatched, report a setup/cache issue first. Do not hand-edit formatting or chase linter drift until the version report matches repository expectations.

## 5. Make tool versions reproducible

CI should make tool drift visible and boring:

- Pin or constrain formatters, linters, test frameworks, language runtimes, and package managers where reproducibility matters.
- Prefer checked-in constraints, lockfiles, `rust-toolchain.toml`, `.python-version`, `.node-version`, or equivalent project-owned version declarations.
- Add required-version checks for high-churn tools when a mismatch would cause noisy diffs.
- Emit version evidence near the start of CI logs.
- Treat stale agent or CI caches as setup failures, not as formatter or linter regressions.

Version evidence is part of debugging. A claim that a failure cannot be reproduced is incomplete without commit, status, and tool-version output.

## 6. Design GitHub Actions workflows for reviewability

Use workflow structure that maps clearly to local validation:

- Trigger on `pull_request` for proposed changes.
- Trigger on `push` to the default branch for post-merge confidence.
- Include `workflow_dispatch` when maintainers benefit from manual reruns.
- Use explicit workflow names such as `Validation`, `Coverage`, `Smoke validation`, or `Release tag validation`.
- Use clear step names matching canonical commands.
- Prefer repository scripts in steps so local, CI, and agent validation use the same entrypoints.
- Keep heavyweight, networked, or long-running checks separate from the fast pull-request path when practical.

Avoid burying unrelated stacks in a single step named `test`. If a mixed repository has Python, Rust, and web assets, make the lanes legible.

## 7. Add workflow YAML and meta-CI guardrails

Malformed workflow YAML can masquerade as CI breakage. When a repository provides a workflow checker, run it before deeper debugging. LRH uses:

```bash
scripts/check-workflows
```

This catches workflow YAML syntax issues locally and in CI. Deeper semantic linting such as `actionlint` can be valuable, but it should be a deliberate follow-up because it introduces another tool contract to install, pin, and explain.

## 8. Debug with evidence, not optimism

Before saying CI is flaky, fixed, or unreproducible, collect evidence:

```bash
git rev-parse HEAD
git status --short
scripts/version tools
scripts/check-workflows
scripts/format --check --diff
scripts/lint
scripts/test
```

For non-LRH repositories, substitute their canonical commands. Include relevant logs, coverage reports, screenshots, replay files, build artifacts, or review notes when they explain the outcome. Do not summarize status more optimistically than the evidence supports.

## 9. Minimal CI acceptance criteria

A minimal, useful CI setup should satisfy these criteria:

- The setup path is documented or encoded in scripts.
- CI reports tool/runtime versions before validation.
- Fast pull-request validation runs format check, lint, and tests where applicable.
- Workflow YAML is checked when the repository has GitHub Actions workflows.
- Local commands and CI commands are the same or intentionally mapped.
- Failure logs are specific enough for a human to reproduce the failing command locally.
- Heavy smoke, packaging, release, GPU, browser, or simulation checks are separated when they are too slow or fragile for every pull request.
- Documentation says which checks are canonical and which are optional diagnostics.

## 10. Use templates or fragments only when they reduce rediscovery

Reach for templates or reusable fragments when several repositories have converged on the same command categories, triggers, cache rules, and evidence needs. Do not start with a universal template for an unfamiliar repository.

Good candidates for fragments include:

- common checkout/setup/version-report steps;
- language-specific validation lanes with stable commands;
- workflow YAML checks; and
- release or smoke lanes with clearly documented prerequisites.

Keep fragments small, documented, and easy to override. If dogfooding shows every repository needs heavy edits, keep the guidance as a playbook instead of maintaining brittle shared YAML.

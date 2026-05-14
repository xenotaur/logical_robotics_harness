# CI Migration Implementation Request (Assessment-Gated)

Implement a focused CI migration PR only if this repository is an appropriate candidate under the LRH CI setup and debugging playbook at `docs/project-setup/ci.md`.

Do not start from a one-size-fits-all workflow template. Discover the project family, canonical commands, setup requirements, and existing CI state before editing files.

==================================================
INPUT CONTEXT
==================================================

Optional background / prior assessment:
{{BACKGROUND_CONTEXT}}

Treat any supplied assessment as advisory context only.
You must independently inspect the repository before changing files.

==================================================
MANDATORY GATE: RE-ASSESS BEFORE EDITING
==================================================

Before editing any file:

1. Read and apply the CI playbook at `docs/project-setup/ci.md`.
2. Inspect the repository and produce a brief suitability gate covering:
   - project family and language profile
   - packaging/build/test/tooling baseline
   - setup/bootstrap instructions
   - canonical validation commands from scripts/docs/config
   - existing CI workflows
   - workflow YAML checking command (`scripts/check-workflows` or the closest project-approved equivalent, if workflows exist)
3. Decide whether LRH-style Python CI is appropriate, adaptation is required, native non-Python CI is more appropriate, existing CI is sufficient, or evidence is insufficient.
4. If not appropriate, ABORT with a clear explanation and no file changes.

Acceptable abort reasons include (not exhaustive):
- repository is primarily non-Python (Rust/JS/C++/etc.)
- docs/content/art/book-only repository
- existing CI is already sufficient for project conventions
- insufficient evidence to make safe CI changes
- no canonical setup or validation path can be inferred without human input

==================================================
IMPLEMENTATION OBJECTIVE (ONLY IF GATE PASSES)
==================================================

Create a minimal, maintainable CI slice aligned to existing repository conventions.

Prefer this order:
1. local developer command entry points discovered from or aligned with repository scripts/docs/config
2. GitHub Actions workflows that call those local commands
3. concise documentation of canonical setup and validation commands when existing docs would otherwise be stale

For appropriate Python projects, consider adding/updating only what is needed:
- `scripts/format`
- `scripts/lint`
- `scripts/test`
- `scripts/smoke`
- `scripts/check-workflows`
- `.github/workflows/`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `STYLE.md`
- `CONTRIBUTING.md`

Only edit files that are truly appropriate for the target repository.

==================================================
COMMAND SEMANTICS GUIDANCE
==================================================

Adapt to repository reality; do not force a mismatch.

Discover canonical commands by inspecting repository scripts, docs, and config before proposing or implementing commands. Separate setup/bootstrap from validation, especially in Codex Cloud and other agent environments.

Expected command categories from the playbook:

- setup/bootstrap: install or prepare the development environment; may use network/cache and should not be repeated as ordinary task-phase validation unless the repository explicitly requires it
- tool/version report: show runtime and tool versions before validation
- workflow YAML check: run `scripts/check-workflows` or the closest project-approved equivalent when workflows are touched
- format check: verify formatting without mutating files
- lint check: run static checks without broad rewrites
- tests: run the normal deterministic test suite
- smoke/coverage: run only when appropriate for the repository and task scope

Expected semantics for LRH-style Python repositories:

- `scripts/develop`
  - setup/bootstrap only; in Codex Cloud, run during environment setup/bootstrap rather than routine task-phase validation

- `scripts/version tools`
  - report Python and tool versions before validation
  - if versions are missing or mismatched, report a setup/cache issue before debugging formatter, linter, or test failures

- `scripts/check-workflows`
  - validate workflow YAML syntax when workflows exist or are touched

- `scripts/format`
  - formatting in write mode (typically Black)
  - optionally Ruff fixes if already appropriate

- `scripts/format --check --diff`
  - non-mutating format check for CI and task-phase validation

- `scripts/lint`
  - Ruff/static checks and any repository-approved lint checks

- `scripts/test`
  - normal deterministic unit test suite

- `scripts/smoke`
  - heavier install/build/package checks when intentionally separated from the normal unit suite

If repository already uses pytest, nox, tox, uv, poetry, hatch, npm, cargo, make, just, or similar:
- preserve established workflows
- integrate rather than replacing conventions
- avoid adding stronger tooling such as actionlint, pre-commit, tox/nox, dev containers, or lockfile/toolchain changes unless this task explicitly calls for it or repository evidence shows they are already canonical

==================================================
SECURITY / SAFETY REQUIREMENTS
==================================================

GitHub Actions must use least privilege by default.

Prefer:

```yaml
permissions: read-all
```

or job-specific read-only permissions unless stronger permissions are genuinely required and explicitly justified.

Explicitly avoid:
- secrets/deploy/publish workflows
- write-token workflows
- `pull_request_target` unless there is a specific, security-reviewed need
- weakening existing checks

Action version pinning requirement:
- document your pinning choice
- for normal personal/development repos, major tags (e.g. `actions/checkout@v4`) may be acceptable
- for hardened/security-sensitive repos, full-length commit SHA pinning is the immutable option and should be considered

==================================================
STRICT PROHIBITIONS
==================================================

Do NOT:
- perform broad refactors
- perform language migration
- replace established non-unittest test framework without strong reason
- add fake/vacuous tests
- mass-format unrelated files
- edit unrelated subsystems
- invent CI commands without first checking repository scripts/docs/config
- claim "cannot reproduce", "pre-existing failure", "flaky", or "fixed" without evidence-backed diagnosis
- introduce actionlint, pre-commit, tox/nox, dev containers, or lockfile/toolchain changes unless explicitly requested or already canonical for the repository

==================================================
VALIDATION REQUIREMENTS
==================================================

If you implement changes:

1. Run `git rev-parse HEAD` and `git status --short` to anchor evidence.
2. Run newly added/updated local scripts when feasible.
3. If workflows are touched, run `scripts/check-workflows` or the closest available project-approved workflow YAML check.
4. Run relevant format, lint, and test commands when feasible.
5. Report exact commands and outcomes.
6. If a command cannot run, explain why.
7. Do not claim checks passed unless they actually ran.

For LRH-like repositories, task-phase validation should normally be:

```bash
scripts/version tools
scripts/check-workflows
scripts/format --check --diff
scripts/lint
scripts/test
```

If `scripts/check-workflows` is absent, report that clearly and run the closest approved equivalent or the remaining commands.

==================================================
PR SUMMARY REQUIREMENTS
==================================================

Your final summary must include:
- assessment gate result
- playbook path used: `docs/project-setup/ci.md`
- files changed
- workflows/scripts added or updated
- setup/bootstrap vs validation boundary
- workflow YAML validation command used or why none was available
- validation commands and results
- intentional aborts or skipped pieces
- follow-up recommendations

==================================================
ABORT HANDLING
==================================================

If the gate fails, stop without edits and provide:
- concise evidence-based rationale
- recommended next step (for example native CI approach for the repository stack)

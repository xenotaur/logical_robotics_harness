# Validate a project control directory

## Purpose

Use `lrh validate` to check an LRH `project/` control directory before opening a pull request, merging control-plane changes, or asking an assistant to rely on project state.

Validation loads the source Markdown/frontmatter files, checks cross-file references and policy rules, and prints a text report. It does not edit files.

## Prerequisites

- Run from a repository with an LRH project control directory, usually `project/`.
- Use an environment where LRH is importable or installed.
- For LRH repository task-phase validation, run `scripts/version tools` first and only debug formatter/linter failures after the expected tool versions are present.

## Commands

Validate the default `project/` directory:

```bash
lrh validate
```

Validate a specific project control directory:

```bash
lrh validate --project-dir path/to/project
```

Validate only work-item files and work-item policy rules:

```bash
lrh validate --work-items
```

When the package entry point is not installed but the source tree is importable, use the module form:

```bash
python -m lrh.cli.main validate --project-dir project
```

## Expected output or success criteria

- Exit code `0` means no validation errors were reported.
- Exit code `1` means validation found errors.
- The command prints a human-readable validation report. Treat any reported errors as blocking until fixed or explicitly accepted by maintainers.

## Common troubleshooting notes

- If Python reports `ModuleNotFoundError: lrh`, the environment is not bootstrapped for this repository. In Codex Cloud, treat that as a setup/cache issue rather than an immediate code regression.
- `--project-dir` points at the control directory itself, not necessarily the repository root.
- `--work-items` is narrower than full validation; use full `lrh validate` before relying on whole-project status.

## Related reference

- [CLI reference: `validate`](../reference/cli/validate.md)
- [CLI reference index](../reference/cli/README.md)

# `lrh validate`

## Command purpose

`lrh validate` validates LRH project control files. It reads a project control directory, reports validation errors and warnings, and exits non-zero when errors are present. It does not modify files.

## Canonical invocation patterns

```bash
lrh validate
lrh validate --project-dir project
lrh validate --project-dir /path/to/repo/project
lrh validate --work-items
python -m lrh.cli.main validate --project-dir project
```

## Important options and arguments

- `--project-dir PROJECT_DIR`: path to the project control directory. Defaults to `project`.
- `--work-items`: validate work-item files and policy rules only.
- `-h`, `--help`: print command help.

## Current behavior and limitations

- Exit code `0` means no validation errors were reported.
- Exit code `1` means one or more validation errors were reported.
- The command accepts a project control directory path, not a repository-root flag.
- `--work-items` is intentionally narrower than whole-project validation.
- The command currently emits a text report; there is no `--json` option for `lrh validate`.
- `FRONTMATTER_LINT_UNSAFE_SCALAR` is a report-only warning category that flags unquoted frontmatter plain scalars that either crash real YAML parsing or silently change meaning under it: an unquoted colon-collapse, an unquoted mid-scalar `#` comment, a reserved-indicator-leading scalar, or one of a small set of fields (currently `id` and `title`) whose value would implicitly resolve to `null`, a bool, an int, a float, or a date. Other known string fields where an actual `null` is valid (e.g. `owner`, `commit`, `pr`) are intentionally not flagged. It never fails validation on its own and never rewrites anything — see [`lrh project doctor --fix-frontmatter`](doctor.md) for the corresponding one-time content-migration tool.

## Related how-to pages

- [Validate a project control directory](../../how-to/validate-a-project.md)

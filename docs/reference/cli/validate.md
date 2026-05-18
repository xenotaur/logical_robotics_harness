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

## Related how-to pages

- [Validate a project control directory](../../how-to/validate-a-project.md)

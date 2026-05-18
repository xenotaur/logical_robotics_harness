# `lrh survey`

## Command purpose

`lrh survey` surveys a Python source tree for assist planning workflows. It inventories Python files and symbols, documentation hints, CLI candidates, console scripts, and optional test files.

## Canonical invocation patterns

```bash
lrh survey src/lrh
lrh survey src/lrh --tests-root tests
lrh survey src/lrh --format md --out -
lrh survey src/lrh --format json --out /tmp/lrh-survey.json
python -m lrh.cli.main survey src/lrh --tests-root tests --format json
```

## Important options and arguments

- `root`: required root directory to scan.
- `--tests-root TESTS_ROOT`: optional tests directory to include in the survey.
- `--format {md,json}`: output format. Defaults to `md`.
- `--out OUT`: output file path, or `-` for stdout. Defaults to `-`.
- `-h`, `--help`: print command help.

## Current behavior and limitations

- The root path must exist and be a directory.
- `--tests-root`, when supplied, must exist and be a directory.
- Markdown output is intended for human review.
- JSON output is intended for automation and currently includes a survey `schema_version`.
- When writing to a file, parent directories are created as needed and the command prints `Wrote <format> to <path>`.
- The command surveys Python source trees; it is not a general-purpose repository indexer.

## Related how-to pages

- [Survey a source tree](../../how-to/survey-a-source-tree.md)
- [Generate a context snapshot](../../how-to/generate-a-snapshot.md)

# Survey a source tree

## Purpose

Use `lrh survey` to inspect a Python source tree and produce a lightweight inventory for planning and assist workflows. The survey reports files, symbols, docs/readme hints, CLI candidates, console scripts, and optional test-tree relationships.

The command is read-only except when writing the requested output file.

## Prerequisites

- Choose an existing source root directory, such as `src/lrh`.
- Optionally choose an existing tests root directory, such as `tests`.

## Commands

Print a Markdown survey to stdout:

```bash
lrh survey src/lrh
```

Include a tests root:

```bash
lrh survey src/lrh --tests-root tests
```

Emit JSON instead of Markdown:

```bash
lrh survey src/lrh --format json
```

Write output to a file:

```bash
lrh survey src/lrh --tests-root tests --format json --out /tmp/lrh-survey.json
```

Use `-` to force stdout explicitly:

```bash
lrh survey src/lrh --out -
```

Use module invocation when needed:

```bash
python -m lrh.cli.main survey src/lrh --tests-root tests --format md
```

## Expected output or success criteria

- Exit code `0` means the source tree was surveyed and output was written or printed.
- Markdown is the default output format.
- JSON output uses the implemented survey schema, currently including `schema_version`.
- When writing to a file, LRH prints `Wrote <format> to <path>`.

## Common troubleshooting notes

- The positional `root` must exist and be a directory.
- `--tests-root`, when provided, must also exist and be a directory.
- Use `--format json` for automation and `--format md` for quick human review.

## Related reference

- [CLI reference: `survey`](../reference/cli/survey.md)
- [How to generate a snapshot](generate-a-snapshot.md)

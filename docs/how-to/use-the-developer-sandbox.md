# Use the developer sandbox

## Purpose

Use `scripts/sandbox` when you need to try LRH commands against disposable local state instead of your real repository, HOME, XDG directories, or meta workspace. This is especially useful for `lrh meta init`, `lrh meta register`, and other commands that intentionally write workspace files.

The sandbox is a maintainer helper script, not a separate LRH CLI command.

## Prerequisites

- Run from the LRH repository root.
- Use it for local experimentation and documentation/examples, not as a replacement for normal validation.
- Put the command to run after `--`.

## Commands

Run a command with isolated sandbox state and keep the sandbox for inspection:

```bash
scripts/sandbox -- python -m lrh.cli.main meta init --mode hybrid
```

Run a command and remove sandbox state afterward:

```bash
scripts/sandbox --cleanup -- python -m lrh.cli.main meta where
```

Use the installed entry point inside the sandbox when available:

```bash
scripts/sandbox --cleanup -- lrh meta init --mode local
```

Combine sandboxing with file-producing commands:

```bash
scripts/sandbox --cleanup -- python -m lrh.cli.main survey src/lrh --format json --out /tmp/lrh-survey.json
```

## Expected output or success criteria

- The wrapped command's exit code is the sandbox command's exit code.
- Commands that write meta workspace files do so under the sandbox's isolated environment unless you pass explicit paths outside it.
- With `--cleanup`, temporary sandbox state is removed after the command completes.

## Common troubleshooting notes

- If you need to inspect generated files, omit `--cleanup` and remove the sandbox manually after review.
- The sandbox does not make unsafe commands safe by itself; still review explicit output paths and command arguments.
- Prefer `python -m lrh.cli.main ...` in source-tree experiments when the package entry point may not be installed.

## Related reference

- [CLI reference: `meta`](../reference/cli/meta.md)
- [How to register a project with meta](register-a-project-with-meta.md)
- [How to inspect workspace state](inspect-workspace-state.md)

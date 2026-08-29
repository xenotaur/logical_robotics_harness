# `lrh project doctor`

## Command purpose

`lrh project doctor` diagnoses LRH project bootstrap readiness. It reads a repository root, reports which required and recommended control-plane paths are present or missing, and exits non-zero when required paths are missing. With `--fix-frontmatter`, it instead runs a one-time content migration that re-quotes unsafe frontmatter plain scalars flagged by `lrh validate`'s `FRONTMATTER_LINT_UNSAFE_SCALAR` lint category (see [`validate`](validate.md)); it does not modify files unless `--fix-frontmatter --apply` is given together. Diagnosis checks presence, not path content — it does not validate the contents of a present path.

## Canonical invocation patterns

```bash
lrh project doctor
lrh project doctor --project-root /path/to/repo
lrh project doctor --json
lrh project doctor --strict
lrh project doctor --fix-frontmatter
lrh project doctor --fix-frontmatter --apply
```

## Important options and arguments

- `--project-root PROJECT_ROOT`: target repository root. Defaults to the current directory.
- `--json`: diagnosis mode only. Emit deterministic JSON output instead of the text report. Has no effect when combined with `--fix-frontmatter`, which always prints its own text report.
- `--strict`: diagnosis mode only. Return non-zero when warnings are present, not only on errors. Has no effect when combined with `--fix-frontmatter`, which always exits `0` after a successful scan.
- `--fix-frontmatter`: one-time migration mode, independent of diagnosis mode above. Re-quotes unsafe frontmatter plain scalars — an unquoted colon-collapse, an unquoted mid-scalar `#` (which real YAML reads as a comment and silently truncates), a scalar starting with a reserved YAML indicator character, or one of a small set of fields (currently `id` and `title`) whose value would implicitly resolve to `null`, a bool, an int, a float, or a date. Other known string fields where an actual `null` is valid (e.g. `owner`, `commit`, `pr`) are intentionally left unquoted when null. Scoped to the `project/` subdirectory under `--project-root`, not the whole repository. Dry-run by default: reports what would change without writing.
- `--apply`: with `--fix-frontmatter`, write the fixes to disk instead of only previewing them. Invalid without `--fix-frontmatter`.
- `-h`, `--help`: print command help.

## Current behavior and limitations

- In diagnosis mode, exit code `0` means no errors were reported (or, with `--strict`, no warnings either); exit code `1` means one or more errors were reported, or `--strict` was given and warnings were present.
- In `--fix-frontmatter` mode, exit code is always `0` after a successful scan, regardless of `--json`/`--strict` or how many fields were found.
- `--project-root` takes a repository root, not a `project/` control directory — this differs from `lrh validate`'s `--project-dir`, which points directly at the control directory (see [`validate`](validate.md)'s own note on this).
- `--fix-frontmatter` only rewrites the exact line a finding points to — it never rewrites a `- key: value` list item that is a genuine multi-key YAML mapping (a continuation line indented to align with the first key), and only rewrites such an item under a field already known to hold plain strings. Every write self-verifies by re-parsing the result before it's committed to disk.
- `--fix-frontmatter` shares its detector with `lrh validate`'s `FRONTMATTER_LINT_UNSAFE_SCALAR` lint category, so the two can never disagree about what's unsafe.

## Related how-to pages

- [Validate a project control directory](../../how-to/validate-a-project.md)

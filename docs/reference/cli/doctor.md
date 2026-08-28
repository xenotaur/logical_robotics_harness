# `lrh project doctor`

## Command purpose

`lrh project doctor` diagnoses LRH project bootstrap readiness. It reads a repository root, reports missing or misconfigured control-plane paths, and exits non-zero when errors are present. With `--fix-frontmatter`, it instead runs a one-time content migration that re-quotes unsafe frontmatter plain scalars flagged by `lrh validate`'s `FRONTMATTER_LINT_UNSAFE_SCALAR` lint category (see [`validate`](validate.md)); it does not modify files unless `--fix-frontmatter --apply` is given together.

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
- `--json`: emit deterministic JSON output instead of the text report.
- `--strict`: return non-zero when warnings are present, not only on errors.
- `--fix-frontmatter`: one-time migration mode. Re-quotes unsafe frontmatter plain scalars — an unquoted colon-collapse, an unquoted mid-scalar `#` (which real YAML reads as a comment and silently truncates), a scalar starting with a reserved YAML indicator character, or a known string-typed field whose value would implicitly resolve to a non-string YAML type (bool, null, int, float, or date). Scoped to the `project/` subdirectory under `--project-root`, not the whole repository. Dry-run by default: reports what would change without writing.
- `--apply`: with `--fix-frontmatter`, write the fixes to disk instead of only previewing them. Invalid without `--fix-frontmatter`.
- `-h`, `--help`: print command help.

## Current behavior and limitations

- Exit code `0` means no diagnosis errors were reported (or, with `--fix-frontmatter`, that the migration scan completed).
- Exit code `1` means one or more diagnosis errors were reported, or `--strict` was given and warnings were present.
- `--project-root` takes a repository root, not a `project/` control directory — this differs from `lrh validate`'s `--project-dir`, which points directly at the control directory (see [`validate`](validate.md)'s own note on this).
- `--fix-frontmatter` only rewrites the exact line a finding points to — it never rewrites a `- key: value` list item that is a genuine multi-key YAML mapping (a continuation line indented to align with the first key), and only rewrites such an item under a field already known to hold plain strings. Every write self-verifies by re-parsing the result before it's committed to disk.
- `--fix-frontmatter` shares its detector with `lrh validate`'s `FRONTMATTER_LINT_UNSAFE_SCALAR` lint category, so the two can never disagree about what's unsafe.

## Related how-to pages

- [Validate a project control directory](../../how-to/validate-a-project.md)

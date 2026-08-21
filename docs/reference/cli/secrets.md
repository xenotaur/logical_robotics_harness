# `lrh secrets`

## Command purpose

`lrh secrets` provides a three-stage pipeline for finding, triaging, and
removing secrets from a repository's git history: `scan` (read-only
discovery), `review` (human-decided triage), and `purge` (mirror-clone
history rewrite). Each stage's output is required input for the next —
`scan` never rewrites history, `review` never touches the source repo, and
`purge` refuses to run without `review`'s finalized output. No subcommand
ever runs `git push`; `purge` prints the push command for a human to run
manually.

## Organization

```bash
lrh secrets scan --out-dir <dir>
lrh secrets review --out-dir <dir>
lrh secrets purge --refs-file <file> --replacements <file>
```

Each subcommand is documented separately below. See
[Scan, review, and purge secrets](../../how-to/scan-and-purge-secrets.md) for
the full end-to-end workflow, and
[the secrets-hygiene safety model](../../explanations/secrets-hygiene-safety-model.md)
for why the pipeline is shaped this way.

## `lrh secrets scan`

Read-only full-history secrets scan via [`gitleaks`](https://github.com/gitleaks/gitleaks).

```bash
lrh secrets scan --out-dir /tmp/secrets-audit
lrh secrets scan --project-root /path/to/repo --out-dir /tmp/secrets-audit
lrh secrets scan --out-dir /tmp/secrets-audit --format json
```

- `--project-root PROJECT_ROOT`: target repository root to scan. Defaults to
  the current directory.
- `--out-dir OUT_DIR` (required): directory to write `findings.json` and
  `replacements.txt` into. These files contain real secret values — choose a
  gitignored location, not a directory a later `git add .` would pick up.
  Output file permissions are restricted (`chmod 0600`, best-effort).
- `--format {text,json}`: output format. Defaults to `text`.

`scan` requires the `gitleaks` binary on `PATH` and fails fast with an
install hint if it's missing. It never passes `--config`, `--no-config`, or
`--no-git` — a target repo's own `.gitleaks.toml`, if present, is always
auto-discovered and never suppressed.

**Provider coverage is uneven, not uniform.** Keys with structural prefixes
(`sk-proj-...`, `sk-ant-api03-...`, `AIza...`) are caught reliably by
gitleaks' default rules. Azure-family keys have no distinguishing prefix and
are only caught via contextual rules (the default `generic-api-key` rule, or
a repo's own `.gitleaks.toml`), and are invisible entirely on a
non-suggestive variable name. `.ipynb` files store source as JSON-escaped
strings, which can defeat delimiter-based detection regexes regardless of
provider.

`findings.json` is the raw gitleaks report. `replacements.txt` is a draft
`<secret>==>***REMOVED-<RuleID>***` mapping, one line per unique secret — do
not hand this file to `purge` directly; it has not been reviewed. If no
findings exist, `replacements.txt` is not written (and a stale one from an
earlier, dirtier scan of the same `--out-dir` is removed).

## `lrh secrets review`

Decisions-file-gated triage of a scan's findings.

```bash
lrh secrets review --out-dir /tmp/secrets-audit
lrh secrets review --out-dir /tmp/secrets-audit --decisions decisions.yaml --check
lrh secrets review --out-dir /tmp/secrets-audit --decisions decisions.yaml --apply
```

- `--out-dir OUT_DIR` (required): directory containing `scan`'s
  `findings.json`/`replacements.txt`. `review` never takes `--project-root`
  — it only reads `--out-dir`'s contents, never the source repository.
- `--decisions DECISIONS`: path to a decisions YAML file, one entry per
  secret value:
  ```yaml
  <secret-value>:
    decision: keep     # or: ignore
    reason: "why this is/isn't a real secret to purge"
  ```
  The key is the literal secret value, not a hash — always YAML-quote it,
  since an unquoted value that happens to be YAML-significant (`true`,
  `12345`, `[abc]`, or anything containing `: `) changes its parsed type
  or breaks the file, and `review` matches findings by exact string value.
  This file carries the same trust level as `findings.json` — it contains
  real secret values and must never be committed. A finding counts as
  decided only when it has both a valid `decision` (`keep` or `ignore`)
  *and* a non-empty `reason`.
- `--check`: exit nonzero if any finding lacks a recorded decision. With no
  `--check`/`--apply` flag, `review` prints an annotated report and exits
  `0`.
- `--apply`: write `<out-dir>/replacements.reviewed.txt` — a name distinct
  from `scan`'s draft `replacements.txt`, which `review` never overwrites.
  Requires every finding decided; fails otherwise (and invalidates any
  stale `replacements.reviewed.txt` already present, so a failed `--apply`
  never leaves a stale file that could be mistaken for current output).
  `--check` and `--apply` are mutually exclusive.

`replacements.reviewed.txt` begins with a fixed marker line,
`# lrh-secrets-reviewed v1`, followed by the kept `secret==>placeholder`
lines. This marker is what `purge` checks at runtime to refuse an
unreviewed `scan` draft — not just the filename. Output file permissions
are restricted (`chmod 0600`, best-effort), same as `scan`'s output.

## `lrh secrets purge`

Mirror-clone-scoped [`git-filter-repo`](https://github.com/newren/git-filter-repo)
rewrite, verify, never push.

```bash
lrh secrets purge --refs-file refs.txt --replacements /tmp/secrets-audit/replacements.reviewed.txt --dry-run
lrh secrets purge --refs-file refs.txt --replacements /tmp/secrets-audit/replacements.reviewed.txt --apply
lrh secrets purge --project-root /path/to/repo --source git@example.com:org/repo.git --refs-file refs.txt --replacements replacements.reviewed.txt --mirror-dir /tmp/mirror --apply
```

- `--project-root PROJECT_ROOT`: target repository root, used only to
  default `--source` (via `git remote get-url origin`). Defaults to the
  current directory.
- `--source SOURCE`: URL or path to mirror-clone. Defaults to
  `--project-root`'s `origin` remote. A relative local path is resolved to
  absolute before use, so the push command printed on success is correct
  regardless of the directory it's later run from.
- `--refs-file REFS_FILE` (required): path to a file listing one ref per
  line to rewrite (blank lines and `#`-comments are ignored). **Mandatory —
  `purge` refuses to run unscoped.** A missing or empty refs file is a hard
  failure before any clone is attempted.
- `--replacements REPLACEMENTS` (required): path to `review --apply`'s
  `replacements.reviewed.txt` output — never `scan`'s draft
  `replacements.txt`. **Enforced at runtime, not just by convention**: the
  file's first non-empty line must be exactly `# lrh-secrets-reviewed v1`,
  checked before any clone happens. The marker is stripped before the
  remaining lines are passed to `git-filter-repo`.
- `--mirror-dir MIRROR_DIR`: directory for the mirror clone. Defaults to a
  fresh temp directory.
- `--dry-run`: validate every input (refs file, replacements marker,
  `git-filter-repo` availability) without cloning or rewriting anything.
- `--apply`: mirror-clone the source, rewrite the specified refs, and
  verify. Mutually exclusive with `--dry-run`.

`purge` requires the `git-filter-repo` binary on `PATH` and fails fast with
an install hint if it's missing — checked on both `--dry-run` and `--apply`.

**Verification is mandatory and literal-string, not regex.** After
rewriting, `purge` re-scans the mirror with `git log --all -S<secret>` —
deliberately without `--pickaxe-regex`, so a secret containing regex
metacharacters (e.g. `ab+c`) is verified as a literal string rather than
misinterpreted as a pattern. If any listed secret is still found, `purge`
exits nonzero and **prints no push command**.

**`purge` never runs `git push` under any flag combination.** On a clean
verification, it prints — but never executes — the `git push --force`
command for each rewritten ref, together with two manual-step reminders:
notify every collaborator/branch-owner before pushing (a stale clone's
`git pull` silently reintroduces the purged secret via merge; it does not
error), and file a support request with the git host to purge cached
views/forks if the repository was ever public.

## Related how-to and explanation pages

- [Scan, review, and purge secrets](../../how-to/scan-and-purge-secrets.md) —
  the full end-to-end workflow against a real repository.
- [The secrets-hygiene safety model](../../explanations/secrets-hygiene-safety-model.md) —
  why the pipeline never lets `scan` feed `purge` directly, and why `purge`
  never pushes.

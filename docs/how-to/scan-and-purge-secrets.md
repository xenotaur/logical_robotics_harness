# Scan, review, and purge secrets

## Purpose

Use `lrh secrets scan`, `lrh secrets review`, and `lrh secrets purge` to
find leaked secrets in a repository's git history, decide which findings
are real, and — only after that human decision — rewrite history to remove
them. The three commands are a pipeline: `scan` is read-only, `review`
requires an explicit decision per finding before it will produce
purge-accepted output, and `purge` refuses to run without that output.
Nothing in this pipeline ever runs `git push`.

## Prerequisites

- [`gitleaks`](https://github.com/gitleaks/gitleaks#installing) on `PATH`
  for `scan`.
- [`git-filter-repo`](https://github.com/newren/git-filter-repo#how-do-i-install-it)
  on `PATH` for `purge`.
- A gitignored output directory to hold scan/review artifacts — they
  contain real secret values and must never be committed.
- If purging: a `--refs-file` listing exactly which refs to rewrite (one
  per line), since `purge` refuses to run unscoped.

## Step 1 — Scan

```bash
lrh secrets scan --project-root /path/to/repo --out-dir Audits/
```

```
12:22PM INF 17 commits scanned.
12:22PM INF scanned ~50176 bytes (50.18 KB) in 67.2ms
12:22PM INF no leaks found
gitleaks found 0 finding(s) across all history.
Nothing to review. Not writing replacements.txt.
```

A clean scan writes only `findings.json` (empty) and skips
`replacements.txt` entirely. When gitleaks does find something, `scan`
writes both `findings.json` (the raw report) and a draft `replacements.txt`
— and prints an explicit reminder not to hand that draft to `purge`
directly:

```
gitleaks found 4 finding(s) across all history.
Wrote 4 raw finding(s) to Audits/findings.json
Wrote 4 unique secret(s) to Audits/replacements.txt

STOP: do not hand replacements.txt to `lrh secrets purge` directly.
Run `lrh secrets review` to triage findings.json and produce a
reviewed, purge-accepted replacements.reviewed.txt.
```

## Step 2 — Review

Run `review` with no `--decisions` file first to see what was found:

```bash
lrh secrets review --out-dir Audits/
```

```
4 unique secret(s) found in findings.json.
  ***REMOVED-generic-api-key***: UNDECIDED
  ***REMOVED-generic-api-key***: UNDECIDED
  ***REMOVED-generic-api-key***: UNDECIDED
  ***REMOVED-generic-api-key***: UNDECIDED

4 finding(s) undecided.
```

`review` has no `--project-root` — it only reads `--out-dir`'s contents, so
it never needs source-repo access.

**Gitleaks' `generic-api-key` rule matches on shape, not certainty — expect
false positives.** A pinned-dependency file like `environment.yml` (conda)
can trip this rule on ordinary version-pin strings (for example,
`asttokens=2.0.5=pyhd3eb1b0_0`) purely because they look like a
high-entropy token. This is exactly what the decision step exists to catch:
inspect `findings.json`'s `File`/`Match`/`Commit` fields for each finding,
then record a decision per secret value in a decisions YAML file:

```yaml
# Audits/decisions.yaml
"0.1.4=py311hca03da5_0":
  decision: ignore
  reason: "conda package version pin in environment.yml, not a secret"
```

**Always quote the secret value used as a key.** An unquoted key that
happens to be YAML-significant (`true`, `12345`, `[abc]`, or any value
containing `: `) either changes the key's parsed type or breaks the file
outright — `review` looks up findings by their exact string secret value,
so a key that didn't parse as that same string is silently treated as
undecided instead of matched. Quoting the key, as above, keeps it a
literal string regardless of what the secret's value looks like.

Then check or apply:

```bash
lrh secrets review --out-dir Audits/ --decisions Audits/decisions.yaml --check
lrh secrets review --out-dir Audits/ --decisions Audits/decisions.yaml --apply
```

`--apply` requires every finding decided and writes
`Audits/replacements.reviewed.txt`, beginning with a fixed marker line
(`# lrh-secrets-reviewed v1`). Only findings decided `keep` are written —
`ignore`d findings (like the false positives above) are dropped.

Pointing `--decisions` at a file that doesn't exist yet fails cleanly, not
with a stack trace:

```
$ lrh secrets review --out-dir Audits/ --decisions Audits/decisions.yaml
error: Audits/decisions.yaml not found
```

## Step 3 — Purge

Once `replacements.reviewed.txt` exists and every real secret is decided
`keep`, list the refs to rewrite and validate first:

```bash
echo "refs/heads/main" > refs.txt

lrh secrets purge \
  --project-root /path/to/repo \
  --refs-file refs.txt \
  --replacements Audits/replacements.reviewed.txt \
  --dry-run
```

`--dry-run` validates the refs file, the reviewed-replacements marker, and
`git-filter-repo`'s availability without cloning or rewriting anything. Once
that's clean, run for real:

```bash
lrh secrets purge \
  --project-root /path/to/repo \
  --refs-file refs.txt \
  --replacements Audits/replacements.reviewed.txt \
  --apply
```

On success, `purge` prints the `git push --force` command for each rewritten
ref — but does not run it — together with two reminders: notify every
collaborator/branch-owner before anyone pushes (a stale clone's `git pull`
silently reintroduces the purged secret via merge), and file a support
request with the git host to purge cached views/forks if the repository was
ever public. Pushing and notifying collaborators are always manual next
steps you run yourself.

If verification finds a listed secret still present in the rewritten
history, `purge` exits nonzero and prints no push command — nothing is
left in a state that looks safe to push.

## Expected output or success criteria

- `scan` exit `0` means the scan ran; check `findings.json`'s contents (not
  just the exit code) to know whether anything was found.
- `review --check` exits nonzero while any finding is undecided, `0` once
  every finding has a valid `decision` and non-empty `reason`.
- `review --apply` exits `0` and writes `replacements.reviewed.txt` only
  when every finding is decided; otherwise it exits nonzero and writes
  nothing (invalidating any stale prior output in the same `--out-dir`).
- `purge --apply` exits `0` and prints a push command only when
  post-rewrite verification found zero remaining occurrences of every
  listed secret.

## Common troubleshooting notes

- `scan --out-dir` is required; there is no default.
- `review`'s `--decisions` file must exist before `--check`/`--apply` will
  read it — a missing path is a clean error, not a crash.
- `purge --refs-file` must exist and contain at least one non-comment,
  non-blank line, or `purge` refuses to run before any clone happens.
- `purge --replacements` must be `review --apply`'s own output — pointing
  it at `scan`'s draft `replacements.txt` fails the marker check before any
  clone happens, by design.
- `purge --dry-run` and `--apply` are mutually exclusive.

## Related reference

- [CLI reference: `secrets`](../reference/cli/secrets.md)
- [The secrets-hygiene safety model](../explanations/secrets-hygiene-safety-model.md)

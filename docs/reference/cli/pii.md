# `lrh pii`

## Command purpose

`lrh pii scan` is a read-only, local, deterministic heuristic scan for
misplaced documents and PII-shaped content across a repository's full git
history. It never writes to the repository being scanned; it writes one
output file (`pii_findings.json`) to a separate `--out-dir`.

Layer 1 flags suspicious paths by file type or filename (e.g. `*.pdf`,
`*statement*`); Layer 2 scans file content for PII/secret patterns,
scoped to Layer 1's flagged files by default. See
[PII and Sensitive-Content Philosophy](../../how-to/project-setup/pii.md)
for when and why to run this, how it differs from `lrh secrets`, and its
disclosed detection gaps (no OCR, no ML/NLP content classification, no
cloud DLP dependency).

## Organization

```bash
lrh pii scan --out-dir <dir>
```

`scan` is currently the only subcommand — there is no PII-equivalent of
`lrh secrets`' `review`/`purge` stages. See
[PII and Sensitive-Content Philosophy](../../how-to/project-setup/pii.md#why-remediation-looks-different-for-pii-than-for-credentials)
for why remediation is intentionally left to the human, not a follow-on
command.

## `lrh pii scan`

Read-only full-history PII/misplaced-document scan.

```bash
lrh pii scan --out-dir /tmp/pii-audit
lrh pii scan --project-root /path/to/repo --out-dir /tmp/pii-audit
lrh pii scan --out-dir /tmp/pii-audit --config custom-pii-rules.toml
lrh pii scan --out-dir /tmp/pii-audit --format json
```

- `--project-root PROJECT_ROOT`: target repository root to scan. Defaults to
  the current directory.
- `--out-dir OUT_DIR` (required): directory to write `pii_findings.json`
  into.
- `--config CONFIG`: path to a `.lrh-pii.toml` file, overriding
  auto-discovery at `--project-root`. Auto-discovery finds no config file
  silently and falls back to the built-in defaults; an explicit `--config`
  path that doesn't exist is an error instead — the point of naming a
  config file explicitly is to use it, so a missing one fails loudly
  rather than silently scanning with defaults the user didn't ask for.
- `--format {text,json}`: output format. Defaults to `text`.

`pii_findings.json` is a list of findings, each
`{path, rule_id, category, severity, confidence, commit, content_digest,
still_in_working_tree, matched_layer}`. `matched_layer` is `"path"` for a
Layer 1 (file-type/name) match or `"content"` for a Layer 2 (content
pattern) match. A Layer 1 finding is expanded across every commit that
touched the flagged path, so the same path can appear more than once with
different `commit`/`content_digest` values across its history.

**Content-bound allowlist.** A repo-committed `.lrh-pii-allowlist` file
suppresses previously-approved findings: one fingerprint per line
(`.gitleaksignore`-style — blank lines and a trailing `# reason` comment
are both optional), where the fingerprint is
`sha256(path + rule_id + content_digest)`. Binding the fingerprint to
`content_digest` — not just `path` and `rule_id` — means approving one
value never silently suppresses a *different*, genuinely sensitive value
later found at that same path/rule; a content change produces a fresh
finding.

The `text` format's report includes one line per finding (path, matched
layer, rule, severity/confidence, commit) in addition to the disclosure
block; `json` writes the same schema `pii_findings.json` uses, wrapped
with `findings_count`/`allowlisted_count`/`findings_path` metadata.

## Related how-to and explanation pages

- [PII and Sensitive-Content Philosophy](../../how-to/project-setup/pii.md) —
  when and why to run this, how it differs from `lrh secrets`, the
  content-bound allowlist format, and disclosed detection limitations.

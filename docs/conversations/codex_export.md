# Export Codex conversations

Use this guide when a Codex task contains useful context that should be kept as
a private, non-authoritative transcript for later review. The normal user-facing
entry point is `/lrh-codex-export`, which wraps
`lrh conversation archive-codex-thread` and immediately verifies the
result with `lrh conversation inspect-export`.

## When to use this

Use `/lrh-codex-export` when you need a durable private capture of:

- a design or implementation session whose reasoning may matter later;
- a review-response or closeout session with useful command and validation
  context;
- a dogfood session that demonstrates an LRH workflow;
- follow-up decisions that should later be promoted into a work item, proposal,
  execution record, or evidence note.

Do not export conversations just because they exist. Raw exports can contain
private text, credentials, local paths, unpublished design details, and stale AI
claims. Treat them as private context until selected content is reviewed and
promoted into a separate LRH artifact.

## Capture the current Codex task

If you only need the LRH closeout pointer and do not want to archive transcript
content, run:

```text
/lrh-codex-session
```

That skill wraps:

```bash
lrh conversation current-codex-thread-id --field session-transcript
```

and reports:

```yaml
session_transcript: codex-app:<thread-id>
```

The pointer is the Codex task/thread identity used by the export commands. It is
not an export attempt id, archive directory, `attempt.json` path, raw JSON path,
Markdown export path, or timestamp. This lets closeout records name the current
Codex session without creating an early archive attempt.

## Archive the current Codex task

In Codex, run:

```text
/lrh-codex-export
```

When `CODEX_THREAD_ID` is available, the skill resolves it through the same
shared resolver used by `/lrh-codex-session`. If the environment does not expose
a thread id, provide one explicitly:

```text
/lrh-codex-export 019fc43f-e2d9-7503-88cb-9d9a8136c111
```

The skill creates a private output directory in LRH's durable local session
archive, runs `lrh conversation archive-codex-thread`, then runs:

```bash
lrh conversation inspect-export "$EXPORT_PATH" --source "$RAW_PATH" --format json
```

It reports metadata such as output paths, privacy, sensitivity, warnings,
source-hash status, turn count, message count, and artifact statistics. It does
not print transcript body text.

The default archive root resolves as `--archive-root`, then
`LRH_SESSION_ARCHIVE_ROOT`, then
`~/.local/share/lrh/session-archive`. Codex exports are stored below that root
under `codex/exports/YYYY/MM/`. This root is local and private by convention;
LRH rejects archive roots that resolve inside the current Git worktree.

Each attempted archive export writes `attempt.json` before talking to the Codex
app-server, then updates that file with success, failure, output paths, source
hash, and validation status. This prevents an empty directory from looking like
a completed export.

Use scratch mode only for explicitly ephemeral dogfood or debugging captures:

```bash
lrh conversation archive-codex-thread \
  --thread-id "$CODEX_THREAD_ID" \
  --scratch
```

Scratch exports are reported as ephemeral and may live under platform temporary
storage. Move or re-export anything that needs to survive cleanup.

## Use the CLI directly

For the normal durable archive path, use:

```bash
umask 077
lrh conversation archive-codex-thread \
  --thread-id "$CODEX_THREAD_ID"
```

Use the lower-level explicit-path adapter only when you are scripting a custom
layout:

```bash
umask 077
lrh conversation export-codex-thread \
  --thread-id "$CODEX_THREAD_ID" \
  --out "$PRIVATE_DIR/export.md" \
  --raw-out "$PRIVATE_DIR/raw.json"
```

The low-level CLI requires both `--out` and `--raw-out`. Keep both paths outside
the Git worktree, and keep the raw capture at an absolute private path.

Then inspect the export without printing transcript content:

```bash
lrh conversation inspect-export \
  "$PRIVATE_DIR/export.md" \
  --source "$PRIVATE_DIR/raw.json" \
  --format json
```

See the [`lrh conversation` CLI reference](../reference/cli/conversation.md)
for exact options, defaults, exit behavior, and manifest fields.

## Keep exports private

Every Codex app export writes two files:

- a Markdown artifact with `ConversationExportManifest` frontmatter;
- a raw JSON capture from the Codex app-server response.

Keep both outside the project Git worktree unless a separate reviewed workflow
has produced a sanitized committed artifact. The raw JSON capture is especially
sensitive because it preserves the original app-server response for local audit.

## Import rescued Codex export directories

Use this when older `/lrh-codex-export` dogfood runs left directories such as
`Promptspace/CodexExports/lrh-codex-export-*` outside the durable archive:

```bash
lrh conversation import-codex-exports "$HOME/Workspace/Promptspace/CodexExports"
```

The importer copies each immediate child directory into
`codex/imports/YYYY/MM/` under the durable archive root, writes an `attempt.json`
marker, and reports only metadata. Valid directories with both `export.md` and
`raw.json` are inspected with `inspect-export`. Directories missing one or both
files are preserved as `partial` or `empty` attempts instead of being reported
as successful exports. Imported `export.md`, `raw.json`, and `attempt.json`
files are chmod'd private where supported.

Use `--dry-run` to preview the classification, and `--archive-root` to direct
the import into a configured private archive root. The importer copies by
default; remove or reorganize the original rescued files only after verifying
the archive copy.

Before sharing or promoting any content from an export:

1. Review for secrets, tokens, private URLs, customer data, personal data, and
   proprietary text.
2. Preserve the distinction between human instructions, AI output, and verified
   evidence.
3. Promote only the reviewed claim or excerpt into the target LRH artifact.
4. Keep the raw export labeled as `authority: non_authoritative_context`.

## Verify without previewing transcript text

Use manifest-aware inspection for routine checks:

```bash
lrh conversation inspect-export EXPORT.md --source RAW.json --format text
```

Avoid:

```bash
cat EXPORT.md
head EXPORT.md
tail EXPORT.md
sed -n '1,80p' EXPORT.md
```

The frontmatter can be followed immediately by private transcript content, so
line-based previews can leak conversation text into terminal scrollback, logs,
or PR comments.

## Troubleshooting

If the export command fails because the environment cannot access Codex local
state, rerun only through the environment's approval mechanism. Do not fall back
to scraping undocumented Codex storage files.

If macOS, endpoint security, or Codex reports that the Codex executable is
blocked, quarantined, replaced, or suspicious, stop exporting and investigate
the executable before treating any export as reliable. The exporter records a
trust-state warning because it does not perform executable signature,
notarization, or quarantine diagnostics.

## Related docs

- [`lrh conversation` CLI reference](../reference/cli/conversation.md)
- [Conversation capture options](conversation-capture-options.md)
- [Promote conversation-derived content to a project artifact](promote-conversation-to-project-artifact.md)

# Export Codex conversations

Use this guide when a Codex task contains useful context that should be kept as
a private, non-authoritative transcript for later review. The normal user-facing
entry point is `/lrh-codex-export`, which wraps the lower-level
`lrh conversation export-codex-thread` CLI command and immediately verifies the
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

In Codex, run:

```text
/lrh-codex-export
```

When `CODEX_THREAD_ID` is available, the skill uses it as the thread id. If the
environment does not expose a thread id, provide one explicitly:

```text
/lrh-codex-export 019fc43f-e2d9-7503-88cb-9d9a8136c111
```

The skill creates a private output directory outside the current Git worktree,
runs `lrh conversation export-codex-thread`, then runs:

```bash
lrh conversation inspect-export "$EXPORT_PATH" --source "$RAW_PATH" --format json
```

It reports metadata such as output paths, privacy, sensitivity, warnings,
source-hash status, turn count, message count, and artifact statistics. It does
not print transcript body text.

## Use the CLI directly

Use the CLI directly when you are scripting or working outside an agent skill:

```bash
umask 077
install -d -m 700 "$HOME/.lrh/private/codex"
lrh conversation export-codex-thread \
  --thread-id "$CODEX_THREAD_ID" \
  --out "$HOME/.lrh/private/codex/export.md" \
  --raw-out "$HOME/.lrh/private/codex/raw.json"
```

The direct CLI requires both `--out` and `--raw-out`. Keep both paths outside
the Git worktree, and keep the raw capture at an absolute private path. Use a
restrictive `umask` or explicit permissions so both the Markdown transcript and
raw JSON remain private to the local user.

Then inspect the export without printing transcript content:

```bash
lrh conversation inspect-export \
  "$HOME/.lrh/private/codex/export.md" \
  --source "$HOME/.lrh/private/codex/raw.json" \
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

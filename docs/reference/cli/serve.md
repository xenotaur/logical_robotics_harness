# `lrh serve`

## Command purpose

`lrh serve` starts the safe-default LRH local read-only viewer. It is a local viewer entrypoint for human review workflows and does not run autonomous execution.

## Canonical invocation patterns

```bash
lrh serve
lrh serve --host 127.0.0.1 --port 8765
lrh serve --project-root /path/to/repo
lrh serve --codex-archive-root private/codex-conversations
lrh serve --show-config
python -m lrh.cli.main serve --show-config
```

## Important options and arguments

- `--host HOST`: bind host. Defaults to `127.0.0.1`.
- `--port PORT`: bind port. Defaults to `8765`.
- `--project-root PROJECT_ROOT`: repository root used for read-only viewer summaries. Defaults to `.`.
- `--codex-archive-root PATH`: explicitly configure a local directory of Codex
  conversation Markdown exports for read-only archive viewing. May be supplied
  more than once. Relative paths are resolved under `--project-root`.
- `--allow-nonlocal-host`: explicitly allow binding beyond localhost.
- `--show-config`: validate and print deterministic JSON configuration without serving.
- `-h`, `--help`: print command help.

## Current behavior and limitations

- This command is intentionally safe-default and read-only.
- Non-local host binding requires explicit opt-in with `--allow-nonlocal-host`.
- `--show-config` is a non-serving diagnostics mode.
- The local viewer/workbench is not an autonomous runner.
- Codex archive viewing is opt-in. Without `--codex-archive-root`, the
  conversation archive routes report no exports and do not browse local files.
- Archive index and API list routes expose manifest/status metadata only. The
  HTML detail route renders transcript bodies as escaped inert text after an
  explicit export selection.

## Conversation archive routes

- `/conversations/codex`: HTML index for configured Codex export roots.
- `/conversations/codex/<export_id>`: HTML detail page for one configured export.
- `/api/conversations/codex`: deterministic JSON archive metadata without
  transcript body text.
- `/api/conversations/codex/<export_id>`: deterministic JSON detail metadata
  without transcript body text.

## Related how-to pages

- [Conversation CLI reference](conversation.md)
- [Use the developer sandbox](../../how-to/use-the-developer-sandbox.md)
- [Inspect workspace state](../../how-to/inspect-workspace-state.md)

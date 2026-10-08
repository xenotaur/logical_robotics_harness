# `lrh serve`

## Command purpose

`lrh serve` starts the safe-default LRH local read-only viewer. It is a local viewer entrypoint for human review workflows and does not run autonomous execution.

## Canonical invocation patterns

```bash
lrh serve
lrh serve --host 127.0.0.1 --port 8765
lrh serve --project-root /path/to/repo
lrh serve --codex-archive-root private/codex-conversations
lrh serve --theme dark
lrh serve --show-config
python -m lrh.cli.main serve --show-config
lrh serve --desktop-protocol
```

## Important options and arguments

- `--host HOST`: bind host. Defaults to `127.0.0.1`.
- `--port PORT`: bind port. Defaults to `8765`.
- `--project-root PROJECT_ROOT`: repository root used for read-only viewer summaries. Defaults to `.`.
- `--codex-archive-root PATH`: explicitly configure a local directory of Codex
  conversation Markdown exports for read-only archive viewing. May be supplied
  more than once. Relative paths are resolved under `--project-root`.
- `--allow-nonlocal-host`: explicitly allow binding beyond localhost.
- `--theme {light,dark,system}`: page theme. `system` (the default) follows the
  operating system's light or dark appearance; `light` and `dark` pin every
  page to that theme. Also accepted with `--desktop-protocol`, where LRH Console
  passes its **Appearance** setting.
- `--show-config`: validate and print deterministic JSON configuration without serving.
- `--desktop-protocol`: run under a desktop supervisor. Reads a versioned JSON
  start request on stdin, binds `127.0.0.1` on an OS-assigned port, and reports
  ready/failed and lifecycle events as JSON lines on stdout; human logs go to
  stderr. Cannot be combined with the options above, except `--theme`. See the
  [desktop server protocol](../desktop-server-protocol.md).
- `--desktop-start-timeout SECONDS`: with `--desktop-protocol`, how long to wait
  for the start request (default 10, range 0.1–120).
- `-h`, `--help`: print command help.

## Current behavior and limitations

- This command is intentionally safe-default and read-only.
- Non-local host binding requires explicit opt-in with `--allow-nonlocal-host`.
- `--show-config` is a non-serving diagnostics mode. Its JSON includes the
  `theme`.
- Every HTML page is shown inside the LRH Console frame:
  - a top bar with the LRH icon (always a link home to `/meta`), the page
    name and scope, the render time, refresh, and a gear that links to
    `/settings`;
  - a sidebar with a scope switcher (All projects, or a project from the Meta
    registry) and that scope's views. It collapses to an icon rail without
    scripts, and is a rail by default on narrow screens;
  - a detail drawer, opened by adding `?item=<id>` to a page's URL.
- `/settings` is a read-only display and about page: the theme, how to
  change it, the `lrh` version, and the font and icon licenses. LRH Console
  opens its own Settings window instead.
- `/static/<asset>` serves only the frame's packaged files: the LRH icon, the
  Montserrat subset and its SIL OFL license, and the Lucide icons' ISC license.
  Any other path is 404.
- The Content-Security-Policy allows inline styles and same-origin images and
  fonts only, and no scripts.
- Pages take their colors from the shared LRH Console token file. The
  read-only `/style` page shows every token in the current theme.
- Without `--desktop-protocol`, the command runs in the foreground, prints one
  human-readable `listening on` line to stdout, and stops on Ctrl+C. Desktop
  mode does not change that behavior or any HTTP route or header.
- The local viewer/workbench is not an autonomous runner.
- Codex archive viewing is opt-in. Without `--codex-archive-root`, the
  conversation archive routes report no exports and do not browse local files.
- Archive index and API list routes expose manifest/status metadata only. The
  HTML detail route renders transcript bodies as escaped inert text after an
  explicit export selection.

## Dependency-map route

- `/api/project/<project_id>/dependency-maps/<view>`: the versioned
  `DependencyMapSnapshot` JSON for a view declared in
  `project/views/dependency_maps/<view>.md`. It returns 404 for an unknown
  view, 422 for an invalid declaration, and 500 if the project's control files
  cannot be loaded. `lrh dependency-map snapshot <view>` prints the same JSON;
  see the [dependency-map reference](dependency-map.md).

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

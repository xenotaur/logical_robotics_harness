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
- `--interactive`: add packaged, same-origin scripts. The Content-Security-Policy
  then adds `script-src 'self'`, and nothing else; there is no inline script
  and no `eval`. Every page still works without the scripts. They add:
  - **Tracing:** while nothing is selected, hovering over or focusing a
    dependency-map card previews its upstream and downstream. Clicking selects
    it without a reload, opens its drawer, and updates `?item=` and the page's
    tab links. Escape closes it.
  - **Filters:** checkboxes by state on the map and table. A filter never hides
    an unfinished item that a shown item still needs.
  - **Loading:** when a same-origin page takes longer than about 300 ms to
    load, the page dims and a "Loading…" status appears. Links that open
    elsewhere, downloads, and in-page selections never trigger it.
  - **Theme switch:** Light, Dark, and System in the top bar, remembered by the
    browser for that server address and applied before the page first paints.
    LRH Console's server gets a new port each time it starts, so the choice
    resets when the app or its server restarts; Settings > Appearance is the
    lasting setting. The switch is hidden when `--theme light` or `--theme dark`
    pins the theme.

  Without the flag, the script URLs (`lrh-interactive.js` and
  `lrh-theme-early.js`) return 404. `--show-config` reports
  `interactive`. Also accepted with `--desktop-protocol`, which LRH Console
  always passes.
- `--show-config`: validate and print deterministic JSON configuration without serving.
- `--desktop-protocol`: run under a desktop supervisor. Reads a versioned JSON
  start request on stdin, binds `127.0.0.1` on an OS-assigned port, and reports
  ready/failed and lifecycle events as JSON lines on stdout; human logs go to
  stderr. Cannot be combined with the options above, except `--theme` and
  `--interactive`. See the
  [desktop server protocol](../desktop-server-protocol.md).
- `--desktop-start-timeout SECONDS`: with `--desktop-protocol`, how long to wait
  for the start request (default 10, range 0.1–120).
- `-h`, `--help`: print command help.

## Current behavior and limitations

- This command is intentionally safe-default and read-only.
- The server caches each project's loaded state, validation results, and
  dependency-map snapshots, and reuses them only while that project's
  `project/` files are unchanged (same paths, sizes, modification times, and
  inodes). Any edit, addition, deletion, or rename is picked up on the next
  request, including inside symlinked directories. An edit that keeps a file's
  size and lands within the same filesystem timestamp tick is not detected
  until another change. A cached dependency-map snapshot is
  served with the current time and git HEAD, exactly as a fresh build would
  be.
- Right after it starts listening (in both modes), the server warms that
  cache on one background thread: `/meta`'s projects first, then the served
  project, then every project's dependency-map views. Startup and the
  desktop-protocol ready event never wait for it. A request for a value the
  warm-up is still building waits for that build rather than repeating it.
  It logs one line to stderr when done (`lrh serve: cache warmed for N
  project(s) in Xs`), or the error if it fails; responses are unaffected
  either way.
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

## Statusboard route

- `/meta`: the statusboard, LRH Console's home view. It shows every project in the
  Meta registry in exactly one band, by operational state: **Blocked**, **Needs
  attention**, **Active work**, **Awaiting review**, **Stable**, and **Unknown**
  (when LRH cannot establish a state). Each band has a symbol, label, count, and
  description, so no band is told apart by color alone. Bands are `<details>`
  elements: they collapse and expand without scripts, bands with projects start
  open, and empty bands stay visible but closed.
- Each project card shows its focus, next action, a validation chip, and a
  freshness chip ("Read live" with the time, or why it was not read). The full
  registry facts and diagnostics are under **Details**.
- `/api/meta` returns the same bands as JSON, in the same order, with a
  `read_at` timestamp. Each project's `triage_lane` is its band's `status`.

## Dependency-map routes

- `/project/<project_id>/dependency-maps`: the project's declared views, or an
  explanation of how to declare one.
- `/project/<project_id>/dependency-maps/<view>`: the view as a script-free map
  in the frame. Lanes are columns and phases are rows. Each card shows the
  item's ID, title, structural state (icon, text, and color), a "Not
  prompt-ready" flag when relevant, and why it is waiting or blocked. Solid
  lines are "depends on" and dashed lines are "blocked by"; they run from the
  prerequisite to the item that needs it.
  - `?item=<id>` selects a card: its upstream and downstream cards and lines
    are highlighted, and the detail drawer shows the three state layers,
    placement, reasons, needs, needed-by, the source path, and effort (not
    modeled yet).
  - `?tab=table` shows every item as a table, and `?tab=blockers` lists each
    waiting or blocked item with what it needs.
  - **Check for changes** reloads with `?since=<fingerprint>` and says whether
    the control files changed since the snapshot you were viewing.
  - Narrow screens show the map as a list grouped by phase.
  - It returns 404 for an unknown view, and an explanatory page with 422 for an
    invalid declaration or 500 if the sources cannot be read.

- `/api/project/<project_id>/dependency-maps/<view>`: the versioned
  `DependencyMapSnapshot` JSON for a view declared in
  `project/views/dependency_maps/<view>.md`. It returns 404 for an unknown
  view, 422 for an invalid declaration, and 500 if the view or the project's
  control files cannot be read. As with the other `/project/<project_id>/`
  routes, a `project_id` that the Meta registry cannot resolve to a local
  checkout falls back to the served project. HEAD builds the snapshot as GET
  does, so the two always agree. `lrh dependency-map snapshot <view>` prints
  the same JSON; see the [dependency-map reference](dependency-map.md).

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

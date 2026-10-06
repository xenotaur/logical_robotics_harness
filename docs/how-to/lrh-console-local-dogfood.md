# Use the LRH Console desktop app

LRH Console is a Mac app that runs its own private `lrh serve` and shows the
existing read-only Serve and Meta views in a window. You don't need to start a
server from a terminal. This guide covers building and installing it, first
run, everyday use, recovery, its limitations, and the manual checklist the
dogfood sessions use.

The app is a local developer build. It is not signed or distributed, it does
not bundle Python, and only macOS is supported for daily use.

## Build and install

You need the desktop toolchain once. See
[Setting up the desktop app toolchain](project-setup/desktop-toolchain.md).

```bash
scripts/develop --desktop
```

```bash
apps/desktop/scripts/run bundle
```

This builds `apps/desktop/src-tauri/target/release/bundle/macos/LRH Console.app`.
Drag it to `/Applications` if you want it in Launchpad and the Dock. It is not
code-signed, so if macOS blocks the first open, Control-click the app and
choose **Open**.

## First run

With no saved configuration, the main window shows **Set up LRH Console** and
the Settings window opens. Fill in:

- **Server program.** Choose one of:
  - an installed `lrh` executable, such as `…/envs/lrh/bin/lrh`;
  - a Python interpreter plus an optional `PYTHONPATH`, for a source
    checkout. For example, interpreter `…/envs/lrh/bin/python` and
    `PYTHONPATH` `<checkout>/src`.

  Every path must be absolute. The app never searches your shell `PATH` and
  never activates Conda, because apps opened from the Dock don't see your
  shell's environment.
- **Workspace:** the absolute path of an LRH repository root. Its
  `project/` directory must contain `focus/` and `work_items/`.
- **Browser:** Google Chrome or the default browser. External links and
  **View > Open in …** use this choice.
- **Start the server when LRH Console opens:** on by default.

Choose **Save**. The app checks every value before saving. If a value is
wrong, it is rejected with a message next to the field, and the previous
settings stay in effect. The first save starts the server, unless you turned
that off. Later changes to the program or workspace wait for a restart. The configuration is stored in
`~/Library/Application Support/io.github.xenotaur.lrh-console/config.json`,
and only you can read the file.

To serve a different checkout or switch interpreters, change Settings and
choose **Restart server now**. Changes to the program or workspace only take
effect when the server restarts.

## Everyday use

| Action | How |
| --- | --- |
| Open Settings or Server Details | **LRH Console > Settings…** (⌘,) or **Server > Server Details…** (⌘I). There is only one window, with Settings on the left and Server Details on the right. Choosing either again brings it to the front; **Server Details…** also scrolls to and briefly highlights the details. |
| Start, stop, restart the server | **Server > Start / Stop / Restart Server**. Each item is enabled only when it applies. |
| Go to the dashboard or Meta | **View > Dashboard** (⌘0) or **View > Meta** (⇧⌘M). |
| Reload | **View > Reload** (⌘R). |
| Go back or forward | **View > Back** (⌘[) or **View > Forward** (⌘]). They move between pages of the running server only, never to a status page or a previous server's address, and are enabled only when there is a page to go to. A restart starts a fresh history. |
| Open the current page in a browser | **View > Open in Chrome**, or **View > Open in Default Browser**. |
| Hide the window | Close it (⌘W). The app and server keep running, and clicking the Dock icon brings the window back. |
| Quit | ⌘Q, or **LRH Console > Quit LRH Console**. The window shows "Stopping LRH server…" while the server stops, then the app exits. Quitting from the Dock menu exits at once, and the server then stops itself within a few seconds because its parent is gone. |

How the app behaves:

- The app owns exactly one server. It never adopts, stops, or signals an
  `lrh serve` that you started yourself.
- If the app crashes, its server notices that the parent is gone and exits
  within a few seconds.
- The main window shows only the app's own pages and the current server's
  exact local address.
- Links to other sites open in your browser, at most one per second. Popups
  never open inside the app.
- Web content in the main window has no access to native commands. Only the
  Settings window does, and it shows only the app's own bundled pages.

## Recovery

| Main window shows | What to do |
| --- | --- |
| **Set up LRH Console** | Open Settings (⌘,) and save a program and workspace. |
| **Server failed**, code `workspace_not_lrh_project` or `invalid_workspace` | The workspace is wrong. Fix it in Settings. |
| **Server failed**, code `spawn_failed` | The program path cannot be run. Fix it in Settings. |
| **Server failed**, code `exited_before_ready` | Python could not start LRH, usually because of the interpreter or `PYTHONPATH`. Check **Server Details** for the output. |
| **Server failed**, code `startup_timeout` or `exited_unexpectedly` | Check **Server Details**, then choose **Server > Start Server** again. |
| **Incompatible server** | The configured `lrh` speaks a different desktop protocol version, or served a different workspace. Update `lrh`, or choose another program. |

**Server Details** shows:

- the state and the owned process ID;
- the endpoint;
- the configured and served workspaces. When the configured path is a
  symlink to the served one, the served row says they are the same directory;
- the protocol and server versions;
- the last error and exit code;
- the result of the last browser handoff;
- the last 64 KiB of the server's output.

That output can contain local paths. The app never uploads it or puts it in
URLs.

## Developer launch

To run the built app against this checkout's own source:

```bash
apps/desktop/scripts/run launch
```

The `LRH_CONSOLE_*` variables override the saved Settings for that session.
See [the toolchain how-to](project-setup/desktop-toolchain.md#build-and-run-the-app).

## Embedded view and browser

| Interaction | In the app | In a browser |
| --- | --- | --- |
| Dashboard, Meta, project, work-item, and design pages | Works | Works (same origin, same project) |
| Workbench prompt, run-packet, and run-report previews | Works | Works |
| `?download=1` Markdown downloads | Handed to the chosen browser, which saves the file (the app never writes files) | Works |
| JSON routes (`/api/...`) | Shown as text | Shown as text |
| Links to other sites | Opened in the chosen browser | Normal |

When Chrome is not installed, **View > Open in Chrome** reads "not found: uses
default browser", and handoffs use the default browser. Server Details records
which browser was used. Both views show the same project, because the browser
opens the app's own server address.

## Limitations

- macOS is the only platform supported for daily use. On Linux and Windows,
  closing the window quits the app, and browser handoff is not available on
  Windows.
- The app is not signed or notarized, and has no installer, updates, or login
  autostart.
- One workspace at a time. Use Meta for cross-project views.
- ⌘Q waits for a server that is still starting to finish starting or time
  out, then stops it. The window shows "Stopping…" meanwhile, and the app
  stays responsive.
- Links are handed to the browser whenever page content navigates away from
  the app's pages, including scripted navigation, not only clicks. Serve's
  own pages do not do this. The handoff is limited to one per second.
- The program's protocol version is checked when the server starts, not
  when you save Settings. An incompatible `lrh` shows the **Incompatible
  server** page.

## Validation

```bash
scripts/format --check --diff --desktop
```

```bash
scripts/lint --desktop
```

```bash
scripts/test --desktop
```

```bash
apps/desktop/scripts/run bundle
```

## Manual macOS checklist

Run these checks for each dogfood session. Record the results in
`project/evidence/EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD.md`.

1. Open LRH Console from the Dock. The dashboard appears without any
   terminal.
2. Choose **Server > Stop**. The page shows "Server stopped", and only
   **Start** is enabled.
3. Choose **Server > Start**. The dashboard returns.
4. Choose **Server > Restart**. The dashboard returns on a new port.
5. Use **View > Meta**, **View > Dashboard**, and **View > Reload**. Open
   `/health`, then use **View > Back** (⌘[) to return, and **View > Forward**
   (⌘]) to go there again.
6. Click an internal link; it opens in the app. Click an external link; it
   opens in the browser.
7. Use **View > Open in Chrome** and **Open in Default Browser**. Both show
   the same project as the app.
8. Open **Settings…** twice. There is still only one window, and closing it
   leaves the server running.
9. In Settings, enter a bad workspace path and save. Saving is rejected, and
   the previous settings still work.
10. Change the workspace, choose **Restart server now**, and check that the
    new project is served. Then switch back.
11. Close the window; the app stays in the Dock. Click the Dock icon; the
    window returns.
12. Force a startup failure. Settings rejects paths that are relative,
    missing, or not executable, so use a real interpreter that cannot import
    LRH: set the interpreter to `/usr/bin/python3` (or any Python without LRH
    installed), clear `PYTHONPATH`, save, and choose **Restart server now**.
    Run this with the app opened from the Dock, so no `PYTHONPATH` is
    inherited from a shell. On a Mac without the Command Line Tools,
    `/usr/bin/python3` offers to install them instead; pick another Python. The page shows **Server failed** with
    `exited_before_ready`, and Server Details explains it. Restore your
    interpreter and `PYTHONPATH`, then start the server again.
13. Start an unrelated `lrh serve` in a terminal. Stop, Restart, and Quit in
    the app leave it running.
14. Choose **Server > Restart**, then press ⌘Q at once. The app shows
    "Stopping…", then exits. No `lrh serve --desktop-protocol` process
    remains (`pgrep -fl -- 'serve --desktop-protocol'` prints nothing).
15. Crash the server while the app is running. Use the PID that Server
    Details shows under **Owned process**, so nothing else is signaled:

    ```bash
    kill <owned-process-pid>
    ```

    The page shows **Server failed** with `exited_unexpectedly`. Choose
    **Server > Start Server**, and the dashboard returns.
16. Crash the app. Find the PID of the app installed in `/Applications`.
    The anchored pattern leaves other builds alone, including a dev or bundle
    build running from a worktree:

    ```bash
    pgrep -fl '^/Applications/LRH Console.app/Contents/MacOS/lrh-console'
    ```

    Then kill that PID:

    ```bash
    kill -9 <app-pid>
    ```

    Within a few seconds the server exits on its own, so
    `pgrep -fl -- 'serve --desktop-protocol'` prints nothing. Reopen LRH
    Console from the Dock, and the dashboard returns.
17. Note anything slow, confusing, or missing.

Steps 12, 15, and 16 force failures deliberately. Run them at least once
across the dogfood sessions. You don't need to wait for a real failure.

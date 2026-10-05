---
id: EV-LRH-CONSOLE-DESKTOP-L0-DOGFOOD
title: "LRH Console L0 Mac dogfood sessions"
type: manual_review
status: recorded
related_work_items:
  - WI-LRH-CONSOLE-DESKTOP-DOGFOOD
  - WI-SERVE-QUIET-CLIENT-DISCONNECT
  - WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH
  - WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH
related_focus: []
source:
  kind: manual_dogfood_sessions
  operator: anthony
  command: "LRH Console.app opened from the Dock; manual checklist in docs/how-to/lrh-console-local-dogfood.md"
  captured_at: 2026-10-05T04:08:39Z
  base_commit: ef8c6cbcd396619b7d2cd9a8a6cfec7d77265c8d
summary_result: pass_with_limits
artifacts:
  - docs/how-to/lrh-console-local-dogfood.md
  - project/work_items/proposed/WI-SERVE-QUIET-CLIENT-DISCONNECT.md
  - project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH.md
  - project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH.md
  - project/design/backlog.md
metrics:
  sessions_recorded: 9
  sessions_with_explicit_dock_launch: 4
  sessions_with_terminal_server_startup: 0
  session_failures: 0
  checklist_steps_passed: 14
  checklist_steps_partial: 2
  checklist_steps_not_exercised: 0
  forced_failures_recovered: 3
  python_tests: 1907
  desktop_rust_tests: 58
blocked_actions:
  - "External-link handoff (checklist step 6) was not exercised by hand, because Serve's pages contain no external links."
  - "The Chrome-absent fallback was not exercised. Chrome showed as installed in every session that recorded the row, and no automated test covers the fallback path."
  - "A forced workspace mismatch (Incompatible backend because a different workspace was served) was not exercised. The symlinked-workspace case was observed in every session instead."
  - "All sessions used the LRH workspace. LCATS was not used, so the work item's open question is answered as LRH only for L0."
  - "Per-session dates were not recorded. The owner reports that sessions 0 to 0.3 ran mostly on 2026-10-02, and sessions 1 to 5 mostly on 2026-10-04, ending just after midnight on 2026-10-05 local time."
  - "The session notes show that a separately started lrh serve kept working (step 13), but not which app actions ran while it was up. The owner later thinks Stop, Restart, Quit, and the forced failure were all tried with it running. That is a recollection, not a session-time record, so an explicit re-check is tracked in the backlog."
  - "Only macOS was observed. This record makes no Linux or Windows claim."
modified_actions:
  - "Checklist step 12 could not be run as written, because Settings rejects bad paths. The how-to now gives a recipe (a real interpreter that cannot import LRH), and adds steps 15 and 16 for backend and app crash recovery. Steps 1 to 14 keep their numbers. The process checks now use kill <owned-process-pid> and pgrep -fl -- 'serve --desktop-protocol', so they cannot match unrelated processes. The app-crash step now kills only the installed app's PID, found with pgrep -fl 'LRH Console.app/Contents/MacOS/lrh-console'. The owner's session 5 used the earlier pkill -9 -x lrh-console and pgrep -fl desktop-protocol forms."
  - "Code defects were filed as three grouped work items rather than one per defect, at the owner's direction."
approval_records:
  - "2026-10-05: the owner, in chat, waived the Chrome-absent fallback, forced workspace mismatch, and external-link handoff checks for L0 closure, deferring them to later dogfooding."
  - "2026-10-05: after PR #766 review, the owner, in chat, accepted two further acceptance gaps for L0 closure: per-session dates known only at day level from the owner's recollection, and a Dock launch known only from recollection for session 2, the fifth of the five sessions counted toward the gate."
---

# LRH Console L0 Mac dogfood sessions

This records the owner's real use of the LRH Console Mac app for the L0b gate
in `WS-LRH-CONSOLE-LOCAL-DOGFOOD`. That gate asks for "five real sessions
without terminal startup", plus setup, crash, stop/restart, close/reopen, and
Quit evidence on macOS.

Every session result below comes from the owner's own notes. The agent that
drafted this record ran no sessions and added no results. Its own
contribution is limited to the automated checks under
[Automated validation](#automated-validation-observed) and the code facts
cited for each defect.

## Environment

| Item | Value |
| --- | --- |
| Mac | macOS 27.0.1 (build 26A434, Darwin 27.0.0, arm64) |
| App | LRH Console 0.1.0, unsigned local build from `apps/desktop/scripts/run bundle`, copied to `/Applications` and kept in the Dock |
| Backend program | Python mode: interpreter `/Users/centaur/anaconda3/bin/python3` (3.11.8), with `PYTHONPATH` set to `<workspace>/src` |
| Backend versions | `lrh 0.2.5.dev3035+g127172996` (sessions 0 to 0.3); `lrh 0.2.5.dev3040+gef8c6cbcd` (sessions 1 to 4; session 5 did not record Server Details) |
| Configured workspace | `/Users/centaur/Workspace/LogicalRoboticsHarness/logical_robotics_harness`, a symlink |
| Served workspace | `/Users/centaur/Tempspace/Projects/LogicalRoboticsHarness/logical_robotics_harness`, the symlink's target |
| Browser | Google Chrome, shown as installed in every session that recorded the row (0.1, 0.3, 2, 3, and 4) |

## Sessions

Every session ran on the same Mac, with the workspace above and app 0.1.0. In
sessions 0 to 4, Server Details showed state `running`, a process "started by
this app", protocol version 1, and no last error or exit code. Session 5 did not
record Server Details.

| # | Opened | Length | Used for | Actions | Result | Friction and findings |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | After build and install | Not timed | First impressions; built the session template | Built, installed, started, configured Settings | Worked | Startup procedure: "A little clunky, but we'll get there." "Docs were reasonably easy to use." Overall: "It's a start but hard to tell what to do yet." The app does not look like the mockups (R6). The Settings window is too small (R4). Header and sidebar requests (R1, R2). File pickers (R5). Bigger buttons (R3). The build output location question (P1). macOS did not block the unsigned app. |
| 0.1 | Dock | 1 min | Dock double-click after adding the app to the Dock | Opened, configured Settings, quit | Worked | None |
| 0.2 | Dock | 5 min | UX review | Opened, followed various links, configured Settings, quit | Worked | Server Output showed a `BrokenPipeError` traceback, possibly after using Back (D5). `/health` has no way back (D8). Requests for a startup-page setting (R10) and starting on Meta (R11). Pages are complete but not yet actionable (R14). |
| 0.3 | Dock | 2 min | Startup window review | Clicked the Dock icon, opened Settings with ⌘,, quit | Worked | Slow start (R9). Request: show the cached last view, with a butter bar while the server starts (R12). |
| 1 | After copying to Applications | 2 min | Checklist "First run" | Built, copied to Applications, opened Settings with its shortcut, set the backend and workspace, tried wrong values (all caught), saved, restarted, stopped, started, resized both windows, ⌘Q | Worked | Request to remember window sizes (R13). Wording: "LRH Serve" versus "server" (D7). |
| 2 | Not stated | 8 min | Checklist "Everyday use" | Settings refocus, Stop/Start/Restart, Server Details, ⌘0 Dashboard, ⇧⌘M Meta, Reload, Open in Chrome, Open in Default Browser, ⌘W then Dock/menu to bring back, About, Quit | Worked | Server Details with Settings already open gives no visible response (D6). |
| 3 | Not stated | 2 min | Checklist "Recovery" | None needed | Worked | Same owned process (pid 31837) as session 2, so this continued that app run rather than starting a new launch. Recovery was forced in session 5. |
| 4 | Dock | ~10 min | Checklist "Manual macOS checklist" | Steps 1 to 14 (see below) | Worked | View Meta "kind of slow" (R9). Step 12 could not be forced from Settings (P6). |
| 5 | Not stated (reopened from the Dock after the app crash) | ~5 min | The checklist items missed in session 4 | Forced a startup failure, a backend crash, and an app crash (see below) | Worked | View Meta "kind of slow" (R9) |

No session needed a terminal server start. Four sessions (0.1, 0.2, 0.3, and
4) record a Dock launch at the start. Session 5 records a Dock reopen after
the forced app crash. Sessions 1, 2, 3, and 5 don't say how the app was
first opened. Session 3 shares session 2's owned process, so it is not a
separate launch.

## Manual checklist (observed)

The numbers follow `docs/how-to/lrh-console-local-dogfood.md`. Steps 1 to 14
ran in session 4 unless another session is named. Steps 15 and 16 were added
by this work item and ran in session 5.

| Step | Check | Observed |
| --- | --- | --- |
| 1 | Dock launch with no terminal | Pass. "Open from doc[k] doesn't start a terminal." |
| 2 | Server > Stop | Pass. Only Start was enabled. |
| 3 | Server > Start | Pass. The dashboard returned. |
| 4 | Server > Restart | Pass. The server came back on a new port. |
| 5 | View > Meta, Dashboard, Reload | Pass (sessions 2 and 4). Meta was "kind of slow" (sessions 4 and 5). |
| 6 | Internal and external links | **Partial.** Internal links opened in the app. There are no external links in Serve's pages to test. |
| 7 | Open in Chrome, Open in Default Browser | Pass (sessions 2 and 4). Both showed the same view as the app. |
| 8 | Open Settings twice | Pass. Still one window. In session 2, clicking another window and then Settings brought the same window back. |
| 9 | Bad workspace path | Pass (sessions 1 and 4). Bad paths were rejected, and all errors were caught. |
| 10 | Change the workspace and restart | **Partial.** A change was accepted only for a valid path. The notes don't say whether a second project was actually served. |
| 11 | Close the window, then click the Dock icon | Pass (sessions 2 and 4). The app stayed in the Dock, and the window returned. |
| 12 | Forced startup failure | Pass in session 5. In session 4 Settings rejected every bad value, so no failure could be forced. In session 5 the owner set a bad interpreter and `PYTHONPATH`. The page showed **Server failed**, "lrh exited before it was ready, often because Python could not import LRH…", error code `exited_before_ready`. After the owner restored the values, Start worked. |
| 13 | A separately started `lrh serve` | **Pass, with a limit.** The owner recorded "Independent `lrh serve` still works". The session notes don't say which app actions ran while it was up. Asked afterwards, the owner thinks they tried Stop, Restart, Quit, and the forced failure with it running (see [Owner decisions](#owner-decisions)). |
| 14 | Restart, then ⌘Q at once | Pass. The app quit, and the owner confirmed `pgrep -fl desktop-protocol` printed nothing afterwards. |
| 15 | Backend crash | Pass (session 5). The owner killed the backend process. The page showed **Server failed**, "LRH Serve stopped unexpectedly…", error code `exited_unexpectedly`. Start Server recovered. |
| 16 | App crash | Pass (session 5). `pkill -9 -x lrh-console` was entered at the 00:08:29 prompt (local time). `pgrep -fl desktop-protocol` was entered at the 00:08:39 prompt and printed nothing, so the orphaned backend had exited by then, at least 10 s later. Reopening from the Dock worked. |
| 17 | Notes | See the findings below. |

### Work item coverage

| Required check | Evidence |
| --- | --- |
| Dock launch | Step 1 and sessions 0.1, 0.2, 0.3, and 4 at start; step 11 (Dock icon brings the window back); session 5's Dock reopen after the app crash |
| Menus and keyboard | ⌘, (sessions 0.3 and 1), ⌘0 and ⇧⌘M (session 2), ⌘W and ⌘Q (sessions 1, 2, and 4), and the Server and View menus (sessions 2 and 4) |
| Close and reopen | Step 11 |
| Start, Stop, Restart, Quit | Steps 2 to 4 and 14, and sessions 1 and 2 |
| App crash and backend crash recovery | Steps 15 and 16 |
| Browser handoff | Step 7. The external-link handoff and the Chrome-absent fallback were not exercised (see the limitations). |
| Workspace mismatch | No forced mismatch. The symlink case ran in every session: Configured and Served differed as strings and resolved to the same directory. The app served it correctly and did not wrongly report **Incompatible backend**, but Details does not say the paths match (D1). |
| Separately started server untouched; CLI intact | Step 13: an independent `lrh serve` "still works". The session notes don't record which app actions ran alongside it. The owner thinks all of them did, including the forced failure (see [Owner decisions](#owner-decisions)). |

## Embedded versus browser interaction matrix (observed)

| Interaction | In the app | In Chrome or the default browser |
| --- | --- | --- |
| Dashboard and Meta | Works (sessions 2 and 4). Meta was "kind of slow" (sessions 4 and 5). | Works, with the same project and view (step 7) |
| Project, work-item, and design pages through internal links | Works (session 0.2 and step 6) | Not recorded separately. Step 7 opened the current page. |
| `/health` and other JSON routes | Shown as text. It is a dead end with no Back control (D8). | Not recorded |
| Workbench previews and `?download=1` downloads | Not exercised in these sessions | Not exercised in these sessions |
| External links | Not exercised, because none exist | Not applicable |

## Findings

### Code defects (work items filed)

| # | Defect | Source | Work item |
| --- | --- | --- | --- |
| D5 | Serve prints a `BrokenPipeError` traceback when the client leaves mid-response. It appears in Server Details' Recent Server Output ("Error log shows up in settings"), though Last error stayed "—". | Session 0.2, "perhaps" after using Back. The request served `project_viewer_payload` (`/api/project`) through `serve.py` `do_GET` → `_write_json` → `wfile.write`. | `WI-SERVE-QUIET-CLIENT-DISCONNECT` |
| D8 | There is no Back control. Link-less pages such as `/health` are dead ends. | Session 0.2 | `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` |
| D7 | The wording is inconsistent: "Starting LRH Serve…" (`ui/status.js`) versus "server" elsewhere. | Session 1 | `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH` |
| D6 | Server Details does not scroll into view when Settings is already open. Both menu items call `show_settings`. | Session 2 | `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` |
| D1 | A symlinked workspace looks like a mismatch in Server Details. | Every session | `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` |
| D2, D3 | The env-override wording is inaccurate, both for the browser choice and for an invalid override. | PR #763 final cold review | `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` |
| D4 | A dead `let _ = pid;` line in a supervisor test. | PR #763 final cold review | `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH` |

### Requests (routed to later increments, no work items yet)

| # | Request | Route |
| --- | --- | --- |
| R1, R2 | A top bar with logo, page name, and settings gear, and a collapsible left sidebar instead of the horizontal navigation | The visual-language style guide (`lrh-console-visual-language` proposal), then L1 UI |
| R3, R4 | Larger Save and Restart buttons, and a larger default Settings window | `WI-LRH-CONSOLE-DESKTOP-SETTINGS-POLISH`, and the style guide for button sizing |
| R5 | File-picker dialogs for paths | A separate decision. It needs Tauri's dialog plugin, a new native capability. |
| R6, R14 | "Could look more like mockups". Pages have "complete information, but it's not yet organized enough to be actionable and clear". | L1 and the visual-language proposal |
| R9 | Slow start (session 0.3) and slow Meta (sessions 4 and 5) | Measure Serve rendering versus the webview early in L1. L2 performance work if confirmed. |
| R10, R11 | A startup-page setting (default, last page, chosen page), and starting on Meta | L2 (daily workspace console). Depends on Meta speed. |
| R12 | Show the cached last view at startup, with server start as a butter bar or console line | L2 or L3 polish |
| R13 | Remember window sizes | A small shell item. Tauri's window-state plugin would be a capability decision. |
| P1 | Build output lives in `apps/desktop/src-tauri/target/`, which `scripts/clean` does not remove | A small repo-tooling item, such as `scripts/clean --desktop` running `cargo clean`, plus a STYLE entry |

## Automated validation (observed)

These ran on the dogfood Mac from this work item's branch, built from
`origin/main` at `e85a31e6`. Format and lint used the `LrhLocalAgent` conda
env's pinned tools, with `PYTHONPATH` set to this worktree's `src`.

| Command | Result |
| --- | --- |
| `scripts/test --desktop --log` | Python: `Ran 1907 tests in 120.772s`, `OK`. Rust: 27 unit, 9 capability-boundary, and 22 supervisor tests passed. Exit 0. |
| `scripts/format --check --diff --desktop` | Pass |
| `scripts/lint --desktop` | Pass |
| `scripts/check-workflows` | Pass |
| `lrh validate` | `Validation completed: 0 error(s), 0 warning(s)` |

## Recommendation

**Close the L0 gate. The owner has waived the checks that were not run (see
[Owner decisions](#owner-decisions)).** Across nine sessions the lifecycle held:

- no session failure;
- every forced failure recovered;
- an orphaned backend exited on its own after the app crashed;
- a separately started `lrh serve` kept working.

The work item requires a Chrome-absent fallback check and a deliberately
forced workspace mismatch. Neither was run, and the external-link handoff
was not shown either. The owner waived these three for L0 closure, and they
are tracked for later dogfooding. The separately started server's survival
of an app-side failure rests on the owner's recollection, and an explicit
re-check is tracked too. None of them is a lifecycle risk that should block
L1.

**L1 (dependency maps): proceed, with three adjustments.**

1. **The owner's friction is organization, not lifecycle.** The pages are
   complete but not actionable (R6, R14), and navigation is weak (R1, R2,
   D8). Decide the visual-language basics before building the L1 graph UI on
   top: header, sidebar, button sizing, and the "server" term. That way L1 is
   not restyled later.
2. **Measure Meta and full-page render time at the start of L1** (R9). L1 adds
   rendering cost, so a baseline is needed now.
3. **Answer LCATS early in L1.** L0 dogfood was LRH only, and the L1 gate
   requires LRH and LCATS planning questions.

The two polish work items can land before or alongside L1. They are
independent of the graph work.

**L3 (self-contained desktop): keep it gated as planned. Do not pull it
forward.** Setup worked:

- the unsigned app opened without a Gatekeeper block;
- first run caught every wrong value (session 1).

Sessions 0 to 0.3 each list Settings configuration among their actions, so
the notes don't show whether the absolute-path backend setup is fully
one-time.

On the build, install, and setup procedure, the owner wrote "A little
clunky, but we'll get there" and "Docs were reasonably easy to use". That is
friction, not a blocker. The proposal pulls packaging forward only if executable setup is the measured obstacle,
and these sessions do not show that. Carry these into L3 planning:

- startup feel (R12);
- window state (R13);
- the build output location (P1);
- bundling Python, so the interpreter and `PYTHONPATH` settings disappear.

Signing, notarization, and reboot and sleep/wake checks stay L3 evidence.

## Owner decisions

The owner answered these questions on 2026-10-05, after reading a draft of
this record. The answers are recollections given in chat, not session-time
notes, and are recorded with the owner's own hedging.

| Question | Owner's answer | Effect on this record |
| --- | --- | --- |
| How was the app opened at the start of sessions 1, 2, 3, and 5? | "Almost certainly the Dock. That's almost always where I open it." | With 0.1, 0.2, 0.3, and 4 (Dock launches in the notes), sessions 1, 2, and 5 bring Dock launches to seven by recollection. Session 3 continued session 2's app run. The five-session gate is met on the owner's recollection: four Dock launches recorded explicitly, three recalled. |
| Which app actions ran while the separately started `lrh serve` was up (step 13)? | "I think I tried all of those recommended actions while my server was running." | Step 13 is taken as covering Stop, Restart, Quit, and the forced failure, on the owner's recollection ("I think"). No session-time note records it, so an explicit re-check is tracked in the backlog. |
| Waive the checks that were not run? | "Waive these checks for now but leave them in the backlog or work items to dogfood later." | The question named three checks, and these are waived for L0 closure: the Chrome-absent fallback, a forced workspace mismatch, and external-link handoff. They are tracked in `project/design/backlog.md` under "Deferred LRH Console L0 dogfood checks". |

PR #766's hosted review then pointed out two acceptance gaps that the first
waiver did not cover. The work item asks each of five sessions to record its
Dock launch, date, and versions.

| Gap | What the record has | Owner's decision |
| --- | --- | --- |
| Per-session dates | No session-time dates. The owner recalls sessions 0 to 0.3 mostly on 2026-10-02, and sessions 1 to 5 mostly on 2026-10-04 to just after midnight on 2026-10-05. | Accepted at day level from recollection ("Go with A") |
| Five Dock-launched sessions with versions | Sessions 0.1, 0.2, 0.3, and 4 record a Dock launch and backend version. Session 2 records its backend version, and its Dock launch is recalled. Session 5 recorded no backend version and is not counted. | Accepted: session 2's Dock launch by recollection ("Go with A") |

With both waivers recorded, the recommendation above applies: close the L0
gate.

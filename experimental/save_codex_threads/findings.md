# Save Codex Threads Spike Findings

## 2026-08-07 Initial Context

- Current branch for this spike: `codex/codex-thread-export-spike`.
- Raw transcript data must not be committed.
- The previously implemented LRH Codex conversation path is file-based support,
  not a complete current-session exporter.
- The active technical risk is current Codex task capture.

## Already Observed Before This Spike Directory

- This Codex task exposes a current thread id through `CODEX_THREAD_ID`.
- `codex_app.list_threads` listed the current task by that id.
- `codex_app.read_thread` returned real current-task turn data by that id.
- `codex_app.read_thread` returned pagination metadata including `nextCursor`
  and `hasMore`.
- A follow-up `read_thread` call with the returned cursor returned older turns,
  so pagination is at least partially demonstrated.
- The model-visible tool route is therefore plausible for a skill-backed
  exporter.

## macOS Codex CLI Safety Finding

- While probing `codex app-server --help`, macOS displayed a malware warning for
  `codex-aarch64-apple-darwin`.
- `/opt/homebrew/bin/codex` pointed at
  `/opt/homebrew/Caskroom/codex/0.118.0/codex-aarch64-apple-darwin`.
- The target file was removed from the Homebrew cask directory.
- macOS logs showed `syspolicyd` moved an item with identifier `codex` and Team
  ID `2DC432GLL2` to Trash.
- Conclusion: do not use the Homebrew `codex` binary for this spike unless it is
  repaired or replaced from a trusted current source.

## Open Questions

- Can a user-run script call the same thread-read surface, or is it available
  only as a model-visible Codex app tool?
- Can a trusted app-server route read the current desktop task by
  `CODEX_THREAD_ID`?
- Does `read_thread` with high limits and pagination provide complete enough
  history for durable export?
- Which item types should be included in a raw transcript artifact, and which
  should be summarized or omitted by default?
- Should reasoning summaries be exported at all?

## Next Findings To Add

- Larger bounded page count and turn count from a `read_thread` pagination pass.
- Item type histogram from saved raw pages.
- Truncation and omitted-output observations.
- App-server route result, if a safe documented route is found.

## 2026-08-07 Phase 1 Bounded Read

Ran a bounded model-visible `codex_app.read_thread` call against the current
thread id from the Codex app context.

Sanitized observations:

- The call succeeded for the current thread.
- The returned thread metadata identified the thread as `kind: codex`, with
  `hostId: local`, an active status, and the LRH worktree as its current working
  directory.
- The response returned `schemaVersion: 1`.
- The response used newest-first paging.
- A `turnLimit` of 5 returned 5 turns.
- The returned page had `hasMore: true` and a `nextCursor`, so additional older
  history is available.
- The newest returned turn was still `inProgress`, which means an exporter must
  either mark active-turn captures as partial or default to completed turns only.
- The returned item types included `userMessage`, `reasoning`, `agentMessage`,
  and `fileChange`.
- With `includeOutputs: false`, command/tool output bodies were not expanded in
  this bounded read.

Implications:

- The model-visible `codex_app.read_thread` route can access real current-task
  data and pagination metadata.
- A skill-backed exporter is technically plausible.
- The exporter design needs an explicit policy for active turns and reasoning
  summaries.
- This does not yet prove a standalone LRH subprocess can read the same thread;
  that remains Phase 3.

## 2026-08-07 Phase 1 Pagination Continuation

Continued the model-visible `codex_app.read_thread` pagination pass using the
cursor returned by the initial page. The continuation remained bounded and used
`includeOutputs: false` to avoid expanding command or tool output bodies.

Sanitized observations:

- The second page request used `turnLimit: 10` and returned another page with
  `schemaVersion: 1`, newest-first ordering, `hasMore: true`, and a new
  `nextCursor`.
- The third page request used that cursor with `turnLimit: 10` and again
  returned newest-first ordering, `hasMore: true`, and a new `nextCursor`.
- Across the three bounded pages, the app tool returned 25 turns total without a
  pagination error.
- The continuation reached older completed LRH workflow turns, including prior
  work-item creation, execution, landing, and closeout activity in the same
  Codex task.
- Completed turns include start/completion timing and duration metadata.
- The item stream can contain multiple assistant commentary messages inside one
  turn, plus `reasoning` summaries and `fileChange` records.
- With output expansion disabled, the page still exposes enough turn and item
  structure to reconstruct a useful high-level transcript outline, but not
  enough command output detail for a faithful raw export.

Implications:

- Pagination appears stable enough to support a skill-backed bounded export
  prototype for long Codex tasks.
- The exporter should persist page-level cursor/completeness metadata in any
  private raw artifact so incomplete captures are auditable.
- A useful first exporter can probably default to metadata plus user/assistant
  messages and file-change summaries, with command output expansion controlled
  by an explicit privacy/sensitivity option.
- The model-visible route still does not establish that ordinary LRH CLI code
  can fetch the same task without Codex app tool mediation.

## 2026-08-07 Phase 3 App-Server Route First Pass

Fetched the current official Codex manual and inspected the documented
app-server route before attempting any standalone execution.

Sanitized observations:

- The official manual documents `codex app-server` as the interface for rich
  clients and conversation history.
- The documented app-server protocol is JSON-RPC over stdio, WebSocket, or Unix
  socket transports.
- The manual documents the required `initialize` / `initialized` handshake.
- The manual lists `thread/read` as the stable method to read a stored thread by
  id without resuming it.
- The running ChatGPT desktop app process has a child app-server process:
  `/Applications/ChatGPT.app/Contents/Resources/codex -c
  features.code_mode_host=true app-server --analytics-default-enabled`.
- That running child process does not show a `--listen` argument, which is
  consistent with default stdio transport rather than an attachable localhost or
  Unix-socket listener.
- `lsof` showed the process has this task's rollout JSONL file open, but the
  spike continues to treat direct storage inspection as out of scope because the
  plan forbids relying on undocumented Codex app storage internals.
- The ChatGPT-bundled candidate binary and the plugin-appserver candidate binary
  are byte-identical by SHA-256:
  `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`.
- Both candidate binaries failed `codesign --verify --strict --verbose=4` with
  `invalid signature (code or signature have been modified)`.
- The enclosing `/Applications/ChatGPT.app` bundle also failed
  `codesign --verify --deep --strict`.
- Because of the earlier macOS malware block and the failed signature
  verification, no standalone app-server binary was executed in this pass.

Implications:

- The documented JSON-RPC method needed by LRH exists: `thread/read`.
- The already-running desktop app-server is not obviously attachable through a
  documented listener from an ordinary LRH subprocess.
- The current local executable candidates are not acceptable for a safe
  standalone route test until the local installation is repaired or replaced
  from a trusted source.
- Phase 3 is therefore blocked on installation trust, not on the documented API
  shape.
- The safest next implementation direction remains a skill-backed exporter
  using `codex_app.read_thread`, while a standalone LRH CLI adapter should wait
  for a trusted app-server executable or listener.

## 2026-08-07 Post-Reinstall Trust Check

After reinstalling ChatGPT/Codex and reinstalling the Homebrew Codex cask, ran a
second read-only trust check before attempting any standalone app-server
execution.

Sanitized observations:

- Homebrew now points `/opt/homebrew/bin/codex` at
  `/opt/homebrew/Caskroom/codex/0.147.0/bin/codex`.
- The previous stale `0.118.0` Homebrew installation is no longer the active
  path.
- The Homebrew `0.147.0` binary is a Mach-O arm64 executable.
- `codesign --verify --strict --verbose=4 /opt/homebrew/bin/codex` still fails
  with `invalid signature (code or signature have been modified)`.
- `spctl -a -vvv -t execute /opt/homebrew/bin/codex` returns
  `internal error in Code Signing subsystem`.
- The Homebrew cask payload has `com.apple.quarantine` and
  `com.apple.provenance` extended attributes.
- ChatGPT is now version `26.803.41515`.
- `codesign --verify --deep --strict --verbose=2 /Applications/ChatGPT.app`
  still fails with `invalid signature (code or signature have been modified)`.
- `codesign --verify --strict --verbose=4
  /Applications/ChatGPT.app/Contents/Resources/codex` still fails with
  `invalid signature (code or signature have been modified)`.
- The Homebrew binary and ChatGPT-bundled app-server binary are different
  files by SHA-256, and both currently fail local signature verification.
- No `codex --version`, `codex app-server`, or embedded app-server executable
  was run in this check because verification failed first.

Implications:

- Reinstallation fixed the stale Homebrew path, but it did not make the local
  standalone executable candidates pass macOS signature checks.
- This preserves the Phase 3 blocker: LRH should not yet use a standalone
  app-server subprocess route on this machine.
- The safest next LRH implementation path remains a Codex-skill-mediated export
  using the already-proven `codex_app.read_thread` tool.
- In parallel, the local trust issue should be reported or investigated
  upstream with version, hash, code-signing, quarantine, and Gatekeeper outputs.

## 2026-08-07 Re-Run Suspected Help Command

After user confirmation and monitoring for macOS pop-ups, re-ran the command
that likely triggered the original malware block before the reinstall:

```bash
/opt/homebrew/bin/codex app-server --help
```

Sanitized observations:

- Before the run, `/opt/homebrew/bin/codex` pointed at
  `/opt/homebrew/Caskroom/codex/0.147.0/bin/codex`.
- Before the run, the target binary existed with size `219997536` and inode
  `349419851`.
- The command exited with status 0 and printed app-server help text.
- The help text documented `daemon`, `proxy`, `generate-ts`,
  `generate-json-schema`, and `help` subcommands.
- The help text documented `--listen` values: `stdio://`, `unix://`,
  `unix://PATH`, `ws://IP:PORT`, and `off`, with default `stdio://`.
- After the run, the target binary still existed with the same size and inode.
- `codesign --verify --strict --verbose=4 /opt/homebrew/bin/codex` still failed
  with `invalid signature (code or signature have been modified)`.
- The binary still had `com.apple.quarantine` and `com.apple.provenance`
  extended attributes.

Implications:

- The original malware block was not reproduced by this single post-reinstall
  `app-server --help` run.
- The Homebrew `0.147.0` command can at least print app-server help in this
  environment.
- The local trust state remains ambiguous: successful execution does not
  override the failed strict signature verification.
- A narrowly scoped follow-up could test a local `stdio://` app-server
  JSON-RPC handshake against the Homebrew binary, but doing so would execute
  more of the same binary than `--help`; that should remain an explicit user
  decision.

## 2026-08-07 Minimal Stdio App-Server Handshake

After user confirmation and monitoring for macOS pop-ups, added and ran
`probe_app_server_stdio.py`, a minimal sanitized probe for the documented
app-server stdio route.

Probe behavior:

- Spawned `/opt/homebrew/bin/codex app-server --listen stdio://`.
- Sent `initialize` with LRH spike client metadata.
- Sent the `initialized` notification.
- Sent `thread/read` with the current task id and `includeTurns: false`.
- Printed only a structural summary of the returned thread object.
- Closed stdin and terminated the app-server process after the response.

Sanitized observations:

- The probe exited with status 0.
- `thread/read` returned `ok: true` for thread
  `019fc43f-e2d9-7503-88cb-9d9a8136c111`.
- The returned thread summary reported `ephemeral: false`.
- The returned runtime status was `notLoaded`, matching the expectation that
  `thread/read` does not resume or load the thread.
- `turns` was present as an empty list because the request used
  `includeTurns: false`.
- The returned thread summary included metadata keys such as `cwd`, `gitInfo`,
  `historyMode`, `modelProvider`, `name`, `path`, `preview`, `sessionId`,
  `source`, `threadSource`, and timestamps.
- After the run, the Homebrew target binary still existed with the same size and
  inode observed before the run.
- `codesign --verify --strict --verbose=4 /opt/homebrew/bin/codex` still failed
  with `invalid signature (code or signature have been modified)`.

Implications:

- The standalone Homebrew Codex app-server route can perform the documented
  stdio `initialize` / `initialized` / `thread/read` sequence on this machine.
- This substantially reduces the technical risk for an LRH CLI-backed
  app-server adapter.
- A raw export still requires a second, explicit test that requests actual turn
  data, either via stable `thread/read` with `includeTurns: true` or via the
  experimental paged `thread/turns/list` method.
- The trust state remains unresolved: functional success does not explain or
  clear the failed strict signature verification.

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

## Initial Open Questions

- Can a user-run script call the same thread-read surface, or is it available
  only as a model-visible Codex app tool?
- Can a trusted app-server route read the current desktop task by
  `CODEX_THREAD_ID`?
- Does `read_thread` with high limits and pagination provide complete enough
  history for durable export?
- Which item types should be included in a raw transcript artifact, and which
  should be summarized or omitted by default?
- Should reasoning summaries be exported at all?

These are answered or reframed later in this file. The most important update is
that both the model-visible tool route and the standalone app-server route can
read this real Codex task.

## Next Findings To Add Or Defer

- Optional private raw capture inspection under `/private/tmp`.
- Optional upstream/local investigation of the failed strict signature
  verification.
- Production work item creation from the recommended implementation scope below.

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

## 2026-08-07 Turn Data Route Comparison

Extended `probe_app_server_stdio.py` with a sanitized compare mode and tested
multiple app-server routes for actual turn data.

Probe behavior:

- Used the same stdio app-server handshake as the prior probe.
- Enabled `experimentalApi` in the client capabilities so experimental methods
  could be tested explicitly.
- Ran stable `thread/read` with `includeTurns: true`.
- Ran experimental `thread/turns/list` with `itemsView: notLoaded`.
- Ran experimental `thread/turns/list` with `itemsView: summary`.
- Followed the `itemsView: summary` `nextCursor` once to test page 2.
- Ran experimental `thread/turns/list` with `itemsView: full` and a limit of 2.
- Printed only sanitized structural summaries: counts, keys, item types,
  statuses, cursor presence, and small turn metadata samples.

Sanitized observations:

- All comparison probes returned `ok: true`.
- Stable `thread/read` with `includeTurns: true` returned all 116 turns in one
  response.
- The full stable read included 115 completed turns and 1 interrupted turn.
- The full stable read included item types: `userMessage`, `agentMessage`,
  `reasoning`, `fileChange`, `webSearch`, and `contextCompaction`.
- The full stable read appears to return the thread in chronological order, with
  the oldest sampled turns first.
- `thread/turns/list` with `itemsView: notLoaded` returned 5 newest turns with
  statuses and timing metadata, but no item content.
- `thread/turns/list` with `itemsView: summary` returned 5 newest turns with
  `userMessage` and `agentMessage` summary items only.
- The summary route returned both `nextCursor` and `backwardsCursor`, and a
  second request using `nextCursor` returned another 5 turns.
- `thread/turns/list` with `itemsView: full` and limit 2 returned full item
  structure for the newest turns, including `reasoning`, `fileChange`, and
  `webSearch` item types.
- After the comparison run, the Homebrew target binary still existed with the
  same size and inode observed before the run.
- `codesign --verify --strict --verbose=4 /opt/homebrew/bin/codex` still failed
  with `invalid signature (code or signature have been modified)`.

Fitness comparison:

- `thread/read` with `includeTurns: true` is the best stable route for a first
  complete raw export prototype because it returns the whole stored thread in a
  single documented call.
- `thread/read` with `includeTurns: true` is less attractive for very large
  tasks because it is not paged; large responses may be memory-heavy and harder
  to resume after interruption.
- `thread/turns/list` with `itemsView: notLoaded` is useful for inventory,
  completeness checks, status summaries, and planning a paged export, but cannot
  render transcript content.
- `thread/turns/list` with `itemsView: summary` is a good safe-default preview
  or lightweight export route because it is paged and avoids expanded item
  detail, but it omits reasoning, file changes, and other item types needed for
  a faithful LRH session archive.
- `thread/turns/list` with `itemsView: full` is the best shape for scalable raw
  export because it is paged and includes rich item structure, but it is
  experimental and should be treated as an adapter behind a capability check.

Implications:

- The original LRH goal is feasible through a standalone app-server adapter:
  current-session data can be fetched through documented app-server methods.
- A conservative implementation should use stable `thread/read` as the initial
  complete-export path, with a later optional paged adapter using
  `thread/turns/list` when experimental APIs are allowed.
- The production exporter must avoid printing raw transcript content by default,
  write raw artifacts only to private/local paths, and include manifest warnings
  for active/interrupted turns, omitted item classes, pagination completeness,
  and experimental API use.

## 2026-08-07 Private Raw Capture Write

Extended `probe_app_server_stdio.py` with `--raw-out` for thread-read mode and
ran one private raw full-turn capture under `/private/tmp`.

Probe behavior:

- Ran stable `thread/read` with `includeTurns: true`.
- Wrote a private JSON capture envelope under `/private/tmp`.
- Printed only the sanitized structural summary to the terminal.
- Did not add or commit the raw capture file.

Sanitized observations:

- The raw capture write succeeded.
- The private raw capture file size was 1,517,381 bytes.
- The full-turn read returned 118 turns at capture time: 117 completed and 1
  interrupted.
- The earlier comparison returned 116 turns; the increase is expected because
  this active Codex task continued while the spike continued.
- The item type set remained consistent with the prior full read:
  `userMessage`, `agentMessage`, `reasoning`, `fileChange`, `webSearch`, and
  `contextCompaction`.

Implications:

- The adapter can produce the raw source artifact needed for a manifest-backed
  Markdown export.
- Production code must treat live Codex tasks as moving targets. It should
  record `captured_at`, turn counts, status counts, and whether the source task
  was active near capture time.
- The default terminal output should remain metadata-only; raw captures should
  stay in private archive locations and should never be committed.

## 2026-08-07 Raw Source Shape For LRH

The preferred initial raw source shape is the app-server `thread/read` response
with `includeTurns: true`, captured as private JSON before rendering. This is
the smallest stable shape that preserves enough information to render a
complete transcript artifact and audit the capture later.

Recommended raw capture envelope:

```json
{
  "capture_kind": "lrh_codex_app_server_thread_read_capture",
  "capture_schema_version": 1,
  "captured_at": "<timezone-aware timestamp>",
  "source_command": "codex app-server --listen stdio://",
  "app_server_method": "thread/read",
  "request": {
    "threadId": "<codex thread id>",
    "includeTurns": true
  },
  "response": {
    "thread": {}
  },
  "capture_warnings": []
}
```

The raw `response.thread` object should be stored without transformation in the
private source artifact. Observed top-level thread metadata includes stable
export inputs such as:

- `id`, `name`, `preview`, `createdAt`, `updatedAt`, and `recencyAt`;
- `cwd`, `gitInfo`, `historyMode`, `modelProvider`, `sessionId`, `source`, and
  `threadSource`;
- `ephemeral` and runtime `status`;
- `turns`.

Observed turn objects include:

- `id`;
- `status`;
- `error`;
- `startedAt`;
- `completedAt`;
- `durationMs`;
- `items`;
- `itemsView`.

Observed item types include:

- `userMessage`;
- `agentMessage`;
- `reasoning`;
- `fileChange`;
- `webSearch`;
- `contextCompaction`.

Recommended raw-source hash:

- `source_sha256` in `ConversationExportManifest` should hash the exact raw JSON
  bytes written by the app-server capture adapter, not the rendered Markdown.
- The raw JSON should be deterministic enough for hashing after capture:
  UTF-8, sorted top-level envelope keys when LRH writes the envelope, and no
  post-write normalization.
- If LRH later supports paged captures, each page should also have a page hash
  and the envelope should record page order, cursors, and completeness.

## 2026-08-07 Render Shape

The rendered Markdown artifact should continue to use the existing
`ConversationExportManifest` frontmatter contract rather than inventing a new
manifest. The current manifest already supports the needed fields:

- `source_tool: codex`;
- a new `source_adapter`, recommended as `codex_app_server_thread_read`;
- `source_id` set to the Codex thread id;
- `source_sha256` set to the private raw JSON capture hash;
- `privacy: private`;
- `authority: non_authoritative_context`;
- `warnings`;
- `transcript_statistics` including rendered `turn_count` and `message_count`
  where known.

Recommended Markdown structure:

```md
---
<ConversationExportManifest frontmatter>
---

# Codex Conversation Export

Thread: <thread id>
Title: <thread name or "untitled">
Captured: <timestamp>
Source adapter: codex_app_server_thread_read

## Thread Metadata

- Status: <status>
- CWD: <cwd>
- History mode: <historyMode>
- Model provider: <modelProvider>

## Turns

### Turn 1: <turn id>

- Status: <status>
- Started: <startedAt>
- Completed: <completedAt>

#### User

<user message text>

#### Assistant

<assistant message text>

#### File Changes

- <path> (<kind>, <status>)

#### Web Searches

- <query or redacted summary>

#### Reasoning Summaries

<included only if policy allows>
```

Recommended item mapping:

- `userMessage`: render as a user section. Preserve text content, but keep the
  raw JSON private and subject the rendered text to the sensitivity scanner.
- `agentMessage`: render as an assistant section. Preserve phase metadata such
  as `commentary` or `final_answer` in a small label when present.
- `fileChange`: render a path/kind/status list. Do not read file contents.
- `webSearch`: render search query/action metadata and result counts by default;
  avoid storing large result payloads in the Markdown unless explicitly enabled.
- `reasoning`: omit by default or include only summarized reasoning behind an
  explicit option such as `--include-reasoning-summaries`. Record a manifest
  warning either way so downstream readers know the policy used.
- `contextCompaction`: render a marker that compaction happened; do not pretend
  the transcript is continuous without noting it.
- Unknown item types: render a metadata-only placeholder and add a manifest
  warning.

Recommended warnings:

- `codex_signature_verification_failed` when the local executable still fails
  strict signature verification at capture time.
- `codex_trust_state_ambiguous` while successful execution and failed strict
  verification coexist.
- `interrupted_turn_present` when any turn status is `interrupted`.
- `active_or_incomplete_turn_omitted` if the exporter excludes active turns.
- `reasoning_items_omitted` or `reasoning_summaries_included` depending on the
  selected policy.
- `context_compaction_present` when compaction markers appear.
- `web_search_results_summarized` when result payloads are not fully rendered.
- `experimental_thread_turns_list_used` if the paged experimental adapter is
  used.
- `unknown_item_type_present` when an unrecognized item type is encountered.

## 2026-08-07 Recommended Implementation Work Item

Recommended work item id:

`WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`

Recommended title:

`Implement Codex app-server conversation export adapter`

Recommended scope:

- Add an LRH library adapter that spawns a configured Codex executable with
  `app-server --listen stdio://`.
- Implement the documented JSON-RPC handshake:
  `initialize`, `initialized`, and `thread/read`.
- Accept an explicit `--thread-id`; defaulting from `CODEX_THREAD_ID` is useful
  for Codex sessions but should be visible in CLI help.
- Write private raw JSON captures to an explicit output path or private archive
  root.
- Render a Markdown export using the existing `ConversationExportManifest`
  frontmatter.
- Use stable `thread/read` with `includeTurns: true` for the initial complete
  exporter.
- Add a later, optional `--experimental-paged-full` route using
  `thread/turns/list` with `itemsView: full`.
- Run sensitivity scanning on rendered Markdown body text.
- Provide metadata-only terminal output: output path, privacy, sensitivity,
  warning count, turn count, item-type counts, and source hash status.
- Add tests with fake app-server JSONL subprocess boundaries, not real Codex
  execution in unit tests.
- Put real Codex smoke probes in `tests/smoke` or an explicit manual smoke
  script, not the normal unit suite.

Recommended acceptance criteria:

- `lrh conversation export-codex-thread --thread-id ID --out EXPORT.md` creates
  a private Markdown export from a documented app-server `thread/read` response.
- The command never prints raw transcript text by default.
- The command records `source_adapter: codex_app_server_thread_read` and
  `source_id: ID`.
- The command writes or can write the private raw source JSON and records its
  SHA-256 in the manifest.
- The renderer handles observed item types and records warnings for omitted,
  summarized, interrupted, compacted, or unknown data.
- Focused unit tests cover JSON-RPC handshake handling, successful thread reads,
  malformed app-server responses, app-server errors, timeout/exit behavior,
  renderer mapping, warnings, and manifest statistics.
- `lrh conversation inspect-export` accepts the generated artifact.
- `lrh validate` remains clean.

Recommended non-goals:

- Do not scrape `.codex/sessions` JSONL files directly.
- Do not depend on ChatGPT desktop private storage internals.
- Do not make conversation exports authoritative project state.
- Do not implement automatic promotion from transcript to work items,
  decisions, or evidence.
- Do not require experimental app-server APIs for the first production adapter.
- Do not run real Codex app-server in normal unit tests.

## 2026-08-07 Residual Risks And Open Questions

Resolved spike questions:

- Current-task data is available to model-visible Codex tools.
- Current-task data is also available to an ordinary LRH subprocess through the
  documented app-server stdio route.
- Stable `thread/read` can return complete turn data for this real long task.
- Experimental `thread/turns/list` can page turn data and full item structure.
- Direct app storage scraping is unnecessary for the target exporter.

Residual risks:

- Local trust remains ambiguous because `codesign --verify --strict` still fails
  for the Homebrew Codex executable even though the app-server probes run.
- `thread/read` is complete but not paged; very large tasks may need the
  experimental paged adapter later.
- Reasoning summaries need a product/policy decision before production export.
- Web search result payloads may contain external source snippets and should be
  summarized by default.
- File-change records identify paths; those paths can themselves be sensitive.
- Context compaction means a transcript may be incomplete from a literal
  turn-by-turn archaeology perspective even when all stored turns are exported.
- The active current turn may move while an export is running; production code
  should record capture timestamps and statuses, and may need an option to omit
  active turns.
- The app-server schema is versioned by the installed Codex binary; production
  code should record CLI version when available and tolerate unknown item types.

Remaining spike work before closure:

- Optionally draft the actual work item file using `/lrh-work-item` in a new
  follow-up step.
- Use the canonical design backlog entries "Experimental-code linkage
  guardrail" and "Codex executable trust and signature investigation" to carry
  the lint-boundary and local trust follow-ups out of this spike.
- Close this experimental branch by pushing/opening a documentation-only PR, or
  keep it local until the follow-up work item is created from these findings.

Recommended stop point:

This spike has enough evidence to stop before closure and move to planning the
implementation work item. The main technical feasibility risk has been retired:
LRH can fetch the current Codex session through documented app-server APIs.

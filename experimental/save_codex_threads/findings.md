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

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

- Raw page count and turn count from a bounded `read_thread` pagination pass.
- Item type histogram from saved raw pages.
- Truncation and omitted-output observations.
- App-server route result, if a safe documented route is found.


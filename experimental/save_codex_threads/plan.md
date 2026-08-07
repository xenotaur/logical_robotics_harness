# Save Codex Threads Spike Plan

## Purpose

Reduce the highest-risk unknown for LRH Codex conversation export: whether a
real Codex task can be read from a supported API path and saved as private local
data for later LRH rendering.

This spike is not the production exporter. It is a short-lived investigation
that should produce enough evidence to decide whether `/lrh-codex-export` should
be implemented as:

- a Codex skill that uses model-visible Codex app thread tools;
- an LRH CLI command that talks to a documented Codex app-server API;
- a hybrid skill plus CLI/library design; or
- a different design if neither route is reliable.

## Safety Boundary

- Do not run the Homebrew `codex` CLI until the macOS malware block is resolved
  or the user explicitly authorizes a narrowly scoped diagnostic command.
- Do not restore or execute the binary macOS moved to Trash.
- Keep raw thread JSON and transcript exports in `/private/tmp`.
- Commit only this plan, sanitized findings, and helper code.
- Do not rely on undocumented Codex app storage internals.

## Phase 1: Model-Visible `codex_app.read_thread`

Goal: prove the current Codex task can be read through the app-provided thread
tool and determine the raw shape, pagination behavior, truncation behavior, and
privacy risks.

Steps:

1. Read the current thread id from `CODEX_THREAD_ID`.
2. Call `codex_app.read_thread` for that thread with a small `turnLimit`.
3. Confirm the result includes thread metadata, turns, items, and `page` cursor
   fields.
4. Page backward using `page.nextCursor` until either `hasMore` is false or a
   bounded manual stop is reached.
5. Save raw JSON pages under `/private/tmp/lrh-codex-thread-spike/<thread-id>/`
   only if needed for inspection.
6. Use `inspect_read_thread_pages.py` to summarize saved pages without printing
   raw transcript content.
7. Record sanitized findings in `findings.md`.

Questions:

- Does `read_thread` include enough completed history to reconstruct useful
  transcripts?
- Are active turns incomplete or clearly marked?
- Are tool outputs and file changes present, summarized, truncated, or omitted?
- Is pagination stable enough to capture a long task?
- Is this tool available only to Codex skills/agents, or can it be invoked by
  LRH code?

## Phase 2: Renderer Shape

Goal: decide whether existing LRH manifest and inspector code can consume a
thread-derived source shape.

Steps:

1. Sketch a raw JSON source schema for captured Codex thread pages.
2. Map `userMessage`, `agentMessage`, `commandExecution`, `fileChange`, and tool
   call items to Markdown transcript sections.
3. Decide whether reasoning summaries should be included, omitted, or included
   behind an explicit flag.
4. Decide how to record truncation, omitted raw output, active-turn exclusion,
   and pagination completeness in manifest warnings.

## Phase 3: Safe Documented App-Server Route

Goal: determine whether the same task can be read by a normal executable path,
not only by model-visible tools.

Precondition: do not use the Homebrew `codex` CLI until it has been repaired or
reinstalled from a trusted current source.

Candidate executable routes:

- `/Applications/ChatGPT.app/Contents/Resources/codex`
- `/Users/centaur/.codex/plugins/.plugin-appserver/codex`
- a freshly reinstalled current Homebrew cask, after verification

Steps:

1. Verify candidate binaries without executing where practical (`codesign`,
   `file`, path, version metadata if available).
2. Prefer the already-running ChatGPT desktop app-server if a documented local
   connection endpoint can be identified.
3. If a trusted app-server route exists, issue a minimal JSON-RPC
   `initialize` / `initialized` / `thread/read` sequence for `CODEX_THREAD_ID`.
4. Compare the response shape against Phase 1.
5. Record whether standalone CLI-backed LRH export is feasible.

## Decision Criteria

- If Phase 1 succeeds and Phase 3 fails, build a skill-backed
  `/lrh-codex-export` first and keep CLI support as a later adapter.
- If Phase 1 and Phase 3 both succeed, build an LRH CLI/library adapter for
  `lrh conversation export-codex-thread`.
- If Phase 1 fails, stop and redesign; the current app surface is insufficient.

## Current Spike Conclusion

As of 2026-08-07, Phase 1 and Phase 3 have both succeeded in bounded probes:

- the model-visible `codex_app.read_thread` route can read and page through this
  real Codex task;
- the standalone Homebrew `codex app-server --listen stdio://` route can perform
  the documented `initialize` / `initialized` / `thread/read` sequence;
- stable `thread/read` with `includeTurns: true` returned all turns for this
  task in one response;
- experimental `thread/turns/list` can page turn metadata, summary items, and
  full item structure.

Therefore, the recommended implementation path is an LRH CLI/library adapter
for `lrh conversation export-codex-thread`, using stable `thread/read` as the
initial complete-export route. A Codex skill can remain the user-facing
current-task workflow wrapper, and a later optional adapter can use
experimental paged `thread/turns/list` for very large exports.

The remaining non-export blocker is local trust ambiguity: post-reinstall
Homebrew Codex commands ran successfully in user-approved probes, but
`codesign --verify --strict` still reports an invalid signature. Treat this as
an upstream/local installation risk to document and monitor, not as a blocker to
the API feasibility conclusion.

## Non-Goals

- No production LRH CLI changes in this spike.
- No committed raw transcripts.
- No undocumented local storage scraping.
- No full archive viewer changes.
- No changes to execution-record `session_transcript` grammar.

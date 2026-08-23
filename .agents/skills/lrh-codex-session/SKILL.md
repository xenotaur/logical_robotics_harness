---
name: lrh-codex-session
description: 'Report the current or specified Codex task/thread identity as an LRH
  `session_transcript: codex-app:<id>` pointer without exporting transcript content.
  Use when a closeout or execution record needs the Codex session pointer but the
  user has not asked to archive the transcript.

  '
---

# lrh-codex-session Skill

This skill is a metadata-only wrapper around LRH's shared Codex session
identity resolver. It does not export, inspect, print, or archive transcript
content.

Use it when an LRH execution or closeout record needs the Codex app session
pointer before a transcript archive should be written.

---

## Inputs

Provide a Codex thread id as the optional argument:

```text
/lrh-codex-session 019fc43f-e2d9-7503-88cb-9d9a8136c111
```

If no argument is supplied, the shared resolver defaults to `CODEX_THREAD_ID`.
If neither an argument nor `CODEX_THREAD_ID` is available, ask the user for the
Codex thread id before proceeding.

The returned id is a Codex task/thread pointer. It is not an export attempt id,
archive directory, `attempt.json` path, raw JSON path, transcript Markdown path,
or timestamp.

---

## Reference Knowledge

Use the repository CLI documentation as the command contract:

- `docs/reference/cli/conversation.md` for
  `lrh conversation current-codex-thread-id`.

The relevant CLI guarantees are:

- `current-codex-thread-id` uses the same shared resolver contract as
  `/lrh-codex-export` and the Codex export CLIs.
- `--thread-id` overrides `CODEX_THREAD_ID`.
- missing and whitespace-only ids are rejected clearly.
- terminal output is metadata-only.
- no transcript content is exported, read, or printed.

---

## Safety Rules

Follow these rules for every run:

1. Do not run `/lrh-codex-export` unless the user explicitly asks to export or
   archive the transcript.
2. Do not inspect undocumented Codex app storage internals.
3. Do not print transcript text or line-preview export artifacts.
4. Do not use archive paths, raw JSON paths, `attempt.json`, or timestamps as
   the execution record's `session_transcript` value.
5. Report the closeout-ready pointer exactly as
   `session_transcript: codex-app:<id>`.

---

## Execution Steps

Work through these steps in order.

### Step 1 -- Resolve the thread id

If the user supplied an argument, pass it as `--thread-id`.

If no argument was supplied, use the shared resolver default:

```bash
lrh conversation current-codex-thread-id
```

If no thread id is available, stop and ask the user for the Codex thread id.

### Step 2 -- Report the pointer

For human-readable output, run:

```bash
lrh conversation current-codex-thread-id --thread-id "$THREAD_ID"
```

For execution-record copy/paste output, run:

```bash
lrh conversation current-codex-thread-id \
  --thread-id "$THREAD_ID" \
  --field session-transcript
```

Report both:

- `Thread ID: <id>`
- `session_transcript: codex-app:<id>`

### Step 3 -- Close out

Tell the user that no transcript was exported. If they later need a private
archive capture, use `/lrh-codex-export` explicitly.

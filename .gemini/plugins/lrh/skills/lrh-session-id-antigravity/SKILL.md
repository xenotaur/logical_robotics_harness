---
name: lrh-session-id-antigravity
description: 'Report the current or specified Google Antigravity conversation identity
  as an LRH `session_transcript: antigravity-app:<id>` pointer without exporting transcript
  content. Use when a closeout or execution record needs the pointer but no archive
  was requested.

  '
---

# lrh-session-id-antigravity Skill

This skill is a metadata-only wrapper around LRH's shared Antigravity conversation
identity resolver, `lrh conversation current-antigravity-conversation-id`. It does
not export, inspect, print, or archive transcript content.

Use it when an LRH execution or closeout record needs the Antigravity session
pointer before a transcript archive should be written.

---

## Inputs

Provide an Antigravity conversation ID (UUID) as the optional argument:

```text
/lrh-session-id-antigravity e047cde6-ac54-486b-9681-56c0af5c8f1a
```

If no argument is supplied, the shared resolver defaults to
`ANTIGRAVITY_CONVERSATION_ID`. If neither an argument nor
`ANTIGRAVITY_CONVERSATION_ID` is available, the resolver checks for `--latest` or
reports `pending`.

The returned ID is an Antigravity conversation pointer. It is not an export
attempt ID, archive directory, transcript Markdown path, or timestamp.

---

## Reference Knowledge

Use the installed LRH CLI as the operational command contract:

```bash
lrh conversation --help
lrh conversation current-antigravity-conversation-id --help
```

The LRH checkout's `docs/reference/cli/conversation.md` is an optional
maintainer reference, not a client-repository prerequisite. If it is absent,
continue with CLI help and the explicit capability check above. A missing
documentation file is not evidence that conversation-ID resolution is
unavailable; only a missing or incompatible CLI command is a runtime blocker.

The relevant CLI guarantees are:

- `current-antigravity-conversation-id` uses the same shared resolver contract as
  `/lrh-antigravity-export` and the Antigravity export CLIs.
- `--conversation-id` overrides `ANTIGRAVITY_CONVERSATION_ID`.
- missing, whitespace-only, and malformed UUIDs are rejected clearly with exit code 2.
- terminal output is metadata-only.
- no transcript content is exported, read, or printed.

---

## Safety Rules

Follow these rules for every run:

1. Do not run `/lrh-antigravity-export` unless the user explicitly asks to export
   or archive the transcript.
2. Do not inspect undocumented Antigravity app storage internals.
3. Do not print transcript text or line-preview export artifacts.
4. Do not use archive paths, raw JSONL paths, or timestamps as the execution
   record's `session_transcript` value.
5. Report the closeout-ready pointer exactly as
   `session_transcript: antigravity-app:<id>`.
6. When the conversation cannot be determined, report
   `session_transcript: pending` rather than failing the caller or guessing
   without `--latest`.

---

## Execution Steps

Work through these steps in order.

### Step 1 -- Resolve the conversation ID

Capture the resolved conversation ID from the command:

If the user supplied an argument, pass it as `--conversation-id`:

```bash
CONVERSATION_ID="$1"
lrh conversation current-antigravity-conversation-id --conversation-id "$CONVERSATION_ID"
```

If no argument was supplied, use the default resolution:

```bash
lrh conversation current-antigravity-conversation-id
```

If the command exits with code 2 (unresolved environment and no argument), report
`session_transcript: pending` and ask the user if they would like to provide an
explicit conversation ID or discover via `--latest`.

If the command succeeds, capture the resolved conversation ID from the output.

### Step 2 -- Report the pointer

Using the resolved conversation ID from Step 1, report both:

- `Conversation ID: <id>` (or `pending`)
- `session_transcript: antigravity-app:<id>` (or `session_transcript: pending`)

For programmatic/copy-paste output using the CLI, pass the resolved conversation ID:

```bash
lrh conversation current-antigravity-conversation-id \
  --conversation-id "$CONVERSATION_ID" \
  --field session-transcript
```

### Step 3 -- Close out

Tell the user that no transcript was exported. If they later need a private
archive capture, use `/lrh-antigravity-export` explicitly.

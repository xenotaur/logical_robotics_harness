---
id: PROP-LRH-EXPORT-SESSION-ID-APPENDIX-ANTIGRAVITY
type: design_proposal
title: "Appendix: Antigravity Session Identity Investigation Findings"
status: proposed
created_on: 2026-09-26
updated_on: 2026-09-26
parent: PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES
---

# Appendix: Antigravity Session Identity Investigation Findings

## Summary

This appendix documents the findings of **`WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION`**,
fulfilling the prerequisite investigation mandated by
**`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 5**.

The purpose of this investigation was to determine whether an agent running
inside a Google Antigravity session can reliably identify its current
conversation ID, choose the canonical `session_transcript:` pointer format for
Antigravity, specify resolver fallback behavior, and provide an explicit
recommendation for **`WI-ANTIGRAVITY-SESSION-ID-RESOLVER`**.

## Investigation Methodology

The investigation was conducted live within an active Google Antigravity
session on macOS. The candidate identity sources evaluated were:
1. Environment variables exposed to child terminal processes.
2. In-session agent context (system prompt, working paths, artifact directories).
3. Filesystem layout, hierarchy, and timestamp behavior in
   `~/.gemini/antigravity/brain/`.
4. Documented Antigravity SDKs and APIs.

Per the safety requirements of `WI-ANTIGRAVITY-SESSION-ID-INVESTIGATION`,
environment variable values that could potentially contain tokens or credentials
were inspected for presence and schema only, without recording secret contents.
No transcript text was printed or committed.

## Findings Table

| Candidate Source | Mechanism | Observed Behavior / Evidence | Reliability Verdict |
|---|---|---|---|
| **`ANTIGRAVITY_CONVERSATION_ID`** | Environment variable | Contains a 36-character hyphenated lowercase UUID (e.g. `e047cde6-ac54-486b-9681-56c0af5c8f1a`). Exactly matches the current conversation ID and the name of the active conversation's directory under `~/.gemini/antigravity/brain/`. Automatically exported to all subprocesses and terminals spawned by Antigravity. | **Reliable (Primary)** |
| **`ANTIGRAVITY_TRAJECTORY_ID`** | Environment variable | Contains a 36-character hyphenated UUID distinct from `ANTIGRAVITY_CONVERSATION_ID`. Identifies the current execution trajectory/step rather than the overarching conversation session. | **Unsuitable** (Trajectory-scoped, not conversation-scoped) |
| **`ANTIGRAVITY_APP_DATA_DIR`** | Environment variable | Contains the absolute path to the Antigravity application data root (`/Users/<user>/.gemini/antigravity`). Reliable path locator for discovering the `brain/` storage tree. | **Reliable Supporting Path** |
| **Other Antigravity Env Vars** | Environment variables | `ANTIGRAVITY_PROJECT_ID` (identifies workspace/project), `ANTIGRAVITY_AGENT` (agent type), `ANTIGRAVITY_AGENTAPI_EXE` (path to runtime binary), `ANTIGRAVITY_LS_ADDRESS`, `ANTIGRAVITY_LS_VERSION`. Do not expose conversation identity. | **Informational only** |
| **Agent Prompt Context** | System prompt & metadata | Injected at session initialization: `<user_information>` contains `Conversation ID: <uuid>`; `<artifacts>` contains `Artifact Directory Path: <appDataDir>/brain/<conversation-id>`; `<conversation_transcript>` cites `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`. Exactly matches `ANTIGRAVITY_CONVERSATION_ID`. | **Reliable (In-Agent Context Only)**; unavailable to standalone external CLI calls without env inheritance |
| **Filesystem Recency (`brain/` mtime)** | Filesystem inspection (`--latest`) | `~/.gemini/antigravity/brain/<uuid>/` holds conversation state (`scratch/`, `.user_uploaded/`, `.system_generated/logs/transcript.jsonl` or `transcript_full.jsonl`). On POSIX/macOS, appending to child transcript files updates the transcript file's mtime, not the directory's mtime. Furthermore, when multiple conversations are open concurrently or receiving background tasks, recency sorting can misidentify the current session. | **Heuristic Fallback Only**; acceptable with explicit `--latest` flag and warning, but unsafe as default; candidate selection must sort transcript files by mtime rather than directory mtime |
| **Antigravity Python SDK (`google-antigravity`)** | Python SDK | Provides `Agent`, `Conversation`, and `Connection` classes for spawning and managing agent workflows in Python. It is an agent-creation framework rather than an OS-level session discovery daemon. | **Not Applicable** (Environment variables provide the direct inter-process contract) |

## Session Transcript Pointer Format

Following the precedent established by:
- Codex: `codex-app:<task-or-thread-id>` (`src/lrh/conversations/codex_session.py`)
- Claude Code: `claude-app:<host-uuid-stem>` (`src/lrh/conversations/claude_session.py`)

The canonical `session_transcript:` pointer format for Google Antigravity is:

```
antigravity-app:<conversation-id>
```

Example:
```yaml
session_transcript: antigravity-app:e047cde6-ac54-486b-9681-56c0af5c8f1a
```

### Format Specification
- **Prefix:** `antigravity-app:`
- **Identifier:** The canonical 36-character hyphenated UUID of the Antigravity
  conversation (matching `ANTIGRAVITY_CONVERSATION_ID` and the `brain/<id>`
  directory name).
- **Semantics:** Identifies the stateful conversation thread within the
  Antigravity desktop/CLI application, distinct from an individual trajectory or
  an export attempt.

## Resolver Behavior and Fallback Specification

The proposed resolver (CLI subcommand and `/lrh-session-id-antigravity` skill)
should implement the following resolution hierarchy:

1. **Explicit Identifier:**
   If an explicit `--conversation-id <id>` argument is supplied, validate that it
   matches UUID formatting and return `antigravity-app:<id>`. If malformed, raise
   an error immediately (exit code 2).
2. **Environment Variable Discovery (Default):**
   Read `ANTIGRAVITY_CONVERSATION_ID`. If present:
   - Validate that it conforms to UUID syntax (36 characters, hexadecimal with
     standard hyphens).
   - If valid, return `antigravity-app:<value>`.
   - If present but malformed, treat as a **hard error** (exit code 2) and fail
     immediately; do **not** silently fall through to `--latest` or any other heuristic.
3. **Explicit `--latest` Heuristic Fallback:**
   If `ANTIGRAVITY_CONVERSATION_ID` is absent (for instance, when run from an
   independent terminal emulator not launched by Antigravity) and the caller
   explicitly passes `--latest`:
   - Inspect `~/.gemini/antigravity/brain/` (resolved via
     `ANTIGRAVITY_APP_DATA_DIR` if set, otherwise defaulting to
     `~/.gemini/antigravity/brain/`).
   - Match the discovery contract of `src/lrh/conversations/antigravity_export.py:494-502`:
     glob both `*/.system_generated/logs/transcript.jsonl` and
     `*/.system_generated/logs/transcript_full.jsonl`, sort candidate transcript
     files by file `st_mtime` (never by directory mtime, which does not update
     when child logs are appended), and extract the conversation UUID from the
     matched transcript's parent directory structure.
   - Emit a prominent warning to stderr that the session ID was resolved via
     filesystem recency heuristic rather than active environment context.
   - Return `antigravity-app:<discovered-id>`.
4. **Unresolved State:**
   If `ANTIGRAVITY_CONVERSATION_ID` is absent and `--latest` is not passed:
   - Do **not** silently guess using recency.
   - The CLI subcommand must exit with code 2 (matching the failure contract of
     `src/lrh/conversations/codex_session.py:85-89` and
     `src/lrh/conversations/claude_session.py:167-173`) with an explanatory
     message indicating that no active Antigravity conversation environment was
     detected and directing the user to supply `--conversation-id` or `--latest`.
   - Higher-level caller workflows (such as `/lrh-closeout` or `/lrh-session-id`)
     catch this exit code 2 and record `session_transcript: pending` in closeout
     metadata rather than failing the landing chain.

## Recommendation for `WI-ANTIGRAVITY-SESSION-ID-RESOLVER`

**Recommendation: Proceed with `WI-ANTIGRAVITY-SESSION-ID-RESOLVER` as scoped.**

### Rationale
The central unknown identified in `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`
Decision 5 was whether a reliable current-session source exists in Antigravity.
This investigation confirms that **`ANTIGRAVITY_CONVERSATION_ID` is standard,
exported to subprocesses, and reliably identifies the active conversation**.

`WI-ANTIGRAVITY-SESSION-ID-RESOLVER` does not need scope alteration or
deferral. It can proceed immediately using `ANTIGRAVITY_CONVERSATION_ID` as its
primary source, mirroring the implementation pattern of
`src/lrh/conversations/codex_session.py` and
`src/lrh/conversations/claude_session.py`.

---
name: lrh-session-id-claude
description: 'Report the current or specified Claude.app session identity as an LRH
  `session_transcript: claude-app:<host-uuid-stem>` pointer, plus the title, branch,
  PR, and child-id-alias eligibility that `lrh prompt record-session-alias` needs,
  without exporting or reading transcript content. Use when a closeout or execution
  record needs the Claude session pointer, or when /lrh-closeout, /lrh-land, or /lrh-implement
  resolves one.

  '
---

# lrh-session-id-claude Skill

This skill is a metadata-only wrapper around LRH's Claude session-identity
resolver, `lrh conversation current-claude-session-id`, plus the Claude
desktop app's session-management tools (`get_session`, `list_sessions`). It
does not export, inspect, print, or archive transcript content. It is the
Claude variant of the session-ID skill family; the Codex counterpart is
`/lrh-codex-session` (to be renamed `/lrh-session-id-codex`).

`/lrh-closeout` Step 3, `/lrh-land` Step 3, and `/lrh-implement`'s alias
capture call this skill instead of restating the resolution order. It is
metadata-only and writes nothing, so it may be invoked from those skills or
directly by the user.

---

## Inputs

All arguments are optional. With none, the skill resolves the **current
window's** session:

```text
/lrh-session-id-claude
/lrh-session-id-claude local_6f9b846e-c6f9-45aa-9cf9-8c744ec57026
/lrh-session-id-claude 716
/lrh-session-id-claude https://github.com/<owner>/<repo>/pull/716
/lrh-session-id-claude xenotaur/feat/my-branch
```

- A `local_<uuid>` or bare UUID is taken as a **host** session id for another
  session (strip `local_`).
- A PR number or URL selects **another** session by its `prNumber`.
- A branch name selects **another** session by its `branch`.
- A future `/lrh-session-id` dispatcher passes its remaining arguments
  through unchanged, so treat them exactly as above.

The reported id is a Claude.app **host** session pointer. It is not the child
SDK id that names a `~/.claude/projects/.../<child-uuid>.jsonl` file, an
export path, or a timestamp.

---

## Reference Knowledge

Use the repository CLI documentation as the command contract:

- `docs/reference/cli/conversation.md`, section
  `lrh conversation current-claude-session-id`.

The relevant CLI guarantees are:

- It reads `CLAUDE_CODE_SESSION_ID` (the child id, required) and, if set,
  `CLAUDE_CODE_HOST_SESSION_ID` (the host id, `local_` stripped).
- `--format json` prints `session_id`, `session_transcript`,
  `transcript_path`, and `exported: false`. `session_transcript` is `null`
  when the host id is unset; the text format shows `unknown` for it.
- It exits `0` on success and `2` when the session cannot be resolved: the
  session id is unset, empty, or has whitespace or a path separator, or the
  transcript glob matches zero or several files.
- Output is metadata-only. No transcript content is read or printed.

---

## Safety Rules

Follow these rules for every run:

1. Do not export, archive, or read transcripts, and never call the
   session-management `export_transcript` tool. `/lrh-export-claude` is the
   explicit, user-requested export path.
2. The pointer comes **only** from the host id. `CLAUDE_CODE_SESSION_ID` and
   JSONL filenames are child ids: use them only as the
   `record-session-alias --child-id` alias, never as the pointer.
3. Do not print transcript text, and do not report absolute transcript paths
   as the pointer. Never write an absolute path into an execution record.
4. Report the closeout-ready pointer exactly as
   `session_transcript: claude-app:<host-uuid-stem>`, or as
   `session_transcript: pending` when no confident host id was resolved.
5. Never widen the fallback in Step 1 beyond "the subcommand is unavailable."

---

## Execution Steps

Work through these steps in order.

### Step 1 -- Resolve the current window (no argument)

Run the resolver:

```bash
lrh conversation current-claude-session-id --format json
```

Branch on the result:

- **Exit 0 with a non-null `session_transcript`:** use it as the pointer
  and `session_id` as the current window's child id.
- **Exit 0 with `session_transcript: null`** (host id unset): record **no**
  pointer. Report `session_transcript: pending` and say the host id was not
  available in this window. Do not derive a pointer from the child id.
- **The subcommand is unavailable:** `lrh` is not found, or an older
  installed CLI rejects the subcommand. Argparse reports this with an
  "invalid choice" error on exit code `2`. **Detect it by that message, not
  by the exit code**, because a real resolution failure also exits `2`. Only
  in this case, read the env vars directly:

  ```bash
  echo "$CLAUDE_CODE_HOST_SESSION_ID"   # host id; strip local_
  echo "$CLAUDE_CODE_SESSION_ID"        # child id; alias only
  ```

  An unset or empty host id still means `pending`, with no pointer.
- **Any other non-zero exit** (for example `error: CLAUDE_CODE_SESSION_ID is
  not set`, or zero or several matching transcripts): this is a real
  resolution failure. Surface the error to the user, record **no** pointer,
  and report `session_transcript: pending`. Do **not** fall back to the env
  vars.

Why so strict: those failures concern the child id and the transcript path,
not the host id. Blocking the pointer on them is a deliberate conservative
choice, so this skill is never weaker than the CLI it wraps. Relaxing it is a
design decision to raise explicitly, not a fallback to widen silently.

**Confirm before callers store it.** The current window is not always the
session that authored the work (a long, resumed, or forked session, or a
closeout run from a different window). Where the session-management
`get_session` tool is available, call it with `"self"` and report the
session's title and branch alongside the pointer, so the user can recognize
the session. If the caller or user says it is not the right session, go to
Step 2.

**The app's `branch` is the session's *recorded* branch, not necessarily the
current one.** `get_session` and `list_sessions` report the branch the
desktop app associated with the session, which is typically the worktree
branch it started on. If the session later switched branches inside its
worktree, that value is stale, and the same applies to its `prNumber`. Use it
to *recognize* a session, but callers recording `--branch` should prefer the
authoritative branch for the work they are recording: the branch they
created, or the PR's head branch (`gh pr view <pr> --json headRefName`).

### Step 2 -- Resolve another session (argument given, or current window rejected)

These paths use the Claude desktop app's session-management tools. In a
CLI-only environment where they are unavailable: accept a host id the user
supplied as the argument (strip `local_`; report title and branch as
unavailable); otherwise say so and ask the user for the host id
(`local_<uuid>`), or report `pending`.

1. **Host id given:** strip `local_`, then call `get_session` with it to
   confirm it exists and to read its title, branch, and PR.
2. **PR given:** call `list_sessions` and match the `prNumber`. If exactly
   one session matches, use its `sessionId`. If several match, list them and
   ask the user to pick. If none matches, continue to path 3 with the PR's
   head branch (`gh pr view <pr> --json headRefName,title`) and title.
3. **Branch or title given or known:** match `list_sessions` rows by
   `branch` first, then by title. Exactly one match: use it. Several: list
   them and ask the user to pick. None: continue to path 4.
4. **No confident match:** call `list_sessions` (with
   `include_archived: true` when the authoring session may be archived).
   Show the likely candidates by title, branch, PR, and last activity, and
   ask the user to pick one, or to confirm `pending`/`none`. `list_sessions`
   excludes the session it is called from (per that tool's own contract), so
   also offer the current session from `get_session` (`"self"`) as a
   candidate.

A session resolved in this step belongs to a different window than the one
running now, or was picked by the user rather than read from this window's
environment. Either way, **no child-id alias may be paired with it.**

### Step 3 -- Report

Report one block, suitable for callers to read field by field:

```text
Session ID (host): <host-uuid-stem | none>
session_transcript: claude-app:<host-uuid-stem>   # or: pending
Title: <title | unavailable>
Branch (as recorded by the app): <branch | unavailable>
PR: <pr-url-or-number | none>
Child-id alias: <child-uuid, pairable> | not pairable (<reason>)
Resolved via: resolver | env-var fallback (subcommand unavailable) | get_session | list_sessions by PR | list_sessions by branch/title | user pick
```

`Child-id alias` is **pairable** only when Step 1 resolved the current window
(through the resolver or the restricted env-var fallback) and the user or
caller confirmed it is the right session. Every Step 2 path is **not
pairable**.

Callers that record the identity use these fields directly:

```bash
# Alias pairable (current window, confirmed):
lrh prompt record-session-alias \
  --host-id <host-uuid-stem> \
  --child-id <child-uuid> \
  --title "<title>" \
  --branch <branch> \
  --pr <pr-url> \
  --project-root .

# Alias not pairable (any Step 2 path): no --child-id flag at all.
lrh prompt record-session-alias \
  --host-id <host-uuid-stem> \
  --title "<title>" \
  --branch <branch> \
  --pr <pr-url> \
  --project-root .
```

Omit `--title` or `--branch` when they were unavailable. Never pass an
empty `--child-id` value. For `--branch`, prefer the authoritative branch of
the work being recorded (see Step 1) over the app-recorded branch.

### Step 4 -- Close out

Tell the user that no transcript was exported or read. If they later need a
private archive capture, use `/lrh-export-claude` explicitly.

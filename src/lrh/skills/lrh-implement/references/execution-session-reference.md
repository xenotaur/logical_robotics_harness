# Execution Session Reference

Practical facts from `PROP-LRH-EXECUTION-SESSIONS` needed when running
`/lrh-implement`. Read this before Step 3 (instruction phase) and Step 9
(execution record).

---

## Prompt workflow commands

### Mint a prompt ID

```bash
# For a work item:
lrh prompt label --slug <slug> --work-item <WI-ID>

# For an ad-hoc task:
lrh prompt label --slug <slug>
```

The `--slug` value is lower-kebab-case, derived from the work item ID:
`WI-SKILLS-LRH-SETUP` → `wi-skills-lrh-setup`. For ad-hoc tasks, ask the
user for a short descriptive slug if one is not obvious.

The command outputs a `prompt_id` in the form:

```
PROMPT(<WI-ID-OR-AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601-TIMESTAMP>]
```

`<SLUG_UPPER_UNDERSCORE>` is the slug with `-` replaced by `_` then
uppercased: `wi-skills-lrh-setup` → `WI_SKILLS_LRH_SETUP`.

### Check for prior execution

```bash
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

If this returns a `landed` or `in_progress` record, stop and report to the
user — do not proceed without explicit instruction to rerun.

### Update execution record to landed

Use this after a PR merges, typically from `/lrh-closeout` Step 5:

```bash
lrh prompt update-execution \
  --execution-id <execution-id> \
  --status landed \
  --pr <pr-url> \
  --commit <merge-commit-sha> \
  --session-transcript <backend-session-pointer-or-sentinel> \
  --project-root .
```

- `--execution-id`: the `execution_id:` field value from the record
  (e.g. `2026_06_28_11_30_26_WI_PROMPT_CLI_CLOSEOUT`)
- `--commit`: required when `--status landed`; use the merge commit SHA
- `--session-transcript`: optional; if absent when the record was created,
  the command inserts it after the `commit:` line
- Only `in_progress → landed` is a valid status transition
- Prints `updated: <path>` on success; exits non-zero with a message on error

### Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item <WI-ID or AD_HOC> \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

This creates a new file at:
`project/executions/<WI-ID-OR-AD_HOC>/<timestamp>_<SLUG_UPPER_UNDERSCORE>.md`

Immediately edit the generated file to add the three optional fields (below).

---

## Branch naming convention

Format: `<username>/<type>/<slug>`

Get the GitHub login for `<username>`:

```bash
gh api user --jq .login
```

Map the work item `type` field to `<type>`:

| Work item type | Branch type |
|---|---|
| `deliverable` | `feat` |
| `operation` | `chore` |
| `investigation` | `spike` |
| `evaluation` | `audit` |
| ad-hoc / unknown | `chore` |

`<slug>` is the same lower-kebab slug used for the prompt label.

Example: `xenotaur/feat/wi-skills-lrh-setup`

Do not use the `agents/<backend>/<id>` namespace — reserved for future
autonomous backends.

---

## Execution record optional fields

These three fields are defined by `PROP-LRH-EXECUTION-SESSIONS`. Add them
immediately after running `lrh prompt record-execution`:

```yaml
agent: <agent-backend>
instruction_source: <path-or-description>
session_transcript: pending
```

### `agent`

Identifies the execution backend:

| Value | Use when |
|---|---|
| `claude_app` | Implemented in a Claude Code (Claude.app) session |
| `codex_app` | Implemented in a Codex desktop app task |
| `codex_cloud` | Submitted to and executed by Codex Cloud |
| `manual` | Implemented manually without an AI backend |

### `instruction_source`

References the instruction-phase artifact:

- Work item: path to the work item file (e.g.
  `project/work_items/proposed/WI-SKILLS-LRH-SETUP.md`)
- Ad-hoc: brief description of the task origin (e.g.
  `ad_hoc conversation — design session for /lrh-implement skill`)
- Codex Cloud: path or Taurcode reference to the prompt file
- Outside the repository: a scheme-prefixed reference such as
  `promptspace:<relative-path>`, resolved against the configured prompt
  archive root. Never an absolute path.

### `session_transcript`

Points at the agent session that produced the work. The value is a
scheme-prefixed scalar `<backend>:<id>`, or one of two sentinels:

| Value | Meaning |
|---|---|
| `claude-app:<host-uuid-stem>` | Claude.app session (see below) |
| `codex-app:<task-or-thread-id>` | Codex desktop app task or thread, when available |
| `codex-cloud:<task-id>` | Codex Cloud task |
| `chatgpt:<conversation-id>` | ChatGPT conversation |
| `pending` | Session exists, ID not yet recorded — **a to-do** |
| `none` | Backend produced no retrievable transcript — **terminal** |

Do not write `pending` for a backend that has no retrievable session; that
misrepresents a finished record as unfinished work. Use `none`.

For Claude.app, use the short form:

```
claude-app:<host-uuid-stem>
```

Desktop-app Claude Code sessions have **two** identifiers:

- **Host session id** — `local_<uuid>`: the durable app-level key. This is
  what View > Copy URL yields and what the session-management tools (e.g.
  `list_sessions`) return.
- **Child SDK session id** — the UUID stem of the transcript file at
  `~/.claude/projects/<project-slug>/<child-uuid>.jsonl`. On resumed or
  continued sessions this differs from the host id.

The canonical stored value is the **host** UUID stem with the `local_`
prefix stripped: `claude-app:<host-uuid-stem>`. In-session, both ids are
available as environment variables: `CLAUDE_CODE_HOST_SESSION_ID` (host,
`local_`-prefixed) and `CLAUDE_CODE_SESSION_ID` (child).

**Use `pending` when the session ID is not yet known.** Update the field
before or when the PR lands. Never commit an absolute path (`~/.claude/...`
or `/Users/...`) — it leaks your local workspace layout to everyone who
clones the repository. Never commit the transcript itself — see the
2026-07-23 decision-log entries (`project/memory/decision_log.md`) for both
the never-commit rule and this pointer grammar.

A sequence of these scalars is reserved for executions that genuinely span
multiple backends (e.g. design in one tool, execution in another).
Single-backend records stay scalar.

---

## Session identity capture (`project/sessions/`)

Per `PROP-LRH-SESSION-ARCHIVE-SYNC` Stage 1: `session_transcript` stores
only the **host** id, but transcript files on disk are named by the
**child** SDK id, and on resumed/continued sessions these differ. Nothing
else durably records that mapping, so a dangling `session_transcript`
pointer cannot always be resolved back to its transcript. `project/sessions/index.jsonl`
closes that gap by recording both ids together, plus title, PRs, and
branch/`written_branches` fields reserved for later fork stitching
(Stage 3 enriches this schema; it does not replace it).

### `lrh prompt record-session-alias`

```bash
lrh prompt record-session-alias \
  --host-id <host-uuid-stem> \
  --child-id <child-uuid-or-omit> \
  --pr <pr-url> \
  --branch <branch-name> \
  --title <short-title> \
  --project-root .
```

- `--host-id`: required; the same stem used in `session_transcript`
  (`local_` already stripped).
- `--child-id`: **omit** when the host id was resolved cross-session — via
  `list_sessions` by PR number, or a pasted browser URL — rather than
  directly from `$CLAUDE_CODE_HOST_SESSION_ID` in the current window.
  Pairing a cross-session host id with the *current* window's
  `$CLAUDE_CODE_SESSION_ID` would record a false alias: that child id
  belongs to a different conversation than the one that authored the work.
  Only pair the two when both were read from the live environment of the
  session that actually did the work.
- `--pr`, `--branch`, `--title`: optional context; each observation is
  additive and idempotent — the same host id's row is updated in place
  (child ids and PRs accumulate; title and branch take the latest value),
  never duplicated.
- Repeat `--written-branch <name>` for any additional branch this session
  wrote to; reserved for Stage 3's fork stitching, unused until then.

Writing to `project/sessions/index.jsonl` is independent of the
`session_transcript` field and does not change its grammar or validator
rules. This file is committed and regenerated by observation, never
hand-edited.

### When each caller writes an observation

- **`/lrh-implement` Step 9** — always live, single-session: read both env
  vars directly and pair them (see that skill's Step 9).
- **`/lrh-closeout` Step 5** — every record, on every resolution path; only
  the `--child-id` pairing is conditional — include it on Step 3 path 1
  (same window), omit the flag entirely on paths 2/3 (cross-session), since
  the host id and PR are still worth recording either way (see
  `references/closeout-workflow.md`'s "Session identity capture" section).

### `lrh sessions` — the Stage 2 archive reconciler

Per `PROP-LRH-SESSION-ARCHIVE-SYNC` Stage 2
(`WI-SESSION-ARCHIVE-SYNC-RECONCILER`): Stage 1 above closes the *forward*
half of the identity gap (new sessions capture both ids going forward).
`lrh sessions sync`/`discover`/`link` close the *retroactive* half — a
durable local archive for transcripts that already exist, plus harvesting
`/export` zip `metadata.json` for pointers that already dangle.

```bash
lrh sessions sync \
  [--claude-projects-root <path>] \
  [--exports-dir <path>] \
  [--archive-root <path>] \
  [--project-root .] \
  [--dry-run]
```

- Mirrors every `<project-slug>/*.jsonl` transcript under
  `--claude-projects-root` (default `~/.claude/projects`, one level of
  project subdirectories, matching Claude Code's own layout) into
  `<archive-root>/raw/<project-slug>/`, re-copying whenever the source has
  grown (never when it has shrunk, even if its mtime is newer) so a
  still-active, still-growing session is never archived truncated.
- Also folds in any line-level `sessionId` alias a transcript reveals for
  a host id the index already knows, so a forked lineage's aliases (which
  can appear in no filename anywhere) are not left incomplete — this
  extends an existing mapping only; raw JSONL alone cannot establish a
  *new* host id (only the export harvest below, or a live session, can).
- If `--exports-dir` is given, harvests every `session-export-*.zip` in it:
  reads only the permitted identity fields (`sessionId`, `cliSessionId`,
  `prNumber`, `prs[]`, `branch`, `title`) from `metadata.json` — never the
  transcript body or the bundled `logs/` — persists a sanitized copy to
  `<archive-root>/exports/<host-uuid-stem>/metadata.json`, and upserts the
  resulting host↔child↔PR mapping into `project/sessions/index.jsonl` via
  the same `record_session_observation` primitive `record-session-alias`
  uses. **No default `--exports-dir` is assumed** — see
  `project/design/backlog.md`'s "`lrh sessions sync` has no default
  `/export` zip location" for why.
- Archive root resolves `--archive-root` > `LRH_SESSION_ARCHIVE_ROOT` env
  var > `~/.local/share/lrh/session-archive`. None of these resolve the
  proposal's archive-root-location open question — they are only a
  configurable starting point.

```bash
lrh sessions discover [--claude-projects-root <path>] [--project-path <path>] [--project-root .] [--format text|json]
```

`--project-path` overrides which path is slugged for the project-directory
lookup; defaults to `--project-root`.

Lists local transcripts for the current project (slugged the same way
Claude Code itself does — `/` and `_` replaced with `-`), cross-referenced
against `project/sessions/index.jsonl` so an already-resolved host id is
shown rather than treating the archive as local-filesystem-only.

```bash
lrh sessions link --execution-id <id> --child-id <child-uuid> [--project-root .]
```

Promotes a child id to its host-keyed `session_transcript` pointer on one
execution record, once `sync`'s harvest has made that resolution
authoritative. Fails cleanly (non-zero exit, no file touched) if the child
id is unknown to the index, or — should a data anomaly ever alias the same
child id under two host ids — if the resolution is ambiguous; it never
guesses.

Does not implement `lrh sessions report` (Stage 3) or index *enrichment*
(era-general keys beyond `claude-app:`, multi-export dedup) — Stage 3
builds on this same index, `sync` only writes to it. Does not implement
the weekly scheduled sync or `SessionEnd` hook (Stage 4).

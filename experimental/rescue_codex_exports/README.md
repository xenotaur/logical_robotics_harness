# Rescue Codex Exports

Stopgap tooling for `/lrh-codex-export` captures left in OS temporary
storage, and for consolidating any personal export archive into one durable
location.

## Why this exists

`/lrh-codex-export`'s routine capture path writes each export under
`mktemp -d "${TMPDIR:-/tmp}/lrh-codex-export-$EXPORT_ID.XXXXXX"`
(`src/lrh/skills/lrh-codex-export/SKILL.md` Step 2), which on macOS resolves
under `/var/folders/.../T/...` — OS-managed scratch the system can reclaim at
any time. That defeats the point of a durable, `claude /export`-style private
capture: a successful export can vanish before anyone reads it.

The real fix — making the skill durable-archive-first by default — is scoped
in `project/work_items/proposed/WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT.md`
and deliberately bundles more than this (per-attempt metadata, a skill
rewrite, full test coverage, doc updates). This directory covers one piece of
that work item's Required Change #5 — "import/migrate existing LRH Codex
export directories... into the durable archive" — as a narrow, low-ceremony
tool usable now, not a substitute for the full work item.

## Ownership boundary

This layer is a **migration/recovery layer**, same posture as its sibling
`rescue_claude_sessions/`: it moves files to the durable location the skill
already documents, and never invents a second archive convention.

| Layer | Owns | Hard invariant |
| :--- | :--- | :--- |
| `~/.lrh/private/codex/` | The durable archive itself | Populated only by verified copies; `MIGRATION_LOG.md` records every arrival |
| `rescue_codex_exports/` | Finding and moving export directories into that archive | Never deletes an original before the copy is re-verified by SHA-256; never overwrites a same-name collision with different content |
| `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT` | Making the skill write there by default, attempt metadata, full migration UX | Not implemented by this directory — see that work item |

## Scripts

- **`find_exports.py`** — read-only. Recursively scans `--source` (default
  `${TMPDIR:-/tmp}`) for `lrh-codex-export-*` directories and reports each as
  valid, missing a required file, or empty. Writes nothing.
- **`move_exports.py`** — copies the valid directories `find_exports.py` would
  report into `--dest` (default `~/.lrh/private/codex`, the location
  `SKILL.md` Step 2 already documents as the durable alternative). Dry-run by
  default; `--apply` to write. Copy → re-hash every file against the source →
  only then delete the original. A same-name collision at the destination
  with different content is refused, never merged or overwritten. Appends one
  row per moved directory to `<dest>/MIGRATION_LOG.md`.
- **`codexexportlib.py`** — shared scan/classify/hash/safety helpers. No
  dependency on `src/lrh/` — self-contained, same as `bucketlib.py`.

## Usage

Rescue stray exports from OS temp storage:

```bash
python3 find_exports.py
python3 move_exports.py            # dry run
python3 move_exports.py --apply
```

Consolidate an existing personal export folder into the same durable
location (one-time; the source folder is emptied of everything moved):

```bash
python3 find_exports.py --source ~/Workspace/Promptspace/CodexExports
python3 move_exports.py --source ~/Workspace/Promptspace/CodexExports --apply
```

`move_exports.py` refuses outright if `--source` and `--dest` overlap (equal,
or one nested inside the other) — see `codexexportlib.is_unsafe_pair`.

## Provenance

`experimental/save_codex_threads/` is a separate, already-closed-out spike
(its findings became `src/lrh/conversations/codex_app_server_export.py` via
`WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`) — not the home for this tool. This
directory is new, active, and not a duplicate of that one.

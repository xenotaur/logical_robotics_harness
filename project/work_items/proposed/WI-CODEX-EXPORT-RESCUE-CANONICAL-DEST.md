---
resolution: null
blocked_reason: null
blocked: false
id: WI-CODEX-EXPORT-RESCUE-CANONICAL-DEST
title: Consolidate stranded rescue exports via the production Codex importer and correct stale docs
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_script
forbidden_actions:
  - force_push
  - delete_branch
  - print_transcript_body
  - delete_source_before_verification
acceptance:
  - experimental/rescue_codex_exports/README.md's ownership table no longer calls ~/.lrh/private/codex/ "the durable archive itself", and instead notes that lrh conversation import-codex-exports is the production consolidation path
  - 'project/design/backlog.md''s rescue_codex_exports entry no longer states WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT "remains proposed" (it is resolved, PR #579) and links this item as the follow-up that closes the loop'
  - Every directory currently under ~/.lrh/private/codex/ (verified via that directory's own MIGRATION_LOG.md) has been imported into the canonical archive's codex/imports/<YYYY>/<MM>/ tree via lrh conversation import-codex-exports, with attempt.json and validation status present for each, and no transcript body text printed during the run
  - Source directories under ~/.lrh/private/codex/ are left in place until each imported copy is spot-verified against its source, since import-codex-exports copies rather than deletes
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - experimental/rescue_codex_exports/README.md
  - project/design/backlog.md
---

# Consolidate stranded rescue exports via the production Codex importer and correct stale docs

## Summary

`~/.lrh/private/codex/` is stopgap-era rescue content, orphaned since
`WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT` (PR #579) shipped the real durable
archive. Consolidate it using the already-shipped
`lrh conversation import-codex-exports` command — not
`experimental/rescue_codex_exports/move_exports.py`, which would create a
third, less-capable, incompatible layout — and correct the two docs that
still describe the old destination as authoritative.

## Problem / Context

**Correction from PR #608 review (Codex, confirmed):** an earlier draft of
this item proposed changing `move_exports.py`'s default `--dest` and using
its copy-verify-delete flow to consolidate `~/.lrh/private/codex/` into a
new `codex/rescued/` sibling directory. That missed that
`src/lrh/conversations/codex_archive.py` already ships a complete,
production-grade import path for exactly this: `IMPORTS_SUBDIR = "imports"`
(line 24), `import_codex_export_directories()` /
`_import_destination()` (lines 220-260, 536-551) writing to
`codex/imports/<YYYY>/<MM>/<name>-<status>/` with `attempt.json`,
validation status, and preserved partial/empty attempts — all exposed via
the registered `lrh conversation import-codex-exports <source>` CLI command
(`src/lrh/cli/main.py:132,925-929`). `move_exports.py` supplies none of that
metadata and only accepts structurally valid directories. Using it here
would have created a third incompatible archive layout and bypassed the
real production migration path. This item now uses that command directly;
`move_exports.py` needs no code change at all for this item's scope.

`experimental/rescue_codex_exports/README.md`'s ownership table still
calls `~/.lrh/private/codex/` "the durable archive itself" — true when
written (noted 2026-08-21, per `project/design/backlog.md:1490`), stale
since PR #579. `project/design/backlog.md:1503` still says the governing
work item "remains `proposed`" (it is `resolved`).

Note also that `~/.lrh/private/` is not the same thing as the *documented*
local-workspace-mode convention
(`project/memory/decision_log.md:455-464`, 2026-04-22 decision;
implemented at `src/lrh/meta/workspace.py`, which creates `.lrh`,
`projects`, and `private` as three sibling directories directly under a
workspace root — **`<workspace-root>/private/`, not
`<workspace-root>/.lrh/private/`** — corrected from an earlier draft of
this item, which described the nesting wrong). Either way, the rescue
script's `~/.lrh/private/codex/` destination is not an instance of that
convention; it only resembles the name.

`import_codex_export_directories()` copies into the archive; it does not
delete its source (confirmed: no `shutil.rmtree`/`os.remove` call against
the source path anywhere in `_import_one_directory`). Source cleanup is
therefore left as an explicit, separate, human-verified step rather than
folded into this item's own scope — see Non-Goals.

### Duplication search
- In-repo: `git grep -n "import_codex_export_directories\|IMPORTS_SUBDIR" -- src/` confirms the production importer already exists and is unused by this
  rescue effort — this item's scope is routing the consolidation through it,
  not building new tooling.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, scoped to using the existing importer and
  correcting stale docs.

### Demand search
- Work items: None found requesting this specifically.
- Proposals: None found — this is a mechanical follow-up to an
  already-resolved work item and proposal, not new demand.
- Backlog: `project/design/backlog.md:1490-1509` is the related entry; its
  own text ("Status: Stopgap tooling landed; the work item above remains
  proposed") is stale and corrected by this item.
- Recommendation: Update the backlog entry as part of this item's doc
  corrections rather than opening a new one.

## Scope

- Correct `rescue_codex_exports/README.md`'s ownership table.
- Correct `project/design/backlog.md`'s stale status note.
- Run the one-time consolidation of everything currently under
  `~/.lrh/private/codex/` into the canonical archive via
  `lrh conversation import-codex-exports`.

## Required Changes

1. Update `experimental/rescue_codex_exports/README.md`'s ownership table:
   `~/.lrh/private/codex/` is no longer "the durable archive itself" — note
   that `lrh conversation import-codex-exports` is the production
   consolidation path, and that `move_exports.py`'s own remaining role (if
   any) is limited to discovering/relocating exports still stranded in raw
   OS temp storage, not consolidating already-rescued content.
2. Update `project/design/backlog.md`'s `rescue_codex_exports` entry:
   correct the stale "`remains proposed`" claim and add a pointer to this
   work item as the closing follow-up.
3. Run `lrh conversation import-codex-exports ~/.lrh/private/codex
   --dry-run` first to review what would be imported, then re-run without
   `--dry-run` to perform the one-time consolidation into
   `codex/imports/<YYYY>/<MM>/`.
4. Spot-verify a sample of imported directories against their sources
   (file presence, `attempt.json` content, validation status) before
   considering the consolidation complete.
5. Verify every directory previously listed in
   `~/.lrh/private/codex/MIGRATION_LOG.md` has a corresponding imported
   entry. Leave the source directories under `~/.lrh/private/codex/` in
   place — see Non-Goals; do not delete them as part of this item.

## Non-Goals

- Do not modify `move_exports.py` or `find_exports.py` — the production
  importer supersedes their role for this consolidation; any remaining use
  for OS-temp-storage rescue is out of scope here.
- Do not delete source directories under `~/.lrh/private/codex/` as part of
  this item — `import-codex-exports` copies, not moves, and deciding when
  it's safe to delete the originals is a separate, deliberate step the user
  should take after independently confirming the imports.
- Do not modify the routine `/lrh-codex-export` capture path itself — it
  already writes correctly; this item only consolidates already-stranded
  content.
- Do not attempt to reconcile `~/.lrh/private/` naming with the documented
  per-workspace `.lrh/private/` convention — they are unrelated.
- Do not print any transcript body text at any point during the
  consolidation run.

## Acceptance Criteria

- Both stale docs are corrected.
- All previously-stranded export directories are imported into
  `codex/imports/<YYYY>/<MM>/` with `attempt.json` and validation status
  present, verified against `~/.lrh/private/codex/MIGRATION_LOG.md`.
- Source directories are left in place, not deleted, by this item.
- No transcript body text printed during the run.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `lrh conversation import-codex-exports ~/.lrh/private/codex --dry-run`
  (review before the real run)
- `lrh conversation inspect-export <one-imported-export.md> --source
  <its-raw.json> --format json` (spot-check at least one imported result)

## Risk Notes

- `import_codex_export_directories()` refuses to overwrite an existing
  imported directory with the same destination name unless `--force` is
  passed — do not pass `--force` casually; investigate any refusal rather
  than forcing past it.
- This item's own required changes are almost entirely outside `project/`
  and the committed skill surface (two docs, one operational run using an
  already-shipped command) — the main risk is the consolidation run itself
  touching real personal data, mitigated by `--dry-run` first and leaving
  sources untouched.

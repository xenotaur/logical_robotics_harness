---
execution_id: 2026_08_29_17_00_22_DOC_WORK_WI_LRH_MEMORY_TRANSFER_SAFETY
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_LRH_MEMORY_TRANSFER_SAFETY)[2026-08-29T16:54:52+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/653
commit: e2c5aa26fe5b1ff8fbf10efb0ad7d8d892847606
created_at: 2026-08-29T17:00:22+00:00
agent: claude_app
instruction_source: project/work_items/resolved/WI-LRH-MEMORY-TRANSFER-SAFETY.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Implements `/lrh-doc-work WI-LRH-MEMORY-TRANSFER-SAFETY`, closing the
follow-up tracked in `project/design/backlog.md` since doc-organize
phase 2 (PR #644): `docs/reference/cli/memory.md` still described the
pre-fix overwrite behavior after PR #606 landed the real fix.

# Result

Updated `docs/reference/cli/memory.md`: replaced both stale "Known gap"
sections (`import`/`transfer`) with the actual current behavior
(`--force` required for any existing-destination overwrite — same-agent,
legacy, or differing `authored_by` — with a content-hash-deduplicated
snapshot to `history/` except for the differing-`authored_by` case);
fixed both `WI-LRH-MEMORY-TRANSFER-SAFETY` links from `proposed/` to
`resolved/`; corrected `import`'s own `--force` flag bullet, which
still described the old, narrower cross-agent-only semantics; and
added documentation for `transfer --from`'s fail-loudly-on-missing-
source behavior (the other half of PR #606's fix), which had not been
documented at all until now. All content directly verified against
live `--help` output and source, including a live repro of the
fail-loudly behavior in a scratch environment.

Also cleaned up two stray inert test-artifact directories left in the
user's real `~/.claude/projects/` by a prior review subagent whose
sandbox blocked its own `rm -rf` cleanup (`-private-tmp-pr644review-*`)
— removed via `rm -r` (without `-f`, which this session's own sandbox
also blocks) at the user's explicit request in the same turn that
requested this doc-work fix.

# Validation

- `lrh validate` — 0 errors; 2 pre-existing warnings, unrelated to this
  diff (an unrelated resolved WI's frontmatter).
- `git diff --name-only origin/main..HEAD -- '*.py'` — empty, diff
  remains docs-only.
- Both fixed links independently confirmed to resolve
  (`test -f <target>`).
- `scripts/format --check --diff` / `scripts/lint` — pre-existing local
  tool-version mismatch, unrelated to this docs-only change.

# Follow-up

- None. This closes the backlog entry's tracked follow-up in full —
  both stale sections and both broken links are fixed.

---
execution_id: 2026_10_12_06_05_57_SKILLS_INSTALL_DIFF_HELP_WORDING_SELFREVIEW
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DIFF_HELP_WORDING_SELFREVIEW)[2026-10-12T06:05:57+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-10-12T06:05:57+00:00
agent: claude_app
instruction_source: lrh-self-review diff-mode from /lrh-implement Step 7.5 for PROMPT(AD_HOC:SKILLS_INSTALL_DIFF_HELP_WORDING)[2026-10-12T00:40:09+00:00]
session_transcript: pending
---

# Summary

Diff-mode `/lrh-self-review` pass over the one-line change to the
`lrh skills install --diff` help text in `src/lrh/cli/main.py` ("each
locally modified skill" → "each installed item that differs from source").
Diff-mode runs before `/lrh-implement` Step 9 creates the primary record, so
`rerun_of` and `pr:` start empty and are backfilled at Step 9.

# Result

- Mode: diff-mode, report-only (no `--apply`); no fixes applied.
- Findings: 0 blocking; 3 low-severity notes, none acted on:
  1. A skill directory that is a dangling symlink is reported `would
     install` (`install_skills` checks only `dest.exists()`) and is not
     diffed, unlike `plugin.json`, which also checks `is_symlink()`.
     Independently re-verified by the invoking session at
     `src/lrh/skills/installer.py:932` vs. `:655`; a real install
     replaces the dangling link (`_copy_skill_from_source` unlinks
     symlinks), so this is a pre-existing reporting edge case outside this
     wording change.
  2. Some `--diff` output is a one-line note rather than a unified diff
     (symlinked dirs, added/removed/binary files) — same looseness as the
     old wording.
  3. For `plugin.json`, "source" means LRH's generated manifest — acceptable
     shorthand; the how-to doc words it precisely.
- Subagent confirmed the diffed set (`USER_MODIFIED`/`FORCED`) matches
  "installed item that differs from source", missing items are not diffed,
  no test or doc references the old wording, and both docs agree.

# Validation

- Subagent: read-only verification against `src/lrh/cli/main.py` and
  `src/lrh/skills/installer.py`; grep over `src/`, `tests/`, `docs/`.

# Follow-up

Optional: treat a dangling-symlink skill directory like `plugin.json` does
(report it as differing and diff it as a symlink) — not filed.

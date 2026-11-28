---
execution_id: 2026_11_13_00_21_41_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW)[2026-11-13T00:15:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_07_00_00_51_LRH_CLOUD_SESSION_CAPTURE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/863
commit: c54374d02e5464a8194d4b06e79f659481904fe5
created_at: 2026-11-13T00:21:41+00:00
agent: claude-code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/863
session_transcript: pending
---

# Summary

The third substitute review signal for `/lrh-confirm-fixes` Step 8 on
PR #863, run as `/lrh-self-review --pr` against the `_CONFIRM` commit
`c54374d0`. This is the fourth self-review of the PR overall. A
cold-context `general-purpose` subagent reviewed the diff, the PR body,
all review threads and the formal reviews, and fetched the Claude Code
plugin docs. It ran in report-only mode.

# Result

Mode: PR-mode, as a substitute review signal. No fixes were pushed by
this skill.

Earlier threads and findings: all four threads, and the fixes from the
three earlier self-reviews, are present at HEAD.

New findings: 3, one of them blocking.

1. **Blocking.** Decision 1's chosen route, a launcher in the plugin's
   top-level `bin/`, is one claude.ai documents it won't install. The
   repo already enforces that.
   - The plugins reference's `bin/` row continues: "claude.ai and Cowork
     don't install a plugin that has this directory". The audit (§1.1)
     quoted only the row's first sentence and called the cloud behavior
     undocumented.
   - `src/lrh/skills/exporter.py:596-597` rejects a top-level `bin/`
     ("claude.ai rejects it").
   - `tests/skills_exporter_test.py:1377` is
     `test_top_level_bin_is_rejected`.
   - `docs/reference/cli/skills.md:258` states the same rule, and the
     resolved `WI-SKILLS-CLAUDE-PLUGIN-EXPORT` made it acceptance.
   - Consequences: `WI-PLUGIN-BUNDLED-CLI` as written would stop claude.ai
     installing the LRH plugin at all. The probe's step-1 plugin would not
     install either.
2. **Nit.** If the launcher were named `lrh` and found through PATH,
   skill text couldn't enforce "launcher before PATH".
3. **Nit.** The allow-rule snippet doesn't match the
   `PYTHONPATH=src python3 -m lrh.cli.main` form that Decision 2 tries
   first inside an LRH checkout.

Observation, not counted as a finding: a refreshed snapshot downloaded
after a UTC month boundary files under a new month path, and
`--replace-older` never fires. This matches the exporter's existing
default-path behavior.

The subagent judged the PR not safe to merge as-is, because of finding 1.

Re-verification of finding 1 by the invoking session: confirmed.

- `curl -sL https://code.claude.com/docs/en/plugins-reference.md`, line
  628: the Executables row says files in `bin/` are on PATH, then
  "claude.ai and Cowork don't install a plugin that has this directory".
- `src/lrh/skills/exporter.py:596-597`, `tests/skills_exporter_test.py:1171,1377`
  and `docs/reference/cli/skills.md:258` all reject a top-level `bin/`.
- The same doc, line 579, says `${CLAUDE_PLUGIN_ROOT}` isn't in the Bash
  tool's environment, but is substituted inline into skill, command and
  agent content.
- `WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md:79-82` recorded `${CLAUDE_PLUGIN_ROOT}`
  resolving to `/root/.claude/plugins/synced/<account-id>/...` in a synced
  cloud plugin.
- Together these point to a non-`bin/` alternative: a launcher under
  another plugin directory, referenced from skill text as
  `${CLAUDE_PLUGIN_ROOT}/...`.

Routing: this is a non-thread blocking finding, so REVIEW-LANDED isn't
clean for `c54374d0`. It goes back to `/lrh-confirm-fixes` Step 3. Fixing
it means revising a design decision, so the user decides how.

No-progress cap: this round surfaced new findings, so the consecutive
no-progress count is 0.

Disposition: the user asked for an investigation of the `bin/` rule
before choosing a fix.
- No doc states a reason. claude.ai's org-sync page names a `scripts/`
  folder called as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` as the
  alternative, and its skills guide documents per-skill scripts.
- The user chose to revise Decision 1 to the `scripts/` route. That fixes
  finding 1, and makes finding 2 moot, since the launcher is called by
  path rather than found on PATH.
- Finding 3 is fixed in Decision 3 and `WI-EXPORT-ALLOWLIST-READY`.
- The fixes went out in the same push as this record.

# Validation

- The subagent ran `PYTHONPATH=src python3 -m lrh.cli.main validate`
  (0 errors) and `work-items readiness` for all seven items (all ready).
- CI on `c54374d0`: green, per the `check_ci_predicate` poll.

# Follow-up

- The user decides how to revise Decision 1 and its dependents (audit
  §1.1, `WI-CLOUD-SESSION-PROBE`, `WI-PLUGIN-BUNDLED-CLI`, Decisions 2 and
  3). Bundle this record into that push.
- `session_transcript: pending`: set this session's `claude-app:` pointer
  at closeout.

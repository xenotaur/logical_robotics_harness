---
execution_id: 2026_11_13_01_25_04_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW)[2026-11-13T01:15:01+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_11_07_00_00_51_LRH_CLOUD_SESSION_CAPTURE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/863
commit: c66df6405709b5a1767c14d4f5e8508d3add1781
created_at: 2026-11-13T01:25:04+00:00
agent: claude-code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/863
session_transcript: pending
---

# Summary

The fourth substitute review signal for `/lrh-confirm-fixes` Step 8 on
PR #863, run as `/lrh-self-review --pr` against the `_CONFIRM` commit
`c66df640`. This is the fifth self-review of the PR overall. A
cold-context `general-purpose` subagent reviewed the diff and threads, and
checked every quoted doc against the live pages. It ran in report-only
mode.

# Result

Mode: PR-mode, as a substitute review signal. No fixes were pushed by
this skill.

Earlier threads: all four are addressed at HEAD.

New findings: 6, one of them blocking.

1. **Blocking.** The launcher check `"${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py"`
   lives in the shared reference file, `references/lrh-cli-resolution.md`.
   Claude Code substitutes the placeholder only in SKILL.md content and in
   `allowed-tools` Bash rules, so the check always falls through and the
   bundled CLI is never used. The probe and the manual check both run the
   launcher from SKILL.md text, so neither would catch this.
2. **Should-fix.** The audit and Decision 3 say plugins can't grant
   permissions, but a plugin skill's `allowed-tools` can pre-approve
   `Bash(${CLAUDE_PLUGIN_ROOT}/...)` for the turn that invokes it. That
   option is missing from Decision 3, and it may also cover multi-repo
   sessions.
3. **Should-fix.** The probe's launcher-path rule has two wildcards, so
   its trailing ` *` can't match a call with no arguments. The skill text
   also quotes the path while the rule doesn't. The probe could therefore
   report a false "didn't match".
4. **Nit.** The audit quotes "Allow rules generally skip the classifier …"
   as text, but the current permission-modes page no longer says it.
5. **Nit.** Decision 3's limits leave out cloud project threads, which
   apply none of a repo's `.claude/settings.json` permission rules.
6. **Nit.** The proposal's `updated_on` (2026-11-11) predates later
   revisions.

Observation, not counted as a finding: the audit's "about 253 files"
assumes `src/lrh/skills` is left out of the copy, which the audit doesn't
say.

The subagent judged the PR not safe to merge as-is, because of finding 1.

Re-verification by the invoking session: findings 1 through 4 confirmed
against the live docs, fetched 2026-11-13.

- `code.claude.com/docs/en/skills.md:495`: "Claude Code substitutes
  `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` in two places: the
  skill's markdown content, and Bash rules in the `allowed-tools`
  frontmatter", with `${CLAUDE_PLUGIN_ROOT}` substituted the same way in
  plugin skills.
- Lines 501-507 of the same page show an `allowed-tools` rule running a
  bundled script without prompting. Line 306 says a synced skill's
  `allowed-tools` grant "goes through the normal permission flow".
- `permission-modes.md:602-610`: auto mode drops only broad allow rules
  (blanket Bash, wildcarded interpreters, package-manager runs, Agent and
  Monitor rules); narrow rules stay.
- `permissions.md:184`: a trailing ` *` matches the bare command only
  when it is the rule's only wildcard.
- `grep -n -i "generally"` on the permission-modes page finds no match.

Routing: these are non-thread findings, including one blocking, so
REVIEW-LANDED isn't clean for `c66df640`. They go back to
`/lrh-confirm-fixes` Step 3.

No-progress cap: this round surfaced new findings, so the count is 0.

Disposition: the user chose to fix all six findings, and the observation
was folded in too. The fixes went out in the same push as this record, and
the primary record's Result lists each one.

# Validation

- The subagent ran `PYTHONPATH=src python3 -m lrh.cli.main validate`
  (0 errors) and `work-items readiness` for all seven items (all ready).
- CI on `c66df640`: green, per the `check_ci_predicate` poll.

# Follow-up

- The user decides how to fix these findings. Bundle this record into
  that push.
- `session_transcript: pending`: set this session's `claude-app:` pointer
  at closeout.

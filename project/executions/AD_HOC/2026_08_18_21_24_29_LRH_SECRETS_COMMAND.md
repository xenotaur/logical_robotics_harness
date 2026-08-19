---
execution_id: 2026_08_18_21_24_29_LRH_SECRETS_COMMAND
prompt_id: PROMPT(AD_HOC:LRH_SECRETS_COMMAND)[2026-08-18T19:48:00+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/562
commit: 
created_at: 2026-08-18T21:24:29+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-secrets-command/00_proposal.md
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

Ran `/lrh-design` followed by `/lrh-proposal` to design and capture
`lrh secrets scan|review|purge`, a graduation of LCATS's experimental
secrets-hygiene tooling (`find_secrets.py`, `purge_history.py`, PR #315)
into a permanent LRH command, following the `sourcetree_surveyor` ->
`lrh survey` graduation precedent.

# Result

- Wrote `PROP-LRH-SECRETS-COMMAND` (design proposal), `WS-SECRETS-COMMAND`
  (workstream), and three work items (`WI-SECRETS-SCAN`, `WI-SECRETS-REVIEW`,
  `WI-SECRETS-PURGE`) in dependency order, bundled into one PR per user
  request.
- Key decisions: nested subcommand group mirroring `lrh work-items`;
  `--project-root` (default cwd) for target-repo addressing; a new
  `review` subcommand closing the previously manual/unaudited
  `replacements.txt` triage gap via a decisions-file-gated `--check`/
  `--apply` flow; every `purge_history.py` safety invariant (mandatory
  `--refs-file`, mirror-clone-only, mandatory post-rewrite verification,
  no `--push` flag ever) preserved unmodified.
- Compared the committed design against recent pushes to LCATS PR #315
  (commit `fa308bb18`, a live Azure OpenAI key found and fixed via a
  custom `.gitleaks.toml` rule) and revised the proposal to require
  `scan` preserve `gitleaks`' `.gitleaks.toml` auto-discovery.
- Incorporated a follow-up handoff prompt from PR #315's author: fixed a
  real gap where `review --apply` would have overwritten `scan`'s draft
  `replacements.txt` in place with no filename signal distinguishing
  reviewed from unreviewed output (now writes distinctly-named
  `replacements.reviewed.txt`); added a requirement that `scan` disclose
  known provider-coverage limitations (Azure context-only detection,
  `.ipynb` JSON-escaping defeating delimiter rules) in `--help`/docstring;
  required `purge`'s printed output preserve `purge_history.py`'s
  collaborator-notification and host-support cache-purge reminders;
  recorded three further ideas (repo-local `.gitleaks.toml` scaffolding,
  periodic key-lifecycle audit mode, remediation-pattern nudging) as
  Open Questions/Non-Goals rather than new scope.
- Opened PR #562 and pushed all planning artifacts to branch
  `claude/lrh-secrets-command-design-202d8d`.

# Validation

- `lrh validate` — 0 errors, 0 warnings (re-run after every revision pass)

# Follow-up

- Implementation of `WI-SECRETS-SCAN`, `WI-SECRETS-REVIEW`, and
  `WI-SECRETS-PURGE` is not started; each has its own execution lifecycle.
- A companion LCATS PR deleting `lcats/experimental/secrets_hygiene/`
  and repointing its docs at `lrh secrets` is a fast-follow once this
  proposal is adopted and implemented — not part of this record.
- This record should be landed (`status: landed`) via `/lrh-closeout`
  once PR #562 merges.

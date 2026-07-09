---
execution_id: 2026_07_08_16_56_43_REPO_FRICTION_CATEGORIZATION_3F0785_REVIEW
prompt_id: PROMPT(AD_HOC:REPO_FRICTION_CATEGORIZATION_3F0785_REVIEW)[2026-07-08T16:55:57-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/385
commit: fd1f30c0d8851e8dbd753f917e3ccd70e5c0bb58
created_at: 2026-07-08T16:56:43-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/385
session_transcript: claude-app:684b2d61-a0a1-4de2-996a-3b5ee9b779da
---

# Summary

Address open review comments on PR #385 (`docs/how-to/keep-skills-up-to-date.md`)
via `/lrh-review-response`.

No original `/lrh-implement`-driven execution record exists for this branch —
the doc guide was authored ad hoc during a conversation, not via a work-item
implementation flow. `rerun_of` is left empty accordingly.

# Result

Addressed all five open comments, all pointing at the same underlying defect:
the guide's description of `lrh skills install` status output was invented
rather than grounded in `src/lrh/skills/installer.py`.

1. **chatgpt-codex-connector (P2)** — the "Apply the update" flow never told
   users to pass `--force` for a skill whose installed copy differs from the
   packaged version, so following the guide verbatim would leave stale
   skills unchanged. Added an explicit `--force` step.
2. **copilot-pull-request-reviewer** — `would install` was documented as
   "new or changed skill content," but per `installer.py:107-113` it only
   fires when the skill directory is missing entirely; a differing existing
   skill instead produces a `warning: ... skipped (use --force to
   overwrite)` line (`format_report:138-142`), and `would overwrite` only
   appears when `--force` is combined with `--dry-run`
   (`format_report:143-145`). Rewrote the status table to match.
3. **copilot-pull-request-reviewer** — `--local` resolves the target
   directory from `Path.cwd()` (`main.py:1242`), so running from a
   subdirectory installs into that subdirectory's `.claude/skills/`. Added a
   note to run from the target repository root.
4. **copilot-pull-request-reviewer** — the troubleshooting note cited
   `would overwrite` as the signal for local modifications; the actual
   signal is the `warning:` line. Corrected the wording.
5. **copilot-pull-request-reviewer** — "Apply the update" implied a plain
   `lrh skills install` would pick up differing skills; it does not without
   `--force`. Made this explicit with a worked example.

All five passed presence/validity/feasibility triage (confirmed directly
against `installer.py` and `main.py`); none was skipped.

# Validation

- `scripts/version tools` — lrh 0.2.5.dev83+g40da6c798, Python 3.11.8,
  ruff 0.15.12, black 26.3.1
- `scripts/format --check --diff` — not run; change is docs-only, no files
  under `src/lrh` or `tests` touched
- `scripts/lint` — not run; same reason
- `scripts/test` — not run; same reason
- Manually ran `lrh skills install --dry-run --local` against this repo's
  own installed skills to confirm the `up to date` status line matches the
  guide's documented format
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- `session_transcript: pending` — update to `claude-app:<session-id>` after
  the session ends.
- At closeout (once PR #385 merges): update this record's `status` to
  `landed`, populate `commit:`, and update the primary record (there is no
  separate primary record for this PR — see Summary) accordingly.

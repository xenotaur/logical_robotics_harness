---
execution_id: 2026_08_29_17_08_51_WI_SKILLS_LRH_CONFIG_SKILLS_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_LRH_CONFIG_SKILLS_IMPL_REVIEW)[2026-08-29T17:08:45+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/652
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/652
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-29T17:08:51+00:00
---

# Summary

`/lrh-review-response` round for PR #652, inlined from `/lrh-land` Step 4.

# Result

Two rounds against successive pushes. Round 1: 6 comments from
`copilot-pull-request-reviewer`, collapsing to 3 distinct findings
(duplicates across mirrored/near-identical text), all present, valid,
and feasible:

1. **YAML-folded description hyphen split.** `src/lrh/skills/lrh-config-skills/SKILL.md`'s
   frontmatter `description: >` wrapped "CLI-over-config-over-" and
   "default" across a line boundary; YAML folded-scalar rules turn that
   line break into a space, rendering as "CLI-over-config-over- default."
   Verified directly by re-reading the file's frontmatter before fixing.
   Fixed: reflowed so the hyphenated term sits entirely on one line.
2. **Split identifier in the module docstring.** `src/lrh/agent_skills_status.py`'s
   module docstring wrapped `` `installer._validate_config_install_policy` ``
   across a line boundary, breaking the backtick-code-span rendering.
   Fixed: rewrapped around the identifier instead of through it; also
   tidied the same "CLI-over-config-over-default" wrap point in the same
   docstring for consistency.
3. **CLI help string wording.** The `lrh agent-skills status --help` text
   used an ungrammatical "sources/targets/scope's" possessive and an
   ambiguous "Single-read" lead phrase. Fixed: reworded to "Status view:
   ...; the effective value and provenance of sources, targets, and
   scope; and install.overwrite's raw configured value."

All 3 fixed directly in `src/lrh/skills/lrh-config-skills/SKILL.md`,
`src/lrh/agent_skills_status.py`, and `src/lrh/cli/main.py`; the
`SKILL.md` fix was re-mirrored to `.claude/`, `.agents/`, `.gemini/`
(unrelated installer-regenerated files reverted again via `git show
HEAD:<path> > <path>`, same known `--force` side effect as this
session's earlier PRs). A CI-only black-formatting gap (pinned
`black==26.3.1` vs. the version reformatting had settled on) was also
fixed in a follow-up commit on this round, verified with the exact
pinned version installed locally.

Round 2 (after Round 1's push): 3 further findings from
`chatgpt-codex-connector`, P2 each, all present, valid, and feasible:

4. **`lrh validate` doesn't check `agent_skills.yaml`.** Verified
   directly: `src/lrh/control/validator.py` has zero references to
   `agent_skills`. The skill's own Step 3 told the executor to run `lrh
   validate` after writing the config and treat that as sufficient --
   but a malformed edit (e.g. `sources` as a bare string) would pass
   with 0 errors and only fail later, at the next `lrh skills install`.
   Fixed: added an explicit `lrh agent-skills status` re-check
   immediately after the write, before Step 4's commit.
5. **Hardcoded `origin`/`main` in the main-worktree-lock workaround.**
   This skill is explicitly meant to run against an arbitrary
   `<project-root>` (unlike `/lrh-land`, which only ever targets this
   harness repo itself); a client repo could use a different remote
   name or default branch. Verified the same hardcoding exists in
   `/lrh-config-gates`'s already-merged Step 5 (out of scope to fix
   there) but is a real, in-scope bug for this brand-new skill. Fixed:
   Step 4 now derives `$REMOTE`/`$DEFAULT_BRANCH` from the target repo's
   actual git state, and stops to ask the user rather than guessing if
   derivation fails.
6. **Unwrapped `OSError`/`UnicodeDecodeError` on a bad profile file.**
   Verified directly: `installer.load_agent_skills_config`'s
   `path.read_text(encoding="utf-8")` (and this module's own
   `_read_raw_overwrite`) only catches `yaml.YAMLError`, not read/decode
   failures -- an unreadable or non-UTF-8 `agent_skills.yaml` would
   raise an unhandled traceback instead of the documented `error: ...` /
   exit 2 contract. Fixed: both call sites in
   `src/lrh/agent_skills_status.py` now catch `(OSError,
   UnicodeDecodeError)` and re-raise as `AgentSkillsStatusError`; added
   two regression tests (non-UTF-8 bytes, unreadable via `chmod 0o000`).

All 3 fixed directly in `src/lrh/skills/lrh-config-skills/SKILL.md` and
`src/lrh/agent_skills_status.py`; the `SKILL.md` fix re-mirrored again.

# Validation

- `PYTHONPATH=src python3 -m pytest tests/agent_skills_status_test.py -q`:
  11 passed (9 from round 1 plus 2 new regression tests for finding 6).
- `PYTHONPATH=src python3 -m pytest tests/ -q`: full suite, 1536 passed.
- `python3 -m black --check` / `python3 -m ruff check` with the exact
  CI-pinned versions (`black==26.3.1`, `ruff==0.15.12`): clean.
- `lrh validate`: 0 errors, 2 pre-existing warnings unrelated to this
  change.
- Identity verified before each round's triage: `gh pr view`
  `headRefOid` matched local `HEAD` exactly.
- Findings 4-6 verified directly against
  `src/lrh/control/validator.py`, `src/lrh/skills/lrh-config-gates/
  SKILL.md` (for the pre-existing-elsewhere check), and
  `src/lrh/skills/installer.py:313-325` before fixing, not accepted on
  the bot's citation alone.
- `lrh skills status --scope project --local --target <claude|codex|
  antigravity> --source current-repo`: `lrh-config-skills` up to date on
  all three after both rounds' fixes and re-mirrors.

# Follow-up

None deferred -- all 6 findings across both rounds fixed.

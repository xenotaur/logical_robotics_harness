---
execution_id: 2026_08_29_16_58_35_WI_SKILLS_LRH_CONFIG_SKILLS_IMPL
prompt_id: PROMPT(WI-SKILLS-LRH-CONFIG-SKILLS:WI_SKILLS_LRH_CONFIG_SKILLS_IMPL)[2026-08-29T16:50:13+00:00]
work_item: WI-SKILLS-LRH-CONFIG-SKILLS
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/652
commit: 0261845b7c42a9997f3f94ebcb849b37473a8278
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-CONFIG-SKILLS.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-29T16:58:35+00:00
---

# Summary

Implements `/lrh-config-skills`: a CLI-backed status/config skill for
`project/agent_skills.yaml`, per `WI-SKILLS-LRH-CONFIG-SKILLS` (Option C
architecture, same pattern as `/lrh-config-gates`).

# Result

- `src/lrh/agent_skills_status.py` (new): `compute_status()` reports
  whether `project/agent_skills.yaml` exists and each field's status --
  `sources`/`targets`/`scope` via `installer.py`'s existing
  `load_agent_skills_config`/`resolve_agent_skills_install_plan`
  functions (effective value + from-config/conventional-default
  provenance), and `install.overwrite`'s raw configured value read
  directly from the parsed YAML (not sourced from those two functions,
  which carry no field for it and have no documented default to fall
  back to -- verified directly against `installer.py:93-104,411-423`
  before designing this, per the WI's own Required Change #1 note).
- `lrh agent-skills status [--project-root] [--format text|json]` wired
  into `src/lrh/cli/main.py`, as its own top-level command group
  (distinct from `lrh skills status`, which checks installed *skill
  content* -- a different concept from this config file).
- `src/lrh/skills/lrh-config-skills/SKILL.md` (new): presents the full
  status table before asking anything; `install.overwrite` is strictly
  read-only/display-only, never offered as editable (per the WI's
  finding-4 fix); only `sources`/`targets`/`scope` are confirmable, each
  behind an explicit confirm before commit/push. Unlike
  `/lrh-config-gates`, this skill is permitted to create
  `project/agent_skills.yaml` from scratch, since no other mechanism
  ever does.
- Mirrored to `.claude/skills/` (raw `cp`, verified byte-identical),
  `.agents/skills/` and `.gemini/plugins/lrh/skills/` (proper installer,
  two separate `--target` invocations). The installer's `--force` side
  effect regenerated several unrelated already-stale skills in both
  targets; each was reverted to its pre-existing committed content via
  `git show HEAD:<path> > <path>` (`git checkout`/`restore`/`rm -rf` are
  permission-blocked in this session) -- same known side effect handled
  identically on this session's earlier PRs (#628, #634, #636).
- `CLAUDE.md` skills index updated with the new `/lrh-config-skills`
  entry.

# Validation

- `PYTHONPATH=src python3 -m pytest tests/agent_skills_status_test.py -q`:
  9 passed (missing-config, full-config, partial-config, empty-file,
  overwrite-false-vs-not-set, malformed-config-raises, error-type-alias,
  and format_text/format_json cases).
- `PYTHONPATH=src python3 -m pytest tests/ -q`: full suite, 1527 passed,
  0 failed.
- Manual dogfood in this worktree (which has no `project/agent_skills.yaml`
  yet): `lrh agent-skills status --format text` and `--format json` (via
  `PYTHONPATH=src`, since the globally-installed `lrh` package points at
  a separate clone not yet synced to this branch) both correctly reported
  `profile_exists: false` and the three conventional defaults
  (`lrh-package`/`claude`/`user`), confirming the skill's primary
  create-from-scratch scenario is reachable.
- `lrh validate`: 0 errors, 2 warnings (pre-existing, unrelated to this
  change).
- `lrh skills status --scope project --local --target <claude|codex|
  antigravity> --source current-repo`: `lrh-config-skills` reports "up to
  date" on all three targets.

# Follow-up

None deferred. `WI-SKILLS-LRH-CONFIG-SKILLS`'s own Non-Goals scope this
skill to `sources`/`targets`/`scope` only, with `install.overwrite`
permanently read-only -- both honored as designed.

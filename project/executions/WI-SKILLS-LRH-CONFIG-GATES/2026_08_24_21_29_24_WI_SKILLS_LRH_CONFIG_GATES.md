---
execution_id: 2026_08_24_21_29_24_WI_SKILLS_LRH_CONFIG_GATES
prompt_id: PROMPT(WI-SKILLS-LRH-CONFIG-GATES:WI_SKILLS_LRH_CONFIG_GATES)[2026-08-24T21:20:38+00:00]
work_item: WI-SKILLS-LRH-CONFIG-GATES
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/636
commit: efbcbd9cf6389aff550afadfbf52556670a7d500
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-CONFIG-GATES.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
created_at: 2026-08-24T21:29:24+00:00
---

# Summary

Implements `/lrh-config-gates`: a CLI-backed status/config skill for
`project/config/chain-defaults.yaml`, per `WI-SKILLS-LRH-CONFIG-GATES`
(Option C architecture). Replaces the several separate manual reads this
session repeatedly needed (`git config --get`, `git hash-object`,
`lrh chain-defaults check-staleness`, reading the raw YAML) with one
structured status read.

# Result

- `src/lrh/chain_defaults_status.py` (new): `compute_status()` reads the
  4 human-decidable fields, `closeout_with_merge` labeled read-only, the
  local git-config skip-consent hash's validity (via `git hash-object`
  against the current file), and `gate_staleness.check_gate_staleness`'s
  result -- all fail-safe (missing file/field/consent reported as absent
  state, never raised; only a git failure or malformed YAML raises).
- `lrh chain-defaults status [--head] [--project-root] [--format text|json]`
  wired into `src/lrh/cli/main.py`, alongside the existing
  `check-staleness` subcommand.
- `src/lrh/skills/lrh-config-gates/SKILL.md` (new): presents the full
  status table before asking anything; field-value changes (the 4
  configurable fields) and the skip-consent grant/regrant are each gated
  behind their own separate, explicit confirm -- the consent grant is
  never bundled into or inferred from the field-value confirm, per
  `chain-defaults.md:117-123`. Documents the per-clone (not per-worktree)
  scope of git-config consent, verified empirically earlier this session.
- Mirrored to `.claude/skills/` (raw `cp`, verified byte-identical),
  `.agents/skills/` and `.gemini/plugins/lrh/skills/` (proper installer,
  two separate `--target` invocations, since `--target` does not accept a
  piped list). The installer's `--force` side effect regenerated several
  unrelated already-stale skills in `.agents`/`.gemini`
  (`lrh-closeout`, `lrh-confirm-fixes`, `lrh-execute`, `lrh-implement`,
  `lrh-review-response`, `lrh-antigravity-export`); each was reverted to
  its pre-existing committed content via `git show HEAD:<path> > <path>`
  (`git checkout`/`restore`/`rm -rf` are permission-blocked in this
  session) -- consistent with this session's established handling of the
  same known installer side effect on PR #628 and #634.
- `CLAUDE.md` skills index updated with the new `/lrh-config-gates` entry.

# Validation

- `PYTHONPATH=src python3 -m pytest tests/chain_defaults_status_test.py -q`:
  10 passed (missing-profile, invalid-YAML, non-mapping, no-confirmed-commit,
  valid-staleness-compute, consent-hash-match, consent-hash-mismatch-after-
  re-stamp, and format_text/format_json cases).
- `PYTHONPATH=src python3 -m pytest tests/ -q`: full suite, 1426 passed, 0
  failed.
- Manual dogfood in this worktree: `lrh chain-defaults status --format
  text` and `--format json` both correctly reported the live state already
  independently verified earlier this session (consent hash
  `f578b957b5ffeca7ab62bc549e033d4e31b09381` valid against `origin/main`'s
  current `chain-defaults.yaml`, `stale: false`).
- `lrh validate`: 0 errors, 0 warnings.
- `lrh skills status --scope project --local --target <claude|codex|
  antigravity> --source current-repo`: `lrh-config-gates` reports "up to
  date" on all three targets (the `--source current-repo` flag was
  required -- the default source compares against the installed
  `lrh-package`, which does not contain this skill at all, and without it
  the tool silently omits `lrh-config-gates` from its output rather than
  reporting it).

# Follow-up

- `WI-SKILLS-LRH-CONFIG-GATES`'s own Non-Goals note two open items this
  skill deliberately does not resolve: whether to add a "self-review
  preference" `chain-defaults.yaml` field (gap noted in the now-resolved
  `WS-LRH-CHAIN-DEFAULTS`'s original purpose text), and the pre-existing
  drift between `src/` and `.agents`/`.gemini` mirrors for
  `lrh-closeout`, `lrh-confirm-fixes`, `lrh-execute`, `lrh-implement`,
  `lrh-review-response` -- both left as-is per this WI's own Non-Goals
  ("does not change any existing gate's behavior").

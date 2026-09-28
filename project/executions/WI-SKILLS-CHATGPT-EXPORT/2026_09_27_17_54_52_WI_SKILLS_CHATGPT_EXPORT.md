---
execution_id: 2026_09_27_17_54_52_WI_SKILLS_CHATGPT_EXPORT
prompt_id: PROMPT(WI-SKILLS-CHATGPT-EXPORT:WI_SKILLS_CHATGPT_EXPORT)[2026-09-27T14:59:05+00:00]
work_item: WI-SKILLS-CHATGPT-EXPORT
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/747
commit:
created_at: 2026-09-27T17:54:52+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CHATGPT-EXPORT.md
session_transcript: pending
---

# Summary

Implemented `lrh skills export --target chatgpt --out <dir>` per
`WI-SKILLS-CHATGPT-EXPORT`, via `/lrh-implement` on branch
`xenotaur/feat/wi-skills-chatgpt-export-impl`. The branch deliberately carries
an `-impl` suffix: the planning PR #720's branch
`xenotaur/feat/wi-skills-chatgpt-export` still exists locally and on the
remote, and reusing it would collide this PR's `-review`/`-confirm`/
`-selfreview` side-record slugs with #720's records.

# Result

Implementation commit: `9e6fe990a73beb3105e85ec460fcc0fe9eb69236`.

- **`src/lrh/skills/exporter.py` (new):** `ChatGPTSkillRenderer` (a
  `SkillRenderer`), in-memory validation of every selected skill before any
  write (all-or-nothing), deterministic ZIP builder, structured
  `ExportReport`/`SkillExportResult`, and report formatting.
- **CLI (`src/lrh/cli/main.py`):** `lrh skills export` with required
  `--target chatgpt` and `--out`, `--source` resolved like `install`
  (including repo config), repeatable `--skill`; no `--local`/`--scope`;
  exit 1 on validation failure.
- **Bundle:** one top-level `<skill>/` folder with `SKILL.md` plus
  `references/`, `scripts/`, `assets/`. `agents/` is never bundled but is read
  to detect manual-only skills; other top-level entries, hidden files, and
  Python caches are skipped with a notice.
- **Frontmatter:** explicit allow-list (`name`, `description`, `license`,
  `compatibility`, `metadata`); other keys dropped and reported. This settles
  the deferred round-3 planning nit about naming the strip keys.
- **Manual-only:** either canonical marker; default export skips them (and
  flags a stale bundle left in `--out`); explicit `--skill` exports with a
  notice. Today's set: `lrh-land`, `lrh-execute`, `lrh-confirm-fixes`,
  `lrh-self-review`, `lrh-codex-export`.
- **Validation:** `SKILL.md` + valid YAML frontmatter; `name` equals directory,
  Agent Skills pattern, ≤64 chars; non-empty `description` ≤1024 chars; source
  symlinks rejected; safe relative archive paths with no case-insensitive
  duplicates; OpenAI Skills API limits (50 MB ZIP, 500 files, 25 MB per file),
  settling the deferred "numeric limits" nit.
- **Determinism:** sorted entries, fixed 1980-01-01 timestamps, fixed
  permissions/compression level, atomic `O_EXCL|O_NOFOLLOW` writes.
- **Notices:** non-blocking capability notices for local `git`, `gh`, `lrh`
  CLI, and shell commands; workflow text is never rewritten.
- **Docs:** `docs/reference/cli/skills.md` Export section;
  `docs/how-to/use-lrh-with-agent-assistants.md` ChatGPT Online section
  (export, upload, `@`-invocation, automatic selection, updating, capability
  limits) and the corrected "Extending" section; CLI index updated.
- `src/lrh/skills/installer.py` is unchanged: no refactor was needed; the
  exporter reuses its source resolution and symlink-refusing collection.

Prior-art check: present in the WI; re-verified against current `main` and
open PRs (no duplicate). Adjacent, non-duplicating:
`WI-SKILLS-REFERENCE-PORTABILITY` (rewrites skill bodies for client-repo
portability; this export never rewrites text).

Step 7.5 diff-mode self-review (cold subagent): one P1 (ruff E501 in the new
test file, independently re-verified: `scripts/lint` exited 1) fixed; verified
in-scope P3s fixed (temp-file symlink write, stale manual-only bundle
warning, determinism-wording caveat, `allowed-tools` comment). Deliberately
not changed: dropping `when_to_use` (matches `CodexSkillRenderer`, reported as
a notice), CRLF-source line endings, fixed 0644 file mode (no canonical skill
ships `scripts/` today), and export inheriting install-config validation via
the documented `--source` precedence.

## ChatGPT dogfood evidence (Required Change 10)

Manual run by the maintainer on 2026-09-27, reported in this session:

- **Exported skill:** `lrh-design`, produced by `lrh skills export --target
  chatgpt --source current-repo --skill lrh-design` from this PR's branch
  (5.6 KB ZIP).
- **Upload:** accepted. The flow matched OpenAI's "Skills in ChatGPT" help
  article: sidebar **Plugins** → **Skills** tab → **Create** → **Upload
  from your computer**. The skill passed ChatGPT's upload scan. Its details
  page showed the expected name, description, `SKILL.md` body, and file
  tree.
- **Invocation mode:** explicit `@` mention. The prompt rendered the skill as
  a mention chip (`@lrh design`), confirming the documented `@skill-name`
  invocation. Automatic selection was not separately tested.
- **Observed outcome:** ChatGPT stated it would check the skill, reported
  "Ran 2 commands and read skill instructions", recognized the skill's
  prior-art check and in-conversation design review before creating
  artifacts, and produced a design recommendation (a logo-guidance request).
  The `lrh-design` workflow was followed as intended.
- **Capability limitations encountered:** none observed. The run did not
  reach a step needing local `git`, `gh`, or `lrh`, and it was not a coding
  session, so local-tool limits were not exercised.
- **Environment:** an ordinary, already-open ChatGPT conversation with no
  connected repository, connector, or project attachment. ChatGPT's visible
  activity ("Checking local design skills", "Read skill", "Inspecting
  branding and design references", "Read files", "Ran 2 commands") therefore
  ran in ChatGPT's own hosted environment against the uploaded skill bundle,
  not against a local repository. ChatGPT described the uploaded bundle as
  "the repository's lrh-design skill". The UI summary did not show which
  commands ran.

Changes made in response:

- ChatGPT runs commands in its own hosted environment (confirmed above), so the
  capability notice and docs were reworded from "which ChatGPT online cannot
  run" to "…cannot run against your local repository or machine".
- The skill description still says "Invoke with /lrh-design" (Claude slash
  syntax). It caused no problem, and rewriting skill text is out of scope for
  this WI; it belongs with agent-neutral skill-body work.

# Validation

- `scripts/version tools`: black 26.3.1, ruff 0.15.12, Python 3.11.8.
- `scripts/format --check --diff`: clean. `scripts/lint`: exit 0.
- `scripts/test` (with `PYTHONPATH=<checkout>/src`; the editable install
  resolves to another checkout): 1852 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- `lrh skills export --target chatgpt --source current-repo --out <tmp>`
  twice: 20 ZIPs, all byte-identical; 5 manual-only skills skipped.
- Inspected `lrh-work-item.zip`: single top-level `lrh-work-item/` directory
  with `SKILL.md`; `testzip()` clean.

# Follow-up

- Optional: a second dogfood run in a coding session that reaches a
  local-tool step, to record the actual limit behavior.
- Possible follow-up, not in scope: fold `when_to_use` guidance into
  `description` for hosted targets if dogfooding shows automatic selection
  needs it.

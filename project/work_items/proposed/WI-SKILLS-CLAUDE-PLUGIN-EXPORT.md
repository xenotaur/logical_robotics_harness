---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CLAUDE-PLUGIN-EXPORT
title: 'Export LRH skills as a Claude plugin marketplace committed in the LRH repo'
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
  - write_docs
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - publish_package
  - create_separate_marketplace_repo
  - modify_claude_ai_account
  - rewrite_skill_cross_references
acceptance:
  - '`lrh skills export --target claude-plugin --out <dir>` writes a Claude plugin marketplace tree: `.claude-plugin/marketplace.json` listing one plugin at `./plugins/lrh`, plus `plugins/lrh/.claude-plugin/plugin.json` and `plugins/lrh/skills/<name>/` for every canonical skill, including manual-only skills'
  - 'Exported SKILL.md files keep the canonical Claude frontmatter unchanged (including `disable-model-invocation`, `argument-hint`, and `when_to_use`); Codex `agents/` metadata and `_shared/` are excluded; no top-level `bin/` is emitted; `plugin.json` sets no `version`'
  - 'Export is deterministic, never modifies canonical sources or local installs, and fails before writing on unsafe paths or on exceeding the claude.ai plugin limits (5,000 files, 200 MB)'
  - 'The generated marketplace tree is committed at the LRH repo root, and an automated test fails when it drifts from `src/lrh/skills/`'
  - '`claude plugin validate` passes on the repo root (marketplace) and on `plugins/lrh` (plugin); output recorded in the implementation execution record'
  - 'Documentation covers adding the LRH repo as a claude.ai marketplace, Sync automatically, what reaches cloud sessions, and the lrh CLI requirement'
  - 'Manual dogfood: the LRH repo is added as a marketplace on claude.ai, and at least one instruction-centric LRH skill is invoked successfully in a Claude Code cloud session; the execution record names the skill, invocation form, observed outcome, and the answers found for the Open Questions'
  - 'scripts/format --check --diff, scripts/lint, scripts/test, and lrh validate complete successfully'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - src/lrh/cli/main.py
  - tests/skills_exporter_test.py
  - tests/cli_tests/skills_test.py
  - .claude-plugin/marketplace.json
  - plugins/lrh/.claude-plugin/plugin.json
  - 'plugins/lrh/skills/<name>/ for each canonical skill'
  - docs/reference/cli/skills.md
  - docs/how-to/use-lrh-with-agent-assistants.md
  - 'project/executions/WI-SKILLS-CLAUDE-PLUGIN-EXPORT/<implementation-execution-record>.md containing cloud-session dogfood evidence'
---

## Summary

Add `lrh skills export --target claude-plugin` and commit its output, a Claude
plugin marketplace, at the LRH repo root. A claude.ai account that adds the
LRH repo as a marketplace then gets current LRH skills in Claude Code cloud
sessions, updated on every merge to `main`.

## Problem / Context

Claude Code cloud sessions (claude.ai/code) don't read `~/.claude/skills/`,
and they don't install plugins declared in a repo's `.claude/settings.json`.
They load only skills committed to the cloned repo, plus what is enabled on
the user's claude.ai account. A cloud session on a repo without committed
LRH skills therefore has none. Per-repo commits go stale as LRH evolves.

A probe on 2026-10-26 showed that a plugin uploaded to a personal claude.ai
account loads as a real plugin in a Claude Code cloud session.
`${CLAUDE_PLUGIN_ROOT}` resolved to
`/root/.claude/plugins/synced/<account-id>/lrh-cloud-probe`. Anthropic's docs
(plugins/loading.md, "Plugins synced from claude.ai") list only terminal,
Desktop, IDE, and Cowork for this, so the behavior is real but undocumented.
In the same probe:
- claude.ai accepted a plugin skill whose frontmatter has `argument-hint` and
  `disable-model-invocation: true`. Plain claude.ai skill uploads reject these
  keys.
- `$ARGUMENTS` substitution worked.
- The `disable-model-invocation` skill was absent from the model's skill list.

A plugin therefore preserves LRH's manual-only skills, and the account-skill
route cannot. Decision: host the marketplace in the public LRH repo and ship
on every merge to `main`, rather than in a separate repo.

The existing ChatGPT exporter (`src/lrh/skills/exporter.py`, from
WI-SKILLS-CHATGPT-EXPORT) supplies source resolution, path safety, limits,
and atomic publishing. Its renderer strips frontmatter to the portable keys,
which this target must not do.

### Duplication search
- In-repo: No Claude plugin or marketplace export exists. Related:
  `src/lrh/skills/exporter.py` (ChatGPT per-skill ZIPs) and
  `src/lrh/skills/installer.py` (filesystem installs).
- Sibling repos: None identified.
- External libraries: None identified. claude.ai's marketplace sync is the
  hosting mechanism; LRH only packages for it.
- Recommendation: Proceed by extending `exporter.py` with a second target.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` (adopted) frames hosted
  export targets; no Claude plugin target is named.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Add a `claude-plugin` hosted-export target beside `chatgpt`.
- Generate and commit the marketplace tree at the LRH repo root.
- Guard the committed tree against drift with an automated test.
- Document the claude.ai setup, and dogfood in a cloud session.

## Required Changes

1. Add `CLAUDE_PLUGIN = "claude-plugin"` to `ExportTarget`
   (`src/lrh/skills/exporter.py:92`) and to `--target` choices
   (`src/lrh/cli/main.py:310`).
2. Implement a plugin-tree renderer in `exporter.py`:
   - copy `SKILL.md`, `references/`, `scripts/`, and `assets/` unchanged;
   - keep full Claude frontmatter;
   - exclude `agents/` and `_`/dot-prefixed entries;
   - include manual-only skills, which the plugin route preserves;
   - emit `.claude-plugin/marketplace.json` (plugin source `./plugins/lrh`)
     and `plugins/lrh/.claude-plugin/plugin.json` with name and description
     and no `version`.
3. Reuse `exporter.py`'s path-safety checks and atomic publish. Apply the
   claude.ai plugin limits (5,000 files, 200 MB per plugin) instead of the
   ChatGPT limits, and reject any top-level `bin/`.
4. Run the export with `--source current-repo` into the repo root, and commit
   `.claude-plugin/marketplace.json` and `plugins/lrh/`.
5. Add a test that regenerates the tree in memory and fails on any difference
   from the committed tree.
6. Add tests for the renderer, determinism, exclusions, limits, and CLI
   argument and reporting behavior.
7. Update `docs/reference/cli/skills.md` and
   `docs/how-to/use-lrh-with-agent-assistants.md`. Cover:
   - Customize > Plugins > Add marketplace `xenotaur/logical_robotics_harness`;
   - Sync automatically;
   - the cloud-environment setup script needed to install `lrh`.
8. Dogfood: add the marketplace on claude.ai, run an instruction-centric
   skill in a new claude.ai/code session, and answer the Open Questions in
   the execution record.

## Non-Goals

- Do not create or use a separate marketplace repository.
- Do not add a claude.ai account-skill ZIP target; this is the fallback if
  plugin sync to cloud sessions stops working.
- Do not rewrite the `/lrh-*` cross-references in skill bodies.
- Do not remove or change the committed `.claude/skills/` install.
- Do not implement Team/Enterprise organization sync, release channels, or
  plugin versioning.
- Do not automate installing `lrh` in cloud environments; document it only.

## Acceptance Criteria

- `lrh skills export --target claude-plugin --out <dir>` produces the
  marketplace tree with every canonical skill, including manual-only skills.
- Exported frontmatter equals the canonical frontmatter. `agents/`,
  `_shared/`, and `bin/` are absent, and `plugin.json` has no `version`.
- Output is deterministic. Canonical sources and installs are untouched, and
  unsafe paths or over-limit output fail before anything is written.
- The committed tree is at the repo root, and the drift test fails when a
  skill changes without regeneration.
- `claude plugin validate` passes for the marketplace and the plugin.
- Docs cover the claude.ai setup, Sync automatically, cloud-session reach,
  and the `lrh` CLI requirement.
- A cloud-session dogfood succeeds and is recorded, along with the Open
  Question answers.
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `lrh validate` all pass.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills export --target claude-plugin --source current-repo --out <tmpdir>` and diff `<tmpdir>` against the committed `.claude-plugin/` and `plugins/lrh/`
- `claude plugin validate .`
- `claude plugin validate plugins/lrh`

## Open Questions

- Naming: plugin `lrh` makes commands like `/lrh:lrh-land`, while 426
  references in skill bodies say `/lrh-*`. Does the short form still resolve
  in a cloud session? A short `/probe` resolved in Cowork.
- In LRH-repo sessions, the committed `.claude/skills/lrh-*` and the plugin's
  `lrh:*` copies will both load. Is the duplication harmful or just noisy?
- Does a personally added marketplace with Sync automatically re-sync on push
  to the default branch? This is untested; the organization version does.
- Is behavior the same in a cloud session with a repo attached? The probe
  session had no repo.

## Risk Notes

- Plugin sync to cloud sessions is undocumented and could change. If it
  does, fall back to an account-skill target.
- Every merge to `main` ships immediately to every account that added the
  marketplace. A broken skill reaches cloud sessions at once; the drift test
  and `claude plugin validate` are the guard.
- Committed generated copies add review noise to every skill-changing PR,
  as `.claude/skills/` already does.

## Related Workstream and Designs

- Design: `project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md`
- Precedent: `WI-SKILLS-CHATGPT-EXPORT`, `WI-SKILLS-CHATGPT-EXPORT-HARDENING`

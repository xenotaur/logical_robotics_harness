---
resolution: null
blocked_reason: null
blocked: false
id: WI-PLUGIN-BUNDLED-CLI
title: "Bundle the lrh CLI in the Claude plugin under scripts/, called by path through CLAUDE_PLUGIN_ROOT and pre-approved by the skill's allowed-tools"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
  - project/audits/2026-11-06-cloud-session-export-audit.md
  - project/work_items/resolved/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md
depends_on:
  - WI-CLOUD-SESSION-PROBE
  - WI-LRH-CLI-RESOLUTION-REFERENCE
blocked_by: []
expected_actions:
  - edit_file
  - create_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - publish_package
  - skills_install_force
  - install_or_clone_at_runtime
  - weaken_human_gate
acceptance:
  - "WI-CLOUD-SESSION-PROBE has resolved and confirmed that ${CLAUDE_PLUGIN_ROOT} is substituted in a synced plugin's SKILL.md text in cloud sessions and that python3 -I runs a script under the plugin's scripts/; if it did not, this item is abandoned or rescoped instead of implemented"
  - "lrh skills export --target claude-plugin writes a bootstrap (plugins/lrh/scripts/lrh_cli.py, or a name recorded in the execution record) and a copy of the lrh package under plugins/lrh/scripts/, from the same source tree; it writes no top-level bin/, and the exporter's existing refusal of a top-level bin/ (exporter.py:596-597) and its test stay in place"
  - "The launcher path ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py appears in each consuming SKILL.md body (the line WI-LRH-CLI-RESOLUTION-REFERENCE adds), never only in a references/ file, because Claude Code substitutes it only in SKILL.md content and allowed-tools rules; skills run the CLI as python3 -I <that path> <subcommand> ..., so nothing depends on the executable bit, and nothing is installed, cloned, or downloaded at run time"
  - "The bootstrap puts the copied package first on sys.path from inside Python, computed from its own resolved location; it never relies on PYTHONPATH, which -I ignores. Tests show it imports the copy, not another lrh, when the working directory contains its own lrh/ package and when PYTHONPATH points at a different lrh"
  - "If the probe confirmed the grant holds in cloud auto mode, lrh-export-claude's frontmatter declares allowed-tools rules for exactly python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py conversation followed by current-claude-session-id *, export-claude-session * and inspect-export *, written in the quoting form the probe showed matches the SKILL.md command; the skill's --force and model-initiated confirmation gates are unchanged, and the docs say the grant also matches --force, so where no repository ask rule exists the skill's own gate is the only checkpoint; if the probe showed the grant doesn't hold, no allowed-tools rules are added and the docs point teams needing pre-approval to the setup-script route"
  - "The plugin export keeps allowed-tools in the plugin copy of lrh-export-claude (only the portable-bundle target strips it, exporter.py:36-48), shown by a test"
  - "The execution record confirms or revises Decision 2's order (launcher before lrh on PATH), stating the desktop trade-off that the launcher also beats a newer local install, and records the file names and the PyYAML decision (bundle it or rely on the image)"
  - "The packaging test fails when the committed plugin's copied CLI differs from src/lrh, the export stays within claude.ai's 5,000-file and 200 MB limits, and claude plugin validate passes"
  - "A manual cloud-session check runs /lrh:lrh-export-claude's resolution step with no setup script, shows it reaching the bundled launcher through the SKILL.md path line (not falling through to PATH or stop), and records whether the export commands ran without a permission prompt or classifier check"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - tests/skills_exporter_test.py
  - tests/packaging_tests/skills_claude_plugin_sync_test.py
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - plugins/lrh/scripts/lrh_cli.py
  - "plugins/lrh/scripts/<vendored lrh package path>"
  - plugins/lrh/skills/lrh-export-claude/SKILL.md
  - docs/how-to/use-lrh-with-agent-assistants.md
  - docs/reference/cli/skills.md
---

# WI-PLUGIN-BUNDLED-CLI: Bundle the CLI in the Claude plugin, called by path

## Summary

Make the claude-plugin export ship a small Python bootstrap plus a copy of
the `lrh` package, both under `plugins/lrh/scripts/` and taken from the same
commit as the skills. Skills run it by a path written in their SKILL.md,
`python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py …`, and
`lrh-export-claude` pre-approves exactly those commands with its own
`allowed-tools`. Cloud sessions then find a matching CLI with no setup
script, no install, no clone, and no repository settings.

## Problem / Context

The plugin syncs skills but not the CLI they call. A setup-script install
works, but it has to be configured for each environment and can lag the
skills by up to about seven days because setup is cached. A mid-session
clone triggers the classifier (audit §1.1–1.2).

Three documented facts shape the design (audit §1.1–1.2):

- **No top-level `bin/`.** claude.ai and Cowork don't install a plugin
  that has one (`plugins-reference`, Executables row; claude.ai
  `plugins/org-sync`). The repo's exporter already refuses it
  (`src/lrh/skills/exporter.py:596-597`). claude.ai's documented
  alternative is a script in another folder, referenced as
  `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`.
- **Substitution reaches SKILL.md only.** Claude Code substitutes
  `${CLAUDE_PLUGIN_ROOT}` in a plugin skill's SKILL.md content and its
  `allowed-tools` Bash rules, and nowhere else (`skills.md`, Available
  string substitutions). A path in a `references/` file stays literal. A
  2026-10-26 probe saw the variable resolve for a synced plugin in a cloud
  session (`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`).
- **A skill can pre-approve its own script.** `allowed-tools` with the same
  variable "lets a skill run a bundled script without a permission prompt".
  A synced skill's grant "goes through the normal permission flow", and
  auto mode drops only broad allow rules. A repository's exact rule can't
  name the launcher, because its cloud path contains the account ID.

The package is small: 3.3 MB and 269 files, against claude.ai's limits of
200 MB and 5,000 files. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decisions 1–3.
This item is gated on `WI-CLOUD-SESSION-PROBE`, because substitution and the
grant are documented in general but not yet checked for a synced plugin in
a cloud session.

### Duplication search
- In-repo: Related: `src/lrh/skills/exporter.py` (the `claude-plugin` target), which this extends, and its top-level `bin/` refusal, which this keeps.
- Sibling repos: None identified
- External libraries: None identified. PyPI publishing would be the conventional route, but LRH is unpublished (`scripts/publish`).
- Recommendation: Proceed, once the probe confirms substitution and the grant.

### Demand search
- Work items: None found
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decisions 1–3)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Extend the `claude-plugin` export target with a bootstrap and a copied
  package under `scripts/`.
- `allowed-tools` rules in `lrh-export-claude`, gated on the probe.
- Packaging tests and docs.

## Required Changes

1. Extend the `claude-plugin` target in `src/lrh/skills/exporter.py`:
   - write the `lrh` package (minus tests and anything the CLI doesn't
     need) under `plugins/lrh/scripts/`, for example
     `plugins/lrh/scripts/vendor/lrh/`;
   - write a bootstrap, `plugins/lrh/scripts/lrh_cli.py`. It resolves its
     own location, inserts the copied package's root at the front of
     `sys.path`, and runs `lrh.cli.main` (for example through
     `runpy.run_module(..., run_name="__main__")`) with the original
     arguments;
   - keep the existing refusal of a top-level `bin/`.

   Skills run it as `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py`:
   - `-I` keeps the working directory, `PYTHONPATH` and user site-packages
     from supplying a different `lrh`.
   - Running the file through `python3` avoids depending on the executable
     bit, whose survival through claude.ai upload or sync isn't documented.
   - Don't pass the copy through `PYTHONPATH`: `-I` ignores it.
2. Fill the launcher step of the shared resolution reference. The path line
   `WI-LRH-CLI-RESOLUTION-REFERENCE` adds to each consuming SKILL.md body
   names `${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py`. Use the quoting form
   the probe showed matches the `allowed-tools` rule. Never move the path
   into a `references/` file, where it would stay literal and the step
   would always fall through.
3. If the probe confirmed the grant holds in cloud auto mode, add
   `allowed-tools` to `src/lrh/skills/lrh-export-claude/SKILL.md` for
   exactly three commands. Each is
   `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py conversation`
   followed by `current-claude-session-id *`, `export-claude-session *` or
   `inspect-export *`.
   - Keep the skill's `--force` and model-initiated confirmation gates
     unchanged.
   - The rules also match `--force`. A repository ask rule for `--force`
     still prompts, since rules evaluate deny, then ask, then allow.
     Without one, the skill's own gate is the only checkpoint; say so in
     the docs.
   - Confirm with a test that the plugin export keeps `allowed-tools`.
     Only the portable-bundle target strips it (`exporter.py:36-48`).
   - If the probe showed the grant doesn't hold, add no rules, and point
     teams needing pre-approval to the setup-script route.
4. Decide and record:
   - the bootstrap and vendor-folder names;
   - whether to bundle PyYAML, informed by the probe's image findings;
   - whether Decision 2's order (launcher before `lrh` on PATH) stands,
     with the desktop cost that the launcher also beats a newer local
     install.
5. Extend `tests/skills_exporter_test.py` and
   `tests/packaging_tests/skills_claude_plugin_sync_test.py` so they catch
   drift in the copied CLI and check the size and file limits. Keep the
   top-level `bin/` refusal test.
6. Regenerate `plugins/lrh/`. Update the docs (§5 of
   `docs/how-to/use-lrh-with-agent-assistants.md`, and
   `docs/reference/cli/skills.md`):
   - the bundled launcher and how skills reach it;
   - the `allowed-tools` grant and its `--force` caveat, or its absence;
   - the setup script as the other route;
   - that repository allow rules don't cover the launcher's
     account-specific path.

## Non-Goals

- Do not publish LRH to PyPI.
- Do not install, clone, or download anything at run time.
- Do not ship a top-level `bin/`, or put the launcher on PATH.
- Do not grant broad rules such as `Bash(python3 *)`. Auto mode drops them,
  and they would approve any Python.
- Do not weaken the skill's `--force` or model-initiated confirmation
  gates.
- Do not change the Codex (`.agents`) or Antigravity (`.gemini`) skill
  targets.

## Acceptance Criteria

- The plugin ships a working bootstrap under `scripts/` and no top-level
  `bin/`, and its copied CLI matches `src/lrh`, enforced by test.
- The launcher path lives in each consuming SKILL.md body, and the
  resolution step reaches the launcher in the plugin and falls through
  outside it.
- The bootstrap imports the copy, not another `lrh`, in isolated mode, as
  shown by tests with a shadowing working directory and `PYTHONPATH`.
- `lrh-export-claude` carries exactly the three `allowed-tools` rules,
  only if the probe confirmed them, and its confirmation gates are
  unchanged.
- The export stays within claude.ai's limits, and `claude plugin validate`
  passes.
- A cloud session reaches the bundled launcher through the real resolution
  step, with no setup script. The record says whether it prompted.
- `lrh validate`, `scripts/test`, `scripts/lint` and
  `scripts/format --check --diff` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills export --target claude-plugin --source current-repo --out .`
- `claude plugin validate plugins/lrh`

## Risk Notes

- Every CLI change now changes the committed plugin tree, which makes the
  diffs noisier. The sync test keeps them honest.
- The `allowed-tools` grant lasts only for the turn that invokes the skill.
  A later turn, such as a closeout offer to refresh, runs the commands
  again through `lrh-export-claude`, so it gets the grant again.
- An organization that sets `allowManagedPermissionRulesOnly` makes Claude
  Code ignore `allowed-tools` in project and personal skills, and in synced
  skills (`skills.md`). Check whether it covers plugin skills too. Those
  users get prompts either way.
- The repo has no `python3 -I` precedent for the bootstrap. `-I` drops the
  script's directory, the working directory, `PYTHONPATH` and user
  site-packages from `sys.path`, which is why the bootstrap must add the
  copy's root itself. The tests above guard this.
- Directory submission, which LRH doesn't use, would hold plugins over 512
  files or with any file over 256 KiB for review. The bundled plugin would
  be about 253 files, with no file over 256 KiB. Re-check if LRH is ever
  submitted.

---
resolution: null
blocked_reason: null
blocked: false
id: WI-PLUGIN-BUNDLED-CLI
title: "Bundle the lrh CLI in the Claude plugin under scripts/, called by path through CLAUDE_PLUGIN_ROOT, from the same commit as the skills"
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
acceptance:
  - "WI-CLOUD-SESSION-PROBE has resolved and confirmed that ${CLAUDE_PLUGIN_ROOT} is substituted in a synced plugin's skill text in cloud sessions and that python3 -I runs a script under the plugin's scripts/; if it did not, this item is abandoned or rescoped instead of implemented"
  - "lrh skills export --target claude-plugin writes a bootstrap (plugins/lrh/scripts/lrh_cli.py, or a name recorded in the execution record) and a copy of the lrh package under plugins/lrh/scripts/, from the same source tree; it writes no top-level bin/, and the exporter's existing refusal of a top-level bin/ (exporter.py:596-597) and its test stay in place"
  - "Skill text runs the bundled CLI as python3 -I \"${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py\" <subcommand> ..., so it doesn't depend on the file's executable bit; nothing is installed, cloned, or downloaded at run time"
  - "The bootstrap puts the copied package first on sys.path from inside Python, computed from its own resolved location; it never relies on PYTHONPATH, which -I ignores. Tests show it imports the copy, not another lrh, when the working directory contains its own lrh/ package and when PYTHONPATH points at a different lrh"
  - "The shared CLI-resolution reference from WI-LRH-CLI-RESOLUTION-REFERENCE fills its launcher slot with the bootstrap path, and the execution record confirms or revises Decision 2's order (launcher before lrh on PATH), stating the desktop trade-off that the launcher also beats a newer local install"
  - "Docs state that the plugin launcher isn't covered by the published allow rules, because its path is absolute and account-specific in cloud, and point teams that need pre-approved exports to the setup-script route; any allow rule for the launcher path follows the probe's finding and the proposal's open question, not a guess"
  - "The file names and the PyYAML decision (bundle it or rely on the image) are recorded in the implementation's execution record"
  - "The packaging test fails when the committed plugin's copied CLI differs from src/lrh, the export stays within claude.ai's 5,000-file and 200 MB limits, and claude plugin validate passes"
  - "A manual cloud-session check runs python3 -I \"${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py\" conversation --help from a plugin skill with no setup script, recorded in the execution record"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - tests/skills_exporter_test.py
  - tests/packaging_tests/skills_claude_plugin_sync_test.py
  - plugins/lrh/scripts/lrh_cli.py
  - "plugins/lrh/scripts/<vendored lrh package path>"
  - docs/how-to/use-lrh-with-agent-assistants.md
  - docs/reference/cli/skills.md
---

# WI-PLUGIN-BUNDLED-CLI: Bundle the CLI in the Claude plugin, called by path

## Summary

Make the claude-plugin export ship a small Python bootstrap plus a copy of
the `lrh` package, both under `plugins/lrh/scripts/` and taken from the same
commit as the skills. Skills run it by path,
`python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py" …`, so cloud sessions
find a matching CLI with no setup script, no install, and no clone.

## Problem / Context

The plugin syncs skills but not the CLI they call. A setup-script install
works, but it has to be configured for each environment and can lag the
skills by up to about seven days because setup is cached. A mid-session
clone triggers the classifier (audit §1.1–1.2).

A plugin's top-level `bin/` is not an option. Claude Code would put it on
PATH, but claude.ai and Cowork don't install a plugin that has one
(`plugins-reference`, Executables row; claude.ai `plugins/org-sync`). The
repo's exporter already refuses it (`src/lrh/skills/exporter.py:596-597`).
claude.ai's documented alternative is a script in another folder, referenced
as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`. Claude Code substitutes
`${CLAUDE_PLUGIN_ROOT}` inline in skill content, though not in the Bash
tool's environment. A 2026-10-26 probe saw it resolve for a synced plugin
in a cloud session (`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`).

The package is small: 3.3 MB and 269 files, against claude.ai's limits of
200 MB and 5,000 files. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 1. This
item is gated on `WI-CLOUD-SESSION-PROBE`, because path substitution for a
synced plugin's skills isn't documented for cloud sessions.

### Duplication search
- In-repo: Related: `src/lrh/skills/exporter.py` (the `claude-plugin` target), which this extends, and its top-level `bin/` refusal, which this keeps.
- Sibling repos: None identified
- External libraries: None identified. PyPI publishing would be the conventional route, but LRH is unpublished (`scripts/publish`).
- Recommendation: Proceed, once the probe confirms path substitution.

### Demand search
- Work items: None found
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 1)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Extend the `claude-plugin` export target with a bootstrap and a copied
  package under `scripts/`.
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

   Skills run it as `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py"`:
   - `-I` keeps the working directory, `PYTHONPATH` and user site-packages
     from supplying a different `lrh`.
   - Running the file through `python3` avoids depending on the executable
     bit, whose survival through claude.ai upload or sync isn't documented.
   - Don't pass the copy through `PYTHONPATH`: `-I` ignores it.
2. Decide and record:
   - the bootstrap and vendor-folder names;
   - whether to bundle PyYAML, informed by the probe's image findings.
3. Extend `tests/skills_exporter_test.py` and
   `tests/packaging_tests/skills_claude_plugin_sync_test.py` so they catch
   drift in the copied CLI and check the size and file limits. Keep the
   top-level `bin/` refusal test.
4. Regenerate `plugins/lrh/`. Update the docs (§5 of
   `docs/how-to/use-lrh-with-agent-assistants.md`, and
   `docs/reference/cli/skills.md`):
   - describe the bundled launcher;
   - keep the setup script as the other route;
   - say that the published allow rules don't cover the launcher, because
     its path is absolute and contains the account ID in cloud. Teams that
     need pre-approved exports use the setup-script route.
5. Update the shared CLI-resolution reference (created by
   `WI-LRH-CLI-RESOLUTION-REFERENCE`, hence the dependency):
   - Its launcher slot becomes: run the bootstrap when
     `"${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py"` exists. In a skill copy
     outside the plugin the placeholder isn't substituted, the unset
     variable expands to an empty string, and the test fails and falls
     through.
   - Confirm or revise Decision 2's order, which puts the launcher before
     `lrh` on PATH so a lagging setup-script install can't shadow the
     bundle in cloud.
   - Record the desktop cost: with the plugin enabled, the launcher also
     beats a newer local install.
6. If the probe showed that a launcher-path allow rule can match, with a
   wildcard only for the account segment, record the result. Leave
   publishing such a rule to the proposal's open question: claude.ai's
   skills guide warns that a wildcard before the path approves more than
   intended.

## Non-Goals

- Do not publish LRH to PyPI.
- Do not install, clone, or download anything at run time.
- Do not ship a top-level `bin/`, or put the launcher on PATH.
- Do not change the Codex (`.agents`) or Antigravity (`.gemini`) skill
  targets.

## Acceptance Criteria

- The plugin ships a working bootstrap under `scripts/` and no top-level
  `bin/`, and its copied CLI matches `src/lrh`, enforced by test.
- The bootstrap imports the copy, not another `lrh`, in isolated mode, as
  shown by tests with a shadowing working directory and `PYTHONPATH`.
- The shared resolution reference fills its launcher slot, and falls
  through when the placeholder isn't substituted.
- The docs state that the allow rules don't cover the launcher path.
- The export stays within claude.ai's limits, and `claude plugin validate`
  passes.
- A cloud session runs the bundled `conversation --help` from a plugin
  skill with no setup script.
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
- The launcher route doesn't remove permission prompts in cloud. Its path
  can't be named by a portable exact rule, so the export still goes to a
  prompt or the auto-mode classifier unless the setup-script route and its
  allow rules are used.
- The repo has no `python3 -I` precedent for the bootstrap. `-I` drops the
  script's directory, the working directory, `PYTHONPATH` and user
  site-packages from `sys.path`, which is why the bootstrap must add the
  copy's root itself. The tests above guard this.
- Directory submission, which LRH doesn't use, would hold plugins over 512
  files or with any file over 256 KiB for review. The bundled plugin would
  be about 253 files, with no file over 256 KiB. Re-check if LRH is ever
  submitted.

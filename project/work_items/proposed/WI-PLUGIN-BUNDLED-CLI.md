---
resolution: null
blocked_reason: null
blocked: false
id: WI-PLUGIN-BUNDLED-CLI
title: "Bundle the lrh CLI in the Claude plugin with a bin/ launcher from the same commit as the skills"
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
  - "WI-CLOUD-SESSION-PROBE has resolved and confirmed that a synced plugin's bin/ is on PATH in cloud sessions; if it did not, this item is abandoned or rescoped instead of implemented"
  - "lrh skills export --target claude-plugin writes plugins/lrh/bin/<launcher> and a copy of the lrh package from the same source tree, and the launcher runs that copy with python3 without installing, cloning, or downloading anything at run time"
  - "The launcher's name and the PyYAML decision (bundle it or rely on the image) are recorded in the implementation's execution record, with the PATH-shadowing trade-off for desktop users stated"
  - "The shared CLI-resolution reference from WI-LRH-CLI-RESOLUTION-REFERENCE names the launcher in its resolution order"
  - "The packaging test fails when the committed plugin's copied CLI differs from src/lrh, the export stays within claude.ai's 5,000-file and 200 MB limits, and claude plugin validate passes"
  - "A manual cloud-session check runs '<launcher> conversation --help' successfully with no setup script, recorded in the execution record"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - tests/skills_exporter_test.py
  - tests/packaging_tests/skills_claude_plugin_sync_test.py
  - "plugins/lrh/bin/<launcher>"
  - "plugins/lrh/<vendored lrh package path>"
  - docs/how-to/use-lrh-with-agent-assistants.md
  - docs/reference/cli/skills.md
---

# WI-PLUGIN-BUNDLED-CLI: Bundle the CLI in the Claude plugin

## Summary

Make the claude-plugin export ship a `bin/` launcher plus a copy of the
`lrh` package from the same commit as the skills. In cloud sessions the
skills then find a matching CLI with no setup script, no install, and no
clone.

## Problem / Context

The plugin syncs skills but not the CLI they call. A setup-script install
works, but it has to be configured for each environment and can lag the
skills by up to about seven days because setup is cached. A mid-session
clone triggers the classifier (audit §1.1–1.2). The plugin reference
documents `bin/` as on the Bash tool's PATH while the plugin is enabled.
The package is small: 3.3 MB and 269 files, against claude.ai's limits of
200 MB and 5,000 files. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 1. This
item is gated on `WI-CLOUD-SESSION-PROBE`, because `bin/` for a synced
plugin in cloud sessions is undocumented.

### Duplication search
- In-repo: Related: `src/lrh/skills/exporter.py` (the `claude-plugin` target), which this extends.
- Sibling repos: None identified
- External libraries: None identified. PyPI publishing would be the conventional route, but LRH is unpublished (`scripts/publish`).
- Recommendation: Proceed, once the probe confirms `bin/`.

### Demand search
- Work items: None found
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 1)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Extend the `claude-plugin` export target with a launcher and a copied
  package.
- Packaging tests and docs.

## Required Changes

1. Extend the `claude-plugin` target in `src/lrh/skills/exporter.py`:
   - write the `lrh` package (minus tests and anything the CLI doesn't need)
     under the plugin root;
   - write an executable launcher in `plugins/lrh/bin/` that runs
     `python3 -I -m lrh.cli.main "$@"` with that copy on `PYTHONPATH`,
     resolved relative to the launcher's own location.
2. Decide and record:
   - the launcher name, `lrh` versus a distinct name, given that `bin/`
     could shadow a local `lrh`;
   - whether to bundle PyYAML, informed by the probe's image findings.
3. Extend `tests/skills_exporter_test.py` and
   `tests/packaging_tests/skills_claude_plugin_sync_test.py` so they catch
   drift in the copied CLI and check the size and file limits.
4. Regenerate `plugins/lrh/`. Update the docs (§5 of
   `docs/how-to/use-lrh-with-agent-assistants.md` and
   `docs/reference/cli/skills.md`) to describe the launcher and to keep the
   setup script as the fallback.
5. Update the shared CLI-resolution reference so its order names the
   launcher.

## Non-Goals

- Do not publish LRH to PyPI.
- Do not install, clone, or download anything at run time.
- Do not change the Codex (`.agents`) or Antigravity (`.gemini`) skill
  targets.

## Acceptance Criteria

- The plugin ships a working launcher, and its copied CLI matches `src/lrh`,
  enforced by test.
- The export stays within claude.ai's limits, and `claude plugin validate`
  passes.
- A cloud session runs `<launcher> conversation --help` with no setup
  script.
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
- A launcher named `lrh` could shadow an editable install in desktop
  sessions and run different code than the user expects.
- The repo has no `python3 -I` precedent for the launcher. Check that it
  still works when the session's working directory contains its own `lrh/`
  package.

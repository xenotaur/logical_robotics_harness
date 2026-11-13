---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CLI-RESOLUTION-REFERENCE
title: "Replace the export skills' copied 'Running lrh' fallback with one shared CLI-resolution reference that stops with an exact remedy"
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
  - docs/how-to/use-lrh-with-agent-assistants.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
  - skills_install_force
acceptance:
  - "A single shared reference, with a master copy under src/lrh/skills/_shared/ and synced copies in each consuming skill's references/, defines the lrh resolution order: PYTHONPATH=src python3 -m lrh.cli.main only when the working directory is an LRH checkout; then the plugin's bundled launcher, run as python3 -I \"${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py\" when that file exists, as a named placeholder until WI-PLUGIN-BUNDLED-CLI ships (in a skill copy outside the plugin the placeholder isn't substituted, so the file test fails and falls through); then lrh on PATH; otherwise stop. It states why the launcher precedes PATH (a setup-script install can lag the plugin by about seven days) and the desktop trade-off (the launcher also beats a newer local install)"
  - "The stop path prints the exact setup-script install line and the docs anchor, and never discovers, clones or installs LRH on its own"
  - "Any one-time bootstrap clone is described only as a separate step the user confirms, named for what it does"
  - "lrh-export-claude, lrh-codex-export and lrh-antigravity-export replace their inline 'Running lrh' sections with a pointer to the shared reference"
  - "docs/how-to/use-lrh-with-agent-assistants.md states a pinned-ref setup-script install, and that the cloud environment's setup snapshot can lag the auto-synced plugin by up to about seven days"
  - "Rendered copies (.claude/skills, .agents/skills, .gemini/plugins/lrh/skills, plugins/lrh/skills) are regenerated without --force; the plugin sync test, lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/_shared/lrh-cli-resolution.md
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
  - "src/lrh/skills/<each consuming skill>/references/lrh-cli-resolution.md"
  - docs/how-to/use-lrh-with-agent-assistants.md
  - plugins/lrh/skills/
---

# WI-LRH-CLI-RESOLUTION-REFERENCE: Shared CLI-resolution reference with a stop-with-remedy path

## Summary

Replace the three copied "Running `lrh`" sections in the export skills with
one shared reference. It resolves `lrh` in a fixed order. When nothing is
found, it stops and gives the exact install line instead of letting the
agent improvise a discovery and clone.

## Problem / Context

`lrh-export-claude`, `lrh-codex-export` and `lrh-antigravity-export` each
say: if `lrh` isn't on PATH, run `PYTHONPATH=src python3 -m lrh.cli.main`
"from an LRH checkout". In a client repository's cloud session there's no
checkout, so in the 2026-11-06 taurworks session the agent went looking for
the LRH repo and cloned it. Auto mode's classifier denied that as "Code
from External". `PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 2 chooses
stop-with-remedy instead. The cloud setup-script docs also omit the
snapshot-cache drift (audit §1.1).

### Duplication search
- In-repo: Related: the three inline "Running `lrh`" sections, which this item replaces, and `src/lrh/skills/_shared/`, which holds the synced-copy pattern this reuses.
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found. Adjacent: `WI-EXPORT-SKILL-FAMILY-RENAME` renames `lrh-codex-export` and `lrh-antigravity-export`.
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 2)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- One shared CLI-resolution reference, consumed by the three export skills.
- Setup-script documentation for cloud environments.

## Required Changes

1. Add `src/lrh/skills/_shared/lrh-cli-resolution.md`, with the
   synced-copy header used by `prior-art-check.md`. It defines the
   resolution order (Decision 2: LRH checkout, then the bundled-launcher
   slot at `${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py`, then `lrh` on PATH)
   with its rationale, and the stop message, which includes
   `pip install "git+https://github.com/xenotaur/logical_robotics_harness.git@<ref>"`
   and the docs anchor.
2. Copy it into each consuming skill's `references/`, and replace the inline
   "Running `lrh`" section in the three export skills with a short pointer.
   Keep the existing editable-install caveat (`pip show lrh`) in the shared
   copy.
3. Update `docs/how-to/use-lrh-with-agent-assistants.md` §5's setup-script
   section: pin a ref, and state the roughly seven-day snapshot lag.
4. Regenerate the rendered skill copies and the plugin tree.

## Non-Goals

- Do not build the bundled launcher. That is `WI-PLUGIN-BUNDLED-CLI`; this
  item only names the slot in the order.
- Do not change any CLI behavior.
- Do not touch skills other than the three export skills. Wider adoption of
  the shared reference is a follow-up.

## Acceptance Criteria

- The shared reference exists, defines the order, and its stop path never
  installs or clones.
- The three export skills point to it, and none has an inline fallback left.
- The docs state the pinned install and the snapshot lag.
- Rendered copies are in sync; `lrh validate`, `scripts/test`, `scripts/lint`
  and `scripts/format --check --diff` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills check --target claude --local`

## Risk Notes

- If `WI-EXPORT-SKILL-FAMILY-RENAME` lands first, target the renamed skill
  directories.
- Synced copies drift if edited separately. Follow the `_shared/` header
  convention.

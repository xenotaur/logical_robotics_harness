---
execution_id: "2026_09_24_21_02_46_LRH_CONSOLE_LOCAL_DOGFOOD"
prompt_id: "PROMPT(AD_HOC:LRH_CONSOLE_LOCAL_DOGFOOD)[2026-09-24T20:56:54+00:00]"
work_item: "AD_HOC"
status: "in_progress"
rerun_of: null
pr: "https://github.com/xenotaur/logical_robotics_harness/pull/721"
commit: null
created_at: "2026-09-24T21:02:46+00:00"
agent: "codex_cloud"
instruction_source: "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
session_transcript: "pending"
---

# Summary

Use `/lrh-proposal` to capture the LRH Console design proposal, local L0-L4 roadmap, and later remote/mobile sequence in the user's requested single review PR.
This records creation of a planning artifact, not execution of its future scope.

# Result

Created `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md` as part of
[PR #721](https://github.com/xenotaur/logical_robotics_harness/pull/721).
The package contains one proposal, one workstream, and two initial work items;
all remain proposed. The prior approved design and the user's explicit request
for one combined PR supplied the scope and authorization for the capture.

The package preserves the selected Python backend / shared web UI / Tauri shell
boundary, default content window, native menus, on-demand Settings/Details,
owned-process lifecycle, real-project dependency graph objective, and evidence-gated
local-first roadmap. IDs, `owner: anthony`, and initial workstream `stage: planned`
were inferred from the discussion and repository conventions and are identified
as reviewable choices. Current focus and canonical design were not advanced.

Prior-art checks reused Serve, Meta, typed state, and existing workbench contracts;
related visual-language/triage/blocker demands are linked, not closed. Open
PR #719 was examined and concerns adjacent local-agent experiments rather than a
duplicate desktop/map slice. LCATS and the private prototype source were not
inspected; their eventual reuse/consumer checks remain explicit follow-up.

# Validation

- Source baseline: `8603b6514329ea242294da420aa448d2fc959fd1`.
- `scripts/develop` installed the editable development toolchain in this previously
  uninitialized environment. `scripts/version tools` then reported repository-pinned
  Black 26.3.1, Ruff 0.15.12, and the LRH CLI.
- Pre-mint duplicate checks used `lrh.prompt_workflow_slug.check_slug` with its
  actual local, pull-ref, and inherited-record logic. The missing `gh` executable
  was replaced only as PR-list transport with a fully paginated GitHub REST list;
  each of the four slugs scanned all 21 open PRs and found no prior record.
- `lrh prompt label` minted each creation prompt; secondary exact prompt-ID checks
  returned no matching execution records. Exact-mode exit 1 means no record,
  distinct from slug-mode exit 1's blocking meaning.
- Baseline and planning-artifact `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items validate --format json`: 78 baseline warnings, the same 78 after
  this package, and no new diagnostics.
- `lrh work-items readiness <ID> --format json` for both new leaves: prompt-ready
  with no warnings. This is content readiness, not activation or a waiver of the
  desktop item's explicit prerequisite.
- Verified quoted frontmatter, proposed/unresolved semantics, existing design
  reference paths, reciprocal workstream links, dependency order, and
  `git diff --cached --check`.
- `scripts/lint`: Ruff passed; Black failed to start its multiprocessing manager
  because the environment disallows its socket. `BLACK_NUM_WORKERS=1` did not
  resolve that environment limitation. No full lint/formatter pass is claimed.
- Runtime tests were not run: this PR adds planning documents only. Future Mac
  lifecycle, graph, and dogfood evidence described by the leaves is not claimed.

# Follow-up

Review the package together. Address review feedback with the LRH review workflow;
merge requires its own explicit authorization. After merge, `/lrh-closeout` should
land these AD_HOC creation records while leaving the implementation work items
proposed until their separate implementation lifecycle completes.

Replace `session_transcript: pending` with a durable backend session pointer when
available; no raw transcript or local absolute path is committed. Related demand
items may be linked further or closed only after separate review and actual
satisfying evidence. Add L1 and later leaves after their preceding usage gates,
not as speculative implementation claims in this planning closeout.

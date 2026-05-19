# Planning Tree / Workstream Implementation Audit

Prompt ID: `PROMPT(AD_HOC:PLANNING_TREE_IMPLEMENTATION_AUDIT)[2026-05-16T18:00:00-04:00]`

## 1. Summary

This audit inspected the repository's current planning-tree, workstream, execution-readiness, snapshot, and human-assisted run-packet surfaces against the seven capabilities requested in the prompt.

Headline result: the old Option C prompt package is now **partially obsolete**: obsolete as an implementation bundle, but still useful as historical context. The core workstream/planning-tree slice has already moved beyond design-only state into typed models, loading, validation, indexing, snapshot visibility, readiness validation, and dry-run run-packet generation. It should not be rerun unchanged; only wording that still corresponds to real gaps should be reused.

Highest-priority remaining gap: do **not** rerun planning-tree basics. The next implementation prompt should target the currently documented next package: durable manual run state / run tracking, while preserving safe-default, non-agentic behavior. If a narrower planning-tree follow-up is desired first, it should only clarify public naming/API around `PlanningTreeIndex` versus the older `PlanningRecord` / `PlanningIndex` terminology.

## 2. Capability matrix

| Capability | Status | Files inspected | Evidence | Remaining gap | Recommended next step |
| --- | --- | --- | --- | --- | --- |
| PlanningRecord / PlanningIndex or equivalent | implemented | `src/lrh/control/models.py`; `src/lrh/control/planning_tree.py`; `tests/workstreams_tests/planning_tree_test.py`; `project/workstreams/README.md` | Runtime `Workstream` and `WorkItem` models carry planning metadata; `PlanningArtifact`, `PlanningRelationship`, and `PlanningTreeIndex` provide the equivalent indexed representation and query methods. Tests exercise loading and index behavior. | The exact names `PlanningRecord` and `PlanningIndex` are not present; project root is represented as context, not a first-class indexed artifact. | No broad implementation prompt. If needed, add a small naming/API clarification prompt for public terminology only. |
| Workstream + work item relationship indexing | implemented | `src/lrh/control/planning_tree.py`; `src/lrh/control/loader.py`; `tests/workstreams_tests/planning_tree_test.py`; `project/workstreams/README.md` | The index collects workstream `children`, workstream `work_items`, and work-item `parent_id` relationships, then exposes `children_of`, `parents_of`, roots, active leaves, and status counts. | Current index covers workstreams and work items; it does not model future run artifacts or arbitrary planning-node directories. | Treat complete for the control-plane MVP; extend only when durable run state requires new relationship types. |
| `parent_id` / `children` validation | implemented | `src/lrh/control/validator.py`; `src/lrh/control/planning_tree.py`; `tests/workstreams_tests/planning_tree_test.py`; `tests/workstreams_tests/validator_test.py` | Workstream schema validates `parent_id` as an optional string and `children` as a list field. Relationship validation reports unknown parents, unknown children, self-parenting, multiple parents, and conflicting declarations. | Validation is metadata-driven and does not introduce explicit top-level markers for active workstream roots. | No duplicate prompt. Add top-level/root intent semantics only if future product requirements need it. |
| Cycle detection | implemented | `src/lrh/control/planning_tree.py`; `tests/workstreams_tests/planning_tree_test.py` | `_find_workstream_cycles` performs DFS over workstream-to-workstream child edges and emits `PLANNING_NODE_CYCLE` diagnostics. Tests assert cycle errors. | Cycle detection is intentionally scoped to workstream planning nodes; work items cannot currently parent other work items. | Treat complete for current schema. Revisit only if recursive work-item or arbitrary-node nesting is introduced. |
| Snapshot visibility for workstreams/planning relationships | implemented | `src/lrh/assist/snapshot_cli.py`; `tests/assist_tests/snapshot_cli_test.py`; `project/workstreams/README.md`; `project/focus/current_focus.md` | `lrh snapshot project` workstream summaries build the planning index, show status counts, active workstreams, relationship counts, roots, active leaves, direct workstream-to-work-item mappings, and planning diagnostics. | Snapshot is observability-only and not a scheduler. It does not yet include durable run state because that layer is not implemented. | Keep as-is for planning tree; extend snapshot later with manual run state after the durable run-state package lands. |
| Execution-ready work item validation | implemented | `src/lrh/control/execution_readiness.py`; `src/lrh/control/validator.py`; `src/lrh/control/models.py`; `tests/control_tests/execution_readiness_test.py`; `tests/work_items_tests/validate_test.py` | `ExecutionReadiness` interprets opt-in readiness metadata; `validate_frontmatter` enforces `execution_ready`, required metadata, enums, list/boolean/integer types, non-empty lists, and positive round counts. Work items store the typed readiness object. | Readiness validates metadata and packet eligibility; it does not execute the item, create branches, or approve work automatically. | No readiness reimplementation. Use readiness as an input to durable manual run-state work. |
| Human-assisted run-packet generation | implemented | `src/lrh/assist/run_packet.py`; `src/lrh/assist/request_catalog.py`; `src/lrh/assist/request_cli.py`; `src/lrh/serve.py`; `tests/assist_tests/run_packet_test.py`; `tests/assist_tests/request_cli_test.py`; `tests/cli_tests/serve_test.py` | `run-packet-from-work-item` is cataloged as a structured request. The renderer validates strict readiness, emits a dry-run packet for ready work items, and returns diagnostics for non-ready work items. The request CLI can write or print packets; `lrh serve` exposes safe-default previews. | The packet is a human-reviewable artifact, not a run command. There is no durable run record or autonomous dispatch. | Do not add `lrh run` here. Next prompt should create durable manual run-state artifacts if approved. |

## 3. Detailed findings

### 3.1 PlanningRecord / PlanningIndex or equivalent

Files/code/docs inspected:

- `src/lrh/control/models.py`
- `src/lrh/control/planning_tree.py`
- `tests/workstreams_tests/planning_tree_test.py`
- `project/workstreams/README.md`
- `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`
- `project/design/workstream_schema_mvp.md`
- `project/design/proposals/adopted/safe-default-agentic-extra-packaging/00_proposal.md`

What exists now:

- Runtime models include `WorkItem.parent_id`, `Workstream.parent_id`, `Workstream.children`, and `Workstream.work_items`.
- `PlanningArtifact` is the current record-equivalent: an indexed, durable-ID-addressable planning artifact carrying kind, path, status, title, related references, blockers/dependencies, evidence, and active-leaf state.
- `PlanningTreeIndex` is the current index-equivalent: it stores artifacts, relationships, parent/child maps, diagnostics, cycles, and query helpers.

What is missing:

- There is no exact class named `PlanningRecord` or `PlanningIndex`.
- The index does not represent the project root as a first-class artifact.
- The current schema does not expose arbitrary planning-node documents outside workstreams and work items.

Core/non-agentic or agentic:

- Core/non-agentic. It is deterministic control-plane indexing.

Alignment:

- Aligns with the adopted workstreams/planning-tree proposal because workstreams are planning nodes, work items are leaves, metadata is authoritative, and automation is deferred.
- Aligns with safe-default packaging because the code has no autonomous execution dependency.

Classification: **implemented**, with naming and scope caveats.

### 3.2 Workstream + work item relationship indexing

Files/code/docs inspected:

- `src/lrh/control/planning_tree.py`
- `src/lrh/control/loader.py`
- `src/lrh/control/models.py`
- `tests/workstreams_tests/planning_tree_test.py`
- `project/workstreams/README.md`

What exists now:

- `build_planning_tree` and `build_planning_tree_from_artifacts` index typed workstreams and work items.
- Relationships are collected from workstream `parent_id`, workstream `children`, workstream `work_items`, and work-item `parent_id`.
- The index exposes children, parents, roots, active leaves, status counts, diagnostics, unresolved references, and relationship tuples.

What is missing:

- No runtime run artifacts are indexed yet.
- Directory nesting is intentionally ignored as relationship semantics.

Core/non-agentic or agentic:

- Core/non-agentic.

Alignment:

- Aligns with adopted proposal and schema MVP: metadata is authoritative; paths are human navigation only.
- Aligns with safe-default packaging because indexing is read-only/control-plane behavior.

Classification: **implemented**.

### 3.3 `parent_id` / `children` validation

Files/code/docs inspected:

- `src/lrh/control/validator.py`
- `src/lrh/control/planning_tree.py`
- `tests/workstreams_tests/planning_tree_test.py`
- `tests/workstreams_tests/validator_test.py`
- `project/design/workstream_schema_mvp.md`

What exists now:

- Workstream schema validation checks required fields, enum values, list fields, optional `parent_id` type, ID convention, and bucket/status drift.
- Planning-tree validation converts parsed artifacts to typed models and forwards planning diagnostics into `lrh validate` output.
- Relationship diagnostics cover unknown `parent_id`, unknown `children`, unknown `work_items`, self-parenting, invalid `work_items` child kind, multiple inferred parents, and mismatched declared/inferred parents.

What is missing:

- No explicit schema-level field for intentionally top-level active workstreams.
- Work-item `related_workstreams` remains a relationship/reference field, but the planning tree parent relation is `parent_id` or a parent workstream's `children`/`work_items` declaration.

Core/non-agentic or agentic:

- Core/non-agentic validation.

Alignment:

- Aligns with the adopted proposal's expected future validation list and keeps automation deferred.
- Safe-default boundary is preserved.

Classification: **implemented**.

### 3.4 Cycle detection

Files/code/docs inspected:

- `src/lrh/control/planning_tree.py`
- `tests/workstreams_tests/planning_tree_test.py`

What exists now:

- The planning index detects cycles among workstream planning nodes with DFS and emits `PLANNING_NODE_CYCLE` diagnostics.
- Validation surfaces those diagnostics as errors.
- Tests cover a workstream cycle.

What is missing:

- Cycle detection is limited to workstream-to-workstream relationships because the current model does not allow work items to be parents.
- If LRH later introduces arbitrary recursive node types, this algorithm may need to generalize beyond `Workstream` artifacts.

Core/non-agentic or agentic:

- Core/non-agentic.

Alignment:

- Aligns with the adopted proposal's “no cycles” expectation and does not cross into agentic behavior.

Classification: **implemented**.

### 3.5 Snapshot visibility for workstreams/planning relationships

Files/code/docs inspected:

- `src/lrh/assist/snapshot_cli.py`
- `tests/assist_tests/snapshot_cli_test.py`
- `project/workstreams/README.md`
- `project/focus/current_focus.md`

What exists now:

- Snapshot workstream summaries load workstreams permissively, load work items for snapshot context, build the planning index, and render status counts and active workstream details.
- Snapshot output includes a planning relationship index summary with observability-only mode, relationship count, root workstreams, status counts, active leaves with readiness hints, direct workstream-to-work-item mappings, and diagnostic counts.
- Snapshot warnings include planning diagnostics and bucket/status drift.

What is missing:

- Snapshot does not include future durable manual run-state artifacts.
- Snapshot remains read-only and does not schedule or execute work.

Core/non-agentic or agentic:

- Human-assist/read-only, non-agentic.

Alignment:

- Aligns with the adopted proposal's snapshot support item and safe-default packaging. The output explicitly states it has no execution or scheduling authority.

Classification: **implemented**.

### 3.6 Execution-ready work item validation

Files/code/docs inspected:

- `src/lrh/control/execution_readiness.py`
- `src/lrh/control/models.py`
- `src/lrh/control/validator.py`
- `tests/control_tests/execution_readiness_test.py`
- `tests/work_items_tests/validate_test.py`
- `project/design/execution_framework_mvp.md`
- `project/focus/current_focus.md`

What exists now:

- `ExecutionReadiness` is a typed safe-default interpretation of opt-in readiness metadata.
- `validate_frontmatter` supports normal validation for opted-in work items and strict `require_ready=True` validation for selected executable leaves.
- Required ready fields include `execution_ready`, `autonomy_level`, `operation_risk`, `allowed_paths`, `validation_commands`, and `required_evidence`.
- Validation checks enums, booleans, lists, integers, non-empty required lists, and positive review/CI round counts.
- Work-item models store `execution_readiness` when frontmatter opts in.

What is missing:

- Readiness validation does not start a run, mutate a branch, open a PR, or approve anything.
- Human approval and closeout are metadata gates; durable run-state tracking remains future work.

Core/non-agentic or agentic:

- Core/control-plane plus human-assist. Non-agentic.

Alignment:

- Aligns with adopted planning-tree semantics: execution-ready means sufficiently specified for human or supervised execution, not autonomous execution.
- Aligns with safe-default packaging because the default behavior validates metadata only.

Classification: **implemented**.

### 3.7 Human-assisted run-packet generation

Files/code/docs inspected:

- `src/lrh/assist/run_packet.py`
- `src/lrh/assist/request_catalog.py`
- `src/lrh/assist/request_cli.py`
- `src/lrh/assist/README.md`
- `src/lrh/serve.py`
- `tests/assist_tests/run_packet_test.py`
- `tests/assist_tests/request_catalog_test.py`
- `tests/assist_tests/request_cli_test.py`
- `tests/cli_tests/serve_test.py`
- `project/focus/current_focus.md`

What exists now:

- `run-packet-from-work-item` is a canonical structured request.
- The run-packet renderer parses a work item, validates required work-item fields, performs strict execution-readiness validation, and renders a dry-run/manual packet only when the selected work item passes.
- Non-ready work items produce diagnostic packets and CLI errors instead of silently generating executable-looking instructions.
- The request CLI can print to stdout or write to `--out`.
- `lrh serve` includes safe-default run-packet previews/copy/download surfaces that reuse the package-owned renderer.

What is missing:

- No durable run packet/state directory is created.
- No `lrh run` command, autonomous execution, branch mutation, PR creation, or agent dispatch exists.

Core/non-agentic or agentic:

- Human-assist, non-agentic.

Alignment:

- Aligns with the adopted workstream/planning proposal and safe-default packaging: packet generation is human-assisted and non-mutating, while autonomous execution remains deferred.

Classification: **implemented**.

## 4. Recommended follow-up sequence

Do not blindly reuse the old Option C prompt package. Based on the current implementation state, use this minimal follow-up sequence instead:

1. **Durable manual run-state / run tracking design+implementation prompt**
   - Scope: `project/runs/<RUN-ID>/`, `packet.yaml`, `state.yaml`, `events.jsonl`, prompts, evidence, report links, and manual lifecycle states.
   - Must remain safe-default and non-agentic.
   - Must not add `lrh run`, autonomous dispatch, observation adapters, branch mutation, PR creation, stabilization loops, or merge/publish automation.
2. **Snapshot/read-only viewer extension for durable run state**
   - Scope: expose manual run-state summaries after the run-state schema exists.
   - Must stay observability-only.
3. **Optional public naming/API clarification**
   - Scope: decide whether to document `PlanningTreeIndex` as the canonical equivalent to older `PlanningIndex` wording, or add compatibility aliases only if there is real consumer pressure.
   - This should be small and documentation/API-focused, not a rewrite.

## 5. Non-goals

This audit PR does not:

- implement `PlanningRecord` / `PlanningIndex`
- implement validators
- add CLI commands
- add snapshot behavior
- add execution-ready validation
- add run-packet generation
- add `lrh run`
- add agentic behavior
- reorganize existing work items unless required by repository conventions

## Validation notes for this audit

Validation commands and their results are recorded in the execution record for this prompt. This report is audit-only and does not claim new runtime behavior.

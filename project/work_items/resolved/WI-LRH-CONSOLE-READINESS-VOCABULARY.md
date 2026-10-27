---
id: "WI-LRH-CONSOLE-READINESS-VOCABULARY"
title: "Show one readiness vocabulary, and fix the work-item page that says every item is not ready"
type: "deliverable"
status: "resolved"
blocked: false
blocked_reason: null
resolution: 'Implemented and merged in PR #840 (commit fadee470). LRH Console names each readiness check instead of plain ready or not ready. The work-item page lists Prompt-ready (the lrh work-items readiness check the map uses, with blocking reasons; Not applicable for closed items), Execution-ready flag (run packets: Yes, No, or Not declared), and Authorization; run-packet fields say not declared instead of missing, and required evidence shows the item''s own field. The Statusboard, project and workbench pages say Leaves flagged execution-ready, with counts unchanged. The vocabulary is recorded in the visual-language proposal. The owner checked it in LRH Console and found the terms clear. Showing the validated run-packet result is deferred to WI-LRH-CONSOLE-RUN-PACKET-READINESS.'
owner: "anthony"
contributors:
- "anthony"
assigned_agents: []
parent_id: "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_focus: []
related_roadmap: []
related_workstreams:
- "WS-LRH-CONSOLE-LOCAL-DOGFOOD"
related_design:
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
depends_on: []
blocked_by: []
expected_actions:
- "edit_file"
- "run_tests"
- "create_pr"
forbidden_actions:
- "force_push"
- "delete_branch"
- "merge_pr"
- "publish_package"
- "deploy_remote_service"
acceptance:
- "The work-item page no longer reports a work item as plainly 'not ready' because it has no execution-readiness metadata; each readiness value it shows is labelled with the check that produced it."
- "The map card, details pane, and work-item page never disagree about readiness: the existing 'Not prompt-ready' card flag and details 'Prompt-ready' row are kept, and the full page shows prompt readiness under the same name."
- "One documented set of terms (structural state, prompt readiness, execution readiness, and any statusboard readiness counts) is used across the map, details pane, work-item page, and statusboard, recorded in the visual-language proposal."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "src/lrh/dependency_maps/render.py"
- "tests/cli_tests/serve_test.py"
- "tests/dependency_maps_tests/render_test.py"
- "project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md"
---

# Readiness vocabulary across LRH Console

## Summary

Make every LRH Console screen say which readiness check it shows, using one set of terms. Fix the work-item page, which reports "not ready" for every LRH work item.

## Problem / Context

In the L1 dogfood (`project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`, Run Four), the owner asked what to work on next. They chose `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`, whose map card reads "Unblocked / All prerequisites done" and whose details pane reads "Prompt ready: Yes". The full work-item page read "Readiness state: not ready", and so did the page for every other open item. The owner was left "not sure on readiness".

The cause: `render_project_work_item_page` (`src/lrh/serve.py`, around line 2450) derives its "Readiness state" from `item.execution_readiness`. That is set only when a work item declares at least one of the opt-in execution-readiness fields in `src/lrh/control/execution_readiness.py` (`OPT_IN_FIELDS`, such as `execution_ready` or `autonomy_level`), which serve the agentic run-packet path; otherwise the page reports "not ready". None of LRH's 259 work items declares any of them, so every page says "not ready", under an unqualified label. The map uses structural state (`unblocked`, `waiting`, ...) and prompt readiness from `lrh work-items readiness`: cards already carry a "Not prompt-ready" flag when it applies, and the details pane has a "Prompt-ready" row (`src/lrh/dependency_maps/render.py`, `_not_prompt_ready` and the details list). The statusboard reports ready and readiness-deficient leaf counts. The owner asked that "Not ready should appear on the card or in the details" and that "We should harmonize our vocabulary across unblocked / not ready / prompt ready / etc".

### Duplication search

In-repo: no existing item covers readiness labels. `WI-LRH-CONSOLE-STATUS-SHAPES` changes how structural states look, not what they are called. Recommendation: proceed.

## Scope

- The work-item page: label each readiness value by its check, show prompt readiness, and show "not declared" rather than "not ready" when a work item has no execution-readiness metadata.
- The map card and details pane: keep the existing prompt-readiness cues, renamed if the vocabulary changes.
- A short vocabulary, recorded in the visual-language proposal, and applied to the map, details pane, work-item page, and statusboard.

## Required Changes

1. Change the work-item page's readiness section to name each check, add prompt readiness, and treat missing execution-readiness metadata as undeclared.
2. Make the card flag, details row, and full page use the same terms, without adding a new color.
3. Record the vocabulary in `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`, and align labels on the statusboard.
4. Add tests for the page labels and the card cue, and check with the owner in LRH Console.

## Non-Goals

- No change to how any readiness check is computed.
- No backfill of execution-readiness metadata across work items.

## Acceptance Criteria

- The work-item page no longer reports a work item as plainly 'not ready' because it has no execution-readiness metadata; each readiness value it shows is labelled with the check that produced it.
- The map card, details pane, and work-item page never disagree about readiness: the existing 'Not prompt-ready' card flag and details 'Prompt-ready' row are kept, and the full page shows prompt readiness under the same name.
- One documented set of terms (structural state, prompt readiness, execution readiness, and any statusboard readiness counts) is used across the map, details pane, work-item page, and statusboard, recorded in the visual-language proposal.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Owner check of a work item's card, details pane, and full page in LRH Console.

## Dependencies / Order

- None. Recommended before L2 (see the L1 evidence record).

## Risk Notes

- The run-packet and workbench routes also read execution-readiness metadata; keep their gating unchanged and change only labels.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/evidence/EV-LRH-CONSOLE-L1-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`

---
id: "WI-LRH-CONSOLE-COPY-PROMPT-BUTTON"
title: "Wire the work-item page's Copy generated prompt button and gate it on what it copies"
type: "deliverable"
status: "proposed"
blocked: false
blocked_reason: null
resolution: null
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
depends_on:
- "WI-LRH-CONSOLE-RUN-PACKET-READINESS"
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
- "Clicking an enabled Copy button puts exactly the text the page's Preview generated prompt link shows on the clipboard, and says so, inside LRH Console and in a browser."
- "The button's label and its gating name the same artifact: either it copies the generated prompt and is gated on that prompt's own check, or it copies the run packet and is gated on run-packet validation, as the owner decides."
- "Without page scripts the button is absent or plainly disabled, never a control that does nothing."
required_evidence:
- "test_output"
- "manual_review"
- "lrh_validate"
artifacts_expected:
- "src/lrh/serve.py"
- "tests/cli_tests/serve_test.py"
---

# Copy generated prompt button

## Summary

Make the work-item page's **Copy generated prompt** button work, and gate it on the artifact it copies.

## Problem / Context

`WI-LRH-CONSOLE-RUN-PACKET-READINESS` (PR #855) gated the button on run-packet validation, as its acceptance required. Its run plan noted two problems, and the owner asked for this item:

- The button has no click handler. It is a `<button>` that does nothing when enabled.
- Its label says it copies the *generated prompt* (`lrh request codex-prompt-from-work-item`, the page's Preview link). It is gated on the *run packet*, a different artifact that the page does not offer to copy.

### Duplication search

In-repo: no other item covers this button. The page's Preview and Download links already render the prompt. Recommendation: proceed.

## Scope

- Decide with the owner which artifact the button copies, and gate it on that artifact's own check.
- Wire the copy with a same-origin page script, following the pattern of the existing interactive script. Show a short confirmation.
- Keep the page usable without scripts.

## Required Changes

1. Add the copy behavior and its confirmation.
2. Align the label, the gating and the explanatory text.
3. Add Serve and script tests, and update the readiness vocabulary table if the gating changes.
4. Check with the owner in LRH Console.

## Non-Goals

- No change to prompt or run-packet generation.

## Acceptance Criteria

- Clicking an enabled Copy button puts exactly the text the page's Preview generated prompt link shows on the clipboard, and says so, inside LRH Console and in a browser.
- The button's label and its gating name the same artifact: either it copies the generated prompt and is gated on that prompt's own check, or it copies the run packet and is gated on run-packet validation, as the owner decides.
- Without page scripts the button is absent or plainly disabled, never a control that does nothing.

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- The owner checks the button in LRH Console.

## Dependencies / Order

- Depends on `WI-LRH-CONSOLE-RUN-PACKET-READINESS`.

## Risk Notes

- Clipboard access in WKWebView may need a user gesture or a native path. Check it inside LRH Console, not only in a browser.

## Related Workstream and Designs

- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
- `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` (readiness vocabulary)

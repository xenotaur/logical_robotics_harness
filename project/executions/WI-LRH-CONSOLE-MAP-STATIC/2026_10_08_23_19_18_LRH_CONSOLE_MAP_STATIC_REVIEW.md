---
execution_id: 2026_10_08_23_19_18_LRH_CONSOLE_MAP_STATIC_REVIEW
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-STATIC:LRH_CONSOLE_MAP_STATIC_REVIEW)[2026-10-08T23:19:18+00:00]
work_item: WI-LRH-CONSOLE-MAP-STATIC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/800
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/800"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-08T23:19:18+00:00
---


# Summary

This record covers review-response round 1 for PR #800 (`WI-LRH-CONSOLE-MAP-STATIC`), run as part
of `/lrh-land` inside `/lrh-execute`. It combines the owner's hands-on check with the bot threads.

- **CI** passed 7/7 on `f78797c7`.
- **Copilot** left 3 threads and **Codex** left 1 P2 thread.
- **The owner's check:** the agent launched this branch's LRH Console. The owner reported:
  - "Overall it looks good";
  - there is no precise not-prompt-ready flag, and the only items without prompt-readiness
    were resolved ones, "which is confusing";
  - lines are "somewhat hard to read", and they suggested a partial order with indentation;
  - MAP-STATIC's title was cut off;
  - table and blockers IDs open the drawer rather than going back to the map;
  - abandoned and unknown look similar, and so do in progress and unblocked;
  - the pills carry text and an icon.
- **The owner's decision:** "Yes, apply 1–7 now and file 8 and 9".

# Result

Fixed in `4e24ba7a`:

1. **Owner:** prompt-readiness reads "Not applicable (closed)" for done and abandoned items
   (`_ready_text`).
2. **Owner:** titles get three lines, and `CARD_HEIGHT` went from 124 to 140.
3. **Owner:** "Show on map" appears in the drawer on the Table and Blockers tabs. Earlier I
   misdescribed the table IDs as going back to the map; per the spec they select the item.
4. **Copilot:** the narrow-screen list keeps the Not prompt-ready flag and the outside-view
   count.
5. **Copilot:** the empty-view message also appears in the narrow-screen list.
6. **Copilot:** unmet needs come from the edges (`_unmet_needs`) in the table and the Blockers
   tab. A flagged item still lists its unfinished dependencies, and missing targets count as
   unmet.
7. **Codex P2:** `dependency_map_head_status` builds the snapshot exactly as GET does, for both
   the HTML map and the JSON route, so a source error gives 500 on both. This reverses an
   earlier pre-push suggestion in favor of HEAD and GET agreeing. The `lrh serve` reference is
   updated.

Filed in `5b5367f6`, from the owner's check:

8. **`WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`:** a second `Layout`, with a topological order and
   depth indentation, that becomes the default after the owner compares both.
9. **`WI-LRH-CONSOLE-STATUS-SHAPES`:** In progress filled versus Unblocked outlined, and
   Abandoned cards dotted and muted, recorded in the visual-language proposal.

Both are added to `WS-LRH-CONSOLE-LOCAL-DOGFOOD` and are `prompt_ready: yes`.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Next is confirm-fixes: resolve the 4 threads, then re-check CI.

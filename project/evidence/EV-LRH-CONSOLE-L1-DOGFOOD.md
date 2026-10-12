---
id: EV-LRH-CONSOLE-L1-DOGFOOD
title: "LRH Console L1 dependency-map dogfood on LRH and LCATS"
type: manual_review
status: recorded
related_work_items:
  - WI-LRH-CONSOLE-L1-DOGFOOD
  - WI-LRH-CONSOLE-READINESS-VOCABULARY
  - WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
  - WI-LRH-CONSOLE-DESKTOP-BACK-NAV
  - WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT
  - WI-LRH-PROJECT-UPDATE-SKILL
  - WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT
related_focus: []
source:
  kind: manual_dogfood_sessions
  operator: anthony
  command: "LRH Console branch build launched by the agent with LRH_CONSOLE_PYTHON=<python> apps/desktop/scripts/run launch; the owner asked real planning questions and reported each run in chat"
  captured_at: 2026-10-12T20:05:00Z
  base_commit: 9178953e994d91728d12115ca9d396c502c50db5
summary_result: pass_with_limits
artifacts:
  - project/views/dependency_maps/lrh-console-l1.md
  - "LCATS: lcats/project/views/dependency_maps/worldcon-2026.md (xenotaur/LCATS PR #497, merge a1cc22469410a1ed5ab6bc6d6023936852ab1015)"
  - project/work_items/proposed/WI-LRH-CONSOLE-READINESS-VOCABULARY.md
  - project/work_items/proposed/WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE.md
  - project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-BACK-NAV.md
  - project/work_items/proposed/WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT.md
  - project/work_items/proposed/WI-LRH-PROJECT-UPDATE-SKILL.md
  - project/design/backlog.md
metrics:
  planning_runs_recorded: 4
  runs_on_lcats_map: 1
  runs_on_lrh_map: 2
  runs_off_script: 1
  answers_traced_to_source_records: 4
  adverse_cases_exercised: 7
  adverse_cases_on_real_data: 3
  adverse_cases_on_fixtures_only: 4
  additional_real_adverse_cases: 1
  largest_real_view_nodes: 57
  largest_real_view_edges: 59
  largest_real_view_build_seconds_uncached: "0.61-0.69"
  largest_real_view_served_seconds_cached: "0.046-0.087"
  checkout_bindings_fixed: 4
  work_items_filed: 4
  work_items_amended: 1
  python_tests: 2288
  chrome_comparison_items_checked: 7
  chrome_differences_found: 0
blocked_actions:
  - "The Chrome comparison was one pass by the owner over the LCATS worldcon-2026 map, side by side with the app, after the four runs. The LRH view was not compared in Chrome, and no run was conducted in Chrome."
  - "Cycles, missing IDs, and ambiguous lanes do not occur in the LRH or LCATS views, and a stale snapshot needs an edit during a session, so these four were exercised only on throwaway fixtures in the agent's scratchpad, never committed."
  - "Per-run times were not recorded. All four runs took place on 2026-10-12."
  - "Run One ended when the app closed after the owner rewound the chat. No crash report was written; the agent had launched the app from a shell owned by the chat session, and later relaunched it detached. This is recorded as a launch-method artifact, not an app defect, but it was not reproduced."
  - "Only macOS was observed."
modified_actions:
  - "The work item asks for three planning questions. The owner ran four: Run Three (Prosoc) went off script, and Run Four was added. The gate is judged on Runs One, Two, and Four, which span LCATS and LRH; Run Three is kept as a real adverse case."
  - "With the owner's approval, the agent bound local checkouts for Prosoc, Replication Vector, Velumin, and Narramorph in the owner's private Meta state (`lrh meta set <name> --local-repo-path PATH`). No project repository was changed."
  - "Code defects and requests were filed as four grouped work items, one amended work item, and backlog notes, at the owner's direction."
approval_records:
  - "2026-10-12: the owner approved the run plan, including fixtures for adverse cases that do not occur in real data."
  - "2026-10-12: the owner approved binding Prosoc, then supplied the checkout paths for Replication Vector, Narramorph, and Velumin."
  - "2026-10-12: the owner approved filing the four new work items, amending WI-LRH-PROJECT-UPDATE-SKILL, and extending the backlog."
  - "2026-10-12: the owner, in chat, confirmed the agent's recommendation: close the L1 gate with the recorded limits, land WI-LRH-CONSOLE-READINESS-VOCABULARY and WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE before L2, and make WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT the main L2 design question."
---

# LRH Console L1 dependency-map dogfood on LRH and LCATS

This records the owner's real use of LRH Console's dependency maps for the L1
gate in `WS-LRH-CONSOLE-LOCAL-DOGFOOD`. The gate is "Three LRH/LCATS planning
questions answered with traceable evidence and adverse graph fixtures"
(`project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`).

Every question, step, answer, and friction note below is the owner's own,
quoted or closely paraphrased from their run reports (quotes keep the owner's
spelling). The agent asked no questions of the map on the
owner's behalf. Its contribution is the source-record traces, the adverse-case
checks, and the timings, each marked as such.

## Environment

| Item | Value |
| --- | --- |
| Mac | macOS 27.0.1 (Darwin 27.0.0, arm64) |
| App | LRH Console 0.1.0, unsigned branch build from `apps/desktop/scripts/run bundle` in the agent's worktree |
| Launch | `LRH_CONSOLE_PYTHON=/Users/centaur/anaconda3/envs/LrhLocalAgent/bin/python apps/desktop/scripts/run launch` (Python 3.11.16, `PYTHONPATH` set to the worktree's `src`) |
| LRH | `main` at `9178953e994d91728d12115ca9d396c502c50db5`; view `lrh-console-l1` (25 work items) |
| LCATS | checkout `/Users/centaur/Tempspace/Projects/LCATS/LCATS` at `a1cc22469410a1ed5ab6bc6d6023936852ab1015`; project directory `lcats/project`; view `worldcon-2026` (50 work items in view, 57 nodes with offscreen prerequisites) |
| Meta | global workspace, catalog `/Users/centaur/Workspace/LogicalRoboticsHarness/meta_control_plane`; LCATS bound to its checkout through a private checkout binding |

## LCATS access

LCATS is served through the Meta registry. Its control plane sits one level
down, at `lcats/project`, and its registry record already says
`project_dir: lcats/project`. Only two steps were needed, and neither was a
code gap, so no gap work item was filed:

1. A private checkout binding to the owner's LCATS checkout.
2. The `worldcon-2026` view, landed in LCATS through xenotaur/LCATS PR #497. Its
   lanes are the five WorldCon workstreams, with one phase holding all 50 work
   items.

## Planning runs

### Run One (LCATS map)

- **Question:** "What work remains on the special characters work?"
- **Used:** the Meta dashboard's LCATS card, then the dependency map, the Done
  filter, and the scrollbars.
- **Owner's answer:** "No overtly tracked work items, but the workstream and
  design proposal aren't in the dependency map and have no status listed, so
  I'm not confident here."
- **Trace (agent):** all 10 work items in `WS-SPECIALS-CLEANUP` are `resolved`
  (`WI-SPANOPS-0002` to `WI-CLEAN-0022`). The workstream file
  (`lcats/project/workstreams/proposed/WS-SPECIALS-CLEANUP.md`) is still
  `proposed`, at stage `assessed`, and lists two open questions: where the
  2026-07-09 measurement evidence lives, and how `data/` collection names map
  to `corpora/` for promotion. It has no design proposal; its design links are
  `project/design/design.md`, the 2026-06-16 special-character audit, and the
  2026-06-18 phase-4 repair-review-application integration audit. The
  owner's answer matches the records, and the low confidence was warranted:
  the remaining work is in the workstream, which the map cannot show.
- **Friction (owner):**
  - Statusboard cards "are rather tall and have some information that might go
    in details".
  - The map is wider than the window; "you had to scroll on the right to make
    the scrollbar at the bottom visible".
  - "We still don't have proposals or workstreams in the map, so it's hard to
    put into contet".
  - Lines are hard to read: "the square icons all seem to go through each
    other, and if there is a partial order it isn't clear".
  - Hidden cards keep their space, so "the map be mostly wasted space if most
    items are hidden".
  - Suggestion: a "work remains" button that asks an agent about a lane.

### Run Two (LRH map)

- **Question:** "What work is outstanding in LRH?"
- **Used:** the Statusboard's LRH card (and the sidebar, as a test), the
  dependency map, the Done filter, card selection, and "Open the full page".
- **Owner's answer:** "Don't know - the dependency map is just for the console
  dogfood. Four cards are outstanding." The owner estimated LRH has about 30
  open threads of work.
- **Trace (agent):** the live `lrh-console-l1` snapshot has 25 nodes, 4 not
  resolved, all `proposed` and unblocked: `WI-LRH-CONSOLE-L1-DOGFOOD`,
  `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`, `WI-LRH-CONSOLE-STATUS-SHAPES`, and
  `WI-LRH-PROJECT-UPDATE-SKILL` (in the Unplaced row). Project-wide on `main`,
  LRH has 12 open workstreams (4 active, 8 proposed), 55 open work items (4
  active, 51 proposed), and 19 proposed design proposals. The only LRH view
  covers 1 of the 12 workstreams. The owner's count is right, and so is the
  sense that the map underrepresents LRH.
- **Friction (owner):** the hidden-card whitespace again; "A backbutton would
  be nice in addition to the backspace key."
- **Note (agent):** View > Back (Cmd+[) and View > Forward (Cmd+]) already
  exist, from `WI-LRH-CONSOLE-DESKTOP-SHELL-POLISH`. The owner did not find
  them, so the gap is a visible control.
- **Non-friction (owner):** "App is now pretty snappy once you're moving
  around in it."

### Run Three (off script: Prosoc)

- **Question:** "What's the status of Prosoc?"
- **Used:** the sidebar's Prosoc entry.
- **Owner's answer:** "Prosoc is not yet set up properly." The page said
  `needs_local_checkout` and named the fix,
  `lrh meta set prosoc --local-repo-path PATH`.
- **Trace (agent):** `lrh meta inspect prosoc` showed no checkout binding. The
  checkout exists at `/Users/centaur/Tempspace/Projects/ProsocialRobotics/prosocial`
  (reached through `~/Workspace/ProsocialRobotics/prosocial`), with origin
  `github.com/xenotaur/prosoc` and a `project/` directory. Meta has no checkout
  discovery, so the directory name was not the cause. With the owner's approval
  the agent bound it; the owner reloaded the page without restarting the app,
  and it loaded "fine", showing that landing normative cards as approved is the
  next step, "but little more detail". The agent then bound Replication Vector
  (Stable), Velumin (Needs attention: validation status `error`), and Narramorph (Needs
  attention: `missing_project`, since its checkout has no `project/`).
- **Friction (owner):** "We don't have a way to trigger a refresh of a
  messed-up project. `/lrh-project-doctor` would be an option."

### Run Four (LRH map)

- **Question:** "What's the next thing to work on in the console dogfood?"
- **Used:** the LRH project page, the dependency map, the Done filter, the
  `WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT` card and details, and the full page for
  it and every other open item.
- **Owner's answer:** "I want to run WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT but I'm
  not sure on readiness." The card read "Unblocked / All prerequisites done"
  and the details read "Prompt ready: Yes", but every full page read
  "Readiness: not ready". The owner also noted the open items "do not well
  reflect the ~10 open threads on the console".
- **Trace (agent):** the item is ready. Its one prerequisite,
  `WI-LRH-CONSOLE-MAP-STATIC`, is resolved, and `lrh work-items readiness`
  reports `prompt_ready: yes`. The full page's "Readiness state" comes from
  `render_project_work_item_page` (`src/lrh/serve.py`), which reads
  execution-readiness metadata: the opt-in fields in
  `src/lrh/control/execution_readiness.py` used by the run-packet path, such as
  `execution_ready`. None of LRH's 259 work items declares any of them, so
  every page says "not ready". This is a labelling defect, filed as
  `WI-LRH-CONSOLE-READINESS-VOCABULARY`.
- **Friction (owner):** "Not ready should appear on the card or in the
  details"; "We should harmonize our vocabulary across unblocked / not ready /
  prompt ready / etc"; "Still hard to see all the cards with all that
  whitespace for suppressed items, even in a big window".

### Chrome comparison

After the runs, and in response to PR review, the owner opened the same served
map (`http://127.0.0.1:57089/project/lcats/dependency-maps/worldcon-2026`) in
Chrome while the app showed it, as the L1 design asks ("compare the same
serialized snapshot in Chrome and the embedded renderer"). The owner reported
"it looks good":

1. "Cards look as before."
2. "Lines look the same."
3. "Filters seem to work"
4. "Highlight and details work"
5. "Open full page works"
6. "Scrolling is the same as before"
7. "Note the bottom scrollbar only appears if the page is not super-wide, and
   when it does appear you have to scroll all the way to the bottom to see it."

No difference between Chrome and the app was found. Item 7 matches the
scrollbar friction from Run One, so it is a map-layout issue in both
renderers, recorded in the backlog.

### Gate assessment

Runs One, Two, and Four are genuine planning questions spanning LCATS and LRH,
with one on the LCATS map, and each answer is traced to source records above.
The owner stayed unsure in all three: Run One ("not confident") because the
remaining work sits in a workstream the map does not show, Run Two ("Don't
know") because the only LRH view covers a small slice of the project, and Run
Four ("not sure on readiness") because of the readiness label defect. The
agent's traces show that what the maps did display was correct for each view,
but the owner could not reach a confident answer from the console alone. Whether
that passes the gate was the owner's call; the owner confirmed the agent's
recommendation below.

## Adverse cases (agent-run)

Fixture checks used a throwaway project built in the agent's scratchpad with
the helpers from `tests/dependency_maps_tests/snapshot_test.py`, and were not
committed. Timings come from a one-off timing command run in the session (not
preserved), calling `snapshot.build_snapshot` and `render.render_view` on the
worktree's code three times each, and from three `curl` requests to the running
app's backend.

| Case | Data | Result |
| --- | --- | --- |
| Cycle (A → C → B → A) | Fixture | `cycle` error: "depends_on cycle among WI-A, WI-B, WI-C". The three cards show as waiting, and the map renders. |
| Missing ID | Fixture | `missing_reference` error: "WI-M depends_on WI-DOES-NOT-EXIST, which does not exist". |
| Ambiguous lane | Fixture | `ambiguous_lane` warning naming both workstreams and the `lane_override` fix. |
| Absent phase | Real (LRH) and fixture | `unplaced_phase` info; the card appears in an Unplaced row. On LRH, work items added to the workstream after the view was written (for example `WI-LRH-PROJECT-UPDATE-SKILL`) land there. |
| Hidden dependencies | Real (LCATS) | 7 offscreen prerequisites on `worldcon-2026` (`WI-ASSESS-0031`, `WI-EVENT-0029`, `WI-GENRE-0004`, `WI-LLM-0074`, `WI-PILOT-0051`, `WI-SEGMENT-0069`, `WI-SEGMENT-0070`), all resolved. |
| Stale snapshot | Fixture | After editing a work item, `freshness_diagnostics` returns `stale_snapshot`: "the control files changed after this snapshot was generated ...; refresh before relying on it". Rendering with a `since` value that differs from the current fingerprint shows a page-level "Sources changed" notice; individual changed items are not marked. |
| Missing checkout or project directory | Real (Meta) | Prosoc showed `needs_local_checkout` with the fix command; Narramorph showed `missing_project` after binding. A binding made outside the app appeared on page reload. |
| Largest real view | Real (LCATS `worldcon-2026`: 57 nodes, 59 edges, 154 KB of HTML) | Uncached snapshot build 0.61–0.69 s; render 2–5 ms. Served by the running app, with its cache warm: 46–87 ms. |

LRH's `lrh-console-l1` view (25 nodes) builds uncached in 0.85–0.95 s, slower
than LCATS despite fewer nodes, because the build loads every work item in the
project (259 for LRH). Build cost scales with project size, not view size.

## Findings

### Work items filed

- `WI-LRH-CONSOLE-READINESS-VOCABULARY` (Run Four): the work-item page's
  readiness label, readiness on the card or details, and one vocabulary.
- `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` (Runs One, Two, Four): re-lay out the
  map when filters hide cards.
- `WI-LRH-CONSOLE-DESKTOP-BACK-NAV` (Run Two): a visible Back control; the
  menu commands already exist.
- `WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT` (Runs One, Two, Four): design how the
  map shows workstreams and proposals, and how the console answers
  project-wide questions.
- `WI-LRH-PROJECT-UPDATE-SKILL` (amended, Run Three): adds an in-app re-check,
  the fix for missing checkouts on the project page, and a more detailed
  project page. Its registry criterion now uses a fixture, since the owner's
  registry was fixed by hand during this dogfood.

### Backlog

The LRH Console layout-redesign entry in `project/design/backlog.md` now also
covers map width and scrollbar placement, tangled lines (the target of
`WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT`), statusboard card height, and a per-lane
"work remains" agent button as an L2 idea.

## Automated validation (observed)

- `lrh validate` (worktree code): 0 errors, 0 warnings.
- `lrh work-items readiness` on the four new work items: `prompt_ready: yes`,
  no warnings.
- `scripts/test` (with `PYTHONPATH` set to the worktree's `src`): 2288 tests,
  OK.
- `scripts/format --check --diff`: clean.

This record changes no code, so the desktop suite was not rerun.

## Recommendation

**Close the L1 gate with the limits above.** This was the agent's
recommendation; the owner confirmed it in chat on 2026-10-12. The maps render real LRH and LCATS views quickly,
every adverse case is detected and explained, and what they showed was correct.
But the owner reached a confident answer in none of the three gate runs, so the
gate shows the map works, not yet that it answers planning questions alone.
That gap is what the items below address.

**Before L2, land two items:** `WI-LRH-CONSOLE-READINESS-VOCABULARY`, because a
page that calls every item "not ready" undermines the main question the map is
for, and `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE`, because the whitespace limited
three of four runs.

**Make planning context L2's main design question**
(`WI-LRH-CONSOLE-MAP-PLANNING-CONTEXT`). A declared view answers only for the
workstreams it names, and two of four runs needed what lies outside it: a
workstream's status and open questions (Run One) and the whole project's
outstanding work (Runs Two and Four). Consider with it whether views should
pick up work items added to their workstreams later.

**Keep agent actions out of L2's first step.** The "work remains" button and
`/lrh-project-update` are useful, but the skill can deliver the second without
dispatch from the console.

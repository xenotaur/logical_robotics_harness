---
execution_id: 2026_10_08_19_04_48_LRH_CONSOLE_MAP_STATIC
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-STATIC:LRH_CONSOLE_MAP_STATIC)[2026-10-08T18:34:07+00:00]
work_item: WI-LRH-CONSOLE-MAP-STATIC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/800
commit: 2f64eee46cabd6254943d8b8155489511a17a757
agent: "claude_app"
instruction_source: "user request in session: /lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD (chain approved: \"Approve as stated, including the minimal layout\")"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-08T19:04:48+00:00
---


# Summary

This record covers the implementation of `WI-LRH-CONSOLE-MAP-STATIC` through `/lrh-execute`: the
server-rendered, script-free dependency map, Table and Blockers views, and the swappable layout
interface. The owner approved the chain, the run plan, and the minimal layout in place of a
library ("Approve as stated, including the minimal layout").

# Result

**Layout evaluation.** Before the gate, I checked PyPI on 2026-10-08:

- `networkx` 3.7 needs Python 3.12 or later and doesn't route lines.
- `grandalf` 0.8 is GPL/EPL, its last release was in 2023, and it computes its own layers.
- `igraph` 1.0 is a GPL C extension.
- `graphviz` and `pygraphviz` need native Graphviz.

None fits a fixed lane-and-phase grid without Node or a native binary. The owner approved a
minimal implementation, and the PR records the evaluation.

- **`src/lrh/dependency_maps/layout.py` (new):** the `Layout` protocol, `LayoutResult`, `Box`,
  `Card` and `Line`. The default `LayeredGridLayout` (`layered-grid`):
  - keeps cards in their fixed cells;
  - orders them with Gauss-Seidel barycenter sweeps;
  - routes lines at right angles through lane and phase gutters, on separate tracks;
  - returns cards in reading order;
  - skips nodes that have no lane or phase row.
- **`src/lrh/dependency_maps/render.py` (new):** `render_view` produces:
  - cards as positioned HTML links over an SVG line layer, with solid and dashed lines and
    arrowheads;
  - a legend and a diagnostics banner;
  - the since-fingerprint freshness note;
  - selection with upstream and downstream highlighting, and a drawer with the three state
    layers, placement, reasons, needs and needed-by, source, and the not-modeled effort slot;
  - the Table (row-header ID links), Blockers, and a narrow-screen list;
  - `MAP_STYLES`, which uses tokens only.
- **`src/lrh/serve.py`:** `render_dependency_map_page` serves the index, the view (200), 404
  JSON, and explanatory 422 and 500 pages, through `_dependency_map_document`, with HEAD
  handling and the route list.
- **`src/lrh/ux/frame.py`:** a Dependency maps view in project scope, and the
  `OWN_DRAWER_MARKER` opt-out.
- **Tests:** `tests/dependency_maps_tests/render_test.py` (new) and `serve_test.py` additions.
- **Docs:** the `lrh serve` dependency-map routes, and a layout section in the
  `lrh dependency-map` reference.

**Browser-pane checks** on the real `lrh-console-l1` view found and fixed:

- long IDs wrapping and clipping card content, so cards are now wider and taller with
  ellipsized IDs;
- the table collapsing into one-character columns under the frame's wrap-anywhere, so it now
  wraps normally inside its own scroll area.

I also confirmed light and dark mode, selection and the drawer, the table, blockers and the
index, and 375 px list mode, all with no horizontal page scroll.

**A bug the tests caught:** cell ordering oscillated between sweeps because it read stale
positions. Gauss-Seidel updates now let it settle.

**Pre-push cold review.** Verdict: safe to push. It confirmed routing in every direction,
escaping, token use, contrast and timing. Applied in `3adf63b5`:

- an explicit drawer opt-out, so an unknown item no longer shows the frame placeholder and the
  page says so;
- reading order;
- dashed borders kept on highlighted cards;
- lanes before phases in heading order;
- an aria-hidden close icon and row headers;
- "and N more" on blocked cards;
- dead line tooltips dropped;
- nodes without rows skipped;
- more tests.

**Timing on the real view:** snapshot 0.81 s, layout 0.3 ms, render 0.4 ms per request.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass (2117 tests).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `WI-LRH-CONSOLE-INTERACTIVE` adds client-side tracing over the same layout output.
- Possible later work: cache snapshots by fingerprint, and lay out multi-column cells for
  single-lane views.

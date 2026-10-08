"""Tests for the dependency-map layout and server-rendered views."""

from __future__ import annotations

import dataclasses
import datetime
import re
import unittest

from lrh.dependency_maps import layout, render
from lrh.dependency_maps.snapshot import (
    DependencyMapSnapshot,
    Diagnostic,
    Edge,
    Node,
    ProjectIdentity,
    Row,
    StateReason,
)

_AT = datetime.datetime(2026, 10, 8, tzinfo=datetime.UTC).isoformat()


def _node(
    node_id: str,
    lane: str | None,
    phase: str | None,
    state: str = "unblocked",
    *,
    reasons: tuple[StateReason, ...] = (StateReason(kind="no_prerequisites"),),
    offscreen: bool = False,
    prompt_ready: bool | None = True,
    title: str | None = None,
) -> Node:
    return Node(
        id=node_id,
        title=title or f"{node_id} title",
        lifecycle="proposed",
        source=f"project/work_items/proposed/{node_id}.md",
        offscreen=offscreen,
        lane=lane,
        lane_source="workstream",
        lane_reason=None,
        phase=phase,
        phase_source="declared",
        state=state,
        state_reasons=reasons,
        prompt_ready=prompt_ready,
        prompt_ready_source="lrh work-items readiness",
        authorization="not_derived",
        offscreen_predecessors=0,
    )


def _snapshot(
    nodes: tuple[Node, ...],
    edges: tuple[Edge, ...] = (),
    diagnostics: tuple[Diagnostic, ...] = (),
    lanes: tuple[str, ...] = ("WS-A", "WS-B"),
) -> DependencyMapSnapshot:
    return DependencyMapSnapshot(
        schema_version=1,
        view_id="main",
        view_title="Main view",
        view_source="project/views/dependency_maps/main.md",
        project=ProjectIdentity(name="repo", checkout_id="local:abc", head=None),
        source_fingerprint="sha256:" + "0" * 64,
        generated_at=_AT,
        lanes=tuple(Row(id=lane, title=f"{lane} title") for lane in lanes),
        phases=(
            Row(id="one", title="One"),
            Row(id="two", title="Two"),
            Row(id="unplaced", title="Unplaced", unplaced=True),
        ),
        nodes=nodes,
        edges=edges,
        diagnostics=diagnostics,
    )


def _edge(item: str, target: str, kind: str = "depends_on") -> Edge:
    return Edge(kind=kind, item=item, target=target, resolved=True, source="x.md")


_WAIT = (StateReason(kind="depends_on", target="WI-A", target_lifecycle="proposed"),)


def _example() -> DependencyMapSnapshot:
    return _snapshot(
        (
            _node("WI-A", "WS-A", "one"),
            _node("WI-B", "WS-B", "two", "waiting", reasons=_WAIT, prompt_ready=False),
            _node(
                "WI-C",
                "WS-A",
                "two",
                "blocked",
                reasons=(StateReason(kind="blocked_flag", detail="waiting on ops"),),
            ),
            _node(
                "WI-D",
                "WS-B",
                "one",
                "done",
                reasons=(StateReason(kind="lifecycle", detail="resolved"),),
            ),
            _node("WI-OUT", None, None, offscreen=True),
        ),
        (_edge("WI-B", "WI-A"), _edge("WI-C", "WI-B", "blocked_by")),
    )


def _view(snapshot: DependencyMapSnapshot, **options: object) -> str:
    settings = {"tab": "map", "item": None, "since": None, **options}
    return render.render_view(
        snapshot,
        layout.DEFAULT_LAYOUT,
        full_page_href=lambda item_id: f"/full/{item_id}",
        **settings,
    )


class LayeredGridLayoutTest(unittest.TestCase):
    def test_cards_sit_in_their_lane_and_phase_cells(self) -> None:
        result = layout.DEFAULT_LAYOUT.layout(_example())
        cards = {card.id: card for card in result.cards}
        lanes = {box.id: box for box in result.lanes}
        phases = {box.id: box for box in result.phases}

        self.assertNotIn("WI-OUT", cards, "offscreen items are not placed")
        for card in cards.values():
            lane, phase = lanes[card.lane], phases[card.phase]
            self.assertTrue(
                lane.x <= card.x and card.x + card.width <= lane.x + lane.width
            )
            self.assertTrue(
                phase.y <= card.y and card.y + card.height <= phase.y + phase.height
            )
        self.assertEqual([box.id for box in result.phases], ["one", "two"])

    def test_lines_are_right_angled_and_run_from_prerequisite_to_item(self) -> None:
        result = layout.DEFAULT_LAYOUT.layout(_example())
        cards = {card.id: card for card in result.cards}

        self.assertEqual(len(result.lines), 2)
        for line in result.lines:
            for (x1, y1), (x2, y2) in zip(line.points, line.points[1:]):
                self.assertTrue(x1 == x2 or y1 == y2, line.points)
            source, item = cards[line.source], cards[line.item]
            self.assertEqual(line.points[0][1], source.y + source.height // 2)
            self.assertEqual(line.points[-1][1], item.y + item.height // 2)
        self.assertEqual(
            {(line.source, line.item) for line in result.lines},
            {("WI-A", "WI-B"), ("WI-B", "WI-C")},
        )

    def test_routes_cross_distant_lanes_through_a_channel(self) -> None:
        snapshot = _snapshot(
            (_node("WI-A", "WS-A", "one"), _node("WI-C", "WS-C", "two")),
            (_edge("WI-C", "WI-A"),),
            lanes=("WS-A", "WS-B", "WS-C"),
        )

        (line,) = layout.DEFAULT_LAYOUT.layout(snapshot).lines

        self.assertEqual(len(line.points), 6)
        for (x1, y1), (x2, y2) in zip(line.points, line.points[1:]):
            self.assertTrue(x1 == x2 or y1 == y2)

    def test_cells_order_cards_by_their_neighbours(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-1", "WS-A", "one"),
                _node("WI-2", "WS-A", "one"),
                _node("WI-X", "WS-B", "one"),
                _node("WI-Y", "WS-B", "one"),
            ),
            (_edge("WI-X", "WI-2"), _edge("WI-Y", "WI-1")),
        )

        cards = {card.id: card for card in layout.DEFAULT_LAYOUT.layout(snapshot).cards}

        # Linked cards line up, so the two edges do not cross.
        self.assertEqual(
            cards["WI-1"].y < cards["WI-2"].y, cards["WI-Y"].y < cards["WI-X"].y
        )

    def test_left_and_same_lane_routes_meet_card_sides(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node("WI-B", "WS-A", "two"),
                _node("WI-C", "WS-C", "one"),
                _node("WI-D", "WS-B", "two"),
            ),
            (
                _edge("WI-B", "WI-A"),
                _edge("WI-A", "WI-C"),
                _edge("WI-A", "WI-D"),
            ),
            lanes=("WS-A", "WS-B", "WS-C"),
        )
        result = layout.DEFAULT_LAYOUT.layout(snapshot)
        cards = {card.id: card for card in result.cards}

        for line in result.lines:
            with self.subTest(line=(line.source, line.item)):
                source, item = cards[line.source], cards[line.item]
                for (x1, y1), (x2, y2) in zip(line.points, line.points[1:]):
                    self.assertTrue(x1 == x2 or y1 == y2)
                self.assertIn(line.points[0][0], (source.x, source.x + source.width))
                self.assertIn(line.points[-1][0], (item.x, item.x + item.width))

    def test_cards_come_in_reading_order(self) -> None:
        result = layout.DEFAULT_LAYOUT.layout(_example())
        phases = [box.id for box in result.phases]
        lanes = [box.id for box in result.lanes]

        keys = [
            (phases.index(card.phase), lanes.index(card.lane), card.y)
            for card in result.cards
        ]
        self.assertEqual(keys, sorted(keys))

    def test_nodes_without_rows_are_skipped_not_fatal(self) -> None:
        snapshot = _snapshot((_node("WI-A", None, "one"), _node("WI-B", "WS-A", "one")))

        result = layout.DEFAULT_LAYOUT.layout(snapshot)

        self.assertEqual([card.id for card in result.cards], ["WI-B"])

    def test_layout_is_deterministic_and_named(self) -> None:
        first = layout.DEFAULT_LAYOUT.layout(_example())
        self.assertEqual(first, layout.DEFAULT_LAYOUT.layout(_example()))
        self.assertEqual(first.name, "layered-grid")

    def test_another_layout_replaces_the_default_without_renderer_changes(self) -> None:
        class Stacked:
            name = "stacked"

            def layout(self, snapshot: DependencyMapSnapshot) -> layout.LayoutResult:
                cards = tuple(
                    layout.Card(
                        id=node.id,
                        lane="WS-A",
                        phase="one",
                        x=0,
                        y=i * 100,
                        width=200,
                        height=90,
                    )
                    for i, node in enumerate(
                        n for n in snapshot.nodes if not n.offscreen
                    )
                )
                return layout.LayoutResult(
                    name=self.name,
                    width=200,
                    height=500,
                    lanes=(),
                    phases=(),
                    cards=cards,
                    lines=(),
                )

        page = render.render_view(
            _example(),
            Stacked(),
            tab="map",
            item=None,
            since=None,
            full_page_href=lambda item_id: item_id,
        )

        self.assertIn("Layout: stacked.", page)


class RenderTest(unittest.TestCase):
    def test_cards_carry_id_title_state_text_and_why(self) -> None:
        page = _view(_example())

        self.assertIn('<span class="lrh-mono lrh-card-id">WI-B</span>', page)
        self.assertIn("WI-B title", page)
        self.assertIn('<span aria-hidden="true">⧗</span> Waiting</span>', page)
        self.assertIn("Waiting on WI-A (proposed)", page)
        self.assertIn("Blocked: waiting on ops", page)
        self.assertIn("Not prompt-ready", page)
        self.assertIn("lrh-card--blocked", page)

    def test_every_state_has_a_label_and_icon_not_only_color(self) -> None:
        for state, (_key, glyph, label) in render.STATE_STYLES.items():
            with self.subTest(state=state):
                pill = render._pill(state)
                self.assertIn(label, pill)
                self.assertIn(glyph, pill)

    def test_lines_differ_by_style_and_have_a_legend(self) -> None:
        page = _view(_example())

        self.assertIn('class="lrh-line lrh-line--depends_on"', page)
        self.assertIn('class="lrh-line lrh-line--blocked_by"', page)
        self.assertIn("stroke-dasharray", render.MAP_STYLES)
        self.assertIn("Depends on", page)
        self.assertIn("Blocked by", page)

    def test_selection_highlights_upstream_downstream_and_fills_the_drawer(
        self,
    ) -> None:
        page = _view(_example(), item="WI-B")

        self.assertIn("lrh-card--selected", page)
        self.assertEqual(page.count("lrh-card--related"), 2)
        self.assertIn('<span class="lrh-role">Upstream</span>', page)
        self.assertIn('<span class="lrh-role">Downstream</span>', page)
        self.assertEqual(page.count("lrh-line--selected"), 2)
        drawer = page.split('<aside class="lrh-drawer"', 1)[1]
        for text in (
            "Structural state",
            "Lifecycle",
            "Prompt-ready",
            "Not derived: needs your approval",
            "WS-B title (workstream)",
            "Depends on WI-A (proposed)",
            "project/work_items/proposed/WI-B.md",
            "Not modeled yet",
            'href="/full/WI-B"',
        ):
            self.assertIn(text, drawer)

    def test_an_unknown_item_selects_nothing_and_says_so(self) -> None:
        page = _view(_example(), item="WI-NOPE")

        self.assertNotIn("lrh-drawer", page)
        self.assertNotIn("lrh-card--selected", page)
        self.assertIn("WI-NOPE is not in this view.", page)

    def test_blocked_cards_keep_their_dashed_border_when_highlighted(self) -> None:
        for rule in (".lrh-card--related {", ".lrh-card--selected {"):
            block = render.MAP_STYLES.split(rule, 1)[1].split("}", 1)[0]
            self.assertNotRegex(block, r"\bborder:")

    def test_table_lists_every_node_with_id_links(self) -> None:
        page = _view(_example(), tab="table")

        rows = re.findall(r'<tr><th scope="row">', page)
        self.assertEqual(len(rows), 5)
        self.assertIn('href="?tab=table&amp;item=WI-A"', page)
        self.assertIn("Outside this view", page)

    def test_blockers_lists_waiting_and_blocked_items_with_their_needs(self) -> None:
        page = _view(_example(), tab="blockers")

        self.assertIn("WI-B", page)
        self.assertIn("Needs", page)
        self.assertIn("Blocked: waiting on ops", page)
        self.assertNotIn(">WI-D<", page)

    def test_prompt_readiness_does_not_apply_to_closed_items(self) -> None:
        page = _view(_example(), item="WI-D") + _view(_example(), tab="table")

        self.assertIn("Not applicable (closed)", page)

    def test_needs_come_from_edges_not_only_the_winning_state(self) -> None:
        flagged = _node(
            "WI-F",
            "WS-A",
            "one",
            "blocked",
            reasons=(StateReason(kind="blocked_flag", detail="ops"),),
        )
        snapshot = _snapshot(
            (flagged, _node("WI-A", "WS-B", "one")), (_edge("WI-F", "WI-A"),)
        )

        table = _view(snapshot, tab="table")
        blockers = _view(snapshot, tab="blockers")

        row = table.split('href="?tab=table&amp;item=WI-F"', 1)[1].split("</tr>", 1)[0]
        self.assertIn("WI-A", row)
        self.assertIn("Blocked: ops", blockers)
        self.assertIn('href="?tab=blockers&amp;item=WI-A"', blockers)

    def test_drawer_offers_the_map_from_other_tabs(self) -> None:
        self.assertIn("Show on map", _view(_example(), tab="table", item="WI-B"))
        self.assertNotIn("Show on map", _view(_example(), item="WI-B"))

    def test_the_narrow_list_keeps_flags_counts_and_empty_state(self) -> None:
        outside = dataclasses.replace(
            _node("WI-B", "WS-A", "one", prompt_ready=False), offscreen_predecessors=2
        )
        listing = _view(_snapshot((outside,))).split('<section class="lrh-map-list"')[1]

        self.assertIn("Not prompt-ready", listing)
        self.assertIn("+2 outside this view", listing)
        empty = _view(_snapshot(())).split('<section class="lrh-map-list"')[1]
        self.assertIn("This view has no items yet.", empty)

    def test_blockers_says_so_when_nothing_waits(self) -> None:
        page = _view(_snapshot((_node("WI-A", "WS-A", "one"),)), tab="blockers")

        self.assertIn("Nothing in this view is waiting or blocked.", page)

    def test_diagnostics_and_freshness_are_explicit(self) -> None:
        snapshot = _snapshot(
            (_node("WI-A", "WS-A", "one"),),
            diagnostics=(
                Diagnostic(code="cycle", severity="error", message="depends_on cycle"),
                Diagnostic(code="unplaced_phase", severity="info", message="quiet"),
            ),
        )

        page = _view(snapshot, since="sha256:other")
        fresh = _view(snapshot, since=snapshot.source_fingerprint)

        self.assertIn("depends_on cycle", page)
        self.assertNotIn("quiet", page, "info diagnostics stay out of the banner")
        self.assertIn("Sources changed.", page)
        self.assertIn("No changes since you last checked.", fresh)
        self.assertIn("since=sha256%3A" + "0" * 64, page)

    def test_an_empty_view_says_so(self) -> None:
        page = _view(_snapshot(()))

        self.assertIn("This view has no items yet.", page)

    def test_narrow_screens_get_a_focused_list(self) -> None:
        page = _view(_example())

        self.assertIn('<section class="lrh-map-list"', page)
        self.assertRegex(
            render.MAP_STYLES,
            r"@media \(max-width: 48rem\) \{\s*\.lrh-map-scroll, \.lrh-legend \{ "
            r"display: none; \}\s*\.lrh-map-list \{ display: block; \}",
        )

    def test_untrusted_text_is_escaped_and_there_are_no_scripts(self) -> None:
        hostile = '<script>alert("x")</script>'
        node = _node(
            "WI-A",
            "WS-A",
            "one",
            "blocked",
            title=hostile,
            reasons=(StateReason(kind="blocked_flag", detail=hostile),),
        )
        snapshot = _snapshot(
            (node,),
            diagnostics=(Diagnostic(code="cycle", severity="error", message=hostile),),
        )
        snapshot = dataclasses.replace(
            snapshot,
            view_title=hostile,
            view_source=hostile,
            lanes=(Row(id="WS-A", title=hostile), Row(id="WS-B", title="B")),
        )

        page = _view(snapshot, item="WI-A") + _view(snapshot, tab="blockers")

        self.assertNotIn("<script", page)
        self.assertIn("&lt;script&gt;", page)

    def test_styles_use_tokens_not_literal_colors(self) -> None:
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", render.MAP_STYLES))


if __name__ == "__main__":
    unittest.main()

"""Tests for the dependency-map layout and server-rendered views."""

from __future__ import annotations

import dataclasses
import datetime
import html
import json
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
    lifecycle: str = "proposed",
) -> Node:
    return Node(
        id=node_id,
        title=title or f"{node_id} title",
        lifecycle=lifecycle,
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
    chosen = options.pop("layout_override", layout.DEFAULT_LAYOUT)
    settings = {"tab": "map", "item": None, "since": None, **options}
    return render.render_view(
        snapshot,
        chosen,
        full_page_href=lambda item_id: f"/full/{item_id}",
        **settings,
    )


class LayeredGridLayoutTest(unittest.TestCase):
    def test_cards_sit_in_their_lane_and_phase_cells(self) -> None:
        result = layout.LayeredGridLayout().layout(_example())
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
        result = layout.LayeredGridLayout().layout(_example())
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

        (line,) = layout.LayeredGridLayout().layout(snapshot).lines

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

        cards = {
            card.id: card for card in layout.LayeredGridLayout().layout(snapshot).cards
        }

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
        result = layout.LayeredGridLayout().layout(snapshot)
        cards = {card.id: card for card in result.cards}

        for line in result.lines:
            with self.subTest(line=(line.source, line.item)):
                source, item = cards[line.source], cards[line.item]
                for (x1, y1), (x2, y2) in zip(line.points, line.points[1:]):
                    self.assertTrue(x1 == x2 or y1 == y2)
                self.assertIn(line.points[0][0], (source.x, source.x + source.width))
                self.assertIn(line.points[-1][0], (item.x, item.x + item.width))

    def test_cards_come_in_reading_order(self) -> None:
        result = layout.LayeredGridLayout().layout(_example())
        phases = [box.id for box in result.phases]
        lanes = [box.id for box in result.lanes]

        keys = [
            (phases.index(card.phase), lanes.index(card.lane), card.y)
            for card in result.cards
        ]
        self.assertEqual(keys, sorted(keys))

    def test_nodes_without_rows_are_skipped_not_fatal(self) -> None:
        snapshot = _snapshot((_node("WI-A", None, "one"), _node("WI-B", "WS-A", "one")))

        result = layout.LayeredGridLayout().layout(snapshot)

        self.assertEqual([card.id for card in result.cards], ["WI-B"])

    def test_layout_is_deterministic_and_named(self) -> None:
        first = layout.LayeredGridLayout().layout(_example())
        self.assertEqual(first, layout.LayeredGridLayout().layout(_example()))
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
        # The dashes are heavy and in the Blocked hue, so they show at any zoom.
        blocked = render.MAP_STYLES.split(".lrh-card--blocked {", 1)[1].split("}", 1)[0]
        for declaration in (
            "border-color: var(--lrh-color-status-blocked-line);",
            "border-style: dashed;",
            "border-width: 2px;",
        ):
            self.assertIn(declaration, blocked)

    def test_every_state_has_a_label_and_icon_not_only_color(self) -> None:
        for state, (_key, glyph, label) in render.STATE_STYLES.items():
            with self.subTest(state=state):
                pill = render._pill(state)
                self.assertIn(label, pill)
                self.assertIn(glyph, pill)

    def test_states_sharing_a_hue_differ_by_shape(self) -> None:
        # Q12: In progress and Unblocked are both blue; Abandoned and Unknown
        # share the neutral. Each pair must differ without color.
        for first, second in (("in_progress", "unblocked"), ("unknown", "abandoned")):
            with self.subTest(pair=(first, second)):
                self.assertNotEqual(
                    render.PILL_SHAPES.get(first, "filled"),
                    render.PILL_SHAPES.get(second, "filled"),
                )
        self.assertIn("lrh-pill--filled", render._pill("in_progress"))
        self.assertIn("lrh-pill--outlined", render._pill("unblocked"))
        outlined = render.MAP_STYLES.split(".lrh-pill--outlined {", 1)[1].split("}", 1)[
            0
        ]
        self.assertIn("background: transparent;", outlined)
        self.assertIn("box-shadow: inset 0 0 0 1px currentColor;", outlined)
        self.assertIn("lrh-pill--filled", render._pill("unknown"))
        self.assertIn(
            '<span class="lrh-pill-struck">Abandoned</span>', render._pill("abandoned")
        )
        for rule in (
            ".lrh-pill-struck { text-decoration: line-through; }",
            ".lrh-card--abandoned { background: var(--lrh-color-surface-sunken); }",
            ".lrh-card--abandoned .lrh-card-title { text-decoration: line-through; }",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, render.MAP_STYLES)

    def test_abandoned_cards_are_sunken_and_struck_without_a_new_border(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one", "abandoned", lifecycle="abandoned"),
                _node("WI-B", "WS-A", "one", "unknown", lifecycle="odd"),
            )
        )
        page = _view(snapshot)

        cards = {
            card_id: tag
            for tag, card_id in re.findall(
                r'(<a class="lrh-card[^"]*"[^>]*data-id="([^"]+)")', page
            )
        }
        self.assertIn("lrh-card--abandoned", cards["WI-A"])
        self.assertNotIn("lrh-card--abandoned", cards["WI-B"])
        self.assertNotIn("lrh-card--blocked", cards["WI-A"])
        # Dashed is the only border style, longhand or shorthand, so no card
        # resembles a blocked card's dashed edge.
        styles = "none|hidden|dotted|dashed|double|groove|ridge|inset|outset"
        borders = re.findall(
            rf"border(?:-[a-z]+)*:[^;]*\b({styles})\b", render.MAP_STYLES
        )
        self.assertEqual(set(borders), {"dashed"})
        # Outlined pills set no fill, so they never depend on rule order.
        self.assertNotIn("status-unblocked-bg", render.MAP_STYLES)
        self.assertIn("abandoned cards are sunken with a struck-through title", page)

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

        rows = re.findall(r'<tr data-id="[^"]+"[^>]*><th scope="row">', page)
        self.assertEqual(len(rows), 5)
        self.assertIn('href="?tab=table&amp;item=WI-A"', page)
        self.assertIn("Outside this view", page)

    def test_blockers_lists_waiting_and_blocked_items_with_their_needs(self) -> None:
        page = _view(_example(), tab="blockers")

        self.assertIn("WI-B", page)
        self.assertIn("Needs", page)
        self.assertIn("Blocked: waiting on ops", page)
        self.assertNotIn(">WI-D<", page)
        # Each entry names its item, so focus can return to it, but carries
        # no state: the Blockers tab has no filters.
        self.assertIn('<li data-id="WI-B"><a class="lrh-mono"', page)
        self.assertNotIn("data-state", page.split('<ul class="lrh-blockers">', 1)[1])

    def test_prompt_readiness_does_not_apply_to_closed_items(self) -> None:
        drawer = _view(_example(), item="WI-D").split('<aside class="lrh-drawer"')[1]
        table = _view(_example(), tab="table")
        row = table.split('href="?tab=table&amp;item=WI-D"', 1)[1].split("</tr>", 1)[0]

        self.assertIn("Not applicable (closed)", drawer)
        self.assertIn("Not applicable (closed)", row)

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
            r"@media \(max-width: 48rem\) \{\s*\.lrh-map-scroll, \.lrh-legend, "
            r"\.lrh-layout-toggle \{ "
            r"display: none; \}\s*\.lrh-map-list \{ display: block; \}",
        )

    def test_interactive_mode_prerenders_every_drawer_hidden(self) -> None:
        page = _view(_example(), item="WI-B", interactive=True)

        drawers = re.findall(r'<aside class="lrh-drawer"[^>]*>', page, flags=re.S)
        self.assertEqual(len(drawers), 5)
        hidden = [drawer for drawer in drawers if " hidden" in drawer]
        self.assertEqual(len(hidden), 4)
        self.assertIn(
            'data-drawer-for="WI-B"', next(d for d in drawers if d not in hidden)
        )
        ids = re.findall(r'<h2 id="(lrh-drawer-title-\d+)"', page)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("<script", page)

    def test_items_and_lines_carry_data_for_the_script(self) -> None:
        page = _view(_example())

        self.assertIn('<a class="lrh-card" href="?item=WI-B" data-id="WI-B"', page)
        self.assertNotIn("data-state", page)
        self.assertNotIn("data-unmet", page)
        self.assertIn('data-source="WI-A" data-item="WI-B"', page)
        self.assertIn('class="lrh-dependency-map" data-lrh-tab="map"', page)
        self.assertEqual(page.count("<aside"), 0)

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


def _card_ids(page: str) -> set[str]:
    return set(
        re.findall(r'<a class="lrh-card[^"]*" href="[^"]*" data-id="([^"]+)"', page)
    )


class FilterTest(unittest.TestCase):
    def test_parse_hide_keeps_known_states_only(self) -> None:
        self.assertEqual(render.parse_hide(None), frozenset())
        self.assertEqual(render.parse_hide(""), frozenset())
        self.assertEqual(
            render.parse_hide("done, abandoned,nope"), frozenset({"done", "abandoned"})
        )

    def test_hidden_cards_leave_the_map_table_and_list(self) -> None:
        page = _view(_example(), hide=frozenset({"done"}))
        table = _view(_example(), tab="table", hide=frozenset({"done"}))

        self.assertEqual(_card_ids(page), {"WI-A", "WI-B", "WI-C"})
        self.assertNotIn('<li data-id="WI-D">', page)
        self.assertNotIn('<tr data-id="WI-D">', table)
        self.assertIn('<tr data-id="WI-A">', table)
        self.assertIn("Hidden: 1 Done.", page)

    def test_empty_phases_and_lanes_collapse(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node(
                    "WI-D",
                    "WS-B",
                    "two",
                    "done",
                    reasons=(StateReason(kind="lifecycle", detail="resolved"),),
                ),
            )
        )
        full = layout.LayeredGridLayout().layout(snapshot)
        page = _view(snapshot, hide=frozenset({"done"}))

        self.assertEqual({box.id for box in full.phases}, {"one", "two"})
        self.assertNotIn("WS-B title", page)
        self.assertNotIn('<h3 class="lrh-phase-title">Two</h3>', page)
        self.assertIn('<h3 class="lrh-phase-title">One</h3>', page)
        width = int(re.search(r'<div class="lrh-map" style="width:(\d+)px', page)[1])
        self.assertLess(width, full.width)

    def test_an_unfinished_item_a_shown_item_needs_stays_visible(self) -> None:
        page = _view(_example(), hide=frozenset({"unblocked"}))

        self.assertIn("WI-A", _card_ids(page))
        self.assertIn("1 kept because a shown item needs it.", page)

    def test_needed_ids_with_spaces_stay_visible(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-NEEDS REVIEW", "WS-A", "one"),
                _node("WI-B", "WS-B", "two", "waiting", reasons=_WAIT),
            ),
            (_edge("WI-B", "WI-NEEDS REVIEW"),),
        )

        page = _view(snapshot, hide=frozenset({"unblocked"}))

        self.assertEqual(_card_ids(page), {"WI-NEEDS REVIEW", "WI-B"})

    def test_the_selection_always_stays_visible(self) -> None:
        page = _view(_example(), item="WI-D", hide=frozenset({"done"}))

        self.assertIn("WI-D", _card_ids(page))
        self.assertIn("Nothing hidden.", page)

    def test_links_keep_the_filter(self) -> None:
        page = _view(_example(), item="WI-B", hide=frozenset({"done", "abandoned"}))

        self.assertIn('href="?item=WI-A&amp;hide=done,abandoned"', page)
        self.assertIn('href="?tab=table&amp;item=WI-B&amp;hide=done,abandoned"', page)
        self.assertIn("hide=done,abandoned&amp;since=sha256", page)
        # Done is off, so its toggle turns it back on and keeps the rest.
        self.assertIn(
            '<a class="lrh-filter" href="?item=WI-B&amp;hide=abandoned"'
            ' data-filter-state="done" aria-label="Done: hidden. Show Done.">',
            page,
        )
        self.assertIn(
            '<a class="lrh-filter" href="?item=WI-B&amp;hide=done,blocked,abandoned"',
            page,
        )
        self.assertIn('<a href="?item=WI-B">Show all</a>', page)

    def test_filters_are_links_without_a_filter_applied(self) -> None:
        page = _view(_example())

        self.assertIn('<nav class="lrh-filters" aria-label="Filter by state">', page)
        self.assertIn(
            '<a class="lrh-filter" href="?hide=done" data-filter-state="done"'
            ' aria-label="Done: shown. Hide Done.">',
            page,
        )
        self.assertNotIn("lrh-filter-note", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<form", page)

    def test_hiding_everything_says_so(self) -> None:
        hide = frozenset(render.STATE_STYLES)
        page = _view(_example(), hide=hide)

        self.assertEqual(_card_ids(page), set())
        self.assertIn(render.ALL_HIDDEN, page)
        self.assertNotIn(render.EMPTY_VIEW, page)

    def test_blockers_tab_has_no_filters_but_keeps_them_in_links(self) -> None:
        page = _view(_example(), tab="blockers", hide=frozenset({"done"}))

        self.assertNotIn(
            "lrh-filters", page.split("</header>", 1)[1].split("<style", 1)[0]
        )
        self.assertIn('href="?tab=blockers&amp;item=WI-B&amp;hide=done"', page)

    def test_needs_stay_visible_through_several_levels(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node("WI-B", "WS-A", "two", "waiting", reasons=_WAIT),
                _node("WI-C", "WS-B", "two", "blocked"),
            ),
            (_edge("WI-B", "WI-A"), _edge("WI-C", "WI-B", "blocked_by")),
        )

        page = _view(snapshot, hide=frozenset({"waiting", "unblocked"}))

        self.assertEqual(_card_ids(page), {"WI-A", "WI-B", "WI-C"})
        self.assertIn("2 kept because a shown item needs them.", page)

    def test_lines_to_hidden_cards_are_dropped(self) -> None:
        done = _node(
            "WI-D",
            "WS-B",
            "one",
            "done",
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        snapshot = _snapshot(
            (_node("WI-A", "WS-A", "one"), done), (_edge("WI-A", "WI-D"),)
        )

        full = _view(snapshot)
        page = _view(snapshot, hide=frozenset({"done"}))

        self.assertIn('data-source="WI-D"', full)
        self.assertNotIn('data-source="WI-D"', page)
        self.assertEqual(_card_ids(page), {"WI-A"})

    def test_outside_rows_follow_the_filter_and_are_counted(self) -> None:
        table = _view(_example(), tab="table", hide=frozenset({"unblocked"}))
        shown = _view(_example(), tab="table", hide=frozenset({"done"}))

        self.assertNotIn('<tr data-id="WI-OUT">', table)
        self.assertIn("Hidden: 1 from outside the view.", table)
        self.assertIn('<tr data-id="WI-OUT">', shown)

    def test_outside_rows_are_counted_after_in_view_ones(self) -> None:
        snapshot = dataclasses.replace(
            _example(),
            nodes=_example().nodes
            + (
                _node(
                    "WI-OLD",
                    None,
                    None,
                    "done",
                    offscreen=True,
                    lifecycle="resolved",
                    reasons=(StateReason(kind="lifecycle", detail="resolved"),),
                ),
            ),
        )

        page = _view(snapshot, hide=frozenset({"done"}))

        self.assertIn("Hidden: 1 Done, plus 1 from outside the view.", page)

    def test_cards_say_how_much_upstream_the_filters_hide(self) -> None:
        done = _node(
            "WI-D",
            "WS-A",
            "one",
            "done",
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        snapshot = _snapshot(
            (done, _node("WI-A", "WS-A", "two"), _node("WI-B", "WS-B", "two")),
            (_edge("WI-A", "WI-D"), _edge("WI-B", "WI-D")),
        )

        page = _view(snapshot, item="WI-A", hide=frozenset({"done"}))
        plain = _view(snapshot, item="WI-A")

        # Siblings share a hidden prerequisite: no lines, but each card says so.
        self.assertNotIn("data-source=", page)
        self.assertEqual(page.count("+1 upstream hidden by filters"), 4)
        self.assertIn("<dt>Upstream</dt><dd>1 item (1 hidden by filters)</dd>", page)
        self.assertNotIn("hidden by filters", plain)

    def test_an_empty_view_is_not_blamed_on_the_filters(self) -> None:
        page = _view(_snapshot(()), hide=frozenset({"done"}))

        self.assertIn(render.EMPTY_VIEW, page)
        self.assertNotIn(render.ALL_HIDDEN, page)

    def test_rows_empty_before_filtering_stay(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node(
                    "WI-D",
                    "WS-A",
                    "two",
                    "done",
                    lifecycle="resolved",
                    reasons=(StateReason(kind="lifecycle", detail="resolved"),),
                ),
            )
        )

        page = _view(snapshot, hide=frozenset({"done"}))

        # WS-B held nothing before the filter, so it stays; phase Two held only
        # the hidden card, so it goes.
        self.assertIn("WS-B title", page)
        self.assertNotIn('<h3 class="lrh-phase-title">Two</h3>', page)

    def test_tracing_data_crosses_hidden_items(self) -> None:
        done = _node(
            "WI-D",
            "WS-A",
            "two",
            "done",
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        snapshot = _snapshot(
            (_node("WI-A", "WS-A", "one"), done, _node("WI-C", "WS-B", "two")),
            (_edge("WI-D", "WI-A"), _edge("WI-C", "WI-D")),
        )

        page = _view(snapshot, item="WI-A", hide=frozenset({"done"}))

        self.assertEqual(_card_ids(page), {"WI-A", "WI-C"})
        self.assertNotIn("data-source=", page)
        # The script traces from the full graph, so clicking WI-A still
        # reaches WI-C, as the server's own ?item= tracing does.
        edges = re.search(r'<div class="lrh-map"[^>]*data-edges="([^"]*)"', page, re.S)
        self.assertEqual(
            json.loads(html.unescape(edges[1])), [["WI-A", "WI-D"], ["WI-D", "WI-C"]]
        )
        self.assertIn("lrh-card--related", page.split('data-id="WI-C"', 1)[0][-200:])

    def test_hidden_upstream_counts_every_depth(self) -> None:
        done = _node(
            "WI-C",
            "WS-B",
            "one",
            "done",
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        snapshot = _snapshot(
            (done, _node("WI-B", "WS-A", "one"), _node("WI-A", "WS-A", "two")),
            (_edge("WI-B", "WI-C"), _edge("WI-A", "WI-B")),
        )

        page = _view(snapshot, hide=frozenset({"done"}))
        cards = re.findall(
            r'<a class="lrh-card[^>]*data-id="([^"]+)".*?</a>', page, re.S
        )

        # WI-A reaches the hidden WI-C through the shown WI-B.
        self.assertEqual(cards, ["WI-B", "WI-A"])
        for card in re.findall(r'<a class="lrh-card.*?</a>', page, re.S):
            self.assertIn("+1 upstream hidden by filters", card)

    def test_hidden_items_outside_the_view_are_not_counted_twice(self) -> None:
        outside = _node(
            "WI-OLD",
            None,
            None,
            "done",
            offscreen=True,
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        shown = dataclasses.replace(
            _node("WI-A", "WS-A", "one"), offscreen_predecessors=1
        )
        snapshot = _snapshot((shown, outside), (_edge("WI-A", "WI-OLD"),))

        page = _view(snapshot, item="WI-A", hide=frozenset({"done"}))

        self.assertIn("+1 outside this view", page)
        self.assertNotIn("upstream hidden by filters", page)
        # The drawer's total includes the outside item, so its hidden part does.
        self.assertIn("<dt>Upstream</dt><dd>1 item (1 hidden by filters)</dd>", page)

    def test_a_selected_item_in_a_hidden_state_is_not_counted(self) -> None:
        done = _node(
            "WI-D",
            "WS-A",
            "one",
            "done",
            lifecycle="resolved",
            reasons=(StateReason(kind="lifecycle", detail="resolved"),),
        )
        snapshot = _snapshot(
            (done, _node("WI-A", "WS-A", "two")), (_edge("WI-A", "WI-D"),)
        )

        page = _view(snapshot, item="WI-D", hide=frozenset({"done"}), interactive=True)

        self.assertEqual(_card_ids(page), {"WI-D", "WI-A"})
        self.assertNotIn("hidden by filters", page)

    def test_the_drawer_counts_hidden_downstream_items(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node("WI-B", "WS-B", "two", "waiting", reasons=_WAIT),
            ),
            (_edge("WI-B", "WI-A"),),
        )

        page = _view(snapshot, item="WI-A", hide=frozenset({"waiting"}))

        self.assertEqual(_card_ids(page), {"WI-A"})
        self.assertIn("<dt>Downstream</dt><dd>1 item (1 hidden by filters)</dd>", page)


def _chain(*ids: str, lane: str = "WS-A", phase: str = "one") -> DependencyMapSnapshot:
    """A chain in one cell: each item depends on the one before it."""

    nodes = tuple(_node(node_id, lane, phase) for node_id in ids)
    edges = tuple(_edge(later, earlier) for earlier, later in zip(ids, ids[1:]))
    return _snapshot(nodes, edges)


class OutlineLayoutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.outline = layout.OutlineLayout()

    def test_a_chain_is_ordered_and_indented_by_depth(self) -> None:
        # IDs out of dependency order, to prove the order is not by ID.
        result = self.outline.layout(_chain("WI-C", "WI-A", "WI-B"))
        cards = list(result.cards)

        self.assertEqual([card.id for card in cards], ["WI-C", "WI-A", "WI-B"])
        self.assertEqual(
            [card.x - cards[0].x for card in cards],
            [0, layout.OUTLINE_INDENT, 2 * layout.OUTLINE_INDENT],
        )
        # Cards keep their full width; the lane widens instead.
        self.assertEqual({card.width for card in cards}, {layout.CARD_WIDTH})
        (lane,) = [box for box in result.lanes if box.id == "WS-A"]
        self.assertEqual(
            lane.width,
            layout.CARD_WIDTH
            + 2 * layout.CELL_PADDING
            + layout.OUTLINE_RAIL
            + 2 * layout.OUTLINE_INDENT,
        )
        self.assertEqual(result.name, "outline")

    def test_a_dependent_sits_just_under_what_it_needs(self) -> None:
        snapshot = _snapshot(
            (
                _node("WI-A", "WS-A", "one"),
                _node("WI-B", "WS-A", "one"),
                _node("WI-C", "WS-A", "one"),
            ),
            (_edge("WI-C", "WI-A"),),
        )

        cards = self.outline.layout(snapshot).cards

        self.assertEqual([card.id for card in cards], ["WI-A", "WI-C", "WI-B"])

    def test_indentation_is_capped(self) -> None:
        ids = tuple(f"WI-{index}" for index in range(layout.OUTLINE_MAX_DEPTH + 3))
        cards = self.outline.layout(_chain(*ids)).cards

        indents = [card.x - cards[0].x for card in cards]
        cap = layout.OUTLINE_MAX_DEPTH * layout.OUTLINE_INDENT
        self.assertEqual(max(indents), cap)
        self.assertEqual(indents[-3:], [cap, cap, cap])

    def test_a_cycle_falls_back_to_a_stable_order(self) -> None:
        snapshot = _snapshot(
            tuple(
                _node(node_id, "WS-A", "one") for node_id in ("WI-C", "WI-A", "WI-B")
            ),
            (_edge("WI-A", "WI-C"), _edge("WI-B", "WI-A"), _edge("WI-C", "WI-B")),
        )

        first = self.outline.layout(snapshot)
        second = self.outline.layout(snapshot)

        self.assertEqual({card.id for card in first.cards}, {"WI-A", "WI-B", "WI-C"})
        self.assertEqual(first, second)

    def test_lines_inside_a_cell_run_down_the_rail_clear_of_cards(self) -> None:
        result = self.outline.layout(_chain("WI-A", "WI-B", "WI-C"))
        left = min(card.x for card in result.cards)

        self.assertEqual(len(result.lines), 2)
        for line in result.lines:
            rail_x = line.points[1][0]
            self.assertLess(rail_x, left)
            self.assertEqual(line.points[1][0], line.points[2][0])

    def test_lines_between_cells_and_offscreen_items_as_in_the_grid(self) -> None:
        result = self.outline.layout(_example())
        cards = {card.id: card for card in result.cards}

        self.assertNotIn("WI-OUT", cards)
        self.assertEqual({card.lane for card in result.cards}, {"WS-A", "WS-B"})
        line = next(line for line in result.lines if line.item == "WI-B")
        # From WI-A's right edge in one lane to WI-B's left edge in the next.
        self.assertEqual(line.points[0][0], cards["WI-A"].x + cards["WI-A"].width)
        self.assertEqual(line.points[-1][0], cards["WI-B"].x)

    def test_unknown_layout_names_fall_back_to_the_default(self) -> None:
        self.assertIs(layout.layout_named(None), layout.DEFAULT_LAYOUT)
        self.assertIs(layout.layout_named("nope"), layout.DEFAULT_LAYOUT)
        self.assertEqual(layout.layout_named("outline").name, "outline")

    def test_lines_never_cross_other_cards(self) -> None:
        def crossings(result: layout.LayoutResult) -> list[tuple[str, str]]:
            found = []
            for line in result.lines:
                for (x1, y1), (x2, y2) in zip(line.points, line.points[1:]):
                    for card in result.cards:
                        if card.id in (line.source, line.item):
                            continue
                        left, right = sorted((x1, x2))
                        top, bottom = sorted((y1, y2))
                        if (
                            left < card.x + card.width
                            and right > card.x
                            and top < card.y + card.height
                            and bottom > card.y
                        ):
                            found.append((line.item, card.id))
            return found

        # A deep source exits left; a deep item is entered two lanes away.
        nodes = (
            _node("WI-S", "WS-A", "one"),
            _node("WI-P0", "WS-C", "two"),
            _node("WI-P1", "WS-C", "two"),
            _node("WI-P2", "WS-C", "two"),
            _node("WI-Q", "WS-C", "two"),
            _node("WI-X0", "WS-B", "one"),
            _node("WI-X1", "WS-B", "one"),
            _node("WI-X2", "WS-B", "one"),
            _node("WI-X3", "WS-B", "one"),
            _node("WI-Y", "WS-A", "two"),
        )
        edges = (
            _edge("WI-P1", "WI-P0"),
            _edge("WI-P2", "WI-P1"),
            _edge("WI-P2", "WI-S"),
            _edge("WI-X1", "WI-X0"),
            _edge("WI-X2", "WI-X1"),
            _edge("WI-X3", "WI-X2"),
            _edge("WI-Y", "WI-X3"),
            # A shallow card leaving a lane widened by deeper cards.
            _edge("WI-Q", "WI-X0"),
        )
        snapshot = _snapshot(nodes, edges, lanes=("WS-A", "WS-B", "WS-C"))

        self.assertEqual(crossings(self.outline.layout(snapshot)), [])
        self.assertEqual(crossings(self.outline.layout(_example())), [])

    def test_a_cycle_only_reorders_its_own_edges(self) -> None:
        # WI-A and WI-B form a cycle; WI-AA needs WI-A and must still follow it.
        snapshot = _snapshot(
            tuple(
                _node(node_id, "WS-A", "one")
                for node_id in ("WI-R", "WI-A", "WI-AA", "WI-B")
            ),
            (
                _edge("WI-A", "WI-R"),
                _edge("WI-A", "WI-B"),
                _edge("WI-B", "WI-A"),
                _edge("WI-AA", "WI-A"),
            ),
        )

        order = [card.id for card in self.outline.layout(snapshot).cards]

        self.assertLess(order.index("WI-R"), order.index("WI-A"))
        self.assertLess(order.index("WI-A"), order.index("WI-AA"))

    def test_a_cycle_is_broken_at_a_card_on_the_cycle(self) -> None:
        # WI-X and WI-Y form a cycle; WI-A sorts first but only depends on it.
        snapshot = _snapshot(
            tuple(
                _node(node_id, "WS-A", "one") for node_id in ("WI-A", "WI-X", "WI-Y")
            ),
            (
                _edge("WI-X", "WI-Y"),
                _edge("WI-Y", "WI-X"),
                _edge("WI-A", "WI-X"),
            ),
        )

        order = [card.id for card in self.outline.layout(snapshot).cards]

        self.assertLess(order.index("WI-X"), order.index("WI-A"))

    def test_a_cycle_that_needs_another_stays_below_it(self) -> None:
        # Two cycles, WI-A/WI-B and WI-C/WI-D; WI-A needs WI-C.
        snapshot = _snapshot(
            tuple(
                _node(node_id, "WS-A", "one")
                for node_id in ("WI-A", "WI-B", "WI-C", "WI-D")
            ),
            (
                _edge("WI-A", "WI-B"),
                _edge("WI-B", "WI-A"),
                _edge("WI-C", "WI-D"),
                _edge("WI-D", "WI-C"),
                _edge("WI-A", "WI-C"),
            ),
        )

        order = [card.id for card in self.outline.layout(snapshot).cards]

        self.assertLess(order.index("WI-C"), order.index("WI-A"))
        self.assertLess(order.index("WI-D"), order.index("WI-A"))

    def test_the_cycle_diagnostic_stays_visible_in_the_outline(self) -> None:
        diagnostic = Diagnostic(
            code="cycle", severity="error", message="depends_on cycle among WI-A, WI-B"
        )
        snapshot = _snapshot(
            (_node("WI-A", "WS-A", "one"), _node("WI-B", "WS-A", "one")),
            (_edge("WI-A", "WI-B"), _edge("WI-B", "WI-A")),
            diagnostics=(diagnostic,),
        )

        page = _view(snapshot, layout_override=layout.OutlineLayout())

        self.assertIn("depends_on cycle among WI-A, WI-B", page)
        self.assertIn("Layout: outline.", page)


class LayoutToggleTest(unittest.TestCase):
    def test_outline_is_the_default(self) -> None:
        self.assertEqual(layout.DEFAULT_LAYOUT.name, "outline")
        self.assertIn("Layout: outline.", _view(_example()))

    def test_links_keep_the_layout_and_the_toggle_switches_it(self) -> None:
        page = _view(
            _example(),
            item="WI-B",
            hide=frozenset({"done"}),
            layout_override=layout.LayeredGridLayout(),
        )

        self.assertIn("Layout: layered-grid.", page)
        self.assertIn('<nav class="lrh-layout-toggle" aria-label="Map layout">', page)
        self.assertIn('<span aria-current="true">Grid</span>', page)
        self.assertIn('<a href="?item=WI-B&amp;hide=done">Outline</a>', page)
        self.assertIn('href="?item=WI-A&amp;hide=done&amp;layout=layered-grid"', page)
        self.assertIn(
            'href="?tab=table&amp;item=WI-B&amp;hide=done&amp;layout=layered-grid"',
            page,
        )
        self.assertIn("layout=layered-grid&amp;since=sha256", page)
        self.assertIn('<a href="?item=WI-B&amp;layout=layered-grid">Show all</a>', page)

    def test_the_default_layout_adds_nothing_to_links(self) -> None:
        page = _view(_example(), item="WI-B")

        self.assertNotIn("layout=outline", page)
        self.assertIn('<span aria-current="true">Outline</span>', page)
        self.assertIn('<a href="?item=WI-B&amp;layout=layered-grid">Grid</a>', page)

    def test_the_toggle_sits_with_the_filters(self) -> None:
        page = _view(_example())

        self.assertLess(
            page.index('class="lrh-filters"'), page.index("lrh-layout-toggle")
        )
        self.assertLess(page.index("lrh-layout-toggle"), page.index('lrh-legend"'))

    def test_other_tabs_have_no_toggle(self) -> None:
        page = _view(_example(), tab="table", layout_override=layout.OutlineLayout())

        self.assertNotIn("lrh-layout-toggle", page.split("<style", 1)[0])


if __name__ == "__main__":
    unittest.main()

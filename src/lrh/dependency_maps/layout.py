"""Layouts: a ``DependencyMapSnapshot`` in, positioned cards and routed lines out.

A layout is reached only through the ``Layout`` interface, so the renderer
never depends on how positions are chosen and another implementation (a
curved router, or a library) can replace the default.

``LayeredGridLayout`` follows Revision 2 (Q7): the view's lane and
phase grid fixes each card's cell, so it chooses only the order of cards
within a cell (barycenter sweeps, the standard crossing-reduction step of a
layered layout) and right-angled line routes through the gaps between lanes
and phases. No layout library fits a fixed grid without Node or a native
binary; see the evaluation recorded in PR for WI-LRH-CONSOLE-MAP-STATIC.

``OutlineLayout``, the default, keeps the same lane columns and phase rows, but
lists each cell's cards in dependency order (a prerequisite above what needs it) and
indents each card by its dependency depth within the cell. Lines inside a cell
run down a rail at the cell's left edge; lines between cells route through the
gaps as in the grid. Pages choose a layout by name (``?layout=layered-grid``).

Lines run from the prerequisite (or blocker) to the item that needs it.
Offscreen items are not placed; cards count them instead.
"""

from __future__ import annotations

import dataclasses
from typing import Protocol

from lrh.dependency_maps.snapshot import UNPLACED, DependencyMapSnapshot

CARD_WIDTH = 264
CARD_HEIGHT = 144
CARD_GAP = 14
CELL_PADDING = 16
LANE_GUTTER = 56
PHASE_GUTTER = 40
HEADER_HEIGHT = 44
LABEL_WIDTH = 132
_SWEEPS = 4
_TRACK_SPACING = 6
_TRACKS = 5
OUTLINE_INDENT = 24
OUTLINE_MAX_DEPTH = 4
OUTLINE_RAIL = 24
_RAIL_TRACK_SPACING = 4
_RAIL_TRACKS = 5


@dataclasses.dataclass(frozen=True)
class Box:
    id: str
    title: str
    x: int
    y: int
    width: int
    height: int


@dataclasses.dataclass(frozen=True)
class Card:
    id: str
    lane: str
    phase: str
    x: int
    y: int
    width: int
    height: int


@dataclasses.dataclass(frozen=True)
class Line:
    """A routed edge; ``source`` is the prerequisite, ``item`` needs it."""

    kind: str
    source: str
    item: str
    points: tuple[tuple[int, int], ...]


@dataclasses.dataclass(frozen=True)
class LayoutResult:
    name: str
    width: int
    height: int
    lanes: tuple[Box, ...]
    phases: tuple[Box, ...]
    cards: tuple[Card, ...]
    lines: tuple[Line, ...]


class Layout(Protocol):
    """Turns a snapshot into positions; the renderer depends only on this."""

    name: str

    def layout(self, snapshot: DependencyMapSnapshot) -> LayoutResult: ...


class LayeredGridLayout:
    """Fixed lane and phase cells, ordered cards, right angles."""

    name = "layered-grid"

    def layout(self, snapshot: DependencyMapSnapshot) -> LayoutResult:
        lane_ids = [row.id for row in snapshot.lanes]
        known_phases = {row.id for row in snapshot.phases}
        # Only nodes whose lane and phase rows exist can be placed; the
        # snapshot builder guarantees this, so others are skipped, not fatal.
        placed = [
            node
            for node in snapshot.nodes
            if not node.offscreen
            and (node.lane or UNPLACED) in lane_ids
            and (node.phase or UNPLACED) in known_phases
        ]
        phase_ids = [
            row.id
            for row in snapshot.phases
            if row.id != UNPLACED or any(node.phase == UNPLACED for node in placed)
        ]
        cell_of = {
            node.id: (node.lane or UNPLACED, node.phase or UNPLACED) for node in placed
        }
        neighbours: dict[str, set[str]] = {node.id: set() for node in placed}
        for edge in snapshot.edges:
            if edge.item in neighbours and edge.target in neighbours:
                neighbours[edge.item].add(edge.target)
                neighbours[edge.target].add(edge.item)

        cells: dict[tuple[str, str], list[str]] = {}
        for node_id in sorted(cell_of):
            cells.setdefault(cell_of[node_id], []).append(node_id)
        _order_cells(cells, lane_ids, phase_ids, neighbours)

        heights = {
            phase: max([len(cells.get((lane, phase), [])) for lane in lane_ids] + [1])
            for phase in phase_ids
        }
        column_x = {}
        x = LABEL_WIDTH + LANE_GUTTER
        for lane in lane_ids:
            column_x[lane] = x
            x += CARD_WIDTH + 2 * CELL_PADDING + LANE_GUTTER
        width = x
        row_y = {}
        y = HEADER_HEIGHT + PHASE_GUTTER
        for phase in phase_ids:
            row_y[phase] = y
            y += _row_height(heights[phase]) + PHASE_GUTTER
        height = y

        cards: dict[str, Card] = {}
        for (lane, phase), members in cells.items():
            for index, node_id in enumerate(members):
                cards[node_id] = Card(
                    id=node_id,
                    lane=lane,
                    phase=phase,
                    x=column_x[lane] + CELL_PADDING,
                    y=row_y[phase] + CELL_PADDING + index * (CARD_HEIGHT + CARD_GAP),
                    width=CARD_WIDTH,
                    height=CARD_HEIGHT,
                )

        lanes = tuple(
            Box(
                id=row.id,
                title=row.title,
                x=column_x[row.id],
                y=0,
                width=CARD_WIDTH + 2 * CELL_PADDING,
                height=height,
            )
            for row in snapshot.lanes
        )
        titles = {row.id: row.title for row in snapshot.phases}
        phases = tuple(
            Box(
                id=phase,
                title=titles[phase],
                x=0,
                y=row_y[phase],
                width=width,
                height=_row_height(heights[phase]),
            )
            for phase in phase_ids
        )
        lines = _route(snapshot, cards, lane_ids, phase_ids, row_y)
        return LayoutResult(
            name=self.name,
            width=width,
            height=height,
            lanes=lanes,
            phases=phases,
            # Reading order: phase, then lane, then top to bottom, so keyboard
            # focus follows the grid.
            cards=tuple(
                sorted(
                    cards.values(),
                    key=lambda card: (
                        phase_ids.index(card.phase),
                        lane_ids.index(card.lane),
                        card.y,
                    ),
                )
            ),
            lines=lines,
        )


class OutlineLayout:
    """Lane columns and phase rows as in the grid, but each cell is an
    outline: cards in dependency order, indented by depth within the cell.

    Cards keep their full width; a lane widens by the deepest indent it
    uses, capped at ``OUTLINE_MAX_DEPTH`` levels, and deeper items keep the
    deepest indent. A cycle cannot be ordered, so it is broken at a stable
    point (see ``_outline_order``) and the snapshot's cycle diagnostic stays
    visible. This is the default layout.
    """

    name = "outline"

    def layout(self, snapshot: DependencyMapSnapshot) -> LayoutResult:
        lane_ids = [row.id for row in snapshot.lanes]
        known_phases = {row.id for row in snapshot.phases}
        placed = [
            node
            for node in snapshot.nodes
            if not node.offscreen
            and (node.lane or UNPLACED) in lane_ids
            and (node.phase or UNPLACED) in known_phases
        ]
        phase_ids = [
            row.id
            for row in snapshot.phases
            if row.id != UNPLACED or any(node.phase == UNPLACED for node in placed)
        ]
        cell_of = {
            node.id: (node.lane or UNPLACED, node.phase or UNPLACED) for node in placed
        }
        cells: dict[tuple[str, str], list[str]] = {}
        for node_id in sorted(cell_of):
            cells.setdefault(cell_of[node_id], []).append(node_id)
        depth: dict[str, int] = {}
        for key, members in cells.items():
            cells[key], cell_depth = _outline_order(members, snapshot)
            depth.update(cell_depth)

        heights = {
            phase: max([len(cells.get((lane, phase), [])) for lane in lane_ids] + [1])
            for phase in phase_ids
        }
        # Cards keep their full width; a lane widens by the deepest indent it
        # uses (at most OUTLINE_MAX_DEPTH levels) instead.
        indent_of = {
            node_id: min(depth[node_id], OUTLINE_MAX_DEPTH) * OUTLINE_INDENT
            for node_id in cell_of
        }
        column_width = {
            lane: CARD_WIDTH
            + 2 * CELL_PADDING
            + OUTLINE_RAIL
            + max(
                [
                    indent_of[node_id]
                    for node_id in cell_of
                    if cell_of[node_id][0] == lane
                ]
                + [0]
            )
            for lane in lane_ids
        }
        column_x = {}
        x = LABEL_WIDTH + LANE_GUTTER
        for lane in lane_ids:
            column_x[lane] = x
            x += column_width[lane] + LANE_GUTTER
        width = x
        row_y = {}
        y = HEADER_HEIGHT + PHASE_GUTTER
        for phase in phase_ids:
            row_y[phase] = y
            y += _row_height(heights[phase]) + PHASE_GUTTER
        height = y

        cards: dict[str, Card] = {}
        for (lane, phase), members in cells.items():
            for index, node_id in enumerate(members):
                indent = indent_of[node_id]
                cards[node_id] = Card(
                    id=node_id,
                    lane=lane,
                    phase=phase,
                    x=column_x[lane] + CELL_PADDING + OUTLINE_RAIL + indent,
                    y=row_y[phase] + CELL_PADDING + index * (CARD_HEIGHT + CARD_GAP),
                    width=CARD_WIDTH,
                    height=CARD_HEIGHT,
                )

        lanes = tuple(
            Box(
                id=row.id,
                title=row.title,
                x=column_x[row.id],
                y=0,
                width=column_width[row.id],
                height=height,
            )
            for row in snapshot.lanes
        )
        titles = {row.id: row.title for row in snapshot.phases}
        phases = tuple(
            Box(
                id=phase,
                title=titles[phase],
                x=0,
                y=row_y[phase],
                width=width,
                height=_row_height(heights[phase]),
            )
            for phase in phase_ids
        )
        lines = _outline_route(
            snapshot, cards, lane_ids, phase_ids, row_y, column_x, column_width
        )
        return LayoutResult(
            name=self.name,
            width=width,
            height=height,
            lanes=lanes,
            phases=phases,
            cards=tuple(
                sorted(
                    cards.values(),
                    key=lambda card: (
                        phase_ids.index(card.phase),
                        lane_ids.index(card.lane),
                        card.y,
                    ),
                )
            ),
            lines=lines,
        )


# The owner chose the outline as the default after comparing both on real
# views (WI-LRH-CONSOLE-MAP-OUTLINE-LAYOUT); the grid stays one click away.
DEFAULT_LAYOUT: Layout = OutlineLayout()
LAYOUTS: dict[str, Layout] = {
    layout.name: layout for layout in (DEFAULT_LAYOUT, LayeredGridLayout())
}


def layout_named(name: str | None) -> Layout:
    """Return the layout called ``name``, or the default for an unknown or
    missing name, so a stale or hand-edited URL still renders."""

    return LAYOUTS.get(name or "", DEFAULT_LAYOUT)


def _outline_order(
    members: list[str], snapshot: DependencyMapSnapshot
) -> tuple[list[str], dict[str, int]]:
    """Order one cell's cards prerequisite-first, and give each its depth.

    Only edges inside the cell count. Among the cards whose prerequisites are
    all placed, the next one is a dependent of the most recently placed card
    when there is one, so an item sits just under what it needs, as in an
    outline; otherwise the shallowest, then the first by ID. When cycles
    leave nothing ready, the order is broken inside a cycle that needs no
    unplaced card outside itself (see ``_cycle_to_break``) and resumes, so
    only a cycle's own edges can point upward.
    """

    inside = set(members)
    needs: dict[str, set[str]] = {node_id: set() for node_id in members}
    for edge in snapshot.edges:
        if edge.item in inside and edge.target in inside and edge.item != edge.target:
            needs[edge.item].add(edge.target)
    order: list[str] = []
    depth: dict[str, int] = {}
    remaining = sorted(members)
    while remaining:
        ready = [node_id for node_id in remaining if needs[node_id] <= set(order)]
        if not ready:
            chosen = _cycle_to_break(remaining, needs)
            placed_needs = [depth[other] for other in needs[chosen] if other in depth]
            depth[chosen] = max(placed_needs, default=-1) + 1
            order.append(chosen)
            remaining.remove(chosen)
            continue
        chosen = None
        for previous in reversed(order):
            children = [node_id for node_id in ready if previous in needs[node_id]]
            if children:
                chosen = children[0]
                break
        if chosen is None:
            chosen = min(
                ready,
                key=lambda node_id: (
                    max((depth[other] for other in needs[node_id]), default=-1),
                    node_id,
                ),
            )
        depth[chosen] = max((depth[other] for other in needs[chosen]), default=-1) + 1
        order.append(chosen)
        remaining.remove(chosen)
    return order, depth


def _at_column_edges(
    card: Card, column_x: dict[str, int], column_width: dict[str, int]
) -> Card:
    """The card stretched across its column's content area, so routes built
    from its edges keep their gutters outside the column."""

    left = column_x[card.lane] + CELL_PADDING
    return dataclasses.replace(
        card, x=left, width=column_width[card.lane] - 2 * CELL_PADDING
    )


def _real_edge(
    x: int, card: Card, column_x: dict[str, int], column_width: dict[str, int]
) -> int:
    """Map a stretched card's left or right edge back to the real card's."""

    left = column_x[card.lane] + CELL_PADDING
    if x == left:
        return card.x
    if x == column_x[card.lane] + column_width[card.lane] - CELL_PADDING:
        return card.x + card.width
    return x


def _cycle_to_break(remaining: list[str], needs: dict[str, set[str]]) -> str:
    """Pick the card that breaks a stalled order: the first by ID that lies
    on a cycle and whose unplaced prerequisites all lie on that same cycle.

    When nothing is ready every unplaced card needs another, so the unplaced
    cards contain at least one cycle that needs nothing outside itself (a
    sink of their strongly connected components); breaking there never puts
    a card above an outside prerequisite. ``remaining`` is in ID order.
    """

    pool = set(remaining)

    def reach(start: str) -> set[str]:
        found: set[str] = set()
        stack = [other for other in needs[start] if other in pool]
        while stack:
            node_id = stack.pop()
            if node_id in found:
                continue
            found.add(node_id)
            stack.extend(other for other in needs[node_id] if other in pool)
        return found

    reachable = {node_id: reach(node_id) for node_id in remaining}
    for node_id in remaining:
        if node_id not in reachable[node_id]:
            continue
        own_cycle = {
            other for other in reachable[node_id] if node_id in reachable[other]
        }
        if reachable[node_id] <= own_cycle:
            return node_id
    raise AssertionError("a stalled order always contains a closed cycle")


def _outline_route(
    snapshot: DependencyMapSnapshot,
    cards: dict[str, Card],
    lane_ids: list[str],
    phase_ids: list[str],
    row_y: dict[str, int],
    column_x: dict[str, int],
    column_width: dict[str, int],
) -> tuple[Line, ...]:
    """Lines inside a cell run down the cell's left rail, which no card
    covers. Lines between cells use the grid's routes, computed as if every
    card spanned its column, so their gutters stay outside the column
    whatever the indent; the first and last steps then run along the card's
    own row to its real edge, where no other card sits."""

    lines = []
    tracks: dict[tuple[str, int], int] = {}
    rails: dict[tuple[str, str], int] = {}

    def track(channel: tuple[str, int]) -> int:
        count = tracks.get(channel, 0)
        tracks[channel] = count + 1
        return ((count % _TRACKS) - _TRACKS // 2) * _TRACK_SPACING

    for edge in snapshot.edges:
        source = cards.get(edge.target)
        item = cards.get(edge.item)
        if source is None or item is None:
            continue
        if (source.lane, source.phase) == (item.lane, item.phase):
            key = (source.lane, source.phase)
            count = rails.get(key, 0)
            rails[key] = count + 1
            rail_x = (
                column_x[source.lane]
                + CELL_PADDING
                + OUTLINE_RAIL // 2
                + ((count % _RAIL_TRACKS) - _RAIL_TRACKS // 2) * _RAIL_TRACK_SPACING
            )
            s_mid = source.y + source.height // 2
            i_mid = item.y + item.height // 2
            points = _simplify(
                [
                    (source.x, s_mid),
                    (rail_x, s_mid),
                    (rail_x, i_mid),
                    (item.x, i_mid),
                ]
            )
        else:
            points = list(
                _orthogonal(
                    _at_column_edges(source, column_x, column_width),
                    _at_column_edges(item, column_x, column_width),
                    lane_ids,
                    phase_ids,
                    row_y,
                    track,
                )
            )
            # Extend the end steps along each card's own row to its edge.
            points[0] = (
                _real_edge(points[0][0], source, column_x, column_width),
                points[0][1],
            )
            points[-1] = (
                _real_edge(points[-1][0], item, column_x, column_width),
                points[-1][1],
            )
        lines.append(
            Line(
                kind=edge.kind,
                source=source.id,
                item=item.id,
                points=tuple(points),
            )
        )
    return tuple(lines)


def _row_height(count: int) -> int:
    return 2 * CELL_PADDING + count * CARD_HEIGHT + (count - 1) * CARD_GAP


def _order_cells(
    cells: dict[tuple[str, str], list[str]],
    lane_ids: list[str],
    phase_ids: list[str],
    neighbours: dict[str, set[str]],
) -> None:
    """Reorder each cell by the mean row of its cards' neighbours.

    Cells are visited in phase-then-lane order and positions update as each
    cell is sorted, so connected cells settle instead of swapping back and
    forth between sweeps.
    """

    positions: dict[str, float] = {}

    def place(key: tuple[str, str]) -> None:
        base = phase_ids.index(key[1]) * 1000 if key[1] in phase_ids else 0
        for index, node_id in enumerate(cells[key]):
            positions[node_id] = base + index

    order = sorted(
        cells,
        key=lambda key: (
            phase_ids.index(key[1]) if key[1] in phase_ids else len(phase_ids),
            lane_ids.index(key[0]) if key[0] in lane_ids else len(lane_ids),
        ),
    )
    for key in order:
        place(key)

    def barycenter(node_id: str) -> tuple[float, str]:
        linked = [positions[other] for other in neighbours[node_id]]
        if not linked:
            return (positions[node_id], node_id)
        return (sum(linked) / len(linked), node_id)

    for _sweep in range(_SWEEPS):
        for key in order:
            cells[key] = sorted(cells[key], key=barycenter)
            place(key)


def _route(
    snapshot: DependencyMapSnapshot,
    cards: dict[str, Card],
    lane_ids: list[str],
    phase_ids: list[str],
    row_y: dict[str, int],
) -> tuple[Line, ...]:
    lines = []
    tracks: dict[tuple[str, int], int] = {}

    def track(channel: tuple[str, int]) -> int:
        count = tracks.get(channel, 0)
        tracks[channel] = count + 1
        return ((count % _TRACKS) - _TRACKS // 2) * _TRACK_SPACING

    for edge in snapshot.edges:
        source = cards.get(edge.target)
        item = cards.get(edge.item)
        if source is None or item is None:
            continue
        lines.append(
            Line(
                kind=edge.kind,
                source=source.id,
                item=item.id,
                points=_orthogonal(source, item, lane_ids, phase_ids, row_y, track),
            )
        )
    return tuple(lines)


def _orthogonal(source, item, lane_ids, phase_ids, row_y, track):
    """A right-angled route from ``source`` to ``item`` through the gutters."""

    s_col, i_col = lane_ids.index(source.lane), lane_ids.index(item.lane)
    s_mid = source.y + source.height // 2
    i_mid = item.y + item.height // 2
    if i_col >= s_col:
        start = (source.x + source.width, s_mid)
        out_x = source.x + source.width + CELL_PADDING + LANE_GUTTER // 2
    else:
        start = (source.x, s_mid)
        out_x = source.x - CELL_PADDING - LANE_GUTTER // 2
    out_x += track(("lane", s_col if i_col >= s_col else s_col - 1))
    if i_col > s_col or (i_col == s_col):
        end = (item.x if i_col > s_col else item.x + item.width, i_mid)
    else:
        end = (item.x + item.width, i_mid)
    if abs(i_col - s_col) <= 1:
        points = [start, (out_x, s_mid), (out_x, i_mid), end]
    else:
        phase_index = phase_ids.index(item.phase)
        channel_y = (
            row_y[item.phase] - PHASE_GUTTER // 2 + track(("phase", phase_index))
        )
        in_x = (
            item.x - CELL_PADDING - LANE_GUTTER // 2
            if i_col > s_col
            else (item.x + item.width + CELL_PADDING + LANE_GUTTER // 2)
        )
        points = [
            start,
            (out_x, s_mid),
            (out_x, channel_y),
            (in_x, channel_y),
            (in_x, i_mid),
            end,
        ]
    return tuple(_simplify(points))


def _simplify(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Drop repeated points and the middle of straight runs."""

    result: list[tuple[int, int]] = []
    for point in points:
        if result and result[-1] == point:
            continue
        if len(result) >= 2:
            (x1, y1), (x2, y2) = result[-2], result[-1]
            if (x1 == x2 == point[0]) or (y1 == y2 == point[1]):
                result[-1] = point
                continue
        result.append(point)
    return result

"""Layouts: a ``DependencyMapSnapshot`` in, positioned cards and routed lines out.

A layout is reached only through the ``Layout`` interface, so the renderer
never depends on how positions are chosen and another implementation (a
curved router, or a library) can replace the default.

The default ``LayeredGridLayout`` follows Revision 2 (Q7): the view's lane and
phase grid fixes each card's cell, so it chooses only the order of cards
within a cell (barycenter sweeps, the standard crossing-reduction step of a
layered layout) and right-angled line routes through the gaps between lanes
and phases. No layout library fits a fixed grid without Node or a native
binary; see the evaluation recorded in PR for WI-LRH-CONSOLE-MAP-STATIC.

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
    """The default: fixed lane and phase cells, ordered cards, right angles."""

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


DEFAULT_LAYOUT: Layout = LayeredGridLayout()


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

"""Server-rendered, script-free dependency-map pages.

``render_view`` turns a snapshot and a ``LayoutResult`` into the body of the
map, table, or blockers view. Cards are positioned HTML links over an SVG
line layer, so text wraps natively while lines stay exact. Selection is a URL
(``?item=<id>``): the server highlights the item's upstream and downstream
cards and lines and fills the detail drawer. Every state carries an icon and
text as well as a color, and lines differ by style as well as weight.
"""

from __future__ import annotations

import html
import urllib.parse

from lrh.dependency_maps.layout import Layout, LayoutResult
from lrh.dependency_maps.snapshot import (
    UNPLACED,
    DependencyMapSnapshot,
    Diagnostic,
    Node,
)

TABS = (("map", "Map"), ("table", "Table"), ("blockers", "Blockers"))

# State -> (token key, icon, label). Icons are text, hidden from assistive tech;
# the label always says the state.
STATE_STYLES = {
    "done": ("done", "✓", "Done"),
    "blocked": ("blocked", "✕", "Blocked"),
    "in_progress": ("progress", "▶", "In progress"),
    "waiting": ("waiting", "⧗", "Waiting"),
    "unblocked": ("unblocked", "○", "Unblocked"),
    "abandoned": ("unknown", "⊘", "Abandoned"),
    "unknown": ("unknown", "?", "Unknown"),
}
LINE_LABELS = {"depends_on": "Depends on", "blocked_by": "Blocked by"}


def render_view(
    snapshot: DependencyMapSnapshot,
    layout: Layout,
    *,
    tab: str,
    item: str | None,
    since: str | None,
    full_page_href,
) -> str:
    """Return the page body for one tab of a dependency-map view.

    ``full_page_href(item_id)`` gives the work item's own page.
    """

    nodes = {node.id: node for node in snapshot.nodes}
    selected = item if item in nodes else None
    upstream, downstream = _related(snapshot, selected)
    tab = tab if tab in dict(TABS) else "map"
    parts = [
        _header(snapshot, tab, selected, since),
        _diagnostics(snapshot.diagnostics),
    ]
    if tab == "table":
        parts.append(_table(snapshot, nodes))
    elif tab == "blockers":
        parts.append(_blockers(snapshot, nodes))
    else:
        result = layout.layout(snapshot)
        parts.append(_legend())
        parts.append(_map(snapshot, result, nodes, selected, upstream, downstream))
        parts.append(_focused_list(snapshot, nodes, selected))
    if selected:
        parts.append(
            _drawer(
                snapshot,
                nodes,
                nodes[selected],
                tab,
                upstream,
                downstream,
                full_page_href,
            )
        )
    return "\n".join(part for part in parts if part)


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _href(tab: str, item: str | None = None) -> str:
    query = {"tab": tab} if tab != "map" else {}
    if item:
        query["item"] = item
    encoded = urllib.parse.urlencode(query)
    return "?" + encoded if encoded else "?"


def _related(
    snapshot: DependencyMapSnapshot, selected: str | None
) -> tuple[set[str], set[str]]:
    """Return the selected item's transitive prerequisites and dependents."""

    if selected is None:
        return set(), set()
    needs: dict[str, set[str]] = {}
    needed_by: dict[str, set[str]] = {}
    for edge in snapshot.edges:
        if edge.resolved:
            needs.setdefault(edge.item, set()).add(edge.target)
            needed_by.setdefault(edge.target, set()).add(edge.item)

    def walk(start: str, graph: dict[str, set[str]]) -> set[str]:
        seen: set[str] = set()
        stack = [start]
        while stack:
            for other in graph.get(stack.pop(), ()):
                if other not in seen and other != start:
                    seen.add(other)
                    stack.append(other)
        return seen

    return walk(selected, needs), walk(selected, needed_by)


def _pill(state: str) -> str:
    key, glyph, label = STATE_STYLES.get(state, STATE_STYLES["unknown"])
    return (
        f'<span class="lrh-pill lrh-pill--{key}"><span aria-hidden="true">'
        f"{glyph}</span> {label}</span>"
    )


def _why(node: Node) -> str:
    """One line answering why a card has its state."""

    reasons = node.state_reasons
    if node.state == "blocked":
        reason = reasons[0]
        if reason.kind == "blocked_flag":
            return f"Blocked: {reason.detail or 'no reason given'}"
        return f"Blocked by {reason.target} ({reason.target_lifecycle})"
    if node.state == "waiting":
        first = reasons[0]
        more = f" and {len(reasons) - 1} more" if len(reasons) > 1 else ""
        return f"Waiting on {first.target} ({first.target_lifecycle}){more}"
    if node.state == "unblocked":
        if reasons and reasons[0].kind == "no_prerequisites":
            return "No prerequisites"
        return "All prerequisites done"
    if node.state == "in_progress":
        return "Active"
    if node.state == "unknown":
        return f"Unrecognized status: {node.lifecycle}"
    return node.lifecycle.capitalize()


def _not_prompt_ready(node: Node) -> str:
    if node.prompt_ready is False and node.state not in ("done", "abandoned"):
        return '<span class="lrh-flag">Not prompt-ready</span>'
    return ""


def _header(
    snapshot: DependencyMapSnapshot, tab: str, selected: str | None, since: str | None
) -> str:
    current = ' aria-current="page"'
    tabs = "".join(
        f'<a href="{html.escape(_href(key, selected), quote=True)}"'
        f'{current if key == tab else ""}>{label}</a>'
        for key, label in TABS
    )
    short = snapshot.source_fingerprint.removeprefix("sha256:")[:12]
    check = html.escape(
        "?"
        + urllib.parse.urlencode(
            {
                **({"tab": tab} if tab != "map" else {}),
                **({"item": selected} if selected else {}),
                "since": snapshot.source_fingerprint,
            }
        ),
        quote=True,
    )
    freshness = ""
    if since is not None:
        if since == snapshot.source_fingerprint:
            freshness = (
                '<p class="lrh-fresh-note" role="status">No changes since you last '
                "checked.</p>"
            )
        else:
            freshness = (
                '<p class="lrh-stale" role="status"><strong>Sources changed.</strong> '
                "The control files changed since the snapshot you were viewing; "
                "this page now shows the current state.</p>"
            )
    return f"""<header class="lrh-page-header lrh-map-header">
  <p class="lrh-eyebrow">Dependency map</p>
  <h1>{html.escape(snapshot.view_title)}</h1>
  <p class="lrh-muted">View <code>{html.escape(snapshot.view_id)}</code> from
  <code>{html.escape(snapshot.view_source)}</code>. Snapshot
  <code>{short}</code>, generated {html.escape(snapshot.generated_at)}.
  <a href="{check}">Check for changes</a></p>
  {freshness}
  <nav class="lrh-tabs" aria-label="Map views">{tabs}</nav>
</header>"""


def _diagnostics(diagnostics: tuple[Diagnostic, ...]) -> str:
    shown = [item for item in diagnostics if item.severity != "info"]
    if not shown:
        return ""
    items = "".join(
        f'<li><span class="lrh-severity lrh-severity--{item.severity}">'
        f"{item.severity.capitalize()}</span> <code>{html.escape(item.code)}</code> "
        f"{html.escape(item.message)}</li>"
        for item in shown
    )
    return (
        '<section class="lrh-console-region lrh-diagnostics" '
        'aria-labelledby="lrh-diagnostics-title">'
        '<h2 id="lrh-diagnostics-title">Diagnostics</h2>'
        f"<ul>{items}</ul></section>"
    )


def _legend() -> str:
    pills = "".join(_pill(state) for state in STATE_STYLES)
    return f"""<section class="lrh-legend" aria-label="Legend">
  <div class="lrh-legend-row">{pills}</div>
  <div class="lrh-legend-row">
    <svg width="48" height="12" aria-hidden="true"><line x1="2" y1="6" x2="46" y2="6"
      class="lrh-line lrh-line--depends_on"/></svg> Depends on
    <svg width="48" height="12" aria-hidden="true"><line x1="2" y1="6" x2="46" y2="6"
      class="lrh-line lrh-line--blocked_by"/></svg> Blocked by
    <span class="lrh-muted">Lines run from the prerequisite to the item that needs
    it. Phases are organizational rows, not gates.</span>
  </div>
</section>"""


def _map(
    snapshot: DependencyMapSnapshot,
    result: LayoutResult,
    nodes: dict[str, Node],
    selected: str | None,
    upstream: set[str],
    downstream: set[str],
) -> str:
    related = upstream | downstream | ({selected} if selected else set())
    lanes = "".join(
        f'<div class="lrh-lane" style="left:{box.x}px;width:{box.width}px;'
        f'height:{box.height}px"><h2 class="lrh-lane-title">'
        f"{html.escape(box.title)}</h2></div>"
        for box in result.lanes
    )
    phases = "".join(
        f'<div class="lrh-phase{" lrh-phase--unplaced" if box.id == UNPLACED else ""}"'
        f' style="top:{box.y}px;width:{box.width}px;height:{box.height}px">'
        f'<h3 class="lrh-phase-title">{html.escape(box.title)}</h3></div>'
        for box in result.phases
    )
    paths = []
    for line in result.lines:
        emphasis = (
            selected is not None and line.source in related and line.item in related
        )
        points = " ".join(f"{x},{y}" for x, y in line.points)
        classes = f"lrh-line lrh-line--{line.kind}"
        if emphasis:
            classes += " lrh-line--selected"
        marker = "lrh-arrow-selected" if emphasis else "lrh-arrow"
        label = (
            f"{line.item} {LINE_LABELS.get(line.kind, line.kind).lower()} {line.source}"
        )
        paths.append(
            f'<polyline class="{classes}" points="{points}" '
            f'marker-end="url(#{marker})"><title>{html.escape(label)}</title>'
            "</polyline>"
        )
    cards = []
    for card in result.cards:
        node = nodes[card.id]
        role = ""
        classes = "lrh-card"
        if card.id == selected:
            classes += " lrh-card--selected"
            role = '<span class="lrh-role">Selected</span>'
        elif card.id in upstream:
            classes += " lrh-card--related"
            role = '<span class="lrh-role">Upstream</span>'
        elif card.id in downstream:
            classes += " lrh-card--related"
            role = '<span class="lrh-role">Downstream</span>'
        if node.state == "blocked":
            classes += " lrh-card--blocked"
        outside = (
            f'<span class="lrh-outside">+{node.offscreen_predecessors} outside this '
            "view</span>"
            if node.offscreen_predecessors
            else ""
        )
        cards.append(
            f'<a class="{classes}" href="{_attr(_href("map", card.id))}"'
            f' title="{_attr(card.id + ": " + node.title)}"'
            f' style="left:{card.x}px;top:{card.y}px;width:{card.width}px;'
            f'height:{card.height}px">'
            f'<span class="lrh-card-top"><span class="lrh-mono lrh-card-id">'
            f"{html.escape(card.id)}</span>{role}</span>"
            f'<span class="lrh-card-title">{html.escape(node.title)}</span>'
            f'<span class="lrh-card-status">{_pill(node.state)}'
            f"{_not_prompt_ready(node)}</span>"
            f'<span class="lrh-card-why">{html.escape(_why(node))}{outside}</span></a>'
        )
    empty = (
        '<p class="lrh-muted">This view has no items yet. Add work items to its '
        "lanes or phases.</p>"
        if not result.cards
        else ""
    )
    return f"""<section class="lrh-map-scroll" aria-label="Dependency map">
{empty}<div class="lrh-map" style="width:{result.width}px;height:{result.height}px">
  {phases}{lanes}
  <svg class="lrh-lines" width="{result.width}" height="{result.height}"
       aria-hidden="true">
    <defs>
      <marker id="lrh-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7"
        markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8 z"
        class="lrh-arrowhead"/></marker>
      <marker id="lrh-arrow-selected" viewBox="0 0 8 8" refX="7" refY="4"
        markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8 z"
        class="lrh-arrowhead lrh-arrowhead--selected"/></marker>
    </defs>
    {"".join(paths)}
  </svg>
  {"".join(cards)}
</div>
<p class="lrh-muted lrh-map-meta">Layout: {html.escape(result.name)}.</p>
</section>"""


def _focused_list(
    snapshot: DependencyMapSnapshot, nodes: dict[str, Node], selected: str | None
) -> str:
    """The narrow-screen alternative to the map: cards grouped by phase."""

    groups = []
    for phase in snapshot.phases:
        members = [
            node
            for node in snapshot.nodes
            if not node.offscreen and node.phase == phase.id
        ]
        if not members:
            continue
        current = ' aria-current="true"'
        items = "".join(
            f'<li><a href="{html.escape(_href("map", node.id), quote=True)}"'
            f'{current if node.id == selected else ""}>'
            f'<span class="lrh-mono">{html.escape(node.id)}</span> '
            f"{html.escape(node.title)}</a> {_pill(node.state)}"
            f'<span class="lrh-card-why">{html.escape(_why(node))}</span></li>'
            for node in members
        )
        groups.append(f"<h3>{html.escape(phase.title)}</h3><ul>{items}</ul>")
    return (
        '<section class="lrh-map-list" aria-label="Dependency map as a list">'
        + "".join(groups)
        + "</section>"
    )


def _needs(node: Node) -> list[str]:
    return [reason.target for reason in node.state_reasons if reason.target]


def _table(snapshot: DependencyMapSnapshot, nodes: dict[str, Node]) -> str:
    needed_by: dict[str, list[str]] = {}
    for edge in snapshot.edges:
        needed_by.setdefault(edge.target, []).append(edge.item)
    rows = []
    for node in snapshot.nodes:
        unmet = [
            reason.target
            for reason in node.state_reasons
            if reason.target and reason.target_lifecycle != "resolved"
        ]
        ready = {True: "Yes", False: "No", None: "Unknown"}[node.prompt_ready]
        dependents = sorted(set(needed_by.get(node.id, [])))
        rows.append(
            "<tr>"
            f'<td><a class="lrh-id-link lrh-mono" '
            f'href="{html.escape(_href("table", node.id), quote=True)}">'
            f"{html.escape(node.id)}</a></td>"
            f"<td>{html.escape(node.title)}</td>"
            f"<td>{html.escape(_lane_label(snapshot, node))}</td>"
            f"<td>{html.escape(_phase_label(snapshot, node))}</td>"
            f"<td>{_pill(node.state)}</td>"
            f"<td>{html.escape(node.lifecycle)}</td>"
            f"<td>{ready}</td>"
            f"<td>{html.escape(', '.join(unmet)) or '—'}</td>"
            f"<td>{html.escape(', '.join(dependents)) or '—'}</td>"
            "</tr>"
        )
    return f"""<section class="lrh-console-region lrh-table-wrap">
<table class="lrh-map-table">
  <caption>Every item in this view, plus items it references from outside.</caption>
  <thead><tr><th scope="col">ID</th><th scope="col">Title</th>
  <th scope="col">Lane</th><th scope="col">Phase</th><th scope="col">State</th>
  <th scope="col">Lifecycle</th><th scope="col">Prompt-ready</th>
  <th scope="col">Unmet needs</th><th scope="col">Needed by</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
</section>"""


def _lane_label(snapshot: DependencyMapSnapshot, node: Node) -> str:
    if node.offscreen:
        return "Outside this view"
    titles = {row.id: row.title for row in snapshot.lanes}
    return titles.get(node.lane or UNPLACED, "Unplaced")


def _phase_label(snapshot: DependencyMapSnapshot, node: Node) -> str:
    if node.offscreen:
        return "Outside this view"
    titles = {row.id: row.title for row in snapshot.phases}
    return titles.get(node.phase or UNPLACED, "Unplaced")


def _blockers(snapshot: DependencyMapSnapshot, nodes: dict[str, Node]) -> str:
    stuck = [
        node
        for node in snapshot.nodes
        if node.state in ("blocked", "waiting") and not node.offscreen
    ]
    if not stuck:
        return (
            '<section class="lrh-console-region"><p>Nothing in this view is waiting '
            "or blocked.</p></section>"
        )
    items = []
    for node in stuck:
        needs = "".join(
            "<li>"
            + (
                f"Blocked: {html.escape(reason.detail or 'no reason given')}"
                if reason.kind == "blocked_flag"
                else (
                    f"{'Blocked by' if reason.kind == 'blocked_by' else 'Needs'} "
                    f'<a class="lrh-mono" href="'
                    f'{_attr(_href("blockers", reason.target or ""))}">'
                    f"{html.escape(reason.target or '')}</a> "
                    f"({html.escape(reason.target_lifecycle or '')})"
                )
            )
            + "</li>"
            for reason in node.state_reasons
        )
        items.append(
            f'<li><a class="lrh-mono" href="'
            f'{html.escape(_href("blockers", node.id), quote=True)}">'
            f"{html.escape(node.id)}</a> {html.escape(node.title)} {_pill(node.state)}"
            f"<ul>{needs}</ul></li>"
        )
    return (
        '<section class="lrh-console-region"><h2>Waiting and blocked</h2>'
        f'<ul class="lrh-blockers">{"".join(items)}</ul></section>'
    )


def _drawer(
    snapshot: DependencyMapSnapshot,
    nodes: dict[str, Node],
    node: Node,
    tab: str,
    upstream: set[str],
    downstream: set[str],
    full_page_href,
) -> str:
    needs = sorted({edge.target for edge in snapshot.edges if edge.item == node.id})
    needed_by = sorted({edge.item for edge in snapshot.edges if edge.target == node.id})

    def links(ids: list[str]) -> str:
        if not ids:
            return "None"
        return ", ".join(
            f'<a class="lrh-mono" href="{html.escape(_href(tab, other), quote=True)}">'
            f"{html.escape(other)}</a>"
            for other in ids
        )

    reasons = "".join(
        f"<li>{html.escape(_reason_text(reason))}</li>" for reason in node.state_reasons
    )
    ready = {True: "Yes", False: "No", None: "Unknown (readiness unavailable)"}[
        node.prompt_ready
    ]
    lane = _lane_label(snapshot, node)
    if node.lane_reason:
        lane += f" ({node.lane_source}: {node.lane_reason})"
    else:
        lane += f" ({node.lane_source})"
    close = html.escape(_href(tab), quote=True)
    full = html.escape(full_page_href(node.id), quote=True)
    return f"""<aside class="lrh-drawer" aria-labelledby="lrh-drawer-title">
  <header>
    <h2 id="lrh-drawer-title" class="lrh-mono">{html.escape(node.id)}</h2>
    <a class="lrh-iconbtn lrh-tip-end" href="{close}">✕
      <span class="lrh-tip">Close details</span></a>
  </header>
  <p>{html.escape(node.title)}</p>
  <dl class="lrh-drawer-facts">
    <dt>Structural state</dt><dd>{_pill(node.state)}</dd>
    <dt>Lifecycle</dt><dd>{html.escape(node.lifecycle)}</dd>
    <dt>Prompt-ready</dt><dd>{ready}</dd>
    <dt>Authorization</dt><dd>Not derived: needs your approval</dd>
    <dt>Lane</dt><dd>{html.escape(lane)}</dd>
    <dt>Phase</dt><dd>{html.escape(_phase_label(snapshot, node))}
      ({html.escape(node.phase_source)})</dd>
    <dt>Why</dt><dd><ul>{reasons}</ul></dd>
    <dt>Needs</dt><dd>{links(needs)}</dd>
    <dt>Needed by</dt><dd>{links(needed_by)}</dd>
    <dt>Upstream</dt><dd>{len(upstream)} items</dd>
    <dt>Downstream</dt><dd>{len(downstream)} items</dd>
    <dt>Source</dt><dd><code>{html.escape(node.source)}</code></dd>
    <dt>Effort</dt><dd>Not modeled yet</dd>
  </dl>
  <p><a href="{full}">Open the full page</a></p>
</aside>"""


def _reason_text(reason) -> str:
    if reason.kind == "blocked_flag":
        return f"Flagged blocked: {reason.detail or 'no reason given'}"
    if reason.kind == "no_prerequisites":
        return "No prerequisites"
    if reason.kind == "lifecycle":
        return f"Lifecycle is {reason.detail}"
    verb = "Blocked by" if reason.kind == "blocked_by" else "Depends on"
    return f"{verb} {reason.target} ({reason.target_lifecycle})"


MAP_STYLES = """
  .lrh-map-shell { max-width: none; }
  .lrh-tabs { display: flex; gap: var(--lrh-space-2); margin-top: var(--lrh-space-3); }
  .lrh-tabs a {
    border: 1px solid var(--lrh-color-border-strong);
    border-radius: var(--lrh-radius-pill);
    padding: var(--lrh-space-1) var(--lrh-space-3);
    text-decoration: none;
  }
  .lrh-tabs a[aria-current] {
    background: var(--lrh-color-action-accent);
    border-color: var(--lrh-color-action-accent);
    color: var(--lrh-color-action-on-accent);
  }
  .lrh-stale, .lrh-fresh-note {
    border-radius: var(--lrh-radius-sm);
    padding: var(--lrh-space-2) var(--lrh-space-3);
  }
  .lrh-stale {
    background: var(--lrh-color-status-waiting-bg);
    border-left: 4px solid var(--lrh-color-status-waiting-line);
    color: var(--lrh-color-status-waiting-fg);
  }
  .lrh-fresh-note { background: var(--lrh-color-surface-sunken); }
  .lrh-severity { font-weight: 700; }
  .lrh-severity--error { color: var(--lrh-color-status-blocked-fg); }
  .lrh-severity--warning { color: var(--lrh-color-status-waiting-fg); }
  .lrh-legend {
    align-items: center;
    display: flex;
    flex-direction: column;
    gap: var(--lrh-space-2);
    margin-block: var(--lrh-space-3);
  }
  .lrh-legend-row {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: var(--lrh-space-2);
  }
  .lrh-pill {
    border: 1px solid currentColor;
    border-radius: var(--lrh-radius-pill);
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 0.05rem 0.5rem;
    white-space: nowrap;
  }
  .lrh-pill--done {
    background: var(--lrh-color-status-done-bg);
    color: var(--lrh-color-status-done-fg);
  }
  .lrh-pill--blocked {
    background: var(--lrh-color-status-blocked-bg);
    color: var(--lrh-color-status-blocked-fg);
  }
  .lrh-pill--progress {
    background: var(--lrh-color-status-progress-bg);
    color: var(--lrh-color-status-progress-fg);
  }
  .lrh-pill--waiting {
    background: var(--lrh-color-status-waiting-bg);
    color: var(--lrh-color-status-waiting-fg);
  }
  .lrh-pill--unblocked {
    background: var(--lrh-color-status-unblocked-bg);
    color: var(--lrh-color-status-unblocked-fg);
  }
  .lrh-pill--unknown {
    background: var(--lrh-color-status-unknown-bg);
    color: var(--lrh-color-status-unknown-fg);
  }
  .lrh-flag {
    color: var(--lrh-color-text-muted);
    font-size: 0.75rem;
    font-weight: 700;
    margin-left: var(--lrh-space-1);
  }
  .lrh-map-scroll { overflow-x: auto; padding-bottom: var(--lrh-space-3); }
  .lrh-map {
    background: var(--lrh-color-surface-sunken);
    border-radius: var(--lrh-radius-md);
    position: relative;
  }
  .lrh-lane {
    border-inline: 1px solid var(--lrh-color-border-subtle);
    position: absolute;
    top: 0;
  }
  .lrh-lane-title {
    font-size: 0.95rem;
    margin: 0;
    overflow: hidden;
    padding: var(--lrh-space-2) var(--lrh-space-3);
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .lrh-phase {
    border-top: 1px dashed var(--lrh-color-border-strong);
    left: 0;
    position: absolute;
  }
  .lrh-phase--unplaced { background: var(--lrh-color-surface-page); }
  .lrh-phase-title {
    color: var(--lrh-color-text-muted);
    font-size: 0.8rem;
    margin: 0;
    padding: var(--lrh-space-2);
    width: 7.5rem;
  }
  .lrh-lines { left: 0; pointer-events: none; position: absolute; top: 0; }
  .lrh-line { fill: none; stroke: var(--lrh-color-edge); stroke-width: 1.4; }
  .lrh-line--blocked_by { stroke-dasharray: 6 4; }
  .lrh-line--selected { stroke: var(--lrh-color-edge-strong); stroke-width: 2.6; }
  .lrh-arrowhead { fill: var(--lrh-color-edge); }
  .lrh-arrowhead--selected { fill: var(--lrh-color-edge-strong); }
  .lrh-card {
    background: var(--lrh-color-surface-panel);
    border: 1px solid var(--lrh-color-border-strong);
    border-radius: var(--lrh-radius-md);
    box-sizing: border-box;
    color: var(--lrh-color-text-primary);
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    overflow: hidden;
    padding: var(--lrh-space-2) var(--lrh-space-3);
    position: absolute;
    text-decoration: none;
  }
  .lrh-card:hover { border-color: var(--lrh-color-action-accent); }
  .lrh-card:focus-visible { box-shadow: var(--lrh-focus-ring); outline: none; }
  .lrh-card--blocked { border-style: dashed; }
  .lrh-card--related { border: 2px solid var(--lrh-color-edge-strong); }
  .lrh-card--selected {
    border: 2px solid var(--lrh-color-action-accent);
    box-shadow: 0 0 0 3px var(--lrh-color-action-accent-bg);
  }
  .lrh-card-top {
    display: flex;
    gap: var(--lrh-space-2);
    justify-content: space-between;
  }
  .lrh-card-id {
    font-size: 0.75rem;
    font-weight: 700;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .lrh-role { flex: none; }
  .lrh-role {
    color: var(--lrh-color-text-muted);
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
  }
  .lrh-card-title {
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    display: -webkit-box;
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.25;
    overflow: hidden;
  }
  .lrh-card-why {
    color: var(--lrh-color-text-muted);
    font-size: 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .lrh-outside { margin-left: var(--lrh-space-1); }
  .lrh-map-list { display: none; }
  .lrh-map-list ul { list-style: none; padding: 0; }
  .lrh-map-list li {
    border-bottom: 1px solid var(--lrh-color-border-subtle);
    display: flex;
    flex-wrap: wrap;
    gap: var(--lrh-space-2);
    padding: var(--lrh-space-2) 0;
  }
  .lrh-map-list .lrh-card-why { flex-basis: 100%; white-space: normal; }
  .lrh-table-wrap { overflow-x: auto; }
  /* Normal wrapping in the table; the frame's wrap-anywhere would shrink every
     column to one character. Its wrapper scrolls instead. */
  .lrh-map-table {
    border-collapse: collapse;
    min-width: 60rem;
    overflow-wrap: normal;
    width: 100%;
  }
  .lrh-map-table caption { color: var(--lrh-color-text-muted); text-align: left; }
  .lrh-map-table th, .lrh-map-table td {
    border-bottom: 1px solid var(--lrh-color-border-subtle);
    padding: var(--lrh-space-2);
    text-align: left;
    vertical-align: top;
  }
  .lrh-id-link {
    border: 1px solid var(--lrh-color-border-strong);
    border-radius: var(--lrh-radius-sm);
    display: inline-block;
    padding: 0.1rem 0.4rem;
    text-decoration: none;
    white-space: nowrap;
  }
  .lrh-id-link:hover { border-color: var(--lrh-color-action-accent); }
  .lrh-blockers > li { margin-bottom: var(--lrh-space-3); }
  .lrh-drawer-facts {
    display: grid;
    gap: var(--lrh-space-1) var(--lrh-space-3);
    grid-template-columns: max-content 1fr;
  }
  .lrh-drawer-facts dt { color: var(--lrh-color-text-muted); font-weight: 700; }
  .lrh-drawer-facts dd { margin: 0; overflow-wrap: anywhere; }
  .lrh-drawer-facts ul { margin: 0; padding-left: 1rem; }
  @media (max-width: 48rem) {
    .lrh-map-scroll, .lrh-legend { display: none; }
    .lrh-map-list { display: block; }
  }
"""

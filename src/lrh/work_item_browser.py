"""Read-only work-item browser for ``lrh serve``.

Lists a project's work items grouped under their parent workstreams, with an
``Unparented`` group last, and narrows them with URL query filters. Filters
are plain links rather than a form, because Serve's CSP sets
``form-action 'none'``. Every value taken from the URL or the project files is
HTML-escaped. Each status carries a glyph and text as well as a color.
"""

from __future__ import annotations

import html
import urllib.parse
from collections.abc import Iterable, Mapping

from lrh import core_state
from lrh.control.roadmap import Roadmap
from lrh.dependency_maps import render as dependency_map_render

FILTER_KEYS = ("status", "type", "workstream", "roadmap", "ready", "active")
FLAG_VALUES = ("yes", "no")
UNPARENTED = "Unparented"
LIFECYCLES = ("proposed", "active", "resolved", "abandoned")
LIFECYCLES_OPEN_FIRST = ("active", "proposed", "resolved", "abandoned")

# Lifecycle -> (pill token key, glyph, label). The map's pills encode derived
# dependency states; these reuse its tokens for lifecycle status, and the
# label always says the status.
STATUS_PILLS = {
    "proposed": ("unknown", "○", "Proposed"),
    "active": ("progress", "▶", "Active"),
    "resolved": ("done", "✓", "Resolved"),
    "abandoned": ("unknown", "⊘", "Abandoned"),
}
BLOCKED_PILL = ("blocked", "✕", "Blocked")
# As on the map, pills that share a hue also differ by shape: Abandoned strikes
# its label beside the filled Proposed pill.
STATUS_SHAPES = {"abandoned": "struck"}

STYLES = dependency_map_render.PILL_STYLES + """
  .lrh-wib-filters { display: flex; flex-wrap: wrap; gap: var(--lrh-space-2);
    align-items: baseline; margin-block: var(--lrh-space-2); }
  .lrh-wib-filters-label { font-weight: 700; min-width: 7rem; }
  .lrh-wib-filter[aria-current="true"] { font-weight: 700;
    text-decoration-thickness: 2px; }
  .lrh-wib-table { border-collapse: collapse; width: 100%; }
  .lrh-wib-table th, .lrh-wib-table td { border-bottom: 1px solid
    var(--lrh-color-border-subtle, currentColor); padding: var(--lrh-space-1)
    var(--lrh-space-2); text-align: left; vertical-align: top;
    overflow-wrap: normal; }
  .lrh-wib-table th, .lrh-wib-table td:not(:first-child):not(.lrh-wib-roadmap) {
    white-space: nowrap; }
  .lrh-wib-table td:first-child { min-width: 16rem; overflow-wrap: anywhere; }
  .lrh-wib-group h2 { margin-bottom: var(--lrh-space-1); }
  .lrh-wib-group { overflow-x: auto; }
"""


def parse_filters(query: Mapping[str, str]) -> dict[str, str]:
    """Keep the known filter keys with a non-empty value; ignore the rest."""

    return {
        key: query[key].strip()
        for key in FILTER_KEYS
        if key in query and query[key].strip()
    }


def browser_payload(
    state: core_state.CoreProjectState,
    roadmap: Roadmap,
    project_selector: str,
    filters: Mapping[str, str],
) -> dict[str, object]:
    """Return the grouped, filtered work-item list as JSON-ready data."""

    workstreams = {workstream.id: workstream for workstream in state.workstreams}
    base = f"/project/{_quote(project_selector)}"
    rows = [_row(item, workstreams, base) for item in state.work_items]
    known = _known_values(state, roadmap)
    diagnostics = [
        f"No work item matches {key} {value!r}."
        for key, value in filters.items()
        if value not in known[key]
    ]
    # A value no work item can have matches nothing, rather than being
    # read as some other value (e.g. "ready=maybe" as "no").
    shown = [] if diagnostics else [row for row in rows if _matches(row, filters)]

    groups: list[dict[str, object]] = []
    for workstream, parent in _tree_order(state.workstreams):
        items = _ordered(row for row in shown if workstream.id in row["workstreams"])
        if items:
            groups.append(
                {
                    "id": workstream.id,
                    "title": workstream.title,
                    "status": workstream.status,
                    "parent": parent,
                    "detail_url": f"{base}/workstreams/{_quote(workstream.id)}",
                    "work_items": items,
                }
            )
    unparented = _ordered(row for row in shown if not row["workstreams"])
    if unparented:
        groups.append(
            {
                "id": UNPARENTED,
                "title": "Work items with no parent workstream",
                "status": None,
                "parent": None,
                "detail_url": None,
                "work_items": unparented,
            }
        )
    return {
        "project": project_selector,
        "filters": dict(filters),
        "total": len(rows),
        "types": sorted({str(row["type"]) for row in rows}),
        "shown": len(shown),
        "groups": groups,
        "roadmap": {
            "root": None if roadmap.root is None else roadmap.root.id,
            "phases": [
                {
                    "id": phase.id,
                    "title": phase.title,
                    "status": phase.status,
                    "order": phase.order,
                    "work_items": sum(
                        1
                        for row in rows
                        if phase.id in (match["phase"] for match in row["roadmap"])
                    ),
                }
                for phase in roadmap.phases
            ],
            "unlinked_work_items": sum(1 for row in rows if not row["roadmap"]),
            "diagnostics": [
                {"code": item.code, "message": item.message}
                for item in roadmap.diagnostics
            ],
        },
        "validation": {
            "is_valid": state.validation.is_valid,
            "error_count": state.validation.error_count,
            "warning_count": state.validation.warning_count,
        },
        "diagnostics": diagnostics,
    }


def render_page(payload: Mapping[str, object], styles: str) -> str:
    """Render the browser page from :func:`browser_payload` output."""

    project = str(payload["project"])
    filters = payload["filters"]
    assert isinstance(filters, dict)
    base = f"/project/{_quote(project)}/work-items"
    groups = payload["groups"]
    assert isinstance(groups, list)
    roadmap = payload["roadmap"]
    assert isinstance(roadmap, dict)
    diagnostics = payload["diagnostics"]
    assert isinstance(diagnostics, list)

    summary = (
        f"Showing {payload['shown']} of {payload['total']} work items"
        f"{_filter_summary(filters)}."
    )
    notes = "".join(
        f'<p class="lrh-muted" role="status">{html.escape(str(note))}</p>'
        for note in diagnostics
    )
    validation = payload["validation"]
    assert isinstance(validation, dict)
    if not validation["is_valid"]:
        # Some errors (dependency-map views) leave the work items loaded.
        consequence = (
            ", so its work items cannot be listed"
            if payload["total"] == 0
            else "; the list below may be incomplete"
        )
        notes += (
            '<p role="status"><strong>The project does not validate</strong> '
            f"({validation['error_count']} errors){consequence}. Run "
            "<code>lrh validate</code> to see the errors.</p>"
        )
    if groups:
        body = "".join(_group_html(group, base, filters, project) for group in groups)
    else:
        body = '<p class="lrh-muted">No work items match these filters.</p>'
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Work items: {html.escape(project)}</title>
{styles}<style>{STYLES}</style></head>
<body><div class="lrh-app-shell">
<header class="lrh-page-header"><p class="lrh-eyebrow">{html.escape(project)}</p>
<h1>Work items</h1>
<p><a href="/project/{_quote(project)}">Project dashboard</a> ·
<a href="/workbench">Prompt workbench</a></p>
<p>{html.escape(summary)}{_clear_link(base, filters)}</p>{notes}</header>
<main class="lrh-main-content">
<section class="lrh-console-region" aria-labelledby="wib-roadmap">
<h2 id="wib-roadmap">Roadmap phases</h2>{_roadmap_html(roadmap, base, filters)}
</section>
<section class="lrh-console-region" aria-labelledby="wib-filters">
<h2 id="wib-filters">Filters</h2>{_filters_html(payload, base, filters)}</section>
{body}
</main></div></body></html>"""


def _row(
    item: core_state.WorkItemState,
    workstreams: Mapping[str, core_state.WorkstreamState],
    base: str,
) -> dict[str, object]:
    parents = [parent for parent in item.parent_ids if parent in workstreams]
    roadmap = [{"phase": phase, "via": None} for phase in item.related_roadmap]
    own = set(item.related_roadmap)
    for parent in parents:
        for phase in workstreams[parent].related_roadmap:
            if phase not in own:
                roadmap.append({"phase": phase, "via": parent})
                own.add(phase)
    readiness = item.execution_readiness
    return {
        "id": item.id,
        "title": item.title,
        "status": item.status,
        "type": item.type,
        "blocked": item.blocked,
        "active_leaf": item.is_active_leaf,
        "execution_ready": bool(readiness is not None and readiness.execution_ready),
        "workstreams": parents,
        "roadmap": roadmap,
        "detail_url": f"{base}/work-items/{_quote(item.id)}",
        "prompt_url": f"{base}/work-items/{_quote(item.id)}/prompt",
    }


def _tree_order(
    workstreams: tuple[core_state.WorkstreamState, ...],
) -> list[tuple[core_state.WorkstreamState, str | None]]:
    """Workstreams depth-first: each parent before its child workstreams.

    Returns each workstream with the parent it is listed under, if any.
    Roots and siblings keep their loaded (id) order; a workstream reachable
    twice, or caught in a cycle, is listed once.
    """

    by_id = {workstream.id: workstream for workstream in workstreams}
    ordered: list[tuple[core_state.WorkstreamState, str | None]] = []
    seen: set[str] = set()

    def visit(workstream: core_state.WorkstreamState, parent: str | None) -> None:
        if workstream.id in seen:
            return
        seen.add(workstream.id)
        ordered.append((workstream, parent))
        for child in workstream.child_ids:
            if child in by_id:
                visit(by_id[child], workstream.id)

    for workstream in workstreams:
        if not any(parent in by_id for parent in workstream.parent_ids):
            visit(workstream, None)
    for workstream in workstreams:
        visit(workstream, None)
    return ordered


def _ordered(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Open work first: active, proposed, then resolved and abandoned."""

    def key(row: dict[str, object]) -> tuple[int, str]:
        status = str(row["status"])
        if status in LIFECYCLES_OPEN_FIRST:
            return LIFECYCLES_OPEN_FIRST.index(status), str(row["id"])
        return len(LIFECYCLES_OPEN_FIRST), str(row["id"])

    return sorted(rows, key=key)


def _known_values(
    state: core_state.CoreProjectState, roadmap: Roadmap
) -> dict[str, set[str]]:
    return {
        "status": set(LIFECYCLES) | {item.status for item in state.work_items},
        "type": {item.type for item in state.work_items},
        "workstream": {workstream.id for workstream in state.workstreams}
        | {UNPARENTED},
        "roadmap": {phase.id for phase in roadmap.phases}
        | {phase for item in state.work_items for phase in item.related_roadmap}
        | {
            phase
            for workstream in state.workstreams
            for phase in workstream.related_roadmap
        },
        "ready": set(FLAG_VALUES),
        "active": set(FLAG_VALUES),
    }


def _matches(row: Mapping[str, object], filters: Mapping[str, str]) -> bool:
    for key, value in filters.items():
        if key == "status" and row["status"] != value:
            return False
        if key == "type" and row["type"] != value:
            return False
        if key == "workstream":
            parents = row["workstreams"]
            assert isinstance(parents, list)
            if value == UNPARENTED:
                if parents:
                    return False
            elif value not in parents:
                return False
        if key == "roadmap":
            matches = row["roadmap"]
            assert isinstance(matches, list)
            if value not in (match["phase"] for match in matches):
                return False
        if key == "ready" and row["execution_ready"] != (value == "yes"):
            return False
        if key == "active" and row["active_leaf"] != (value == "yes"):
            return False
    return True


def _group_html(
    group: Mapping[str, object],
    base: str,
    filters: Mapping[str, str],
    project: str,
) -> str:
    group_id = str(group["id"])
    items = group["work_items"]
    assert isinstance(items, list)
    title = html.escape(str(group["title"]))
    if group["detail_url"]:
        heading = (
            f'<a href="{_attr(str(group["detail_url"]))}">{html.escape(group_id)}</a>'
            f" — {title} {_status_pill(str(group['status']))}"
        )
    else:
        heading = f"{html.escape(group_id)} — {title}"
    only = (
        ""
        if filters.get("workstream") == group_id
        else f' <a href="{_attr(_href(base, filters, workstream=group_id))}">'
        "Show only this group</a>"
    )
    rows = "".join(_item_row(item) for item in items)
    count = f"{len(items)} work item{'' if len(items) == 1 else 's'}"
    if group.get("parent"):
        count = f"Part of {html.escape(str(group['parent']))}. {count}"
    return f"""<section class="lrh-console-region lrh-wib-group">
<h2>{heading}</h2><p class="lrh-muted">{count}{only}</p>
<table class="lrh-wib-table"><thead><tr><th scope="col">Work item</th>
<th scope="col">Status</th><th scope="col">Type</th><th scope="col">Flags</th>
<th scope="col">Roadmap</th><th scope="col">Prompt</th></tr></thead>
<tbody>{rows}</tbody></table></section>"""


def _item_row(item: Mapping[str, object]) -> str:
    flags = []
    if item["active_leaf"]:
        flags.append("Active leaf")
    if item["execution_ready"]:
        flags.append("Execution-ready flag set")
    roadmap = item["roadmap"]
    assert isinstance(roadmap, list)
    phases = ", ".join(
        html.escape(str(match["phase"]))
        + ("" if match["via"] is None else f" (via {html.escape(str(match['via']))})")
        for match in roadmap
    )
    status = _status_pill(str(item["status"]))
    if item["blocked"]:
        status += " " + _pill(BLOCKED_PILL)
    return (
        f'<tr><td><a href="{_attr(str(item["detail_url"]))}">'
        f"{html.escape(str(item['id']))}</a><br>{html.escape(str(item['title']))}</td>"
        f"<td>{status}</td><td>{html.escape(str(item['type']))}</td>"
        f"<td>{html.escape(', '.join(flags)) or '—'}</td>"
        f'<td class="lrh-wib-roadmap">{phases or "No phase"}</td>'
        f'<td><a href="{_attr(str(item["prompt_url"]))}">Preview</a></td></tr>'
    )


def _roadmap_html(
    roadmap: Mapping[str, object], base: str, filters: Mapping[str, str]
) -> str:
    phases = roadmap["phases"]
    assert isinstance(phases, list)
    if not phases:
        listing = '<p class="lrh-muted">This project declares no roadmap phases.</p>'
    else:
        entries = "".join(
            f'<li><a href="{_attr(_href(base, filters, roadmap=str(phase["id"])))}"'
            f"{_current(filters, 'roadmap', str(phase['id']))}>"
            f"{html.escape(str(phase['id']))}</a> — {html.escape(str(phase['title']))}"
            f" ({html.escape(str(phase['status']))}; "
            f"{phase['work_items']} linked work items)</li>"
            for phase in phases
        )
        listing = f"<ol>{entries}</ol>"
    if "roadmap" in filters:
        listing += (
            f'<p><a href="{_attr(_href(base, filters, roadmap=None))}">'
            "Show every phase</a></p>"
        )
    unlinked = roadmap["unlinked_work_items"]
    notes = "".join(
        f'<p class="lrh-muted">{html.escape(str(item["message"]))}</p>'
        for item in roadmap["diagnostics"]
        if isinstance(item, dict)
    )
    return (
        f'{listing}<p class="lrh-muted">{unlinked} work items link to no phase,'
        " directly or through their workstream. A phase filter shows only linked"
        f" items.</p>{notes}"
    )


def _filters_html(
    payload: Mapping[str, object], base: str, filters: Mapping[str, str]
) -> str:
    statuses = [(status, STATUS_PILLS[status][2]) for status in LIFECYCLES]
    types = payload["types"]
    assert isinstance(types, list)
    rows = [
        ("Status", "status", statuses),
        ("Type", "type", [(str(value), str(value)) for value in types]),
        ("Execution-ready flag", "ready", [("yes", "Set"), ("no", "Not set")]),
        ("Active leaf", "active", [("yes", "Yes"), ("no", "No")]),
    ]
    if "workstream" in filters:
        # Workstreams are chosen from each group's own link; this row undoes it.
        value = filters["workstream"]
        rows.insert(2, ("Workstream", "workstream", [(value, value)]))
    navs = []
    for label, key, options in rows:
        links = [_filter_link(base, filters, key, None, "Any")]
        links += [
            _filter_link(base, filters, key, value, text) for value, text in options
        ]
        navs.append(
            f'<nav class="lrh-wib-filters" aria-label="Filter by {label.lower()}">'
            f'<span class="lrh-wib-filters-label">{label}</span>{"".join(links)}</nav>'
        )
    return "".join(navs)


def _filter_link(
    base: str, filters: Mapping[str, str], key: str, value: str | None, text: str
) -> str:
    target = _attr(_href(base, filters, **{key: value}))
    return (
        f'<a class="lrh-wib-filter" href="{target}"'
        f"{_current(filters, key, value)}>{html.escape(text)}</a>"
    )


def _filter_summary(filters: Mapping[str, str]) -> str:
    if not filters:
        return ""
    return ", filtered by " + "; ".join(
        f"{key} = {value}" for key, value in filters.items()
    )


def _clear_link(base: str, filters: Mapping[str, str]) -> str:
    if not filters:
        return ""
    return f' <a href="{_attr(base)}">Clear filters</a>'


def _href(base: str, filters: Mapping[str, str], **changes: str | None) -> str:
    merged = dict(filters)
    for key, value in changes.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    ordered = [(key, merged[key]) for key in FILTER_KEYS if key in merged]
    return base + (f"?{urllib.parse.urlencode(ordered)}" if ordered else "")


def _current(filters: Mapping[str, str], key: str, value: str | None) -> str:
    return ' aria-current="true"' if filters.get(key) == value else ""


def _status_pill(status: str) -> str:
    style = STATUS_PILLS.get(status, ("unknown", "?", status or "Unknown"))
    return _pill(style, STATUS_SHAPES.get(status, "filled"))


def _pill(style: tuple[str, str, str], shape: str = "filled") -> str:
    key, glyph, label = style
    text = html.escape(label)
    if shape == "struck":
        text = f'<span class="lrh-pill-struck">{text}</span>'
    return (
        f'<span class="lrh-pill lrh-pill--{key} lrh-pill--{shape}">'
        f'<span aria-hidden="true">{glyph}</span> {text}</span>'
    )


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")

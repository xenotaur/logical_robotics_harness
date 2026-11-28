"""Render pull request briefing data (`data.json`) into an HTML page.

The data has two halves: facts written by `lrh pr-brief gather` (`pr`,
`status`, `files`, `categories`) and narrative written by the
`/lrh-pr-explain` skill (`briefing`). Every text field is HTML-escaped and
then given a tiny inline markup (backticks for code, ``**bold**``). The one
exception is `briefing.figures[].html`, which is model-authored diagram markup
inserted as-is; it must never contain text copied verbatim from the PR.
"""

from __future__ import annotations

import html
import importlib.resources as resources
import json
import re
from typing import Any

SEVERITIES = {
    "blocker": "Blocks merge",
    "check": "Check",
    "info": "Note",
}
CONFIDENCES = {"confirmed": "Confirmed", "likely": "Likely", "unverified": "Unverified"}
TONES = ("accent", "warn", "muted")
FORMATS = ("artifact", "standalone")

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_FIGURE_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_RESERVED_IDS = {"summary", "map", "changes", "files", "tests", "review"}
_PLACEHOLDER_RE = re.compile(r"\{\{(TITLE|FILES_JSON|CONTENT)\}\}")


class BriefingError(ValueError):
    """Raised when briefing data cannot be rendered."""


def inline(text: Any) -> str:
    """Escape text and apply inline markup: `code` and **bold**."""
    parts = str(text if text is not None else "").split("`")
    if len(parts) % 2 == 0:
        # An unmatched backtick stays literal.
        last = parts.pop()
        parts[-1] = parts[-1] + "`" + last
    rendered = []
    for index, part in enumerate(parts):
        escaped = html.escape(part, quote=True)
        if index % 2 == 1:
            rendered.append(f"<code>{escaped}</code>")
        else:
            rendered.append(_BOLD_RE.sub(r"<b>\1</b>", escaped))
    return "".join(rendered)


def _paragraphs(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if str(item).strip()]


def file_slug(path: str, used: set[str]) -> str:
    """Return a unique, hash-safe anchor id for a file path."""
    base = "f-" + (re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower() or "file")
    slug, counter = base, 2
    while slug in used:
        slug, counter = f"{base}-{counter}", counter + 1
    used.add(slug)
    return slug


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_text_or_list(value: Any) -> bool:
    return value is None or isinstance(value, (str, list))


def _is_http_url(value: Any) -> bool:
    return isinstance(value, str) and value.lower().startswith(("https://", "http://"))


def _check_dict_list(value: Any, name: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{name}[{index}] must be an object")


def _structure_errors(data: Any) -> list[str]:
    """Return errors for data whose shape the renderer cannot dereference."""
    if not isinstance(data, dict):
        return ["data.json must hold a JSON object"]
    errors: list[str] = []
    shapes = {
        "pr": dict,
        "status": dict,
        "files": list,
        "categories": list,
        "briefing": dict,
    }
    for key, kind in shapes.items():
        if key not in data:
            errors.append(f"missing top-level key: {key}")
        elif not isinstance(data[key], kind):
            noun = "an object" if kind is dict else "a list"
            errors.append(f"{key} must be {noun}")
    if errors:
        return errors
    pr = data["pr"]
    if not isinstance(pr.get("repo"), str) or not pr["repo"].strip():
        errors.append("pr.repo must be a non-empty string")
    if not _is_count(pr.get("number")):
        errors.append("pr.number must be a non-negative integer")
    for key in ("additions", "deletions", "changed_files"):
        if pr.get(key) is not None and not _is_count(pr[key]):
            errors.append(f"pr.{key} must be a non-negative integer")
    _check_dict_list(pr.get("commits"), "pr.commits", errors)
    status = data["status"]
    for key in ("checks", "reviews", "conflicts"):
        if status.get(key) is not None and not isinstance(status[key], dict):
            errors.append(f"status.{key} must be an object")
    for key in ("ahead_by", "behind_by"):
        if status.get(key) is not None and not _is_count(status[key]):
            errors.append(f"status.{key} must be a non-negative integer or null")
    checks = status.get("checks")
    for key in ("total", "failing", "pending"):
        value = checks.get(key) if isinstance(checks, dict) else None
        if value is not None and not _is_count(value):
            errors.append(f"status.checks.{key} must be a non-negative integer")
    for index, category in enumerate(data["categories"]):
        if not isinstance(category, dict) or not str(category.get("key", "")).strip():
            errors.append(f"categories[{index}] must be an object with a key")
    for index, item in enumerate(data["files"]):
        if not isinstance(item, dict):
            errors.append(f"files[{index}] must be an object")
            continue
        if not isinstance(item.get("path"), str) or not item["path"]:
            errors.append(f"files[{index}].path must be a non-empty string")
        for key in ("additions", "deletions"):
            if not _is_count(item.get(key)):
                errors.append(f"files[{index}].{key} must be a non-negative integer")
        if not isinstance(item.get("previous_path", ""), str):
            errors.append(f"files[{index}].previous_path must be a string")
    briefing = data["briefing"]
    for key in ("figures", "review_notes", "behavior_changes", "at_a_glance"):
        _check_dict_list(briefing.get(key), f"briefing.{key}", errors)
    if not _is_text_or_list(briefing.get("summary")):
        errors.append("briefing.summary must be text or a list of paragraphs")
    for index, note in enumerate(briefing.get("review_notes") or []):
        if isinstance(note, dict) and not _is_text_or_list(note.get("body")):
            errors.append(
                f"briefing.review_notes[{index}].body must be text or a list of "
                "paragraphs"
            )
    tests = briefing.get("tests")
    if tests is not None and not isinstance(tests, dict):
        errors.append("briefing.tests must be an object")
    elif tests:
        _check_dict_list(tests.get("rows"), "briefing.tests.rows", errors)
        if tests.get("gaps") is not None and not isinstance(tests["gaps"], list):
            errors.append("briefing.tests.gaps must be a list")
    notes = briefing.get("files")
    if notes is not None and not isinstance(notes, dict):
        errors.append("briefing.files must be an object keyed by path")
    elif notes:
        for path, note in notes.items():
            if note is not None and not isinstance(note, dict):
                errors.append(f"briefing.files[{path!r}] must be an object")
            elif note and note.get("points") is not None:
                if not isinstance(note["points"], list):
                    errors.append(f"briefing.files[{path!r}].points must be a list")
    return errors


def validate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return `(errors, warnings)` for briefing data."""
    warnings: list[str] = []
    errors = _structure_errors(data)
    if errors:
        return errors, warnings
    category_keys = [str(item.get("key", "")) for item in data["categories"]]
    paths = set()
    for item in data["files"]:
        paths.add(item.get("path"))
        if item.get("category") not in category_keys:
            errors.append(
                f"file {item.get('path')!r} has unknown category "
                f"{item.get('category')!r}; known: {', '.join(category_keys)}"
            )
    url = data["pr"].get("url")
    if url and not _is_http_url(url):
        warnings.append("pr.url is not an http(s) URL; the GitHub link is omitted")
    briefing = data["briefing"]
    if not str(briefing.get("headline_summary", "")).strip():
        warnings.append("briefing.headline_summary is empty")
    file_notes = briefing.get("files") or {}
    for path in sorted(set(file_notes) - paths):
        warnings.append(f"briefing.files has an entry for a path not in the PR: {path}")
    for path in sorted(paths):
        if not str((file_notes.get(path) or {}).get("gist", "")).strip():
            warnings.append(f"no gist for file: {path}")
    seen_ids: set[str] = set()
    for index, figure in enumerate(briefing.get("figures") or []):
        figure_id = str(figure.get("id", ""))
        if (
            not _FIGURE_ID_RE.match(figure_id)
            or figure_id in _RESERVED_IDS
            or figure_id.startswith("f-")
        ):
            errors.append(
                f"figures[{index}].id {figure_id!r} must be lowercase letters, "
                "digits and hyphens, not start with 'f-', and not be a built-in "
                "section id"
            )
        elif figure_id in seen_ids:
            errors.append(f"figures[{index}].id {figure_id!r} is duplicated")
        seen_ids.add(figure_id)
        if not str(figure.get("html", "")).strip():
            errors.append(f"figures[{index}].html is empty")
    for index, note in enumerate(briefing.get("review_notes") or []):
        severity = note.get("severity")
        if not isinstance(severity, str) or severity not in SEVERITIES:
            errors.append(
                f"review_notes[{index}].severity must be one of "
                f"{', '.join(SEVERITIES)}"
            )
        confidence = note.get("confidence", "")
        if confidence and (
            not isinstance(confidence, str) or confidence not in CONFIDENCES
        ):
            errors.append(
                f"review_notes[{index}].confidence must be one of "
                f"{', '.join(CONFIDENCES)}"
            )
    for index, row in enumerate((briefing.get("tests") or {}).get("rows") or []):
        tone = row.get("tone", "accent")
        if not isinstance(tone, str) or tone not in TONES:
            errors.append(f"tests.rows[{index}].tone must be one of {', '.join(TONES)}")
    return errors, warnings


def status_chips(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Derive `(tone, text)` status chips from gathered facts."""
    pr = data["pr"]
    status = data["status"]
    state = str(pr.get("state", "")).upper()
    chips: list[tuple[str, str]] = []
    if state == "MERGED":
        return [("ok", "Merged")]
    if state == "CLOSED":
        return [("", "Closed without merging")]
    chips.append(("warn", "Draft") if pr.get("is_draft") else ("", "Open"))
    conflicts = status.get("conflicts") or {}
    if conflicts.get("checked"):
        # The trial merge ran against the current base tip; it outranks
        # GitHub's mergeability, which may predate a base or head update.
        if conflicts.get("clean"):
            chips.append(("ok", "Merges cleanly"))
        else:
            count = len(conflicts.get("files") or [])
            noun = "file" if count == 1 else "files"
            chips.append(("crit", f"Merge conflict · {count} {noun}"))
    elif str(status.get("mergeable", "")).upper() == "CONFLICTING":
        chips.append(("crit", "Merge conflict"))
    behind = status.get("behind_by")
    if _is_count(behind) and behind > 0:
        noun = "commit" if behind == 1 else "commits"
        chips.append(("warn", f"{behind} {noun} behind {pr.get('base', 'base')}"))
    checks = status.get("checks") or {}
    total = int(checks.get("total") or 0)
    if total == 0:
        chips.append(("warn", "No CI checks reported"))
    elif checks.get("failing"):
        chips.append(("crit", f"{checks['failing']} of {total} checks failing"))
    elif checks.get("pending"):
        chips.append(("warn", f"{checks['pending']} of {total} checks pending"))
    else:
        chips.append(("ok", f"All {total} checks pass"))
    chips.append(_review_chip(status.get("reviews") or {}))
    return chips


def _review_chip(reviews: dict[str, Any]) -> tuple[str, str]:
    """Prefer GitHub's current decision; fall back to effective reviews."""
    decision = str(reviews.get("decision") or "").upper()
    if decision == "CHANGES_REQUESTED":
        return ("crit", "Changes requested")
    if decision == "APPROVED":
        return ("ok", "Approved")
    if decision != "REVIEW_REQUIRED":
        # No decision: the repository does not require reviews.
        if reviews.get("changes_requested"):
            return ("crit", "Changes requested")
        if reviews.get("approvals"):
            return ("ok", "Approved")
    count = reviews.get("count")
    if not count:
        return ("warn", "No reviews yet")
    if decision == "REVIEW_REQUIRED":
        return ("warn", "Review required")
    return ("", f"{count} reviews, none approving")


def _section_head(eyebrow: str, title: str, intro: str = "") -> str:
    intro_html = f"<p>{inline(intro)}</p>" if str(intro).strip() else ""
    return (
        '<div class="sec-head"><div class="eyebrow">'
        f"{inline(eyebrow)}</div><h2>{inline(title)}</h2>{intro_html}</div>"
    )


def _header(data: dict[str, Any]) -> str:
    pr = data["pr"]
    briefing = data["briefing"]
    files = data["files"]
    title = briefing.get("title") or pr.get("title") or f"Pull request #{pr['number']}"
    lede = briefing.get("headline_summary", "")
    author = pr.get("author_name") or pr.get("author_login") or "unknown"
    login = pr.get("author_login", "")
    by = f"<b>{inline(author)}</b>"
    if login and login != author:
        by += f" ({inline(login)})"
    meta = [
        f"<span>By {by}</span>",
        f"<span><code>{html.escape(str(pr.get('head', '')))}</code> → "
        f"<code>{html.escape(str(pr.get('base', '')))}</code></span>",
    ]
    if pr.get("created_at"):
        meta.append(f"<span>Opened <b>{inline(str(pr['created_at'])[:10])}</b></span>")
    if _is_http_url(pr.get("url")):
        meta.append(
            f'<span><a href="{html.escape(str(pr["url"]), quote=True)}">'
            "View on GitHub</a></span>"
        )
    new_files = sum(1 for item in files if item.get("status") == "added")
    commits = len(pr.get("commits") or [])
    stats = [
        (
            f'<span class="add">+{int(pr.get("additions") or 0):,}</span> '
            f'<span class="del">−{int(pr.get("deletions") or 0):,}</span>',
            "lines",
        ),
        (f"{int(pr.get('changed_files') or len(files)):,}", "files"),
        (f"{new_files:,}", "new files"),
        (f"{commits:,}", "commit" if commits == 1 else "commits"),
    ]
    stats_html = "".join(
        f'<div class="stat"><span class="v">{value}</span>'
        f'<span class="k">{label}</span></div>'
        for value, label in stats
    )
    chips_html = "".join(
        f'<span class="chip {tone}">{inline(text)}</span>'
        for tone, text in status_chips(data)
    )
    lede_html = f'<p class="lede">{inline(lede)}</p>' if str(lede).strip() else ""
    return (
        '<header class="hero">'
        f'<div class="eyebrow">{inline(pr["repo"])} · Pull request '
        f"#{int(pr['number'])} · briefing</div>"
        f"<h1>{inline(title)}</h1>{lede_html}"
        f'<div class="hero-meta">{"".join(meta)}</div>'
        f'<div class="stats">{stats_html}</div>'
        f'<div class="chips">{chips_html}</div>'
        "</header>"
    )


def _summary(briefing: dict[str, Any]) -> str:
    paragraphs = _paragraphs(briefing.get("summary"))
    glance = briefing.get("at_a_glance") or []
    if not paragraphs and not glance:
        return ""
    prose = "".join(f"<p>{inline(text)}</p>" for text in paragraphs)
    aside = ""
    if glance:
        rows = "".join(
            f"<dt>{inline(item.get('label', ''))}</dt>"
            f"<dd>{inline(item.get('value', ''))}</dd>"
            for item in glance
        )
        aside = (
            '<aside class="verdict" aria-label="At a glance">'
            f'<div class="eyebrow">At a glance</div><dl>{rows}</dl></aside>'
        )
    return (
        '<section id="summary">'
        + _section_head("The short version", "What this PR does")
        + f'<div class="summary-grid"><div class="prose">{prose}</div>{aside}</div>'
        "</section>"
    )


def _category_colors(categories: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item["key"]): f"var(--cat-{index % 6 + 1})"
        for index, item in enumerate(categories)
    }


def _map(data: dict[str, Any], colors: dict[str, str]) -> str:
    files = data["files"]
    grand = sum(item["additions"] + item["deletions"] for item in files) or 1
    bar = []
    legend = []
    for category in data["categories"]:
        key = category["key"]
        members = [item for item in files if item["category"] == key]
        if not members:
            continue
        lines = sum(item["additions"] + item["deletions"] for item in members)
        pct = 100 * lines / grand
        label = inline(category.get("label", key))
        bar.append(
            f'<span style="width:{pct:.2f}%;background:{colors[key]}" '
            f'title="{html.escape(str(category.get("label", key)), quote=True)}: '
            f'{lines:,} lines"></span>'
        )
        noun = "file" if len(members) == 1 else "files"
        legend.append(
            f'<span><i style="background:{colors[key]}"></i>{label} '
            f"<b>{round(pct)}%</b> · {len(members)} {noun}</span>"
        )
    return (
        '<section id="map">'
        + _section_head(
            "Where the change lands",
            "File map",
            "Each tile is one file, sized by lines changed and grouped by area. "
            "Select a tile to jump to its breakdown.",
        )
        + '<div class="catbar" role="img" aria-label="Share of changed lines by '
        f'area">{"".join(bar)}</div>'
        f'<div class="legend">{"".join(legend)}</div>'
        '<div class="treemap" id="treemap"></div>'
        '<p class="map-note">Very small changes are drawn at a minimum size so they '
        "stay visible. Tiles marked NEW are files this PR adds.</p>"
        "</section>"
    )


def _figures(briefing: dict[str, Any]) -> str:
    sections = []
    for figure in briefing.get("figures") or []:
        caption = figure.get("caption", "")
        caption_html = (
            f"<figcaption>{inline(caption)}</figcaption>"
            if str(caption).strip()
            else ""
        )
        sections.append(
            f'<section id="{figure["id"]}">'
            + _section_head(
                figure.get("eyebrow", "Diagram"),
                figure.get("title", ""),
                figure.get("intro", ""),
            )
            + f'<figure class="figure">{figure["html"]}{caption_html}</figure>'
            "</section>"
        )
    return "".join(sections)


def _behavior_changes(briefing: dict[str, Any]) -> str:
    rows = briefing.get("behavior_changes") or []
    if not rows:
        return ""
    body = "".join(
        '<div class="ba-row">'
        f'<div class="what">{inline(row.get("what", ""))}</div>'
        f'<div class="before"><span class="tag">Before</span>'
        f'{inline(row.get("before", ""))}</div>'
        f'<div class="after"><span class="tag">After</span>'
        f'{inline(row.get("after", ""))}</div></div>'
        for row in rows
    )
    return (
        '<section id="changes">'
        + _section_head(
            "Behavior changes",
            "What existing users will notice",
            briefing.get("behavior_intro", ""),
        )
        + f'<div class="ba">{body}</div></section>'
    )


_STATUS_BADGES = {
    "added": ("new", "new"),
    "removed": ("removed", "removed"),
    "renamed": ("", "renamed"),
    "copied": ("", "copied"),
}


def _file_card(
    item: dict[str, Any], note: dict[str, Any], slug: str, color: str, max_lines: int
) -> str:
    badge_class, badge_text = _STATUS_BADGES.get(
        str(item.get("status")), ("", "modified")
    )
    added_width = 100 * item["additions"] / max_lines
    deleted_width = 100 * item["deletions"] / max_lines
    previous = ""
    if item.get("previous_path"):
        previous = (
            f'<span class="fprev">from {html.escape(item["previous_path"])}</span>'
        )
    gist = str(note.get("gist", "")).strip()
    gist_html = (
        f'<p class="gist">{inline(gist)}</p>'
        if gist
        else '<p class="gist missing">No summary written for this file.</p>'
    )
    points = [str(point) for point in note.get("points") or [] if str(point).strip()]
    points_html = (
        "<ul>" + "".join(f"<li>{inline(point)}</li>" for point in points) + "</ul>"
        if points
        else ""
    )
    snippet = str(note.get("snippet", ""))
    snippet_html = (
        f'<pre class="snip">{html.escape(snippet)}</pre>' if snippet.strip() else ""
    )
    return (
        f'<article class="file" id="{slug}" style="--c:{color}">'
        '<div class="fhead">'
        f'<span class="fpath">{html.escape(item["path"])}</span>'
        f'<span class="badge {badge_class}">{badge_text}</span>{previous}'
        f'<span class="fbar"><span class="add">+{item["additions"]}</span>'
        f'<span class="del">−{item["deletions"]}</span>'
        '<span class="bars" aria-hidden="true">'
        f'<span class="a" style="width:{added_width:.1f}%"></span>'
        f'<span class="d" style="width:{deleted_width:.1f}%"></span></span></span>'
        f"</div>{gist_html}{points_html}{snippet_html}</article>"
    )


def _files(data: dict[str, Any], colors: dict[str, str], slugs: dict[str, str]) -> str:
    files = data["files"]
    notes = data["briefing"].get("files") or {}
    max_lines = max(
        (item["additions"] + item["deletions"] for item in files), default=1
    )
    max_lines = max(max_lines, 1)
    groups = []
    for category in data["categories"]:
        key = category["key"]
        members = sorted(
            (item for item in files if item["category"] == key),
            key=lambda item: (-(item["additions"] + item["deletions"]), item["path"]),
        )
        if not members:
            continue
        added = sum(item["additions"] for item in members)
        deleted = sum(item["deletions"] for item in members)
        noun = "file" if len(members) == 1 else "files"
        cards = "".join(
            _file_card(
                item,
                notes.get(item["path"]) or {},
                slugs[item["path"]],
                colors[key],
                max_lines,
            )
            for item in members
        )
        groups.append(
            '<div class="group"><div class="group-head">'
            f'<span class="sw" style="background:{colors[key]}"></span>'
            f'<h3>{inline(category.get("label", key))}</h3>'
            f'<span class="gstat"><span class="add">+{added:,}</span> '
            f'<span class="del">−{deleted:,}</span> · {len(members)} {noun}</span>'
            f"</div>{cards}</div>"
        )
    return (
        '<section id="files">'
        + _section_head(
            "Detail",
            "File by file",
            "Grouped by area, largest change first within each group.",
        )
        + "".join(groups)
        + "</section>"
    )


def _tests(briefing: dict[str, Any]) -> str:
    tests = briefing.get("tests") or {}
    rows = tests.get("rows") or []
    gaps = [str(gap) for gap in tests.get("gaps") or [] if str(gap).strip()]
    if not rows and not gaps:
        return ""
    table = ""
    if rows:
        body = "".join(
            f"<tr><td>{inline(row.get('behavior', ''))}</td>"
            f'<td class="mono">{inline(row.get("where", ""))}</td>'
            f'<td><span class="kind {row.get("tone", "accent")}">'
            f"{inline(row.get('how', ''))}</span></td></tr>"
            for row in rows
        )
        table = (
            '<div class="table-box"><table class="tests"><thead><tr>'
            "<th>Behavior</th><th>Where</th><th>How</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div>"
        )
    gaps_html = ""
    if gaps:
        gaps_html = (
            '<div class="gaps"><div class="eyebrow">Not covered</div><ul>'
            + "".join(f"<li>{inline(gap)}</li>" for gap in gaps)
            + "</ul></div>"
        )
    return (
        '<section id="tests">'
        + _section_head("Verification", "What the tests cover", tests.get("note", ""))
        + table
        + gaps_html
        + "</section>"
    )


def _review_notes(briefing: dict[str, Any]) -> str:
    notes = briefing.get("review_notes") or []
    if not notes:
        return ""
    cards = []
    for note in notes:
        severity = note["severity"]
        label = note.get("label") or SEVERITIES[severity]
        confidence = note.get("confidence", "")
        confidence_html = (
            f'<span class="conf">{CONFIDENCES[confidence]}</span>' if confidence else ""
        )
        body = "".join(
            f"<p>{inline(text)}</p>" for text in _paragraphs(note.get("body"))
        )
        where = note.get("where", "")
        where_html = f'<p class="where">{inline(where)}</p>' if where else ""
        cards.append(
            f'<div class="note"><span class="sev {severity}">{inline(label)}</span>'
            f"<div><h3>{inline(note.get('title', ''))}{confidence_html}</h3>"
            f"{body}{where_html}</div></div>"
        )
    return (
        '<section id="review">'
        + _section_head(
            "Review notes",
            "Before you merge",
            "Ordered by how much each one affects landing. Confirmed means checked "
            "against the code or a trial merge; Likely means read from the code but "
            "not run.",
        )
        + f'<div class="notes">{"".join(cards)}</div></section>'
    )


def _footer(data: dict[str, Any]) -> str:
    pr = data["pr"]
    head = html.escape(str(pr.get("head_sha", ""))[:7])
    base = html.escape(str(pr.get("base_sha", ""))[:7])
    generated = html.escape(str(data.get("generated_at", ""))[:10])
    base_name = html.escape(str(pr.get("base", "base")))
    if pr.get("base_sha_is_tip") is False:
        against = (
            f"the PR's recorded {base_name} base <code>{base}</code> (the "
            f"current tip of {base_name} could not be resolved, so this may be "
            "stale)"
        )
    else:
        against = f"{base_name} <code>{base}</code>"
    lines = [
        f"<span>Generated from head commit <code>{head}</code> against "
        f"{against} on {generated}.</span>"
    ]
    note = data["briefing"].get("footer_note", "")
    if str(note).strip():
        lines.append(f"<span>{inline(note)}</span>")
    return f"<footer>{''.join(lines)}</footer>"


def _nav(data: dict[str, Any]) -> str:
    briefing = data["briefing"]
    entries = []
    if _paragraphs(briefing.get("summary")) or briefing.get("at_a_glance"):
        entries.append(("summary", "Summary"))
    entries.append(("map", "File map"))
    for figure in briefing.get("figures") or []:
        entries.append((figure["id"], figure.get("nav") or figure.get("title", "")))
    if briefing.get("behavior_changes"):
        entries.append(("changes", "What users notice"))
    entries.append(("files", "File by file"))
    tests = briefing.get("tests") or {}
    if tests.get("rows") or tests.get("gaps"):
        entries.append(("tests", "Tests"))
    if briefing.get("review_notes"):
        entries.append(("review", "Before you merge"))
    links = "".join(
        f'<a href="#{anchor}">{inline(label)}</a>' for anchor, label in entries
    )
    return f'<nav class="toc" aria-label="Sections">{links}</nav>'


def _files_json(
    data: dict[str, Any], colors: dict[str, str], slugs: dict[str, str]
) -> str:
    payload = {
        "colors": colors,
        "files": [
            {
                "p": item["path"],
                "s": slugs[item["path"]],
                "c": item["category"],
                "a": item["additions"],
                "d": item["deletions"],
                "n": item.get("status") == "added",
            }
            for item in data["files"]
        ],
    }
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return (
        encoded.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    )


def _page_title(data: dict[str, Any]) -> str:
    repo_name = str(data["pr"]["repo"]).split("/")[-1]
    return f"{repo_name.capitalize()} PR {int(data['pr']['number'])} Briefing"


def render(data: dict[str, Any], *, output_format: str = "artifact") -> str:
    """Render briefing data to HTML; raise `BriefingError` on invalid data."""
    if output_format not in FORMATS:
        raise BriefingError(f"unknown format {output_format!r}")
    errors, _ = validate(data)
    if errors:
        raise BriefingError("; ".join(errors))
    colors = _category_colors(data["categories"])
    used: set[str] = set()
    slugs = {item["path"]: file_slug(item["path"], used) for item in data["files"]}
    briefing = data["briefing"]
    content = "".join(
        [
            _header(data),
            _nav(data),
            _summary(briefing),
            _map(data, colors),
            _figures(briefing),
            _behavior_changes(briefing),
            _files(data, colors, slugs),
            _tests(briefing),
            _review_notes(briefing),
            _footer(data),
        ]
    )
    template = (
        resources.files("lrh.pr_brief")
        .joinpath("templates", "briefing.html")
        .read_text(encoding="utf-8")
    )
    values = {
        "TITLE": html.escape(_page_title(data)),
        "FILES_JSON": _files_json(data, colors, slugs),
        "CONTENT": content,
    }
    page = _PLACEHOLDER_RE.sub(lambda match: values[match.group(1)], template)
    if output_format == "standalone":
        page = (
            '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"</head><body>\n{page}\n</body></html>\n"
        )
    return page

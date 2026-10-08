"""The LRH Console app frame shared by every Serve page.

The frame is a top bar (the LRH icon, which always goes home to the
statusboard, the page name and scope, snapshot time, refresh, and the gear),
a scoped sidebar that collapses to an icon rail with CSS only, the page
itself, and a detail drawer opened by ``?item=<id>``. It uses no scripts.

Serve wraps each HTML page in the frame when it writes the response, so page
renderers stay unchanged. Icons are Lucide SVGs (ISC license) packaged under
``static/icons`` and inlined so they take the text color; the LRH icon and the
Montserrat subset (SIL OFL) are served same-origin from ``static/``.
"""

from __future__ import annotations

import dataclasses
import datetime
import functools
import html
import importlib.resources
import re
import urllib.parse

HOME_PATH = "/meta"
SETTINGS_PATH = "/settings"
STATIC_PREFIX = "/static/"

# Every file /static/ may serve, with its content type. Nothing else is
# reachable through that route.
STATIC_FILES = {
    "lrh-icon-64.png": "image/png",
    "lrh-icon-128.png": "image/png",
    "fonts/montserrat-latin.woff2": "font/woff2",
    "fonts/OFL-montserrat.txt": "text/plain; charset=utf-8",
    "icons/LICENSE-lucide.txt": "text/plain; charset=utf-8",
}

ICON_NAMES = (
    "external-link",
    "folder",
    "house",
    "layers",
    "layout-dashboard",
    "network",
    "panel-left",
    "refresh-cw",
    "settings",
    "table",
    "triangle-alert",
    "x",
)

_BODY_OPEN = re.compile(r"<body[^>]*>")
_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.S)


@dataclasses.dataclass(frozen=True)
class Project:
    """One registered project, as the scope switcher lists it."""

    selector: str
    label: str


@dataclasses.dataclass(frozen=True)
class FrameContext:
    """What the frame needs to know about the current request."""

    path: str
    query: dict[str, str]
    projects: tuple[Project, ...] = ()
    rendered_at: datetime.datetime | None = None


def read_static(name: str) -> bytes | None:
    """Return a packaged static file's bytes, or None if it is not served."""

    if name not in STATIC_FILES:
        return None
    return (
        importlib.resources.files("lrh.ux")
        .joinpath("static", *name.split("/"))
        .read_bytes()
    )


@functools.cache
def icon(name: str) -> str:
    """Return a packaged Lucide icon as inline SVG, hidden from assistive tech."""

    if name not in ICON_NAMES:
        raise ValueError(f"unknown icon {name!r}")
    svg = (
        importlib.resources.files("lrh.ux")
        .joinpath("static", "icons", f"{name}.svg")
        .read_text(encoding="utf-8")
    )
    svg = " ".join(svg.split())
    return _SVG_OPEN.sub(
        lambda match: match.group(0)[:-1]
        + ' class="lrh-icon" aria-hidden="true" focusable="false">',
        svg,
        count=1,
    )


def scope_selector(path: str, query: dict[str, str]) -> str | None:
    """Return the project a page belongs to, or None for All projects."""

    if path.startswith("/project/"):
        parts = [part for part in path.removeprefix("/project/").split("/") if part]
        if parts:
            return urllib.parse.unquote(parts[0])
    if path == "/meta/project" and query.get("project"):
        return query["project"]
    return None


def apply_frame(page: str, context: FrameContext) -> str:
    """Wrap an HTML page's body in the app frame."""

    opening = _BODY_OPEN.search(page)
    closing = page.rfind("</body>")
    if opening is None or closing < opening.end():
        return page
    title_match = _TITLE.search(page)
    title = title_match.group(1).strip() if title_match else "LRH Console"
    before, body, after = (
        page[: opening.end()],
        page[opening.end() : closing],
        page[closing:],
    )
    return before + _frame_open(title, context) + body + _frame_close(context) + after


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _labels(context: FrameContext) -> tuple[str | None, str]:
    selector = scope_selector(context.path, context.query)
    if selector is None:
        return None, "All projects"
    for project in context.projects:
        if project.selector == selector:
            return selector, project.label
    return selector, selector


def _views(selector: str | None) -> list[tuple[str, str, str]]:
    if selector is None:
        return [
            ("Statusboard", HOME_PATH, "layout-dashboard"),
            ("Workspace", "/", "house"),
            ("Workbench", "/workbench", "network"),
            ("Conversations", "/conversations/codex", "table"),
            ("Style", "/style", "layers"),
        ]
    return [
        ("Overview", f"/project/{_quote(selector)}", "house"),
        ("Statusboard", HOME_PATH, "layout-dashboard"),
    ]


def _current_url(context: FrameContext, **overrides: str | None) -> str:
    query = {**context.query, **overrides}
    query = {key: value for key, value in query.items() if value is not None}
    encoded = urllib.parse.urlencode(query)
    return context.path + (f"?{encoded}" if encoded else "")


def _frame_open(title: str, context: FrameContext) -> str:
    selector, scope_label = _labels(context)
    rendered_at = context.rendered_at or datetime.datetime.now(datetime.UTC)
    stamp = rendered_at.astimezone(datetime.UTC).strftime("%H:%M:%S UTC")
    scope_items = [
        _scope_link("All projects", HOME_PATH, selector is None),
        *(
            _scope_link(
                project.label,
                f"/project/{_quote(project.selector)}",
                project.selector == selector,
            )
            for project in context.projects
        ),
    ]
    views = "".join(
        _view_link(label, href, name, href == context.path)
        for label, href, name in _views(selector)
    )
    refresh = html.escape(_current_url(context), quote=True)
    return f"""
<input type="checkbox" id="lrh-rail" class="lrh-rail-toggle">
<div class="lrh-frame">
  <header class="lrh-topbar">
    <a class="lrh-home" href="{HOME_PATH}">
      <img src="/static/lrh-icon-64.png" srcset="/static/lrh-icon-128.png 2x"
           width="28" height="28" alt="">
      <span class="lrh-brand">LRH Console</span>
      <span class="lrh-sr">, home</span>
    </a>
    <label for="lrh-rail" class="lrh-iconbtn lrh-rail-button">{icon("panel-left")}
      <span class="lrh-tip">Collapse or expand the sidebar</span></label>
    <div class="lrh-pagename">
      <span class="lrh-pagetitle">{title}</span>
      <span class="lrh-scopename">{html.escape(scope_label)}</span>
    </div>
    <div class="lrh-search-slot"></div>
    <span class="lrh-fresh">Rendered {stamp}</span>
    <a class="lrh-iconbtn" href="{refresh}">{icon("refresh-cw")}
      <span class="lrh-tip">Refresh</span></a>
    <a class="lrh-iconbtn" href="{SETTINGS_PATH}">{icon("settings")}
      <span class="lrh-tip">Settings</span></a>
  </header>
  <nav class="lrh-sidebar" aria-label="Scope and views">
    <details class="lrh-scope">
      <summary>{icon("folder")}<span class="lrh-label">{html.escape(scope_label)}</span>
        <span class="lrh-sr">: change scope</span></summary>
      <ul>{"".join(scope_items)}</ul>
    </details>
    <ul class="lrh-views">{views}</ul>
  </nav>
  <main class="lrh-main">"""


def _frame_close(context: FrameContext) -> str:
    return "\n  </main>\n" + _drawer(context) + "</div>\n"


def _scope_link(label: str, href: str, current: bool) -> str:
    marker = ' aria-current="true"' if current else ""
    return (
        f'<li><a href="{html.escape(href, quote=True)}"{marker}>'
        f"{html.escape(label)}</a></li>"
    )


def _view_link(label: str, href: str, name: str, current: bool) -> str:
    marker = ' aria-current="page"' if current else ""
    return (
        f'<li><a href="{html.escape(href, quote=True)}"{marker}>{icon(name)}'
        f'<span class="lrh-label">{html.escape(label)}</span></a></li>'
    )


def _drawer(context: FrameContext) -> str:
    item = context.query.get("item")
    if not item:
        return ""
    selector, _label = _labels(context)
    close = html.escape(_current_url(context, item=None), quote=True)
    if selector is None:
        full_page = (
            '<p class="lrh-muted">Choose a project scope to open this item\'s '
            "full page.</p>"
        )
    else:
        href = html.escape(
            f"/project/{_quote(selector)}/work-items/{_quote(item)}", quote=True
        )
        full_page = (
            f'<p><a href="{href}">{icon("external-link")} Open full page</a></p>'
        )
    return f"""  <aside class="lrh-drawer" aria-labelledby="lrh-drawer-title">
    <header>
      <h2 id="lrh-drawer-title" class="lrh-mono">{html.escape(item)}</h2>
      <a class="lrh-iconbtn" href="{close}">{icon("x")}
        <span class="lrh-tip">Close details</span></a>
    </header>
    <p class="lrh-muted">Item details arrive with the dependency map.</p>
    {full_page}
  </aside>
"""


FRAME_STYLES = """
  @font-face {
    font-family: "Montserrat";
    src: url("/static/fonts/montserrat-latin.woff2") format("woff2");
    font-weight: 100 900;
    font-display: swap;
  }
  .lrh-sr {
    border: 0; clip: rect(0 0 0 0); height: 1px; margin: -1px;
    overflow: hidden; padding: 0; position: absolute; white-space: nowrap;
    width: 1px;
  }
  .lrh-mono { font-family: var(--lrh-font-mono); }
  .lrh-icon { flex: none; height: 1.15rem; width: 1.15rem; }
  .lrh-rail-toggle { opacity: 0; pointer-events: none; position: absolute; }
  .lrh-frame {
    display: grid;
    grid-template-areas: "top top" "side main";
    grid-template-columns: 15rem minmax(0, 1fr);
    grid-template-rows: auto 1fr;
    min-height: 100vh;
  }
  .lrh-topbar {
    align-items: center;
    background: var(--lrh-color-surface-panel);
    border-bottom: 1px solid var(--lrh-color-border-subtle);
    box-sizing: border-box;
    display: flex;
    gap: var(--lrh-space-3);
    grid-area: top;
    height: 3.25rem;
    padding: var(--lrh-space-2) var(--lrh-space-4);
    position: sticky;
    top: 0;
    z-index: 5;
  }
  .lrh-home {
    align-items: center;
    display: inline-flex;
    gap: var(--lrh-space-2);
    text-decoration: none;
  }
  .lrh-home img { border-radius: var(--lrh-radius-sm); }
  .lrh-brand, .lrh-pagetitle {
    font-family: var(--lrh-font-display);
    font-weight: 700;
  }
  .lrh-pagename {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
    min-width: 0;
  }
  .lrh-pagetitle { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .lrh-scopename, .lrh-fresh { color: var(--lrh-color-text-muted); font-size: 0.85rem; }
  .lrh-search-slot { flex: 1; }
  .lrh-iconbtn {
    align-items: center;
    border-radius: var(--lrh-radius-sm);
    color: var(--lrh-color-text-primary);
    cursor: pointer;
    display: inline-flex;
    justify-content: center;
    padding: var(--lrh-space-2);
    position: relative;
  }
  .lrh-iconbtn:hover { background: var(--lrh-color-surface-sunken); }
  .lrh-tip {
    background: var(--lrh-color-text-primary);
    border-radius: var(--lrh-radius-sm);
    color: var(--lrh-color-surface-panel);
    font-size: 0.8rem;
    left: 50%;
    opacity: 0;
    padding: 0.2rem 0.5rem;
    pointer-events: none;
    position: absolute;
    top: calc(100% + 4px);
    transform: translateX(-50%);
    white-space: nowrap;
    z-index: 10;
  }
  .lrh-iconbtn:hover .lrh-tip, .lrh-iconbtn:focus-visible .lrh-tip,
  .lrh-rail-toggle:focus-visible ~ .lrh-frame .lrh-rail-button .lrh-tip {
    opacity: 1;
  }
  .lrh-iconbtn:focus-visible, .lrh-home:focus-visible,
  .lrh-sidebar a:focus-visible, .lrh-scope summary:focus-visible,
  .lrh-rail-toggle:focus-visible ~ .lrh-frame .lrh-rail-button {
    box-shadow: var(--lrh-focus-ring);
    outline: none;
  }
  .lrh-sidebar {
    background: var(--lrh-color-surface-panel);
    border-right: 1px solid var(--lrh-color-border-subtle);
    grid-area: side;
    padding: var(--lrh-space-3) var(--lrh-space-2);
  }
  .lrh-sidebar ul { list-style: none; margin: 0; padding: 0; }
  .lrh-scope { margin-bottom: var(--lrh-space-3); }
  .lrh-scope summary, .lrh-views a {
    align-items: center;
    border-radius: var(--lrh-radius-sm);
    cursor: pointer;
    display: flex;
    gap: var(--lrh-space-2);
    padding: var(--lrh-space-2);
    position: relative;
    text-decoration: none;
  }
  .lrh-scope summary { font-weight: 700; list-style: none; }
  .lrh-scope summary::-webkit-details-marker { display: none; }
  .lrh-scope ul {
    border-left: 2px solid var(--lrh-color-border-subtle);
    margin: var(--lrh-space-1) 0 0 var(--lrh-space-4);
  }
  .lrh-scope li a {
    display: block;
    padding: var(--lrh-space-1) var(--lrh-space-3);
    text-decoration: none;
  }
  .lrh-sidebar a[aria-current], .lrh-views a:hover, .lrh-scope summary:hover,
  .lrh-scope li a:hover {
    background: var(--lrh-color-action-accent-bg);
  }
  .lrh-sidebar a[aria-current] { font-weight: 700; }
  /* Long paths and URLs wrap, so pages never scroll sideways in the frame. */
  .lrh-main { grid-area: main; min-width: 0; overflow-wrap: anywhere; }
  .lrh-main .lrh-summary-grid > div { min-width: 0; }
  .lrh-main .lrh-app-shell { padding-top: var(--lrh-space-4); }
  /* The drawer overlays the page below the top bar, so the page keeps its width. */
  .lrh-drawer {
    background: var(--lrh-color-surface-overlay);
    border-left: 1px solid var(--lrh-color-border-strong);
    bottom: 0;
    box-shadow: var(--lrh-shadow-drawer);
    box-sizing: border-box;
    overflow-y: auto;
    padding: var(--lrh-space-4);
    position: fixed;
    right: 0;
    top: 3.25rem;
    width: min(26rem, 100vw);
    z-index: 4;
  }
  .lrh-drawer header {
    align-items: center;
    display: flex;
    justify-content: space-between;
  }
  .lrh-drawer h2 { font-size: 1.1rem; margin: 0; overflow-wrap: anywhere; }
  .lrh-drawer a { align-items: center; display: inline-flex; gap: var(--lrh-space-1); }

  /* The icon rail: labels hide, and show as tooltips on hover and focus. */
  .lrh-rail-toggle:checked ~ .lrh-frame {
    grid-template-columns: 3.5rem minmax(0, 1fr);
  }
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-scope ul { display: none; }
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-sidebar .lrh-label {
    background: var(--lrh-color-text-primary);
    border-radius: var(--lrh-radius-sm);
    color: var(--lrh-color-surface-panel);
    font-size: 0.8rem;
    font-weight: 400;
    left: calc(100% + 6px);
    opacity: 0;
    padding: 0.2rem 0.5rem;
    pointer-events: none;
    position: absolute;
    white-space: nowrap;
    z-index: 10;
  }
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-sidebar a:hover .lrh-label,
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-sidebar a:focus-visible .lrh-label,
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-scope summary:hover .lrh-label,
  .lrh-rail-toggle:checked ~ .lrh-frame .lrh-scope summary:focus-visible .lrh-label {
    opacity: 1;
  }

  /* Narrow screens: the rail is the default, and the drawer becomes the page. */
  @media (max-width: 48rem) {
    .lrh-frame { grid-template-columns: 3.5rem minmax(0, 1fr); }
    .lrh-fresh, .lrh-brand { display: none; }
    .lrh-scope ul { display: none; }
    .lrh-sidebar .lrh-label {
      background: var(--lrh-color-text-primary);
      border-radius: var(--lrh-radius-sm);
      color: var(--lrh-color-surface-panel);
      font-size: 0.8rem;
      left: calc(100% + 6px);
      opacity: 0;
      padding: 0.2rem 0.5rem;
      pointer-events: none;
      position: absolute;
      white-space: nowrap;
      z-index: 10;
    }
    .lrh-sidebar a:hover .lrh-label, .lrh-sidebar a:focus-visible .lrh-label,
    .lrh-scope summary:hover .lrh-label, .lrh-scope summary:focus-visible .lrh-label {
      opacity: 1;
    }
    .lrh-rail-toggle:checked ~ .lrh-frame {
      grid-template-columns: 15rem minmax(0, 1fr);
    }
    .lrh-rail-toggle:checked ~ .lrh-frame .lrh-scope ul { display: block; }
    .lrh-rail-toggle:checked ~ .lrh-frame .lrh-sidebar .lrh-label {
      background: none;
      color: inherit;
      font-size: inherit;
      opacity: 1;
      padding: 0;
      position: static;
    }
    .lrh-main .lrh-app-shell { padding: var(--lrh-space-3); }
    .lrh-drawer {
      left: 0;
      width: auto;
      z-index: 20;
    }
  }
"""

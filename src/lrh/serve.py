"""Safe-default local read-only HTTP viewer for ``lrh serve``."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import http.server
import json
import shlex
import socket
import socketserver
import sys
import urllib.parse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lrh import core_state, desktop_protocol
from lrh import version as lrh_version
from lrh.assist import run_packet, run_report, work_item_prompt_core
from lrh.control import loader as control_loader
from lrh.conversations import export_inspector
from lrh.dependency_maps import layout as dependency_map_layout
from lrh.dependency_maps import render as dependency_map_render
from lrh.dependency_maps import snapshot as dependency_map_snapshot
from lrh.dependency_maps import view as dependency_map_view
from lrh.meta import workspace as meta_workspace
from lrh.ux import dashboard, frame, tokens

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
UNSAFE_HOSTS = frozenset({"0.0.0.0", "::", ""})
THEMES = ("light", "dark", "system")
DEFAULT_THEME = "system"
_HTML_ROOT_TAG = '<html lang="en">'
_WORKBENCH_ARTIFACT_ROUTES = frozenset(
    {"/workbench/prompt", "/workbench/run-packet", "/workbench/run-report"}
)
_WORKBENCH_API_ROUTES = frozenset(
    {"/api/workbench/prompt", "/api/workbench/run-packet", "/api/workbench/run-report"}
)
_STATUS_ROUTES = (
    "/",
    "/workbench",
    "/workbench/prompt",
    "/workbench/run-packet",
    "/workbench/run-report",
    "/conversations/codex",
    "/conversations/codex/<export_id>",
    "/meta",
    "/meta/project",
    "/style",
    "/settings",
    "/static/<asset>",
    "/project/<project_id>",
    "/project/<project_id>/designs/<design_id>",
    "/project/<project_id>/workstreams/<workstream_id>",
    "/project/<project_id>/work-items/<work_item_id>",
    "/project/<project_id>/dependency-maps",
    "/project/<project_id>/dependency-maps/<view>",
    "/project/<project_id>/work-items/<work_item_id>/prompt",
    "/health",
    "/api/status",
    "/api/project",
    "/api/project/<project_id>/dependency-maps/<view>",
    "/api/workbench",
    "/api/conversations/codex",
    "/api/conversations/codex/<export_id>",
    "/api/meta",
    "/api/workbench/prompt",
    "/api/workbench/run-packet",
    "/api/workbench/run-report",
)


@dataclass(frozen=True)
class ServeConfig:
    """Configuration for the safe-default local LRH server."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    project_root: Path = Path(".")
    allow_nonlocal_host: bool = False
    codex_archive_roots: tuple[Path, ...] = ()
    theme: str = DEFAULT_THEME
    interactive: bool = False

    def resolved_project_root(self) -> Path:
        """Return the deterministic absolute project root used for status labels."""

        root = self.project_root.expanduser().resolve()
        try:
            project_dir = control_loader.find_project_dir(root)
        except FileNotFoundError:
            return root
        if project_dir.name == "project":
            return project_dir.parent
        return project_dir


_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; "
    "font-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
    "form-action 'none'"
)
# --interactive adds only same-origin scripts: never inline script or eval.
_INTERACTIVE_CONTENT_SECURITY_POLICY = _CONTENT_SECURITY_POLICY + "; script-src 'self'"
_INTERACTIVE_SCRIPT = "lrh-interactive.js"
_THEME_EARLY_SCRIPT = "lrh-theme-early.js"
_INTERACTIVE_SCRIPTS = frozenset({_INTERACTIVE_SCRIPT, _THEME_EARLY_SCRIPT})
_INTERACTIVE_SCRIPT_TAG = f'<script src="/static/{_INTERACTIVE_SCRIPT}" defer></script>'
# Runs before first paint so a stored theme does not flash; tiny and blocking.
_THEME_EARLY_SCRIPT_TAG = f'<script src="/static/{_THEME_EARLY_SCRIPT}"></script>'


def content_security_policy(config: ServeConfig) -> str:
    """Return the policy for this server: script-free unless --interactive."""

    if config.interactive:
        return _INTERACTIVE_CONTENT_SECURITY_POLICY
    return _CONTENT_SECURITY_POLICY


def apply_interactive(page: str, interactive: bool) -> str:
    """Add the packaged script to an HTML page's head under --interactive."""

    if not interactive or "<head>" not in page or "</head>" not in page:
        return page
    page = page.replace("<head>", "<head>" + _THEME_EARLY_SCRIPT_TAG, 1)
    return page.replace("</head>", _INTERACTIVE_SCRIPT_TAG + "</head>", 1)


def _frame_projects(config: ServeConfig) -> tuple[frame.Project, ...]:
    """Return the registered projects for the scope switcher, or none."""

    try:
        workspace = meta_workspace.resolve_meta_workspace(
            cwd=config.resolved_project_root(),
            options=meta_workspace.MetaWorkspaceResolveOptions(),
        )
        results = meta_workspace.list_registered_project_loads_in_workspace(workspace)
    except (
        meta_workspace.MetaWorkspaceResolutionError,
        meta_workspace.MetaRegistryError,
        OSError,
        ValueError,
    ):
        # The frame is best-effort: a broken registry must not break pages.
        return ()
    # A record that fails to load is still listed, by its registry name, so
    # the dashboard page for its unavailable card stays reachable.
    return tuple(
        frame.Project(
            selector=result.registry_name,
            label=(result.record and result.record.display_name)
            or result.registry_name,
        )
        for result in results
    )


def dependency_map_payload(
    config: ServeConfig, remainder: str
) -> tuple[int, dict[str, object]]:
    """Answer ``/api/project/<project_id>/dependency-maps/<view>`` read-only.

    Returns the versioned snapshot JSON, 404 for a malformed path, an unknown
    project, or an unknown view, 409 for a registered project with no local
    checkout, 422 for an invalid view declaration, or 500 if the project's
    control files cannot be loaded.
    """

    parts = [urllib.parse.unquote(part) for part in remainder.split("/") if part]
    if len(parts) != 3 or parts[1] != "dependency-maps":
        return 404, {"error": "not_found"}
    project_selector, _, view_id = parts
    try:
        repo_root = _config_for_project_selector(
            config, project_selector
        ).resolved_project_root()
    except ProjectSelectorError as error:
        return error.status, error.to_payload()
    try:
        snapshot = dependency_map_snapshot.build_snapshot(repo_root, view_id)
    except FileNotFoundError:
        return 404, {"error": "not_found", "view": view_id}
    except dependency_map_view.ViewDeclarationError as err:
        return 422, {"error": "invalid_view", "problems": list(err.problems)}
    except dependency_map_snapshot.SnapshotError as err:
        return 500, {"error": "snapshot_failed", "message": str(err)}
    return 200, snapshot.to_dict()


def render_dependency_map_page(
    config: ServeConfig,
    project_selector: str,
    view_id: str | None,
    query: dict[str, str],
) -> tuple[int, str]:
    """Render a dependency-map view, or the project's list of views.

    Returns 404 for an unknown view, 422 for an invalid declaration, and 500
    if the sources cannot be read; the last two render an explanatory page, as
    do an unknown project (404) and a project with no local checkout (409).
    """

    try:
        repo_root = _config_for_project_selector(
            config, project_selector
        ).resolved_project_root()
    except ProjectSelectorError as error:
        return error.status, render_project_selector_error_page(error)
    base = f"/project/{_url_quote(project_selector)}/dependency-maps"
    if view_id is None:
        return 200, _dependency_map_document(
            "Dependency maps", _dependency_map_index(repo_root, base)
        )
    try:
        snapshot = dependency_map_snapshot.build_snapshot(repo_root, view_id)
    except FileNotFoundError:
        return 404, ""
    except dependency_map_view.ViewDeclarationError as err:
        problems = "".join(
            f"<li>{html.escape(problem)}</li>" for problem in err.problems
        )
        body = (
            '<header class="lrh-page-header"><p class="lrh-eyebrow">Dependency map</p>'
            f"<h1>{html.escape(view_id)}: invalid view</h1>"
            f"<p>Fix <code>{html.escape(err.path)}</code>; "
            "<code>lrh validate</code> reports the same problems.</p></header>"
            f'<section class="lrh-console-region"><ul>{problems}</ul></section>'
        )
        return 422, _dependency_map_document(f"{view_id}: invalid view", body)
    except dependency_map_snapshot.SnapshotError as err:
        body = (
            '<header class="lrh-page-header"><p class="lrh-eyebrow">Dependency map</p>'
            f"<h1>{html.escape(view_id)}: unavailable</h1>"
            f"<p>{html.escape(str(err))}</p></header>"
        )
        return 500, _dependency_map_document(f"{view_id}: unavailable", body)
    selector = _url_quote(project_selector)
    body = dependency_map_render.render_view(
        snapshot,
        dependency_map_layout.DEFAULT_LAYOUT,
        tab=query.get("tab", "map"),
        item=query.get("item"),
        since=query.get("since"),
        interactive=config.interactive,
        full_page_href=lambda item_id: (
            f"/project/{selector}/work-items/{_url_quote(item_id)}"
        ),
    )
    return 200, _dependency_map_document(snapshot.view_title, body)


def _dependency_map_index(repo_root: Path, base: str) -> str:
    paths = dependency_map_view.discover_views(repo_root)
    if not paths:
        return (
            '<header class="lrh-page-header"><p class="lrh-eyebrow">Dependency maps</p>'
            "<h1>No dependency-map views</h1>"
            "<p>This project declares none yet. Add one at "
            "<code>project/views/dependency_maps/&lt;name&gt;.md</code>; see the "
            "<code>lrh dependency-map</code> reference.</p></header>"
        )
    items = []
    for path in paths:
        try:
            view = dependency_map_view.parse_view(path, repo_root)
            label = html.escape(view.title)
        except (dependency_map_view.ViewDeclarationError, OSError):
            label = "Invalid declaration"
        href = html.escape(base + "/" + _url_quote(path.stem), quote=True)
        items.append(
            f'<li><a href="{href}">'
            f"{label}</a> <code>{html.escape(path.stem)}</code></li>"
        )
    return (
        '<header class="lrh-page-header"><p class="lrh-eyebrow">Dependency maps</p>'
        "<h1>Dependency maps</h1></header>"
        f'<section class="lrh-console-region"><ul>{"".join(items)}</ul></section>'
    )


def _dependency_map_document(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(title)}</title>{_base_styles()}
<style>{dependency_map_render.MAP_STYLES}</style></head>
<body>
  <div class="lrh-app-shell lrh-map-shell" data-lrh-own-drawer>
{body}
  </div>
</body>
</html>
"""


def dependency_map_head_status(config: ServeConfig, remainder: str) -> int:
    """Return the status GET would give for a dependency-map path.

    HEAD builds the snapshot exactly as GET does, so the two always agree,
    including a 500 when another control file cannot be read.
    """

    parts = [urllib.parse.unquote(part) for part in remainder.split("/") if part]
    if len(parts) != 3 or parts[1] != "dependency-maps":
        return 404
    try:
        repo_root = _config_for_project_selector(
            config, parts[0]
        ).resolved_project_root()
    except ProjectSelectorError as error:
        return error.status
    try:
        dependency_map_snapshot.build_snapshot(repo_root, parts[2])
    except FileNotFoundError:
        return 404
    except dependency_map_view.ViewDeclarationError:
        return 422
    except dependency_map_snapshot.SnapshotError:
        return 500
    return 200


def render_settings_page(config: ServeConfig) -> str:
    """Render the read-only display and about page the gear opens in a browser.

    LRH Console intercepts this path and opens its native Settings window.
    """

    theme = html.escape(config.theme)
    version = html.escape(str(lrh_version.get_installed_version() or "unknown"))
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Display and about</title>{_base_styles()}</head>
<body>
  <div class="lrh-app-shell">
    <header class="lrh-page-header">
      <p class="lrh-eyebrow">LRH Console</p>
      <h1>Display and about</h1>
      <p class="lrh-muted">Read-only. In the LRH Console app, the gear opens
      Settings instead.</p>
    </header>
    <main class="lrh-main-content">
      <section class="lrh-console-region">
        <h2>Theme</h2>
        <p>This server uses the <strong>{theme}</strong> theme.
        <code>system</code> follows your operating system's light or dark
        appearance.</p>
        <p>To choose, restart the server with
        <code>lrh serve --theme light</code>, <code>--theme dark</code>, or
        <code>--theme system</code>. In LRH Console, use
        <strong>Settings &gt; Appearance</strong>.</p>
      </section>
      <section class="lrh-console-region">
        <h2>About</h2>
        <dl class="lrh-summary-grid">
          <div><dt>lrh</dt><dd class="lrh-mono">{version}</dd></div>
          <div><dt>Mode</dt><dd>Read-only local viewer</dd></div>
        </dl>
        <h3>Licenses</h3>
        <ul>
          <li>Montserrat, SIL Open Font License 1.1:
            <a href="/static/fonts/OFL-montserrat.txt">license text</a></li>
          <li>Lucide icons, ISC License:
            <a href="/static/icons/LICENSE-lucide.txt">license text</a></li>
        </ul>
      </section>
    </main>
  </div>
</body>
</html>
"""


def apply_theme(page: str, theme: str) -> str:
    """Pin an HTML page to ``theme``; ``system`` leaves it following the OS.

    Every page renders a bare ``<html lang="en">`` root, so its token
    stylesheet follows ``prefers-color-scheme`` unless a theme is pinned here.
    """

    if theme not in THEMES:
        raise ValueError(f"unknown theme {theme!r}; expected one of {THEMES}")
    if theme == "system":
        return page
    return page.replace(_HTML_ROOT_TAG, f'<html lang="en" data-theme="{theme}">', 1)


def validate_host(config: ServeConfig) -> None:
    """Reject non-local hosts unless the caller explicitly opts in."""

    if config.host in LOCAL_HOSTS:
        return
    if config.allow_nonlocal_host:
        return
    if config.host in UNSAFE_HOSTS:
        raise ValueError(
            f"refusing to bind to {config.host!r}; lrh serve is local-only by "
            "default. Re-run with --allow-nonlocal-host only after reviewing "
            "the documented exposure risk."
        )
    raise ValueError(
        f"refusing to bind to non-local host {config.host!r}; lrh serve defaults "
        "to 127.0.0.1. Re-run with --allow-nonlocal-host only after reviewing "
        "the documented exposure risk."
    )


def status_payload(
    config: ServeConfig,
    bound_address: tuple[object, ...] | None = None,
) -> dict[str, object]:
    """Return deterministic viewer status data without exposing file contents."""

    project_root = config.resolved_project_root()
    host, port = _host_port_from_address(config, bound_address)
    codex_archive_roots = _configured_codex_archive_roots(config)
    return {
        "service": "lrh serve",
        "status": "ok",
        "mode": "safe-default-read-only-viewer",
        "host": host,
        "port": port,
        "project_root_name": project_root.name,
        "codex_archive_root_count": len(codex_archive_roots),
        "codex_archive_root_names": [
            _codex_archive_root_label(root) for root in codex_archive_roots
        ],
        "theme": config.theme,
        "interactive": config.interactive,
        "routes": list(_STATUS_ROUTES),
        "capabilities": _safe_capabilities(),
    }


def render_index(
    config: ServeConfig,
    bound_address: tuple[object, ...] | None = None,
) -> str:
    """Render a minimal package-owned read-only project viewer page."""

    status = status_payload(config, bound_address=bound_address)
    payload = project_viewer_payload(config)
    project_name = html.escape(str(status["project_root_name"]))
    host = html.escape(str(status["host"]))
    port = html.escape(str(status["port"]))
    validation = payload["validation"]
    focus = payload["current_focus"]
    focus_text = "Unknown / unavailable"
    if isinstance(focus, dict):
        focus_text = f"{focus['id']} — {focus['title']} ({focus['status']})"
    active_workstreams = _html_list(
        _artifact_label(workstream) for workstream in payload["active_workstreams"]
    )
    active_leaves = _html_list(
        _artifact_label(item) for item in payload["planning"]["active_leaves"]
    )
    ready_items = _html_list(
        _ready_item_label(item) for item in payload["execution"]["ready_work_items"]
    )
    diagnostics = _html_list(
        _diagnostic_label(diagnostic) for diagnostic in payload["diagnostics"]
    )
    evidence_summary = _evidence_summary_label(payload)
    validation_badge_class = _status_badge_class(str(validation["status"]))
    validation_label = _status_badge_label(str(validation["status"]))
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>LRH Serve</title>
  {styles}
</head>
<body>
  <div class=\"lrh-app-shell\">
    <header class=\"lrh-page-header\">
      <p class=\"lrh-eyebrow\">LRH Console preview</p>
      <h1>Logical Robotics Harness</h1>
      <p>Safe-default read-only project viewer with a local preview workbench.</p>
      <aside class=\"lrh-guardrail-callout\" aria-label=\"Safe-default guardrails\">
        This viewer summarizes existing LRH project-control state. The workbench
        can render prompt, run-packet, and run-report previews only after an
        explicit local link click. It does not serve arbitrary files, dispatch
        agents, mutate branches, create pull requests, make external network calls,
        execute rendered content, or provide write routes.
      </aside>
    </header>
    <nav class=\"lrh-control-spine\" aria-label=\"Read-only LRH serve navigation\">
      <a href=\"#system-overview\">System overview</a>
      <a href=\"#project-summary\">Project summary</a>
      <a href=\"#evidence-summary\">Evidence summary</a>
      <a href=\"#validation-summary\">Validation summary</a>
      <a href=\"/workbench\">Open preview workbench</a>
    </nav>
    <main id=\"main-content\" class=\"lrh-main-content\">
      <section id=\"system-overview\" class=\"lrh-system-overview\"
        aria-labelledby=\"system-overview-heading\">
        <h2 id=\"system-overview-heading\">System overview</h2>
        <dl class=\"lrh-summary-grid\">
          <div><dt>Project</dt><dd>{project_name}</dd></div>
          <div><dt>Bind</dt><dd>{host}:{port}</dd></div>
          <div><dt>Validation</dt><dd><span
            class=\"lrh-status-badge {validation_badge_class}\">
            {validation_label}</span></dd></div>
          <div><dt>Current focus</dt><dd>{focus_text}</dd></div>
          <div><dt>Work items</dt><dd>{work_item_count}</dd></div>
          <div><dt>Workstreams</dt><dd>{workstream_count}</dd></div>
        </dl>
      </section>
      <section id=\"project-summary\" class=\"lrh-project-summary\"
        aria-labelledby=\"project-summary-heading\">
        <h2 id=\"project-summary-heading\">Project summary</h2>
        <section class=\"lrh-console-region\"
          aria-labelledby=\"active-workstreams-heading\">
          <h3 id=\"active-workstreams-heading\">Active workstreams</h3>
          {active_workstreams}
        </section>
        <section class=\"lrh-console-region\" aria-labelledby=\"active-leaves-heading\">
          <h3 id=\"active-leaves-heading\">Active leaf work items</h3>
          {active_leaves}
        </section>
        <section class=\"lrh-console-region\"
          aria-labelledby=\"execution-ready-heading\">
          <h3 id=\"execution-ready-heading\">Execution-ready leaves</h3>
          <p>Workbench packet and report previews are local in-memory renderings;
          they are not execution evidence and do not imply work has run.</p>
          {ready_items}
        </section>
      </section>
      <section id=\"evidence-summary\" class=\"lrh-evidence-summary\"
        aria-labelledby=\"evidence-summary-heading\">
        <h2 id=\"evidence-summary-heading\">Evidence summary</h2>
        <p>{evidence_summary}</p>
      </section>
      <section id=\"validation-summary\" class=\"lrh-validation-summary\"
        aria-labelledby=\"validation-summary-heading\">
        <h2 id=\"validation-summary-heading\">Validation summary</h2>
        <p><span
          class=\"lrh-status-badge {validation_badge_class}\">{validation_label}</span>
        ({error_count} errors, {warning_count} warnings)</p>
        {diagnostics}
      </section>
      <section class=\"lrh-console-region\" aria-labelledby=\"read-only-api-heading\">
        <h2 id=\"read-only-api-heading\">Read-only API</h2>
        <ul>
          <li><a href=\"/health\">/health</a></li>
          <li><a href=\"/api/status\">/api/status</a></li>
          <li><a href=\"/api/project\">/api/project</a></li>
        </ul>
      </section>
      <section class=\"lrh-console-region\" aria-labelledby=\"workbench-heading\">
        <h2 id=\"workbench-heading\">Prompt/packet/report workbench</h2>
        <p><a href=\"/workbench\">Open the local preview workbench</a>.</p>
      </section>
    </main>
  </div>
</body>
</html>
""".format(
        styles=_base_styles(),
        project_name=project_name,
        host=host,
        port=port,
        validation_badge_class=validation_badge_class,
        validation_label=validation_label,
        error_count=validation["error_count"],
        warning_count=validation["warning_count"],
        focus_text=html.escape(focus_text),
        work_item_count=payload["work_items"]["total"],
        workstream_count=payload["workstreams"]["total"],
        active_workstreams=active_workstreams,
        active_leaves=active_leaves,
        ready_items=ready_items,
        diagnostics=diagnostics,
        evidence_summary=html.escape(evidence_summary),
    )


def project_viewer_payload(config: ServeConfig) -> dict[str, Any]:
    """Return a deterministic read-only project viewer summary."""

    try:
        state = core_state.load_core_project_state(config.resolved_project_root())
    except FileNotFoundError as err:
        project_root = config.resolved_project_root()
        return {
            "mode": "safe-default-read-only-viewer",
            "project": {
                "name": project_root.name,
                "identity_source": "project-root-name",
            },
            "validation": {
                "status": "error",
                "is_valid": False,
                "error_count": 1,
                "warning_count": 0,
            },
            "current_focus": None,
            "workstreams": _empty_grouped_summary(),
            "active_workstreams": [],
            "work_items": _empty_grouped_summary(),
            "planning": {
                "relationship_count": 0,
                "relationships": [],
                "active_leaf_ids": [],
                "active_leaves": [],
                "status_counts_by_kind": {},
                "cycles": [],
            },
            "execution": {
                "active_leaf_count": 0,
                "ready_count": 0,
                "ready_work_items": [],
                "packet_surface": "lrh request run-packet-from-work-item",
                "report_surface": "lrh request run-report-from-work-item",
            },
            "diagnostics": [
                {
                    "source": "serve",
                    "file": "project/",
                    "severity": "error",
                    "code": "PROJECT_CONTROL_DIR_NOT_FOUND",
                    "message": str(err),
                }
            ],
            "capabilities": _safe_capabilities(),
        }

    diagnostics = [*_diagnostic_dicts(state.validation.diagnostics)]
    diagnostics.extend(_diagnostic_dicts(state.planning.diagnostics))
    return {
        "mode": "safe-default-read-only-viewer",
        "project": {
            "name": state.identity.project_name,
            "identity_source": "project-root-name",
            "control_dir_name": state.identity.project_dir.name,
        },
        "validation": {
            "status": "valid" if state.validation.is_valid else "error",
            "is_valid": state.validation.is_valid,
            "error_count": state.validation.error_count,
            "warning_count": state.validation.warning_count,
        },
        "current_focus": _focus_dict(state.current_focus, state),
        "workstreams": _workstream_summary(state),
        "active_workstreams": [
            _workstream_dict(workstream, state)
            for workstream in state.workstreams
            if workstream.status == "active"
        ],
        "work_items": _work_item_summary(state),
        "planning": {
            "relationship_count": len(state.planning.relationships),
            "relationships": [
                {
                    "parent_id": relationship.parent_id,
                    "child_id": relationship.child_id,
                    "source_id": relationship.source_id,
                    "source_field": relationship.source_field,
                }
                for relationship in state.planning.relationships
            ],
            "active_leaf_ids": list(state.planning.active_leaf_ids),
            "active_leaves": [
                _work_item_dict(item, state) for item in state.active_leaf_work_items
            ],
            "status_counts_by_kind": {
                kind: dict(counts)
                for kind, counts in sorted(state.planning.status_counts_by_kind.items())
            },
            "cycles": [list(cycle) for cycle in state.planning.cycles],
        },
        "execution": _execution_summary(state),
        "diagnostics": diagnostics,
        "capabilities": _safe_capabilities(),
    }


def meta_dashboard_payload(config: ServeConfig) -> dict[str, object]:
    """Return a read-only operational triage dashboard for registered projects."""

    try:
        workspace = meta_workspace.resolve_meta_workspace(
            cwd=config.resolved_project_root(),
            options=meta_workspace.MetaWorkspaceResolveOptions(),
        )
        load_results = meta_workspace.list_registered_project_loads_in_workspace(
            workspace
        )
        workspace_payload: dict[str, object] = {
            "mode": workspace.mode,
            "resolution_source": workspace.resolution_source,
            "catalog_root_name": workspace.catalog_root.name,
        }
    except (
        meta_workspace.MetaWorkspaceResolutionError,
        meta_workspace.MetaRegistryError,
    ) as err:
        load_results = ()
        workspace_payload = {
            "mode": "unknown",
            "resolution_source": "unavailable",
            "error": str(err),
        }

    cards = [
        _operational_card_from_load_result(workspace, result) for result in load_results
    ]
    meta_view = dashboard.build_meta_dashboard(cards)
    read_at = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    return {
        "mode": "safe-default-read-only-meta-triage",
        "read_at": read_at.isoformat(),
        "workspace": workspace_payload,
        "total_projects": meta_view.total_projects,
        "lanes": [
            {
                "status": lane.status.value,
                "label": lane.label,
                "description": lane.description,
                "count": lane.count,
                "projects": [
                    _operational_card_payload(project) for project in lane.projects
                ],
            }
            for lane in meta_view.lanes
        ],
        "capabilities": _safe_capabilities(),
    }


def render_meta_dashboard(config: ServeConfig) -> str:
    """Render the read-only statusboard: one band per operational state.

    Bands come first; the workspace, guardrail, and API notes follow them.
    Every band is a ``<details>`` element, so it collapses without scripts.
    """

    payload = meta_dashboard_payload(config)
    workspace = payload["workspace"]
    workspace_note = "Meta workspace available."
    if isinstance(workspace, dict) and workspace.get("error"):
        workspace_note = f"Meta workspace unavailable: {workspace['error']}"
    read_at = str(payload.get("read_at") or "")
    band_html = "".join(_meta_lane_html(lane, read_at) for lane in payload["lanes"])
    total = payload["total_projects"]
    if total == 0:
        summary = (
            "No registered projects are available in the active meta workspace. "
            "Register one with <code>lrh meta register</code>."
        )
    else:
        noun = "project" if total == 1 else "projects"
        summary = f"{html.escape(str(total))} registered {noun}, by operational state."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Statusboard</title>
  {_base_styles()}
  <style>{STATUSBOARD_STYLES}</style>
</head>
<body>
  <div class="lrh-app-shell">
    <header class="lrh-page-header lrh-statusboard-header">
      <h1>Statusboard</h1>
      <p>{summary}</p>
    </header>
    <main id="main-content" class="lrh-main-content">
      <div class="lrh-bands">{band_html}</div>
      <section class="lrh-console-region lrh-statusboard-about"
        aria-labelledby="meta-about-heading">
        <h2 id="meta-about-heading">About this view</h2>
        <p>{html.escape(workspace_note)}</p>
        <p>Each project is in exactly one band, chosen from its control-plane
        state: Blocked first, then Needs attention, Active work, Awaiting review,
        Stable, and Unknown when LRH cannot tell.</p>
        <p class="lrh-muted">This safe-default, read-only view summarizes registered
        projects from the LRH meta workspace. It does not inspect arbitrary files,
        expose secrets, dispatch agents, create branches, commit, open pull requests,
        merge, release, publish, or provide write routes. Meta workspace state is
        informative only; project-local project/ control planes remain
        authoritative.</p>
        <p>Read-only API: <a href="/api/meta">/api/meta</a></p>
      </section>
    </main>
  </div>
</body>
</html>
"""


def render_meta_project_placeholder(project_selector: str) -> str:
    """Render a deterministic placeholder for future project detail pages."""

    selector = html.escape(project_selector or "unknown")
    return """<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>LRH Meta Project</title>{styles}</head>
<body>
  <div class=\"lrh-app-shell\">
    <header class=\"lrh-page-header\">
      <p class=\"lrh-eyebrow\">LRH Console preview</p>
      <h1>Project detail: {selector}</h1>
      <p><a href=\"/meta\">Back to meta triage dashboard</a></p>
    </header>
    <main class=\"lrh-main-content\">
      <section class=\"lrh-console-region\">
        <h2>Not implemented yet</h2>
        <p>This read-only detail route is reserved for future project inspectors.
        No repository mutation, arbitrary file browsing, or agent dispatch is
        available.</p>
      </section>
    </main>
  </div>
</body>
</html>
""".format(styles=_base_styles(), selector=selector)


_SPECIMEN_STATES = (
    ("done", "Done", "\u2713"),
    ("progress", "In progress", "\u25b6"),
    ("unblocked", "Unblocked", "\u25cb"),
    ("waiting", "Waiting", "\u29d7"),
    ("blocked", "Blocked", "\u2715"),
    ("review", "Awaiting review", "\u25ce"),
    ("unknown", "Unknown", "?"),
)
_SPECIMEN_BANDS = (
    ("needs-attention", "Needs attention"),
    ("blocked", "Blocked"),
    ("active-work", "Active work"),
    ("awaiting-review", "Awaiting review"),
    ("stable", "Stable"),
    ("unknown", "Unknown"),
)
_SPECIMEN_STYLES = """<style>
  .lrh-specimen-row { display: flex; flex-wrap: wrap; gap: var(--lrh-space-3); }
  .lrh-swatch {
    border: 1px solid var(--lrh-color-border-strong);
    border-radius: var(--lrh-radius-sm);
    min-width: 9rem;
    padding: var(--lrh-space-3);
  }
  .lrh-swatch code, .lrh-specimen-id { font-family: var(--lrh-font-mono); }
  .lrh-specimen-display { font-family: var(--lrh-font-display); font-weight: 700; }
  .lrh-pill {
    border: 1px solid currentColor;
    border-radius: var(--lrh-radius-pill);
    display: inline-block;
    font-weight: 700;
    padding: 0.15rem 0.6rem;
  }
  .lrh-card {
    background: var(--lrh-color-surface-panel);
    border: 1px solid var(--lrh-color-border-subtle);
    border-inline-start: 4px solid var(--card-line);
    border-radius: var(--lrh-radius-md);
    min-width: 12rem;
    padding: var(--lrh-space-3);
  }
  .lrh-card--blocked { border-style: dashed; border-inline-start-style: solid; }
  .lrh-band {
    border-inline-start: 6px solid var(--band-line);
    border-radius: var(--lrh-radius-sm);
    margin-block: var(--lrh-space-2);
  }
  .lrh-band h3 {
    background: var(--band-bg);
    color: var(--band-fg);
    margin: 0;
    padding: var(--lrh-space-2) var(--lrh-space-3);
  }
  .lrh-focus-sample:focus-visible, .lrh-focus-sample--shown {
    box-shadow: var(--lrh-focus-ring);
    outline: none;
  }
  .lrh-sunken {
    background: var(--lrh-color-surface-sunken);
    border-radius: var(--lrh-radius-md);
    padding: var(--lrh-space-3);
  }
</style>"""


def render_style_specimen() -> str:
    """Render a read-only specimen of the shared tokens in the current theme.

    Like every page, it follows the system appearance unless ``--theme`` pins one.
    """

    surfaces = "".join(
        f'<div class="lrh-swatch" style="background: var(--lrh-color-surface-{name})">'
        f'<span class="lrh-specimen-display">Aa</span> <span class="lrh-muted">'
        f"muted</span><br><code>surface-{name}</code></div>"
        for name in ("page", "panel", "sunken", "overlay")
    )
    pills = "".join(
        f'<span class="lrh-pill" style="background: var(--lrh-color-status-{key}-bg);'
        f' color: var(--lrh-color-status-{key}-fg)">'
        f'<span aria-hidden="true">{icon}</span> {label}</span>'
        for key, label, icon in _SPECIMEN_STATES
    )
    cards = "".join(
        f'<div class="lrh-card{" lrh-card--blocked" if key == "blocked" else ""}"'
        f' style="--card-line: var(--lrh-color-status-{key}-line)">'
        f'<span class="lrh-specimen-id">WI-EXAMPLE-{index}</span><br>'
        f"Example work item<br>"
        f'<span class="lrh-pill" style="background: var(--lrh-color-status-{key}-bg);'
        f' color: var(--lrh-color-status-{key}-fg)">'
        f'<span aria-hidden="true">{icon}</span> {label}</span></div>'
        for index, (key, label, icon) in enumerate(_SPECIMEN_STATES, start=1)
    )
    bands = "".join(
        f'<section class="lrh-band" style="--band-bg: var(--lrh-color-band-{key}-bg);'
        f" --band-fg: var(--lrh-color-band-{key}-fg);"
        f' --band-line: var(--lrh-color-band-{key}-line)">'
        f'<h3>{label} <span class="lrh-muted">(0)</span></h3></section>'
        for key, label in _SPECIMEN_BANDS
    )
    line_rows = [
        ("edge", "solid", "Depends on"),
        ("edge", "dashed", "Blocked by"),
        ("edge-strong", "solid", "Selected"),
    ] + [(f"status-{key}-line", "solid", label) for key, label, _ in _SPECIMEN_STATES]
    lines = "".join(
        f'<svg width="260" height="24" role="img" aria-label="{label} line">'
        f'<line x1="4" y1="12" x2="140" y2="12"'
        f' style="stroke: var(--lrh-color-{token}); stroke-width: 2;'
        f' stroke-dasharray: {"6 4" if dash == "dashed" else "none"}"/>'
        f'<text x="150" y="16" style="fill: var(--lrh-color-text-muted);'
        f' font-size: 12px">{label}</text></svg>'
        for token, dash, label in line_rows
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>LRH Style Specimen</title>{_base_styles()}
{_SPECIMEN_STYLES}</head>
<body>
  <div class="lrh-app-shell">
    <header class="lrh-page-header">
      <p class="lrh-eyebrow">LRH Console preview</p>
      <h1 class="lrh-specimen-display">Style specimen</h1>
      <p class="lrh-muted">Every shared token in the current theme: the system
      appearance, unless <code>lrh serve --theme</code> pins light or dark.</p>
    </header>
    <main class="lrh-main-content">
      <section class="lrh-console-region"><h2>Surfaces and text</h2>
        <div class="lrh-specimen-row">{surfaces}</div></section>
      <section class="lrh-console-region"><h2>Status</h2>
        <div class="lrh-specimen-row">{pills}</div>
        <div class="lrh-sunken lrh-specimen-row">{pills}</div></section>
      <section class="lrh-console-region"><h2>Cards</h2>
        <div class="lrh-specimen-row">{cards}</div></section>
      <section class="lrh-console-region"><h2>Bands</h2>{bands}</section>
      <section class="lrh-console-region"><h2>Lines</h2>
        <div class="lrh-specimen-row">{lines}</div>
        <div class="lrh-sunken lrh-specimen-row">{lines}</div></section>
      <section class="lrh-console-region"><h2>Focus and action</h2>
        <p><a class="lrh-focus-sample" href="/style">A focusable link</a>
        <span class="lrh-pill lrh-focus-sample--shown">Focus ring</span>
        <span class="lrh-pill" style="background: var(--lrh-color-action-accent);
        color: var(--lrh-color-action-on-accent)">Primary action</span></p>
      </section>
    </main>
  </div>
</body>
</html>
"""


def render_project_operational_dashboard(
    config: ServeConfig, project_selector: str
) -> tuple[int, str]:
    """Render a read-only operational dashboard for one registered project."""

    payload = meta_dashboard_payload(config)
    selected: dict[str, object] | None = None
    for lane in payload.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        for card in lane.get("projects", []):
            if not isinstance(card, dict):
                continue
            registry_name = str(card.get("registry_name") or "")
            project_id = str(card.get("project_id") or "")
            if project_selector in {registry_name, project_id}:
                selected = card
                break
        if selected is not None:
            break
    if selected is None:
        return (
            404,
            json.dumps({"error": "not_found", "project": project_selector}, indent=2),
        )
    display_name = html.escape(str(selected.get("display_name") or project_selector))
    project_id = html.escape(str(selected.get("project_id") or "unknown"))
    locator = html.escape(str(selected.get("locator") or "Unknown / unavailable"))
    source_state = html.escape(str(selected.get("source_state") or "unknown"))
    validation_status = html.escape(str(selected.get("validation_status") or "unknown"))
    design_links = _html_link_list(
        [
            (
                f"/project/{_url_quote(project_selector)}/designs/"
                f"{_url_quote(design['id'])}",
                f"{design['id']} — {design['title']}",
            )
            for design in _project_design_summaries(project_selector, config)
        ]
    )
    workstream_links = _html_link_list(
        [
            (
                f"/project/{_url_quote(project_selector)}/workstreams/"
                f"{_url_quote(workstream['id'])}",
                f"{workstream['id']} — {workstream['title']}",
            )
            for workstream in _project_workstream_summaries(project_selector, config)
        ]
    )
    setup_guidance = ""
    if selected.get("source_state") == "needs_local_checkout":
        registry = str(selected.get("registry_name") or project_selector)
        quoted_registry = shlex.quote(registry)
        setup_guidance = (
            '<section class="lrh-console-region"><h2>Next useful action</h2>'
            "<p>This project is remote-only in the registry. Bind a local checkout "
            "to unlock project-control validation and triage facts.</p>"
            "<p>Run: <code>"
            f"{html.escape(f'lrh meta set {quoted_registry} --local-repo-path PATH')}"
            "</code></p>"
            "</section>"
        )
    return (
        200,
        """<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>LRH Project Dashboard</title>{styles}</head>
<body>
<div class=\"lrh-app-shell\">
  <header class=\"lrh-page-header\">
    <p class=\"lrh-eyebrow\">LRH Console preview</p>
    <h1>Project Operational Dashboard: {display_name}</h1>
    <p><a href=\"/meta\">Back to meta triage dashboard</a></p>
  </header>
  <main class=\"lrh-main-content\">
    <section class=\"lrh-console-region\"><h2>Project identity and source state</h2>
      <dl class=\"lrh-summary-grid\">
        <div><dt>Project ID</dt><dd>{project_id}</dd></div>
        <div><dt>Locator</dt><dd>{locator}</dd></div>
        <div><dt>Authority</dt><dd>Project-local project/ control plane is
        authoritative.
        </dd></div>
        <div><dt>Source state</dt><dd>{source_state}</dd></div>
      </dl></section>
    <section class=\"lrh-console-region\"><h2>Primary operational summary</h2>
      <p>Validation status: {validation_status}. Active workstreams:
      {active_workstream_count}. Active work items: {active_work_item_count}.</p>
      <p>Ready leaves: {ready_leaf_count}. Readiness-deficient leaves:
      {readiness_deficient_leaf_count}.</p>
      <p>Current focus: {current_focus}.</p>
    </section>
    {setup_guidance}
    <section class=\"lrh-console-region\"><h2>Validation summary</h2>
      <p>Status: {validation_status}; errors: {error_count};
      warnings: {warning_count}.</p></section>
    <section class=\"lrh-console-region\"><h2>Current focus summary</h2>
      <p>{current_focus}</p>
    </section>
    <section class=\"lrh-console-region\"><h2>Design summary</h2>
      <p>Adopted but not implemented: {adopted_not_implemented_design_count}.</p>
      <h3>Design detail pages</h3>{design_links}
    </section>
    <section class=\"lrh-console-region\"><h2>Workstream summary</h2>
      <p>Active workstreams: {active_workstream_count}. Blocked/paused/completed
      counts are exposed as capability gaps when unavailable.</p>
      <h3>Workstream detail pages</h3>{workstream_links}
    </section>
    <section class=\"lrh-console-region\"><h2>Work item summary</h2>
      <p>Active: {active_work_item_count}; ready leaves: {ready_leaf_count};
      readiness-deficient leaves: {readiness_deficient_leaf_count}; blocked
      leaves: unknown / not implemented.</p>
    </section>
    <section class=\"lrh-console-region\"><h2>Capability gaps</h2>{gaps}</section>
    <section class=\"lrh-console-region\"><h2>Diagnostics and details</h2>
      <p>Detailed diagnostics and storage/debug views remain available through
      meta lanes, per-card diagnostics, and detail pages.</p>
    </section>
  </main>
</div>
</body></html>""".format(
            styles=_base_styles(),
            display_name=display_name,
            project_id=project_id,
            locator=locator,
            source_state=source_state,
            validation_status=validation_status,
            error_count=_display_card_value(selected.get("validation_error_count")),
            warning_count=_display_card_value(selected.get("validation_warning_count")),
            current_focus=_display_card_value(selected.get("current_focus_summary")),
            adopted_not_implemented_design_count=_display_card_value(
                selected.get("adopted_not_implemented_design_count")
            ),
            active_workstream_count=_display_card_value(
                selected.get("active_workstream_count")
            ),
            active_work_item_count=_display_card_value(
                selected.get("active_work_item_count")
            ),
            ready_leaf_count=_display_card_value(selected.get("ready_leaf_count")),
            readiness_deficient_leaf_count=_display_card_value(
                selected.get("readiness_deficient_leaf_count")
            ),
            design_links=design_links,
            workstream_links=workstream_links,
            gaps=_html_list(
                [
                    (
                        f"{gap.get('field', 'capability')}: "
                        f"{gap.get('state', 'unknown')} — "
                        f"{gap.get('message', '')}"
                    )
                    for gap in selected.get("capability_gaps", [])
                    if isinstance(gap, dict)
                ]
            ),
            setup_guidance=setup_guidance,
        ),
    )


def _project_from_meta_selector(
    config: ServeConfig, project_selector: str
) -> tuple[meta_workspace.MetaProjectRecord | None, Path | None]:
    try:
        workspace = meta_workspace.resolve_meta_workspace(
            cwd=config.resolved_project_root(),
            options=meta_workspace.MetaWorkspaceResolveOptions(),
        )
        load_results = meta_workspace.list_registered_project_loads_in_workspace(
            workspace
        )
    except (
        meta_workspace.MetaWorkspaceResolutionError,
        meta_workspace.MetaRegistryError,
    ):
        return None, None
    for result in load_results:
        if result.record is None:
            continue
        if project_selector in {result.registry_name, result.record.project_id}:
            return result.record, _registered_project_control_root(
                workspace, result.record
            )
    return None, None


def _project_design_summaries(
    project_selector: str, config: ServeConfig
) -> list[dict[str, str]]:
    _record, project_root = _project_from_meta_selector(config, project_selector)
    if project_root is None:
        return []
    try:
        loaded = control_loader.load_project(project_root)
    except (FileNotFoundError, OSError, ValueError):
        return []
    return [
        {"id": item.id, "title": item.title or "Untitled"}
        for item in loaded.design_proposals
    ]


def _project_workstream_summaries(
    project_selector: str, config: ServeConfig
) -> list[dict[str, str]]:
    _record, project_root = _project_from_meta_selector(config, project_selector)
    if project_root is None:
        return []
    try:
        loaded = control_loader.load_project(project_root)
    except (FileNotFoundError, OSError, ValueError):
        return []
    return [{"id": item.id, "title": item.title} for item in loaded.workstreams]


def render_design_detail_page(
    config: ServeConfig, project_selector: str, design_id: str
) -> tuple[int, str]:
    _record, project_root = _project_from_meta_selector(config, project_selector)
    if project_root is None:
        return 404, json.dumps(
            {"error": "not_found", "project": project_selector}, indent=2
        )
    try:
        loaded = control_loader.load_project(project_root)
    except (FileNotFoundError, OSError, ValueError) as error:
        return 404, json.dumps({"error": "not_found", "message": str(error)})
    proposal = loaded.design_proposals_by_id.get(design_id)
    if proposal is None:
        return 404, json.dumps({"error": "not_found", "design": design_id}, indent=2)
    related_workstreams = [
        w.id for w in loaded.workstreams if design_id in w.related_design
    ]
    related_work_items = [
        w.id for w in loaded.work_items if design_id in w.related_design
    ]
    related_workstream_html = _html_link_list(
        [
            (
                f"/project/{_url_quote(project_selector)}/workstreams/"
                f"{_url_quote(item)}",
                item,
            )
            for item in related_workstreams
        ]
    )
    return (
        200,
        """<!doctype html><html lang="en">
<head><meta charset="utf-8">
<title>Design detail</title>{styles}</head><body><div class="lrh-app-shell">
<header class="lrh-page-header"><h1>Design: {design_id}</h1>
<p><a href="/project/{project}">Back to project dashboard</a></p></header>
<main class="lrh-main-content"><section class="lrh-console-region">
<h2>Lifecycle and source</h2><p>Title: {title}</p><p>Status: {status}</p>
<p>Implementation status: {implementation_status}</p><p>Source: {source}</p>
</section><section class="lrh-console-region"><h2>Traceability</h2>
<h3>Related workstreams</h3>{related_workstreams}
<h3>Related work items</h3>{related_work_items}
<h3>Implemented by</h3>{implemented_by}<h3>Evidence</h3>{evidence}
<h3>Supersedes</h3>{supersedes}<p>Superseded by: {superseded_by}</p></section>
<section class="lrh-console-region"><h2>Capability gaps</h2>{gaps}</section>
</main></div></body></html>""".format(
            styles=_base_styles(),
            design_id=html.escape(proposal.id),
            project=_url_quote(project_selector),
            title=html.escape(str(proposal.title or "Untitled")),
            status=html.escape(proposal.status),
            implementation_status=html.escape(
                str(proposal.implementation_status or "unknown / not implemented")
            ),
            source=html.escape(str(_relative_repo_path(project_root, proposal.path))),
            related_workstreams=related_workstream_html,
            related_work_items=_html_list(related_work_items),
            implemented_by=_html_list(list(proposal.implemented_by)),
            evidence=_html_list(list(proposal.evidence)),
            supersedes=_html_list(list(proposal.supersedes)),
            superseded_by=html.escape(str(proposal.superseded_by or "none")),
            gaps=_html_list(
                ["Prompt actions are not implemented for design detail pages yet."]
            ),
        ),
    )


def render_workstream_detail_page(
    config: ServeConfig, project_selector: str, workstream_id: str
) -> tuple[int, str]:
    _record, project_root = _project_from_meta_selector(config, project_selector)
    if project_root is None:
        return 404, json.dumps(
            {"error": "not_found", "project": project_selector}, indent=2
        )
    try:
        loaded = control_loader.load_project(project_root)
    except (FileNotFoundError, OSError, ValueError) as error:
        return 404, json.dumps({"error": "not_found", "message": str(error)})
    workstream = loaded.workstreams_by_id.get(workstream_id)
    if workstream is None:
        return 404, json.dumps(
            {"error": "not_found", "workstream": workstream_id}, indent=2
        )
    parent = workstream.parent_id or "none"
    children_html = _html_link_list(
        [
            (
                f"/project/{_url_quote(project_selector)}/workstreams/"
                f"{_url_quote(child)}",
                child,
            )
            for child in workstream.children
        ]
    )
    work_item_html = _html_list(list(workstream.work_items))
    return (
        200,
        """<!doctype html><html lang="en">
<head><meta charset="utf-8">
<title>Workstream detail</title>{styles}</head><body><div class="lrh-app-shell">
<header class="lrh-page-header"><h1>Workstream: {workstream_id}</h1>
<p><a href="/project/{project}">Back to project dashboard</a></p></header>
<main class="lrh-main-content"><section class="lrh-console-region">
<h2>Identity and status</h2><p>Title: {title}</p><p>Status: {status}</p>
<p>Stage: {stage}</p><p>Summary: {summary}</p><p>Source: {source}</p></section>
<section class="lrh-console-region"><h2>Relationships</h2><p>Parent: {parent}</p>
<h3>Children</h3>{children}<h3>Work items</h3>{work_items}</section>
<section class="lrh-console-region"><h2>Capability gaps</h2>{gaps}</section>
</main></div></body></html>""".format(
            styles=_base_styles(),
            workstream_id=html.escape(workstream.id),
            project=_url_quote(project_selector),
            title=html.escape(workstream.title),
            status=html.escape(workstream.status),
            stage=html.escape(workstream.stage),
            summary=html.escape(str(workstream.summary or "unknown")),
            source=html.escape(str(_relative_repo_path(project_root, workstream.path))),
            parent=html.escape(parent),
            children=children_html,
            work_items=work_item_html,
            gaps=_html_list(
                ["Hierarchy diagnostics are not fully exposed by shared APIs yet."]
            ),
        ),
    )


def _operational_card_from_load_result(
    workspace: meta_workspace.MetaWorkspace,
    result: meta_workspace.MetaProjectLoadResult,
) -> dashboard.ProjectOperationalCard:
    if result.record is None:
        return dashboard.unavailable_project_operational_card(
            registry_name=result.registry_name,
            message=result.error or "project record could not be loaded",
        )
    record = result.record
    gaps = [
        dashboard.CapabilityGapView(
            field="adopted_not_implemented_design_count",
            state="not_implemented",
            message="Design implementation counting is not exposed by core-state yet.",
        ),
    ]
    source_state = "unknown"
    validation_status = "unknown"
    validation_error_count = None
    validation_warning_count = None
    current_focus_summary = None
    active_workstream_count = None
    active_work_item_count = None
    blocker_count = None
    awaiting_review = None
    steady = None
    ready_leaf_count = None
    readiness_deficient_leaf_count = None
    diagnostics: tuple[str, ...] = ()
    validation_diagnostics: tuple[str, ...] = ()
    validation_next_action: str | None = None
    inspect_result = _inspect_registered_project(workspace, result.registry_name)
    if inspect_result is not None:
        source_state = _source_state_from_inspect_result(inspect_result)
        diagnostics = _diagnostics_for_source_state(inspect_result, source_state)
    else:
        gaps.append(
            dashboard.CapabilityGapView(
                field="source_state_detail",
                state="not_implemented",
                message=(
                    "Source-state detail inspection is not available for this "
                    "project in the current environment."
                ),
            )
        )
    project_root = _registered_project_control_root(workspace, record)
    if inspect_result is not None and source_state in {"live", "missing_project"}:
        project_root = inspect_result.resolved_project_path
    should_load_project_payload = project_root is not None and source_state not in {
        "missing_repo",
        "needs_local_checkout",
    }
    if should_load_project_payload:
        try:
            project_payload = project_viewer_payload(
                ServeConfig(project_root=project_root)
            )
        except (FileNotFoundError, OSError, ValueError) as err:
            source_state = "unavailable"
            validation_status = "unavailable"
            diagnostics = (str(err),)
        else:
            validation = project_payload.get("validation", {})
            if isinstance(validation, dict):
                validation_status = str(validation.get("status", "unknown"))
                validation_error_count = _optional_int(validation.get("error_count"))
                validation_warning_count = _optional_int(
                    validation.get("warning_count")
                )
            validation_diagnostics = _validation_diagnostics_from_project_payload(
                project_payload, validation_status=validation_status
            )
            validation_next_action = _validation_next_action_for_card(
                project_root=project_root,
                source_state=source_state,
                validation_status=validation_status,
            )
            if _project_payload_is_unavailable(project_payload):
                if source_state in {"unknown", "live"}:
                    source_state = "missing_project"
                diagnostics = tuple(
                    _diagnostic_label(diagnostic)
                    for diagnostic in project_payload.get("diagnostics", [])
                )
            else:
                source_state = "live"
            focus = project_payload.get("current_focus")
            if isinstance(focus, dict):
                current_focus_summary = (
                    f"{focus['id']} — {focus['title']} ({focus['status']})"
                )
            workstreams = project_payload.get("active_workstreams")
            if isinstance(workstreams, list):
                active_workstream_count = len(workstreams)
            work_items = project_payload.get("work_items")
            if isinstance(work_items, dict):
                active_work_item_count = _status_count(work_items, "active")
                blocker_count = _blocked_work_item_count(work_items)
                awaiting_review = _has_review_waiting_work(work_items)
            workstream_summary = project_payload.get("workstreams")
            if awaiting_review is not True and isinstance(workstream_summary, dict):
                awaiting_review = _has_reviewing_workstream(workstream_summary)
            steady = _project_payload_is_steady(
                project_payload,
                active_workstream_count=active_workstream_count,
                active_work_item_count=active_work_item_count,
            )
            execution = project_payload.get("execution")
            if isinstance(execution, dict):
                active_leaf_count = execution.get("active_leaf_count")
                ready_count = execution.get("ready_count")
                if isinstance(ready_count, int):
                    ready_leaf_count = ready_count
                if isinstance(active_leaf_count, int) and isinstance(ready_count, int):
                    readiness_deficient_leaf_count = max(
                        active_leaf_count - ready_count, 0
                    )
    return dashboard.project_operational_card_from_record(
        record,
        source_state=source_state,
        validation_status=validation_status,
        validation_error_count=validation_error_count,
        validation_warning_count=validation_warning_count,
        current_focus_summary=current_focus_summary,
        active_workstream_count=active_workstream_count,
        active_work_item_count=active_work_item_count,
        blocker_count=blocker_count,
        awaiting_review=awaiting_review,
        steady=steady,
        ready_leaf_count=ready_leaf_count,
        readiness_deficient_leaf_count=readiness_deficient_leaf_count,
        adopted_not_implemented_design_count=None,
        capability_gaps=tuple(gaps),
        diagnostics=diagnostics,
        validation_diagnostics=validation_diagnostics,
        validation_next_action=validation_next_action,
    )


def _validation_diagnostics_from_project_payload(
    project_payload: dict[str, object], *, validation_status: str
) -> tuple[str, ...]:
    if validation_status != "error":
        return ()
    diagnostics = project_payload.get("diagnostics", [])
    items: list[str] = []
    validation = project_payload.get("validation", {})
    if isinstance(validation, dict):
        error_count = _optional_int(validation.get("error_count"))
        warning_count = _optional_int(validation.get("warning_count"))
        if error_count is not None:
            items.append(f"Validation errors: {error_count}.")
        if warning_count is not None:
            items.append(f"Validation warnings: {warning_count}.")
    if isinstance(diagnostics, list):
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, dict):
                continue
            if diagnostic.get("severity") != "error":
                continue
            items.append(_diagnostic_label(diagnostic))
            if len(items) >= 5:
                break
    if not items:
        items.append("validation_error_details: not_implemented")
    return tuple(items)


def _validation_next_action_for_card(
    *,
    project_root: Path | None,
    source_state: str,
    validation_status: str,
) -> str | None:
    if validation_status != "error":
        return None
    if project_root is not None and source_state in {"live", "missing_project"}:
        checkout_root = project_root
        if project_root.name == "project":
            checkout_root = project_root.parent
        return (
            "Run validation from the project checkout: "
            f"cd {shlex.quote(str(checkout_root))} && lrh validate"
        )
    return (
        "Run validation for this project from its checkout, or inspect the "
        "project detail page for validation output."
    )


def _inspect_registered_project(
    workspace: meta_workspace.MetaWorkspace, registry_name: str
) -> meta_workspace.MetaInspectResult | None:
    try:
        return meta_workspace.inspect_registered_project_in_workspace(
            workspace, selector=registry_name
        )
    except meta_workspace.MetaRegistryError:
        return None


def _source_state_from_inspect_result(
    inspect_result: meta_workspace.MetaInspectResult,
) -> str:
    if inspect_result.repo_path_exists is False:
        return "missing_repo"
    if inspect_result.project_path_exists is False:
        return "missing_project"
    if inspect_result.project_path_exists is True:
        return "live"
    if inspect_result.source_state == "remote_only":
        return "needs_local_checkout"
    return "inaccessible"


def _diagnostics_for_source_state(
    inspect_result: meta_workspace.MetaInspectResult, source_state: str
) -> tuple[str, ...]:
    if source_state in {"live", "unknown"}:
        return ()
    if source_state == "needs_local_checkout":
        project_name = inspect_result.record.registry_name
        return (
            "This project has a remote locator but no local checkout binding. "
            f"Run: lrh meta set {shlex.quote(project_name)} --local-repo-path PATH. "
            f"Then: lrh meta refresh {shlex.quote(project_name)}.",
        )
    if source_state == "missing_repo":
        return ("LOCAL_REPO_PATH_MISSING",)
    if source_state == "missing_project":
        return ("PROJECT_CONTROL_DIR_NOT_FOUND",)
    return ("PROJECT_SOURCE_STATE_INACCESSIBLE",)


def _registered_project_control_root(
    workspace: meta_workspace.MetaWorkspace,
    record: meta_workspace.MetaProjectRecord,
) -> Path | None:
    repo_path = _registered_repo_path(workspace, record.repo_locator)
    if repo_path is None:
        return None
    project_dir = (record.project_dir or "project").strip() or "project"
    if project_dir in {".", "./", ""}:
        return repo_path
    if project_dir == "project":
        return repo_path
    return repo_path / project_dir


def _registered_repo_path(
    workspace: meta_workspace.MetaWorkspace,
    repo_locator: str | None,
) -> Path | None:
    if repo_locator is None:
        return None
    parsed = urllib.parse.urlsplit(repo_locator)
    if parsed.scheme and parsed.netloc:
        return None
    if "://" in repo_locator:
        return None
    repo_path = Path(repo_locator).expanduser()
    if repo_path.is_absolute():
        return repo_path
    base_dir = workspace.workspace_root
    if base_dir is None:
        base_dir = workspace.config_path.parent
    return base_dir / repo_path


def _status_count(summary: dict[str, object], status: str) -> int | None:
    by_status = summary.get("by_status")
    if not isinstance(by_status, dict):
        return None
    value = by_status.get(status, 0)
    return value if isinstance(value, int) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _project_payload_is_unavailable(payload: dict[str, object]) -> bool:
    diagnostics = payload.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        return False
    return any(
        isinstance(diagnostic, dict)
        and diagnostic.get("code") == "PROJECT_CONTROL_DIR_NOT_FOUND"
        for diagnostic in diagnostics
    )


def _blocked_work_item_count(work_items: dict[str, object]) -> int | None:
    raw_items = work_items.get("items")
    if not isinstance(raw_items, list):
        return None
    count = 0
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        blocked_by = item.get("blocked_by")
        status = str(item.get("status", "")).lower()
        if (
            item.get("blocked") is True
            or (isinstance(blocked_by, list) and blocked_by)
            or status in {"blocked", "stalled"}
        ):
            count += 1
    return count


def _has_review_waiting_work(work_items: dict[str, object]) -> bool | None:
    raw_items = work_items.get("items")
    if not isinstance(raw_items, list):
        return None
    review_statuses = {
        "awaiting_review",
        "review",
        "in_review",
        "ready_for_review",
        "ready-for-review",
    }
    return any(
        isinstance(item, dict)
        and str(item.get("status", "")).lower() in review_statuses
        for item in raw_items
    )


def _has_reviewing_workstream(workstreams: dict[str, object]) -> bool | None:
    raw_items = workstreams.get("items")
    if not isinstance(raw_items, list):
        return None
    return any(
        isinstance(item, dict) and str(item.get("stage", "")).lower() == "reviewing"
        for item in raw_items
    )


def _project_payload_is_steady(
    payload: dict[str, object],
    *,
    active_workstream_count: int | None,
    active_work_item_count: int | None,
) -> bool | None:
    validation = payload.get("validation")
    if not isinstance(validation, dict):
        return None
    if validation.get("status") != "valid":
        return False
    if active_workstream_count is None or active_work_item_count is None:
        return None
    focus = payload.get("current_focus")
    work_items = payload.get("work_items")
    has_control_state = isinstance(focus, dict) or (
        isinstance(work_items, dict) and _optional_int(work_items.get("total")) != 0
    )
    return (
        has_control_state
        and active_workstream_count == 0
        and active_work_item_count == 0
    )


def _operational_card_payload(project: object) -> dict[str, object]:
    if not isinstance(project, dashboard.ProjectOperationalCard):
        return {}
    return {
        "project_id": project.project_id,
        "display_name": project.display_name,
        "registry_name": project.registry_name,
        "short_name": project.short_name,
        "locator": project.locator,
        "project_source_access": project.project_source_access,
        "source_state": project.source_state,
        "control_plane_validation": project.control_plane_validation,
        "validation_status": project.validation_status,
        "validation_error_count": project.validation_error_count,
        "validation_warning_count": project.validation_warning_count,
        "triage_lane": project.triage_lane,
        "lane": project.lane,
        "status": project.status.value,
        "current_focus_summary": project.current_focus_summary,
        "active_workstream_count": project.active_workstream_count,
        "active_work_item_count": project.active_work_item_count,
        "ready_leaf_count": project.ready_leaf_count,
        "readiness_deficient_leaf_count": project.readiness_deficient_leaf_count,
        "adopted_not_implemented_design_count": (
            project.adopted_not_implemented_design_count
        ),
        "detail_url": project.detail_url,
        "lrh_capability_gaps": [
            {"field": gap.field, "state": gap.state, "message": gap.message}
            for gap in project.lrh_capability_gaps
        ],
        "capability_gaps": [
            {"field": gap.field, "state": gap.state, "message": gap.message}
            for gap in project.capability_gaps
        ],
        "project_issues": [],
        "operator_warnings": [],
        "other_diagnostics": list(project.other_diagnostics),
        "diagnostics": list(project.diagnostics),
        "validation_diagnostics": list(project.validation_diagnostics),
        "validation_next_action": project.validation_next_action,
    }


# Each band's glyph, so no band is told apart by color alone. The glyphs match
# the dependency map's where the meaning is shared.
_BAND_GLYPHS = {
    "blocked": "✕",
    "needs_attention": "!",
    "active_work": "▶",
    "awaiting_review": "◉",
    "stable": "✓",
    "unknown": "?",
}

STATUSBOARD_STYLES = """
  .lrh-page-header.lrh-statusboard-header {
    padding: 0.9rem 1.1rem; margin-bottom: 0.75rem;
  }
  .lrh-statusboard-header h1 { margin: 0 0 0.25rem; font-size: 1.6rem; }
  .lrh-statusboard-header p { margin: 0; }
  .lrh-bands { display: grid; gap: 0.75rem; margin-bottom: 1.5rem; }
  .lrh-band {
    border: 1px solid var(--lrh-band-line);
    border-left: 6px solid var(--lrh-band-line);
    border-radius: 8px;
    background: var(--lrh-color-surface-panel);
  }
  .lrh-band > summary {
    display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 0.75rem;
    padding: 0.6rem 0.9rem; cursor: pointer; list-style: none;
    background: var(--lrh-band-bg); color: var(--lrh-band-fg);
    border-radius: 2px 7px 7px 2px;
  }
  .lrh-band[open] > summary { border-radius: 2px 7px 0 0; }
  .lrh-band > summary::-webkit-details-marker { display: none; }
  .lrh-band > summary::before { content: "▸" / ""; width: 1em; }
  .lrh-band[open] > summary::before { content: "▾" / ""; }
  .lrh-band > summary:focus-visible {
    outline: 3px solid var(--lrh-color-focus); outline-offset: 2px;
  }
  .lrh-band-glyph { font-weight: 700; width: 1.2em; text-align: center; }
  .lrh-band-label { font-weight: 700; font-size: 1.05rem; }
  .lrh-band-count {
    font-weight: 700; min-width: 1.6em; text-align: center; padding: 0 0.4em;
    border: 1px solid currentColor; border-radius: 999px;
  }
  .lrh-band-description { flex-basis: 100%; padding-left: 2.2em; }
  .lrh-band-body {
    display: grid; gap: 0.75rem; padding: 0.75rem 0.9rem;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 20rem), 1fr));
  }
  .lrh-band-empty { margin: 0; padding: 0.6rem 0.9rem 0.75rem 3.1rem; }
  .lrh-band--blocked { --lrh-band-fg: var(--lrh-color-band-blocked-fg);
    --lrh-band-bg: var(--lrh-color-band-blocked-bg);
    --lrh-band-line: var(--lrh-color-band-blocked-line); }
  .lrh-band--needs_attention { --lrh-band-fg: var(--lrh-color-band-needs-attention-fg);
    --lrh-band-bg: var(--lrh-color-band-needs-attention-bg);
    --lrh-band-line: var(--lrh-color-band-needs-attention-line); }
  .lrh-band--active_work { --lrh-band-fg: var(--lrh-color-band-active-work-fg);
    --lrh-band-bg: var(--lrh-color-band-active-work-bg);
    --lrh-band-line: var(--lrh-color-band-active-work-line); }
  .lrh-band--awaiting_review { --lrh-band-fg: var(--lrh-color-band-awaiting-review-fg);
    --lrh-band-bg: var(--lrh-color-band-awaiting-review-bg);
    --lrh-band-line: var(--lrh-color-band-awaiting-review-line); }
  .lrh-band--stable { --lrh-band-fg: var(--lrh-color-band-stable-fg);
    --lrh-band-bg: var(--lrh-color-band-stable-bg);
    --lrh-band-line: var(--lrh-color-band-stable-line); }
  .lrh-band--unknown { --lrh-band-fg: var(--lrh-color-band-unknown-fg);
    --lrh-band-bg: var(--lrh-color-band-unknown-bg);
    --lrh-band-line: var(--lrh-color-band-unknown-line); }
  .lrh-band .lrh-project-card {
    margin: 0; min-width: 0; padding: 0.75rem;
    border: 1px solid var(--lrh-color-border-subtle);
    border-radius: var(--lrh-radius-md);
    background: var(--lrh-color-surface-page);
  }
  .lrh-card-facts dd, .lrh-chip { overflow-wrap: anywhere; }
  .lrh-visually-hidden {
    position: absolute; width: 1px; height: 1px; overflow: hidden;
    clip-path: inset(50%); white-space: nowrap;
  }
  .lrh-project-card h3 { margin: 0 0 0.4rem; overflow-wrap: anywhere; }
  .lrh-card-facts { margin: 0 0 0.5rem; display: grid; gap: 0.25rem; }
  .lrh-card-facts dt { font-weight: 600; display: inline; }
  .lrh-card-facts dd { display: inline; margin: 0; }
  .lrh-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0 0 0.5rem; }
  .lrh-chip {
    display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px;
    border: 1px solid var(--lrh-color-border-subtle);
    font-size: 0.85rem;
  }
  .lrh-card-details > summary { cursor: pointer; }
"""


def _meta_lane_html(lane: object, read_at: str = "") -> str:
    if not isinstance(lane, dict):
        return ""
    cards = lane.get("projects", [])
    card_html = "".join(
        _meta_card_html(card, read_at) for card in cards if isinstance(card, dict)
    )
    status = str(lane["status"])
    label = html.escape(str(lane["label"]))
    count = int(lane["count"]) if isinstance(lane.get("count"), int) else 0
    noun = "project" if count == 1 else "projects"
    description = html.escape(str(lane["description"]))
    glyph = html.escape(_BAND_GLYPHS.get(status, "?"))
    css = html.escape(status, quote=True)
    if card_html:
        body = f'<div class="lrh-band-body">{card_html}</div>'
    else:
        body = '<p class="lrh-band-empty lrh-muted">No projects in this band.</p>'
        if status == "unknown":
            body = (
                # Neutral on purpose: an unreadable registry also leaves every
                # band empty, without LRH having established anything.
                '<p class="lrh-band-empty lrh-muted">No projects are currently '
                "classified as unknown.</p>"
            )
    # Bands with projects start open; empty bands stay visible but closed.
    is_open = " open" if card_html else ""
    return (
        f'<details class="lrh-band lrh-band--{css}" id="band-{css}"{is_open}>'
        f'<summary><span class="lrh-band-glyph" aria-hidden="true">{glyph}</span>'
        f'<span class="lrh-band-label">{label}</span>'
        f'<span class="lrh-band-count">{count}'
        f'<span class="lrh-visually-hidden"> {noun}</span></span>'
        f'<span class="lrh-band-description">{description}</span></summary>'
        f"{body}</details>"
    )


def _meta_evidence_chip(card: dict[str, object]) -> str:
    """The control-plane validation result, as a short chip."""

    status = str(card.get("validation_status") or "unknown")
    errors = card.get("validation_error_count")
    warnings = card.get("validation_warning_count")
    if isinstance(errors, int) and errors > 0:
        text = f"Validation: {errors} error" + ("" if errors == 1 else "s")
    elif isinstance(warnings, int) and warnings > 0:
        text = f"Validation: {warnings} warning" + ("" if warnings == 1 else "s")
    elif status == "valid":
        text = "Validation: passing"
    else:
        text = f"Validation: {status.replace('_', ' ')}"
    return f'<span class="lrh-chip">{html.escape(text)}</span>'


def _meta_freshness_chip(card: dict[str, object], read_at: str) -> str:
    """When this card's facts were read, or why they were not."""

    source = str(card.get("source_state") or "unknown")
    if source == "live" and read_at:
        stamp = read_at.replace("T", " ").replace("+00:00", " UTC")
        text = f"Read live {stamp}"
    elif source == "live":
        text = "Read live"
    else:
        text = f"Not read: {source.replace('_', ' ')}"
    return f'<span class="lrh-chip">{html.escape(text)}</span>'


def _meta_next_action(card: dict[str, object]) -> str:
    if card.get("source_state") == "needs_local_checkout":
        return "Set a local checkout path"
    next_action = card.get("validation_next_action")
    if isinstance(next_action, str) and next_action.strip():
        return next_action.strip()
    ready = card.get("ready_leaf_count")
    if isinstance(ready, int) and ready > 0:
        return f"{ready} work item" + (" is" if ready == 1 else "s are") + " ready"
    return ""


def _meta_card_html(card: dict[str, object], read_at: str = "") -> str:
    name = html.escape(str(card["display_name"]))
    project_id = html.escape(str(card["project_id"]))
    detail_url = html.escape(str(card.get("detail_url") or "/meta/project"), quote=True)
    registry_anchor = html.escape(
        str(card.get("registry_name") or project_id), quote=True
    )
    gaps = card.get("capability_gaps", [])
    gap_items = []
    if isinstance(gaps, list):
        for gap in gaps:
            if isinstance(gap, dict):
                field = gap.get("field", "capability")
                state = gap.get("state", "unknown")
                message = gap.get("message", "")
                gap_items.append(f"{field}: {state} — {message}")
    gap_html = _html_list(gap_items)
    diagnostics = card.get("diagnostics", [])
    diagnostic_html = _html_list(diagnostics if isinstance(diagnostics, list) else [])
    validation_diagnostics = card.get("validation_diagnostics", [])
    validation_items = (
        validation_diagnostics if isinstance(validation_diagnostics, list) else []
    )
    validation_html = ""
    if validation_items:
        validation_html = (
            f"<h4>Validation diagnostics</h4>{_html_list(validation_items)}"
        )
    fields = (
        ("Project ID", "project_id"),
        ("Short name", "short_name"),
        ("Locator", "locator"),
        ("Project source access", "source_state"),
        ("Control-plane validation", "validation_status"),
        ("Active workstreams", "active_workstream_count"),
        ("Active work items", "active_work_item_count"),
        ("Ready leaves", "ready_leaf_count"),
        ("Readiness-deficient leaves", "readiness_deficient_leaf_count"),
        (
            "Adopted designs not implemented",
            "adopted_not_implemented_design_count",
        ),
    )
    field_html = "".join(
        _card_definition_html(card, label, key) for label, key in fields
    )
    focus = card.get("current_focus_summary")
    focus_html = (
        html.escape(str(focus))
        if isinstance(focus, str) and focus.strip()
        else '<span class="lrh-muted">None recorded</span>'
    )
    next_action = _meta_next_action(card)
    next_html = (
        html.escape(next_action)
        if next_action
        else '<span class="lrh-muted">None recorded</span>'
    )
    setup_guidance = _meta_card_setup_guidance_html(card)
    return (
        f'<article class="lrh-project-card" id="meta-project-{registry_anchor}">'
        f'<h3><a href="{detail_url}">{name}</a></h3>'
        f'<dl class="lrh-card-facts"><div><dt>Focus:</dt> <dd>{focus_html}</dd></div>'
        f"<div><dt>Next:</dt> <dd>{next_html}</dd></div></dl>"
        f'<p class="lrh-chips">{_meta_evidence_chip(card)}'
        f"{_meta_freshness_chip(card, read_at)}</p>"
        f'<details class="lrh-card-details"><summary>Details</summary>'
        f'<dl class="lrh-summary-grid">{field_html}</dl>'
        f"{setup_guidance}"
        f"{validation_html}"
        f"{_meta_card_validation_next_action_html(card)}"
        f"<h4>LRH capability gaps</h4>{gap_html}"
        f"<h4>Other diagnostics</h4>{diagnostic_html}</details></article>"
    )


def _meta_card_validation_next_action_html(card: dict[str, object]) -> str:
    next_action = card.get("validation_next_action")
    if not isinstance(next_action, str):
        return ""
    if not next_action.strip():
        return ""
    return (
        "<h4>Validation next action</h4>" f"<p>{html.escape(next_action.strip())}</p>"
    )


def _meta_card_setup_guidance_html(card: dict[str, object]) -> str:
    source_state = str(card.get("source_state") or "unknown")
    if source_state != "needs_local_checkout":
        return ""
    locator = _display_card_value(card.get("locator"))
    registry_name = str(card.get("registry_name") or "project")
    quoted_registry_name = shlex.quote(registry_name)
    guidance = html.escape(
        f"Run: lrh meta set {quoted_registry_name} --local-repo-path PATH"
    )
    return (
        "<h4>Next useful action</h4>"
        "<p>Set a local checkout path for this remote-only project before "
        "operational summaries can be resolved.</p>"
        f"<p>Locator: {locator}</p>"
        f"<p>{guidance}</p>"
    )


def _card_definition_html(card: dict[str, object], label: str, key: str) -> str:
    return (
        f"<div><dt>{html.escape(label)}</dt>"
        f"<dd>{_display_card_value(card.get(key))}</dd></div>"
    )


def _display_card_value(value: object) -> str:
    if value is None or value == "":
        return "<span>Unknown / not implemented</span>"
    return html.escape(str(value))


@dataclass(frozen=True)
class WorkbenchArtifact:
    """Rendered safe-default workbench artifact metadata and Markdown."""

    kind: str
    work_item_id: str
    title: str
    markdown: str
    diagnostics: tuple[dict[str, str], ...]


def workbench_payload(config: ServeConfig) -> dict[str, object]:
    """Return deterministic prompt/packet/report workbench index data."""

    project_payload = project_viewer_payload(config)
    work_items = project_payload["work_items"]
    items = []
    if isinstance(work_items, dict):
        raw_items = work_items.get("items", [])
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    work_item_id = str(item["id"])
                    items.append(
                        {
                            "id": work_item_id,
                            "title": item["title"],
                            "status": item["status"],
                            "type": item["type"],
                            "is_active_leaf": item["is_active_leaf"],
                            "execution_ready": _work_item_execution_ready(item),
                            "viewer_url": f"/#work-item-{_url_quote(work_item_id)}",
                            "prompt_preview_url": (
                                "/workbench/prompt?work_item="
                                f"{_url_quote(work_item_id)}"
                            ),
                            "packet_preview_url": (
                                "/workbench/run-packet?work_item="
                                f"{_url_quote(work_item_id)}"
                            ),
                            "report_preview_url": (
                                "/workbench/run-report?work_item="
                                f"{_url_quote(work_item_id)}"
                            ),
                        }
                    )
    return {
        "mode": "safe-default-prompt-packet-report-workbench",
        "project": project_payload["project"],
        "validation": project_payload["validation"],
        "work_items": items,
        "diagnostics": project_payload["diagnostics"],
        "safety": _workbench_safety_notes(),
        "capabilities": _safe_capabilities(),
    }


def render_workbench_index(config: ServeConfig) -> str:
    """Render the local prompt/packet/report workbench page."""

    payload = workbench_payload(config)
    items = payload["work_items"]
    if isinstance(items, list) and items:
        item_rows = "".join(_workbench_item_row(item) for item in items)
    else:
        item_rows = (
            '<p class="lrh-muted">No work items are currently available to preview.</p>'
        )
    diagnostics = _html_list(
        _diagnostic_label(diagnostic) for diagnostic in payload["diagnostics"]
    )
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>LRH Serve Workbench</title>
  {styles}
</head>
<body>
  <div class=\"lrh-app-shell\">
    <header class=\"lrh-page-header\">
      <p class=\"lrh-eyebrow\">LRH Console preview</p>
      <h1>LRH Prompt/Packet/Report Workbench</h1>
      <p><a href=\"/\">Back to read-only viewer</a></p>
      <aside class=\"lrh-guardrail-callout\" aria-label=\"Workbench guardrails\">
        This local workbench previews package-rendered Markdown from existing
        LRH project-control files. Rendering happens only when you select a preview
        or download link. It does not execute prompts, dispatch agents, mutate
        branches, create pull requests, run CI loops, merge, release, publish, read
        arbitrary files, or write repository files.
      </aside>
    </header>
    <main id=\"main-content\" class=\"lrh-main-content\">
      <section class=\"lrh-console-region\"
        aria-labelledby=\"renderable-work-items-heading\">
        <h2 id=\"renderable-work-items-heading\">Renderable work items</h2>
        {item_rows}
      </section>
      <section class=\"lrh-validation-summary\"
        aria-labelledby=\"workbench-diagnostics-heading\">
        <h2 id=\"workbench-diagnostics-heading\">Diagnostics</h2>
        {diagnostics}
      </section>
      <section class=\"lrh-console-region\" aria-labelledby=\"workbench-api-heading\">
        <h2 id=\"workbench-api-heading\">Read-only API</h2>
        <ul>
          <li><a href=\"/api/workbench\">/api/workbench</a></li>
        </ul>
      </section>
    </main>
  </div>
</body>
</html>
""".format(styles=_base_styles(), item_rows=item_rows, diagnostics=diagnostics)


def render_workbench_artifact_page(artifact: WorkbenchArtifact) -> str:
    """Render a copy-friendly HTML page for one workbench artifact."""

    diagnostics = _html_list(_diagnostic_label(item) for item in artifact.diagnostics)
    title = html.escape(f"{artifact.kind}: {artifact.work_item_id}")
    markdown = html.escape(artifact.markdown)
    work_item = _url_quote(artifact.work_item_id)
    kind = _url_quote(artifact.kind)
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{title}</title>
  {styles}
</head>
<body>
  <div class=\"lrh-app-shell\">
    <header class=\"lrh-page-header\">
      <p class=\"lrh-eyebrow\">LRH Console preview</p>
      <h1>{title}</h1>
      <nav class=\"lrh-control-spine\" aria-label=\"Artifact preview navigation\">
        <a href=\"/workbench\">Back to workbench</a>
        <a href=\"/#work-item-{work_item}\">Back to viewer context</a>
        <a href=\"/workbench/{kind}?work_item={work_item}&amp;download=1\">
          Download Markdown</a>
      </nav>
      <aside class=\"lrh-guardrail-callout\" aria-label=\"Artifact preview guardrails\">
        This is a local in-memory preview only. It has not been executed and no
        repository files were written. Preview content is unavailable as execution
        evidence until a separate approved workflow runs and records evidence.
      </aside>
    </header>
    <main id=\"main-content\" class=\"lrh-main-content\">
      <section class=\"lrh-validation-summary\"
        aria-labelledby=\"artifact-diagnostics-heading\">
        <h2 id=\"artifact-diagnostics-heading\">Diagnostics</h2>
        {diagnostics}
      </section>
      <section class=\"lrh-workbench-artifact\"
        aria-labelledby=\"copy-markdown-heading\">
        <h2 id=\"copy-markdown-heading\">Copy-friendly Markdown</h2>
        <textarea rows=\"32\" cols=\"100\" readonly>{markdown}</textarea>
      </section>
    </main>
  </div>
</body>
</html>
""".format(
        styles=_base_styles(),
        title=title,
        work_item=work_item,
        kind=kind,
        diagnostics=diagnostics,
        markdown=markdown,
    )


def render_project_work_item_page(
    config: ServeConfig,
    project_id: str,
    work_item_id: str,
) -> tuple[int, str]:
    """Render a read-only readiness detail page for one work item."""

    try:
        scoped_config = _config_for_project_selector(config, project_id)
    except ProjectSelectorError as error:
        return error.status, render_project_selector_error_page(error)
    try:
        state = core_state.load_core_project_state(
            scoped_config.resolved_project_root()
        )
        item = _resolve_workbench_item(state, work_item_id)
    except (FileNotFoundError, OSError, ValueError) as error:
        return 404, json.dumps({"error": "not_found", "message": str(error)})
    readiness = item.execution_readiness
    readiness_state = "unknown"
    if item.status == "blocked":
        readiness_state = "blocked"
    elif readiness is None:
        readiness_state = "not ready"
    elif readiness.execution_ready:
        readiness_state = "ready"
    else:
        readiness_state = "not ready"
    disabled = "disabled" if readiness_state != "ready" else ""
    source_path = _relative_repo_path(scoped_config.resolved_project_root(), item.path)
    validation_commands = (
        ", ".join(readiness.validation_commands) if readiness is not None else "missing"
    )
    required_evidence = (
        ", ".join(readiness.required_evidence) if readiness is not None else "missing"
    )
    allowed_paths = (
        ", ".join(readiness.allowed_paths) if readiness is not None else "missing"
    )
    forbidden_paths = (
        ", ".join(readiness.forbidden_paths) if readiness is not None else "missing"
    )
    prompt_preview = (
        f"/project/{_url_quote(project_id)}/work-items/{_url_quote(item.id)}/prompt"
    )
    prompt_download = f"/workbench/prompt?work_item={_url_quote(item.id)}&download=1"
    cli_command = (
        "lrh request codex-prompt-from-work-item " f"--work-item {html.escape(item.id)}"
    )
    page = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(item.id)}</title>{_base_styles()}</head>
<body><div class="lrh-app-shell">
<h1>{html.escape(item.id)} — {html.escape(item.title)}</h1>
<p>Project: {html.escape(project_id)} | Status: {html.escape(item.status)}
| Type: {html.escape(item.type)}</p>
<p>Source path: <code>{html.escape(source_path)}</code></p>
<p>Readiness state: <strong>{html.escape(readiness_state)}</strong></p>
<p>Required changes summary: work item content is the source of truth; use prompt
preview for a bounded implementation request.</p>
<p>Acceptance criteria summary: see the approved work item and linked criteria in
source markdown.</p>
<p>Validation commands: {html.escape(validation_commands)}</p>
<p>Required evidence: {html.escape(required_evidence)}</p>
<p>Allowed paths: {html.escape(allowed_paths)}</p>
<p>Forbidden paths: {html.escape(forbidden_paths)}</p>
<h2>Prompt affordances</h2>
<ul>
<li><a href="{prompt_preview}">Preview generated prompt</a></li>
<li><button {disabled}>Copy generated prompt</button></li>
<li><a href="{prompt_download}">Download generated prompt Markdown</a></li>
<li>Equivalent CLI: <code>{cli_command}</code></li>
</ul>
<p>Capability gaps: none detected for prompt rendering path; uses shared request
renderer.</p>
</div></body></html>"""
    return 200, page


SERVED_PROJECT_SELECTOR = "main"


class ProjectSelectorError(Exception):
    """A ``/project/<project_id>/`` selector names no locally readable project.

    ``status`` is 404 when nothing matches the selector, and 409 when it names
    a registered project that has no local checkout to read.
    """

    def __init__(
        self,
        selector: str,
        *,
        status: int,
        error: str,
        message: str,
        registry_name: str | None = None,
    ) -> None:
        super().__init__(message)
        self.selector = selector
        self.status = status
        self.error = error
        self.message = message
        self.registry_name = registry_name

    @property
    def next_action(self) -> str | None:
        """The command that binds a local checkout, for a no-checkout error."""

        if self.registry_name is None:
            return None
        return f"lrh meta set {shlex.quote(self.registry_name)} --local-repo-path PATH"

    def to_payload(self) -> dict[str, object]:
        """Return the JSON error body the API routes send."""

        payload: dict[str, object] = {
            "error": self.error,
            "project": self.selector,
            "message": self.message,
        }
        if self.next_action is not None:
            payload["next_action"] = self.next_action
        return payload


def _config_for_project_selector(
    config: ServeConfig, project_selector: str
) -> ServeConfig:
    """Return the config scoped to the project a selector names.

    A selector the Meta registry resolves to a local checkout scopes to that
    checkout. Otherwise only ``main``, the served project's own selector,
    falls back to the served project; a registered project without a local
    checkout raises a 409 ``ProjectSelectorError`` and anything else a 404, so
    a page never shows the served project's data under another project's name.
    """

    try:
        workspace = meta_workspace.resolve_meta_workspace(
            cwd=config.resolved_project_root()
        )
        selection = meta_workspace.inspect_registered_project_in_workspace(
            workspace,
            selector=project_selector,
        )
    except (
        meta_workspace.MetaRegistryError,
        meta_workspace.MetaWorkspaceResolutionError,
        ValueError,
    ) as error:
        if project_selector == SERVED_PROJECT_SELECTOR:
            return config
        message = (
            str(error)
            if isinstance(error, meta_workspace.MetaRegistryError)
            else f"No Meta registry is available to resolve {project_selector!r}."
        )
        raise ProjectSelectorError(
            project_selector,
            status=404,
            error="project_not_found",
            message=message,
        ) from error
    resolved_path = selection.resolved_project_path
    if resolved_path is None:
        registry_name = selection.record.registry_name
        raise ProjectSelectorError(
            project_selector,
            status=409,
            error="no_local_checkout",
            message=(
                f"Project {registry_name!r} is registered but has no local "
                "checkout, so its project files cannot be read."
            ),
            registry_name=registry_name,
        )
    return ServeConfig(
        host=config.host,
        port=config.port,
        project_root=resolved_path,
        allow_nonlocal_host=config.allow_nonlocal_host,
    )


def render_project_selector_error_page(error: ProjectSelectorError) -> str:
    """Render the page for a selector that names no locally readable project."""

    selector = html.escape(error.selector)
    if error.next_action is None:
        title = "Project not found"
        detail = (
            f"<p>{html.escape(error.message)}</p>"
            '<p><a href="/meta">Open the meta triage dashboard</a> to see the '
            "registered projects.</p>"
        )
    else:
        title = "No local checkout"
        name = html.escape(error.registry_name or error.selector)
        detail = (
            f"<p>Project <code>{name}</code> is registered, but it has no local "
            "checkout, so LRH cannot read its project files.</p>"
            "<p>Bind a local checkout, then reload this page:</p>"
            f"<p><code>{html.escape(error.next_action)}</code></p>"
        )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(title)}</title>{_base_styles()}</head>
<body>
  <div class="lrh-app-shell">
    <header class="lrh-page-header"><p class="lrh-eyebrow">{selector}</p>
    <h1>{html.escape(title)}</h1>{detail}</header>
  </div>
</body>
</html>
"""


def render_workbench_artifact(
    config: ServeConfig,
    kind: str,
    work_item_id: str,
) -> WorkbenchArtifact:
    """Render one prompt, run-packet, or run-report preview without writes."""

    state = core_state.load_core_project_state(config.resolved_project_root())
    item = _resolve_workbench_item(state, work_item_id)
    project_root = config.resolved_project_root()
    if kind == "prompt":
        return _render_prompt_artifact(project_root, state, item)
    if kind == "run-packet":
        return _render_packet_artifact(project_root, state, item)
    if kind == "run-report":
        return _render_report_artifact(project_root, state, item)
    raise ValueError(f"unsupported workbench artifact kind: {kind}")


def _render_prompt_artifact(
    project_root: Path,
    state: core_state.CoreProjectState,
    item: core_state.WorkItemState,
) -> WorkbenchArtifact:
    prompt_id = f"PROMPT({item.id}:LRH_SERVE_WORKBENCH_PREVIEW)[UNEXECUTED]"
    style_path = _relative_repo_path(project_root, project_root / "STYLE.md")
    work_item_path = _relative_repo_path(project_root, item.path)
    markdown = work_item_prompt_core.generate_codex_cloud_prompt(
        prompt_id=prompt_id,
        work_item_path=item.path,
        style_guide_path=style_path,
        work_item_reference_path=work_item_path,
    )
    parsed = work_item_prompt_core.parse_work_item_markdown(item.path)
    readiness = work_item_prompt_core.evaluate_prompt_readiness(parsed)
    diagnostics = tuple(
        {
            "source": "prompt-workbench",
            "file": _relative_project_path(state, item.path),
            "severity": "error",
            "code": "PROMPT_READINESS_BLOCKED",
            "message": reason,
        }
        for reason in readiness.blocking_reasons
    )
    return WorkbenchArtifact(
        kind="prompt",
        work_item_id=item.id,
        title=item.title,
        markdown=markdown,
        diagnostics=diagnostics,
    )


def _render_packet_artifact(
    project_root: Path,
    state: core_state.CoreProjectState,
    item: core_state.WorkItemState,
) -> WorkbenchArtifact:
    result = run_packet.render_run_packet_from_work_item(
        item.path,
        project_root=project_root,
    )
    return WorkbenchArtifact(
        kind="run-packet",
        work_item_id=item.id,
        title=item.title,
        markdown=result.markdown,
        diagnostics=_readiness_issue_dicts(state, result.diagnostics),
    )


def _render_report_artifact(
    project_root: Path,
    state: core_state.CoreProjectState,
    item: core_state.WorkItemState,
) -> WorkbenchArtifact:
    result = run_report.render_run_report(
        run_report.RunReportInput(
            work_item_path=item.path,
            outcome="requires-human-review",
            human_verification_tasks=(
                "Review this workbench preview before treating it as execution "
                "evidence.",
            ),
            unresolved_risks=(
                "Workbench preview only; no agent, validation, branch, PR, or CI "
                "action ran.",
            ),
            recommended_next_actions=(
                "If execution is desired, copy the prompt or packet into a "
                "separate approved workflow.",
            ),
        ),
        project_root=project_root,
    )
    diagnostics = tuple(
        {
            "source": "run-report-workbench",
            "file": _relative_project_path(state, item.path),
            "severity": "warning",
            "code": diagnostic.code,
            "message": diagnostic.message,
        }
        for diagnostic in result.diagnostics
    )
    return WorkbenchArtifact(
        kind="run-report",
        work_item_id=item.id,
        title=item.title,
        markdown=result.markdown,
        diagnostics=diagnostics,
    )


def _resolve_workbench_item(
    state: core_state.CoreProjectState,
    work_item_id: str,
) -> core_state.WorkItemState:
    requested = work_item_id.strip()
    for item in state.work_items:
        if item.id == requested:
            return item
    raise FileNotFoundError(f"work item is not available in this project: {requested}")


def _readiness_issue_dicts(
    state: core_state.CoreProjectState,
    diagnostics: tuple[object, ...],
) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "source": "run-packet-workbench",
            "file": _relative_project_path(state, diagnostic.path),
            "severity": diagnostic.severity,
            "code": diagnostic.code,
            "message": diagnostic.message,
        }
        for diagnostic in diagnostics
        if hasattr(diagnostic, "path")
        and hasattr(diagnostic, "severity")
        and hasattr(diagnostic, "code")
        and hasattr(diagnostic, "message")
    )


def _safe_capabilities() -> dict[str, bool]:
    return {
        "write_routes": False,
        "agent_dispatch": False,
        "branch_mutation": False,
        "pull_request_mutation": False,
        "arbitrary_file_serving": False,
        "external_network_calls": False,
        "packet_generation": False,
        "report_generation": False,
        "meta_dashboard": True,
        "prompt_workbench": True,
        "in_memory_downloads": True,
        "packet_preview": True,
        "report_preview": True,
        "codex_archive_viewer": True,
    }


def codex_archive_payload(config: ServeConfig) -> dict[str, object]:
    """Return content-free metadata for explicitly configured Codex archives."""

    roots = _configured_codex_archive_roots(config)
    root_payloads: list[dict[str, object]] = []
    exports: list[dict[str, object]] = []
    for root_index, root in enumerate(roots):
        root_payload: dict[str, object] = {
            "index": root_index,
            "name": _codex_archive_root_label(root),
            "configured": True,
            "available": root.exists() and root.is_dir(),
            "export_count": 0,
            "diagnostics": [],
        }
        diagnostics = root_payload["diagnostics"]
        if not isinstance(diagnostics, list):
            raise TypeError("diagnostics payload must be a list")
        if not root.exists():
            diagnostics.append("archive root does not exist")
        elif not root.is_dir():
            diagnostics.append("archive root is not a directory")
        else:
            for export_path in sorted(root.rglob("*.md")):
                if not export_path.is_file():
                    continue
                if not _is_path_within(export_path.resolve(), root):
                    diagnostics.append(
                        f"skipped path outside archive root: {export_path.name}"
                    )
                    continue
                exports.append(_codex_export_summary(root_index, root, export_path))
            root_payload["export_count"] = sum(
                1 for export in exports if export["archive_root_index"] == root_index
            )
        root_payloads.append(root_payload)
    return {
        "mode": "safe-default-codex-conversation-archive-viewer",
        "configured_root_count": len(roots),
        "roots": root_payloads,
        "exports": exports,
        "safety": _codex_archive_safety_notes(),
    }


def codex_archive_detail_payload(
    config: ServeConfig, export_id: str
) -> dict[str, object] | None:
    """Return metadata for one configured Codex export ID."""

    match = _codex_export_summary_for_id(config, export_id)
    if match is None:
        return None
    _export_path, entry = match
    return {
        "mode": "safe-default-codex-conversation-export-detail",
        "export": entry,
        "safety": _codex_archive_safety_notes(),
        "transcript_body_available": bool(entry.get("valid")),
    }
    return None


def render_codex_archive_index(config: ServeConfig) -> str:
    """Render the safe-default Codex archive index page."""

    payload = codex_archive_payload(config)
    export_rows = "".join(
        _codex_archive_export_row(export)
        for export in payload["exports"]
        if isinstance(export, dict)
    )
    if not export_rows:
        export_rows = "<p>No Codex conversation exports found.</p>"
    root_rows = _html_list(
        _codex_archive_root_summary(root)
        for root in payload["roots"]
        if isinstance(root, dict)
    )
    safety = _html_list(payload["safety"])
    styles = _base_styles()
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Codex conversation archives</title>{styles}</head>
<body><div class="lrh-app-shell">
  <header class="lrh-page-header">
    <p class="lrh-eyebrow">LRH conversation archives</p>
    <h1>Codex Conversation Archives</h1>
    <p>Explicit local archive roots: {payload["configured_root_count"]}</p>
  </header>
  <main id="main-content" class="lrh-main-content">
    <section class="lrh-guardrail-callout">
      <h2>Safety boundary</h2>
      {safety}
    </section>
    <section class="lrh-system-overview">
      <h2>Archive roots</h2>
      {root_rows}
    </section>
    <section class="lrh-project-summary">
      <h2>Exports</h2>
      {export_rows}
    </section>
  </main>
</div></body></html>"""


def render_codex_archive_detail(config: ServeConfig, export_id: str) -> tuple[int, str]:
    """Render one configured Codex export as escaped, inert transcript text."""

    match = _codex_export_summary_for_id(config, export_id)
    if match is None:
        body = json.dumps(
            {"error": "not_found", "message": "Codex export is not configured"},
            sort_keys=True,
        )
        return 404, body
    export_path, export = match
    if not isinstance(export, dict) or not export.get("valid"):
        body = json.dumps(
            {"error": "not_found", "message": "Codex export is not valid"},
            sort_keys=True,
        )
        return 404, body
    try:
        transcript_body = export_inspector.read_export_transcript_body(export_path)
    except (ValueError, export_inspector.ConversationExportInspectionError) as err:
        body = json.dumps(
            {"error": "not_found", "message": _codex_export_error_label(err)},
            sort_keys=True,
        )
        return 404, body
    heading = html.escape(str(export.get("relative_path", export_id)))
    validity = html.escape(str(export.get("inspection_status", "unknown")))
    metadata = _html_list(_codex_archive_detail_items(export))
    transcript = html.escape(transcript_body)
    badge_class = _status_badge_class(validity)
    status_badge = f'<span class="lrh-status-badge {badge_class}">{validity}</span>'
    styles = _base_styles()
    body = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{heading}</title>{styles}</head>
<body><div class="lrh-app-shell">
  <header class="lrh-page-header">
    <p class="lrh-eyebrow">Codex conversation export</p>
    <h1>{heading}</h1>
    <p>Inspection status: {status_badge}</p>
  </header>
  <main id="main-content" class="lrh-main-content">
    <section class="lrh-system-overview">
      <h2>Manifest metadata</h2>
      {metadata}
    </section>
    <section class="lrh-console-region">
      <h2>Transcript</h2>
      <pre>{transcript}</pre>
    </section>
  </main>
</div></body></html>"""
    return 200, body


def _configured_codex_archive_roots(config: ServeConfig) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()
    project_root = config.resolved_project_root()
    for configured in config.codex_archive_roots:
        candidate = configured.expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        root = candidate.resolve()
        if root not in seen:
            roots.append(root)
            seen.add(root)
    return tuple(roots)


def _codex_export_summary(
    root_index: int, root: Path, export_path: Path
) -> dict[str, object]:
    relative_path = export_path.resolve().relative_to(root).as_posix()
    export_id = _codex_export_id(root_index, relative_path)
    try:
        inspection = export_inspector.inspect_export(export_path)
    except export_inspector.ConversationExportInspectionError as err:
        return {
            "id": export_id,
            "archive_root_index": root_index,
            "archive_root_name": _codex_archive_root_label(root),
            "relative_path": relative_path,
            "valid": False,
            "manifest_valid": False,
            "inspection_status": "error",
            "errors": [_codex_export_error_label(err)],
            "detail_url": f"/conversations/codex/{_url_quote(export_id)}",
            "api_detail_url": f"/api/conversations/codex/{_url_quote(export_id)}",
        }
    mapping = inspection.to_mapping()
    return {
        "id": export_id,
        "archive_root_index": root_index,
        "archive_root_name": _codex_archive_root_label(root),
        "relative_path": relative_path,
        "valid": mapping["valid"],
        "manifest_valid": mapping["manifest_valid"],
        "inspection_status": "valid" if mapping["valid"] else "invalid",
        "errors": _codex_export_error_codes(mapping["errors"]),
        "manifest": mapping["manifest"],
        "privacy": mapping["privacy"],
        "authority": mapping["authority"],
        "sensitivity": mapping["sensitivity"],
        "warning_count": mapping["warning_count"],
        "transcript_statistics": mapping["transcript_statistics"],
        "source_hash": _source_hash_summary(mapping["source_hash"]),
        "detail_url": f"/conversations/codex/{_url_quote(export_id)}",
        "api_detail_url": f"/api/conversations/codex/{_url_quote(export_id)}",
    }


def _codex_export_summary_for_id(
    config: ServeConfig, export_id: str
) -> tuple[Path, dict[str, object]] | None:
    for root_index, root in enumerate(_configured_codex_archive_roots(config)):
        if not root.exists() or not root.is_dir():
            continue
        for export_path in sorted(root.rglob("*.md")):
            if not export_path.is_file():
                continue
            resolved = export_path.resolve()
            if not _is_path_within(resolved, root):
                continue
            relative_path = resolved.relative_to(root).as_posix()
            if _codex_export_id(root_index, relative_path) == export_id:
                return resolved, _codex_export_summary(root_index, root, resolved)
    return None


def _source_hash_summary(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {"status": "not_available"}
    return {
        "status": payload.get("status"),
        "expected_sha256": payload.get("expected_sha256"),
        "actual_sha256_present": payload.get("actual_sha256") is not None,
    }


def _codex_archive_export_row(export: dict[str, object]) -> str:
    label = html.escape(str(export["relative_path"]))
    detail_url = html.escape(str(export["detail_url"]), quote=True)
    status = html.escape(str(export["inspection_status"]))
    badge_class = _status_badge_class(status)
    privacy = html.escape(str(export.get("privacy", "unknown")))
    sensitivity = html.escape(str(export.get("sensitivity", "unknown")))
    warning_count = html.escape(str(export.get("warning_count", "unknown")))
    return (
        "<article>"
        f'<h3><a href="{detail_url}">{label}</a></h3>'
        f'<p>Status: <span class="lrh-status-badge {badge_class}">{status}</span></p>'
        f"<p>Privacy: {privacy}; Sensitivity: {sensitivity}; "
        f"Warnings: {warning_count}</p>"
        "</article>"
    )


def _codex_archive_root_summary(root: dict[str, object]) -> str:
    name = str(root["name"])
    available = "available" if root["available"] else "unavailable"
    export_count = root["export_count"]
    diagnostics = root.get("diagnostics", [])
    diagnostic_text = ""
    if isinstance(diagnostics, list) and diagnostics:
        diagnostic_text = "; " + "; ".join(str(item) for item in diagnostics)
    return f"{name}: {available}; exports: {export_count}{diagnostic_text}"


def _codex_archive_detail_items(export: object) -> list[str]:
    if not isinstance(export, dict):
        return []
    items = [
        f"Relative path: {export.get('relative_path', 'unknown')}",
        f"Valid: {export.get('valid', False)}",
        f"Manifest valid: {export.get('manifest_valid', False)}",
        f"Privacy: {export.get('privacy', 'unknown')}",
        f"Authority: {export.get('authority', 'unknown')}",
        f"Sensitivity: {export.get('sensitivity', 'unknown')}",
        f"Warnings: {export.get('warning_count', 'unknown')}",
    ]
    stats = export.get("transcript_statistics")
    if isinstance(stats, dict):
        items.append(f"Transcript statistics: {stats.get('status', 'unknown')}")
    source_hash = export.get("source_hash")
    if isinstance(source_hash, dict):
        items.append(f"Source hash: {source_hash.get('status', 'unknown')}")
    errors = export.get("errors")
    if isinstance(errors, list) and errors:
        items.extend(f"Error: {error}" for error in errors)
    return items


def _codex_archive_safety_notes() -> list[str]:
    return [
        "only explicitly configured archive roots are scanned",
        "archive index and API list routes do not include transcript text",
        "detail pages render transcript bodies as escaped inert text",
        "exports remain private non-authoritative context",
    ]


def _codex_export_error_label(error: Exception) -> str:
    text = str(error)
    if ":" not in text:
        return text
    return text.split(":", maxsplit=1)[0]


def _codex_export_error_codes(errors: object) -> list[str]:
    if not isinstance(errors, list):
        return []
    codes: list[str] = []
    for error in errors:
        label = str(error).split(":", maxsplit=1)[0].strip()
        codes.append(label or "inspection_error")
    return codes


def _codex_export_id(root_index: int, relative_path: str) -> str:
    material = f"{root_index}:{relative_path}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:24]


def _codex_archive_root_label(root: Path) -> str:
    return root.expanduser().name or str(root.expanduser())


def _is_path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _base_styles() -> str:
    """Return the viewport tag, shared tokens, and page styles for every page."""

    return (
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<style>\n" + tokens.token_css() + frame.FRAME_STYLES + _PAGE_STYLES
    )


_PAGE_STYLES = """
  body {
    background: var(--lrh-color-surface-page);
    color: var(--lrh-color-text-primary);
    font-family: var(--lrh-font-body);
    line-height: 1.5;
    margin: 0;
  }

  a { color: inherit; }
  a:focus-visible, textarea:focus-visible {
    box-shadow: var(--lrh-focus-ring);
    outline: none;
  }

  .lrh-app-shell { margin: 0 auto; max-width: 72rem; padding: 2rem; }
  .lrh-page-header, .lrh-control-spine, .lrh-console-region,
  .lrh-system-overview, .lrh-project-summary, .lrh-evidence-summary,
  .lrh-validation-summary, .lrh-workbench-artifact {
    background: var(--lrh-color-surface-panel);
    border: 1px solid var(--lrh-color-border-subtle);
    border-radius: var(--lrh-radius-lg);
    margin-block: 1rem;
    padding: 1rem;
  }
  .lrh-control-spine { display: flex; flex-wrap: wrap; gap: 0.75rem; }
  .lrh-eyebrow, .lrh-muted { color: var(--lrh-color-text-muted); }
  .lrh-guardrail-callout {
    border-inline-start: 0.35rem solid var(--lrh-color-border-subtle);
    padding-inline-start: 1rem;
  }
  .lrh-summary-grid {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  }
  .lrh-summary-grid div {
    border-block-start: 1px solid var(--lrh-color-border-subtle);
    padding-block-start: 0.5rem;
  }
  .lrh-summary-grid dt { color: var(--lrh-color-text-muted); font-weight: 700; }
  .lrh-status-badge {
    border: 1px solid currentColor;
    border-radius: var(--lrh-radius-pill);
    display: inline-block;
    font-weight: 700;
    padding: 0.15rem 0.55rem;
  }
  .lrh-status-badge--needs-attention {
    background: var(--lrh-color-status-needs-attention-bg);
    color: var(--lrh-color-status-needs-attention-text);
  }
  .lrh-status-badge--active-work {
    background: var(--lrh-color-status-active-work-bg);
    color: var(--lrh-color-status-active-work-text);
  }
  .lrh-status-badge--awaiting-review {
    background: var(--lrh-color-status-awaiting-review-bg);
    color: var(--lrh-color-status-awaiting-review-text);
  }
  .lrh-status-badge--stable {
    background: var(--lrh-color-status-stable-bg);
    color: var(--lrh-color-status-stable-text);
  }
  .lrh-status-badge--unknown {
    background: var(--lrh-color-status-unknown-bg);
    color: var(--lrh-color-status-unknown-text);
  }
  textarea { box-sizing: border-box; max-width: 100%; width: 100%; }
</style>"""


def _status_badge_class(status: str) -> str:
    normalized = status.strip().lower().replace("_", "-").replace(" ", "-")
    if normalized in {"valid", "stable", "ok", "complete", "completed", "landed"}:
        return "lrh-status-badge--stable"
    if normalized in {"active", "in-progress", "planned", "ready"}:
        return "lrh-status-badge--active-work"
    if normalized in {"review", "awaiting-review", "requires-human-review"}:
        return "lrh-status-badge--awaiting-review"
    if normalized in {"error", "failed", "blocked", "needs-attention"}:
        return "lrh-status-badge--needs-attention"
    return "lrh-status-badge--unknown"


def _status_badge_label(status: str) -> str:
    text = status.strip() or "unknown"
    return html.escape(text.replace("_", " ").replace("-", " ").title())


def _evidence_summary_label(payload: dict[str, Any]) -> str:
    work_items = payload.get("work_items", {})
    workstream_payload = payload.get("workstreams", {})
    required_evidence = 0
    if isinstance(work_items, dict):
        for item in work_items.get("items", []):
            if isinstance(item, dict):
                evidence = item.get("required_evidence", [])
                if isinstance(evidence, list):
                    required_evidence += len(evidence)
    declared_workstream_evidence = 0
    if isinstance(workstream_payload, dict):
        for workstream in workstream_payload.get("items", []):
            if isinstance(workstream, dict):
                evidence = workstream.get("evidence", [])
                if isinstance(evidence, list):
                    declared_workstream_evidence += len(evidence)
    if required_evidence or declared_workstream_evidence:
        return (
            "Declared evidence references are visible in project-control data: "
            f"{required_evidence} work-item requirements and "
            f"{declared_workstream_evidence} workstream evidence links. "
            "Observed run/test evidence is not yet available in this serve view."
        )
    return (
        "Evidence unavailable: this serve view has no observed run/test evidence "
        "to display."
    )


def _empty_grouped_summary() -> dict[str, object]:
    return {"total": 0, "by_status": {}, "items": []}


def _focus_dict(
    focus: core_state.FocusState | None,
    state: core_state.CoreProjectState,
) -> dict[str, object] | None:
    if focus is None:
        return None
    return {
        "id": focus.id,
        "title": focus.title,
        "status": focus.status,
        "priority": focus.priority,
        "owner": focus.owner,
        "source_path": _relative_project_path(state, focus.path),
        "related_principles": list(focus.related_principles),
    }


def _workstream_summary(state: core_state.CoreProjectState) -> dict[str, object]:
    return {
        "total": len(state.workstreams),
        "by_status": _count_by_status(
            workstream.status for workstream in state.workstreams
        ),
        "items": [
            _workstream_dict(workstream, state) for workstream in state.workstreams
        ],
    }


def _workstream_dict(
    workstream: core_state.WorkstreamState,
    state: core_state.CoreProjectState,
) -> dict[str, object]:
    return {
        "id": workstream.id,
        "title": workstream.title,
        "status": workstream.status,
        "stage": workstream.stage,
        "bucket": workstream.bucket,
        "source_path": _relative_project_path(state, workstream.path),
        "parent_ids": list(workstream.parent_ids),
        "child_ids": list(workstream.child_ids),
        "work_items": list(workstream.work_items),
        "evidence": list(workstream.evidence),
    }


def _work_item_summary(state: core_state.CoreProjectState) -> dict[str, object]:
    return {
        "total": len(state.work_items),
        "by_status": _count_by_status(item.status for item in state.work_items),
        "by_type": _count_by_status(item.type for item in state.work_items),
        "items": [_work_item_dict(item, state) for item in state.work_items],
    }


def _work_item_dict(
    item: core_state.WorkItemState,
    state: core_state.CoreProjectState,
) -> dict[str, object]:
    readiness = item.execution_readiness
    return {
        "id": item.id,
        "title": item.title,
        "type": item.type,
        "status": item.status,
        "priority": item.priority,
        "owner": item.owner,
        "source_path": _relative_project_path(state, item.path),
        "parent_ids": list(item.parent_ids),
        "child_ids": list(item.child_ids),
        "related_focus": list(item.related_focus),
        "related_workstreams": list(item.related_workstreams),
        "depends_on": list(item.depends_on),
        "blocked_by": list(item.blocked_by),
        "blocked": item.blocked,
        "blocked_reason": item.blocked_reason,
        "required_evidence": list(item.required_evidence),
        "artifacts_expected": list(item.artifacts_expected),
        "is_current_focus_related": item.is_current_focus_related,
        "is_active_leaf": item.is_active_leaf,
        "execution_readiness": (
            None
            if readiness is None
            else {
                "execution_ready": readiness.execution_ready,
                "autonomy_level": readiness.autonomy_level,
                "operation_risk": readiness.operation_risk,
                "allowed_paths": list(readiness.allowed_paths),
                "forbidden_paths": list(readiness.forbidden_paths),
                "validation_commands": list(readiness.validation_commands),
                "required_evidence": list(readiness.required_evidence),
                "expected_artifacts": list(readiness.expected_artifacts),
                "requires_human_approval": readiness.requires_human_approval,
                "requires_human_merge": readiness.requires_human_merge,
                "requires_human_closeout": readiness.requires_human_closeout,
                "policy_gates": list(readiness.policy_gates),
                "agent_constraints": list(readiness.agent_constraints),
            }
        ),
    }


def _execution_summary(state: core_state.CoreProjectState) -> dict[str, object]:
    ready_items = [
        item
        for item in state.active_leaf_work_items
        if item.execution_readiness is not None
        and item.execution_readiness.execution_ready
    ]
    return {
        "active_leaf_count": len(state.active_leaf_work_items),
        "ready_count": len(ready_items),
        "ready_work_items": [
            {
                "id": item.id,
                "title": item.title,
                "readiness": _work_item_dict(item, state)["execution_readiness"],
                "run_packet": {
                    "available": True,
                    "surface": "lrh request run-packet-from-work-item",
                    "command": f"lrh request run-packet-from-work-item {item.id}",
                },
                "run_report": {
                    "available": True,
                    "surface": "lrh request run-report-from-work-item",
                    "command": f"lrh request run-report-from-work-item {item.id}",
                },
            }
            for item in ready_items
        ],
        "packet_surface": "lrh request run-packet-from-work-item",
        "report_surface": "lrh request run-report-from-work-item",
    }


def _diagnostic_dicts(
    diagnostics: tuple[core_state.DiagnosticSummary, ...],
) -> list[dict[str, str]]:
    return [
        {
            "source": diagnostic.source,
            "file": diagnostic.file,
            "severity": diagnostic.severity,
            "code": diagnostic.code,
            "message": diagnostic.message,
        }
        for diagnostic in diagnostics
    ]


def _count_by_status(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _relative_project_path(state: core_state.CoreProjectState, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(state.identity.project_dir.resolve()))
    except ValueError:
        return path.name


def _html_list(items: object) -> str:
    values = list(items)
    if not values:
        return "<p>None.</p>"
    return (
        "<ul>"
        + "".join(f"<li>{html.escape(str(value))}</li>" for value in values)
        + "</ul>"
    )


def _html_link_list(items: list[tuple[str, str]]) -> str:
    """Render a list of escaped anchor links."""

    if not items:
        return "<p>None.</p>"
    return (
        "<ul>"
        + "".join(
            (
                f'<li><a href="{html.escape(href, quote=True)}">'
                f"{html.escape(label)}</a></li>"
            )
            for href, label in items
        )
        + "</ul>"
    )


def _artifact_label(artifact: object) -> str:
    if not isinstance(artifact, dict):
        return str(artifact)
    return f"{artifact['id']} — {artifact['title']} ({artifact['status']})"


def _ready_item_label(item: object) -> str:
    if not isinstance(item, dict):
        return str(item)
    packet = item["run_packet"]
    report = item["run_report"]
    return (
        f"{item['id']} — {item['title']} "
        f"[packet: {packet['surface']}; report: {report['surface']}]"
    )


def _work_item_execution_ready(item: dict[str, object]) -> bool:
    readiness = item.get("execution_readiness")
    if not isinstance(readiness, dict):
        return False
    return bool(readiness.get("execution_ready"))


def _workbench_item_row(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    work_item_id = str(item["id"])
    title = html.escape(str(item["title"]))
    status = html.escape(str(item["status"]))
    item_type = html.escape(str(item["type"]))
    ready = "yes" if item["execution_ready"] else "no"
    prompt_url = html.escape(str(item["prompt_preview_url"]), quote=True)
    packet_url = html.escape(str(item["packet_preview_url"]), quote=True)
    report_url = html.escape(str(item["report_preview_url"]), quote=True)
    quoted_id = _url_quote(work_item_id)
    return (
        f'<article id="workbench-item-{html.escape(work_item_id, quote=True)}">'
        f"<h3>{html.escape(work_item_id)} — {title}</h3>"
        f"<p>Status: {status}; Type: {item_type}; Execution-ready: {ready}</p>"
        "<ul>"
        f'<li><a href="{prompt_url}">Preview prompt</a></li>'
        f'<li><a href="{packet_url}">Preview run packet</a></li>'
        f'<li><a href="{report_url}">Preview run report</a></li>'
        f'<li><a href="/#work-item-{quoted_id}">Viewer context</a></li>'
        "</ul>"
        "</article>"
    )


def _workbench_safety_notes() -> list[str]:
    return [
        "render previews only after explicit local GET requests",
        "no agent dispatch or backend execution",
        "no branch, commit, pull-request, merge, release, or publish mutation",
        "no repository writes; downloads are generated from memory",
        "no arbitrary filesystem browsing or arbitrary write paths",
    ]


def _kind_from_workbench_route(route: str) -> str:
    return route.rsplit("/", maxsplit=1)[-1]


def _artifact_payload(artifact: WorkbenchArtifact) -> dict[str, object]:
    return {
        "mode": "safe-default-workbench-artifact-preview",
        "kind": artifact.kind,
        "work_item_id": artifact.work_item_id,
        "title": artifact.title,
        "markdown": artifact.markdown,
        "diagnostics": [dict(item) for item in artifact.diagnostics],
        "safety": _workbench_safety_notes(),
        "download_url": (
            f"/workbench/{_url_quote(artifact.kind)}?"
            f"work_item={_url_quote(artifact.work_item_id)}&download=1"
        ),
    }


def _relative_repo_path(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _url_quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _diagnostic_label(diagnostic: object) -> str:
    if not isinstance(diagnostic, dict):
        return str(diagnostic)
    return (
        f"{diagnostic['severity']} {diagnostic['code']} "
        f"({diagnostic['source']}:{diagnostic['file']}): {diagnostic['message']}"
    )


def _host_port_from_address(
    config: ServeConfig,
    bound_address: tuple[object, ...] | None,
) -> tuple[str, int]:
    if bound_address is None:
        return config.host, config.port
    host, port = bound_address[:2]
    return str(host), int(port)


def _address_family_for_host(host: str) -> socket.AddressFamily:
    if ":" in host:
        return socket.AF_INET6
    return socket.AF_INET


def _format_url_host(host: object) -> str:
    text = str(host)
    if ":" in text and not text.startswith("["):
        return f"[{text}]"
    return text


_CLIENT_DISCONNECT_ERRORS = (
    BrokenPipeError,
    ConnectionResetError,
    ConnectionAbortedError,
)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server with daemon request threads for clean shutdown."""

    daemon_threads = True

    def server_bind(self) -> None:
        """Bind without the reverse-DNS lookup ``HTTPServer`` performs.

        ``http.server.HTTPServer.server_bind`` sets ``server_name`` from
        ``socket.getfqdn(host)``. For a loopback address that is a reverse-DNS
        query, which can block for tens of seconds on a slow or misconfigured
        resolver (observed at about 25 s on GitHub's macOS runners) and stall
        startup before the port is even bound. Serve never uses
        ``server_name``, so record the literal bound host instead.
        """

        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Drop client disconnects quietly; report every other error.

        ``socketserver.BaseServer.handle_error`` prints a full traceback to
        stderr for any exception a request raises. A browser or the desktop
        webview that navigates away before a response is fully written raises
        ``BrokenPipeError``, ``ConnectionResetError``, or (on Windows, or
        occasionally as ``ECONNABORTED``) ``ConnectionAbortedError`` from the
        write. That is normal client behavior, not a server fault, and its
        traceback shows up as an apparent error in the desktop app's Server
        Details.

        Filtering here, rather than guarding each response writer, covers every
        write path in one place: the JSON, text, and download writers, plus
        ``BaseHTTPRequestHandler``'s own error responses. Both
        ``ThreadingMixIn.process_request_thread`` and
        ``BaseServer._handle_request_noblock`` call this from inside their
        ``except`` blocks, so ``sys.exc_info()`` is the request's exception.
        """

        if isinstance(sys.exc_info()[1], _CLIENT_DISCONNECT_ERRORS):
            return
        super().handle_error(request, client_address)


class ThreadingIPv6HTTPServer(ThreadingHTTPServer):
    """Threaded HTTP server configured for IPv6 loopback binds."""

    address_family = socket.AF_INET6


def make_handler(config: ServeConfig) -> type[http.server.BaseHTTPRequestHandler]:
    """Build a request handler scoped to one immutable server configuration."""

    class LrhServeHandler(http.server.BaseHTTPRequestHandler):
        server_version = "LRHServe/0"
        sys_version = ""

        def do_GET(self) -> None:
            route = self._route_path()
            if route == "/":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_index(config, bound_address=self._bound_address()),
                )
                return
            if route == "/workbench":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_workbench_index(config),
                )
                return
            if route == "/conversations/codex":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_codex_archive_index(config),
                )
                return
            if route.startswith("/conversations/codex/"):
                export_id = urllib.parse.unquote(
                    route.removeprefix("/conversations/codex/")
                )
                status_code, body = render_codex_archive_detail(config, export_id)
                if status_code == 200:
                    self._write_text(200, "text/html; charset=utf-8", body)
                else:
                    self._write_json(status_code, json.loads(body))
                return
            if route == "/meta":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_meta_dashboard(config),
                )
                return
            if route == frame.SETTINGS_PATH:
                self._write_text(
                    200, "text/html; charset=utf-8", render_settings_page(config)
                )
                return
            if route.startswith(frame.STATIC_PREFIX):
                self._write_static(route.removeprefix(frame.STATIC_PREFIX))
                return
            if route == "/style":
                self._write_text(
                    200, "text/html; charset=utf-8", render_style_specimen()
                )
                return
            if route == "/meta/project":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_meta_project_placeholder(
                        self._query_values().get("project", "unknown")
                    ),
                )
                return
            if route.startswith("/project/"):
                remainder = route.removeprefix("/project/")
                parts = [
                    urllib.parse.unquote(part) for part in remainder.split("/") if part
                ]
                if len(parts) in (2, 3) and parts[1] == "dependency-maps":
                    status_code, body = render_dependency_map_page(
                        config,
                        parts[0],
                        parts[2] if len(parts) == 3 else None,
                        self._query_values(),
                    )
                    if status_code == 404 and not body:
                        self._write_json(404, {"error": "not_found"})
                    else:
                        self._write_text(status_code, "text/html; charset=utf-8", body)
                    return
                if len(parts) == 3 and parts[1] == "designs":
                    status_code, body = render_design_detail_page(
                        config, parts[0], parts[2]
                    )
                    if status_code == 200:
                        self._write_text(200, "text/html; charset=utf-8", body)
                    else:
                        self._write_json(status_code, json.loads(body))
                    return
                if len(parts) == 3 and parts[1] == "workstreams":
                    status_code, body = render_workstream_detail_page(
                        config, parts[0], parts[2]
                    )
                    if status_code == 200:
                        self._write_text(200, "text/html; charset=utf-8", body)
                    else:
                        self._write_json(status_code, json.loads(body))
                    return
                if len(parts) == 3 and parts[1] == "work-items":
                    status_code, body = render_project_work_item_page(
                        config, parts[0], parts[2]
                    )
                    if status_code == 200 or body.startswith("<!doctype html>"):
                        self._write_text(status_code, "text/html; charset=utf-8", body)
                    else:
                        self._write_json(status_code, json.loads(body))
                    return
                if (
                    len(parts) == 4
                    and parts[1] == "work-items"
                    and parts[3] == "prompt"
                ):
                    try:
                        scoped_config = _config_for_project_selector(config, parts[0])
                    except ProjectSelectorError as error:
                        self._write_text(
                            error.status,
                            "text/html; charset=utf-8",
                            render_project_selector_error_page(error),
                        )
                        return
                    try:
                        artifact = render_workbench_artifact(
                            scoped_config, "prompt", parts[2]
                        )
                    except (FileNotFoundError, OSError, ValueError) as error:
                        self._write_json(
                            404, {"error": "not_found", "message": str(error)}
                        )
                        return
                    self._write_text(
                        200,
                        "text/html; charset=utf-8",
                        render_workbench_artifact_page(artifact),
                    )
                    return
                project_selector = urllib.parse.unquote(route.removeprefix("/project/"))
                status_code, body = render_project_operational_dashboard(
                    config, project_selector
                )
                if status_code == 200:
                    self._write_text(200, "text/html; charset=utf-8", body)
                else:
                    self._write_json(status_code, json.loads(body))
                return
            if route in _WORKBENCH_ARTIFACT_ROUTES:
                self._write_workbench_artifact(route)
                return
            if route == "/health":
                self._write_json(200, {"status": "ok"})
                return
            if route == "/api/status":
                self._write_json(
                    200,
                    status_payload(config, bound_address=self._bound_address()),
                )
                return
            if route == "/api/project":
                self._write_json(200, project_viewer_payload(config))
                return
            if route.startswith("/api/project/"):
                status_code, payload = dependency_map_payload(
                    config, route.removeprefix("/api/project/")
                )
                self._write_json(status_code, payload)
                return
            if route == "/api/workbench":
                self._write_json(200, workbench_payload(config))
                return
            if route == "/api/conversations/codex":
                self._write_json(200, codex_archive_payload(config))
                return
            if route.startswith("/api/conversations/codex/"):
                export_id = urllib.parse.unquote(
                    route.removeprefix("/api/conversations/codex/")
                )
                payload = codex_archive_detail_payload(config, export_id)
                if payload is None:
                    self._write_json(
                        404,
                        {
                            "error": "not_found",
                            "message": "Codex export is not configured",
                        },
                    )
                    return
                self._write_json(200, payload)
                return
            if route == "/api/meta":
                self._write_json(200, meta_dashboard_payload(config))
                return
            if route in _WORKBENCH_API_ROUTES:
                self._write_workbench_artifact_json(route)
                return
            self._write_json(404, {"error": "not_found"})

        def do_HEAD(self) -> None:
            route = self._route_path()
            if route.startswith("/project/"):
                remainder = route.removeprefix("/project/")
                parts = [
                    urllib.parse.unquote(part) for part in remainder.split("/") if part
                ]
                if len(parts) in (2, 3) and parts[1] == "dependency-maps":
                    try:
                        _config_for_project_selector(config, parts[0])
                    except ProjectSelectorError as error:
                        self._write_head(error.status, "text/html; charset=utf-8")
                        return
                    status_code = (
                        dependency_map_head_status(config, remainder)
                        if len(parts) == 3
                        else 200
                    )
                    self._write_head(
                        status_code,
                        (
                            "application/json; charset=utf-8"
                            if status_code == 404
                            else "text/html; charset=utf-8"
                        ),
                    )
                    return
                if len(parts) == 3 and parts[1] in {"designs", "workstreams"}:
                    if parts[1] == "designs":
                        status_code, _body = render_design_detail_page(
                            config, parts[0], parts[2]
                        )
                    else:
                        status_code, _body = render_workstream_detail_page(
                            config, parts[0], parts[2]
                        )
                    if status_code == 200:
                        self._write_head(200, "text/html; charset=utf-8")
                    else:
                        self._write_head(status_code, "application/json; charset=utf-8")
                    return
                project_selector = urllib.parse.unquote(route.removeprefix("/project/"))
                status_code, _body = render_project_operational_dashboard(
                    config, project_selector
                )
                if status_code == 200:
                    self._write_head(200, "text/html; charset=utf-8")
                else:
                    self._write_head(status_code, "application/json; charset=utf-8")
                return
            if route.startswith(frame.STATIC_PREFIX):
                name = route.removeprefix(frame.STATIC_PREFIX)
                if frame.read_static(name) is None:
                    self._write_head(404, "application/json; charset=utf-8")
                else:
                    self._write_static(name, head=True)
                return
            if route in _WORKBENCH_ARTIFACT_ROUTES:
                self._write_workbench_artifact_head(route)
                return
            if route in _WORKBENCH_API_ROUTES:
                self._write_workbench_artifact_json_head(route)
                return
            if route.startswith("/conversations/codex/"):
                export_id = urllib.parse.unquote(
                    route.removeprefix("/conversations/codex/")
                )
                payload = codex_archive_detail_payload(config, export_id)
                status_code = (
                    200
                    if payload is not None
                    and isinstance(payload.get("export"), dict)
                    and payload["export"].get("valid")
                    else 404
                )
                content_type = (
                    "text/html; charset=utf-8"
                    if status_code == 200
                    else "application/json; charset=utf-8"
                )
                self._write_head(status_code, content_type)
                return
            if route.startswith("/api/project/"):
                status_code = dependency_map_head_status(
                    config, route.removeprefix("/api/project/")
                )
                self._write_head(status_code, "application/json; charset=utf-8")
                return
            if route.startswith("/api/conversations/codex/"):
                export_id = urllib.parse.unquote(
                    route.removeprefix("/api/conversations/codex/")
                )
                status_code = (
                    200
                    if codex_archive_detail_payload(config, export_id) is not None
                    else 404
                )
                self._write_head(status_code, "application/json; charset=utf-8")
                return
            if route in {
                "/",
                "/workbench",
                "/conversations/codex",
                "/meta",
                "/meta/project",
                "/style",
                "/settings",
                "/health",
                "/api/status",
                "/api/project",
                "/api/workbench",
                "/api/conversations/codex",
                "/api/meta",
            }:
                content_type = "application/json; charset=utf-8"
                if route in {
                    "/",
                    "/workbench",
                    "/conversations/codex",
                    "/meta",
                    "/meta/project",
                    "/style",
                    "/settings",
                }:
                    content_type = "text/html; charset=utf-8"
                self._write_head(200, content_type)
                return
            self._write_head(404, "application/json; charset=utf-8")

        def do_POST(self) -> None:
            self._write_json(405, {"error": "method_not_allowed"})

        def do_PUT(self) -> None:
            self._write_json(405, {"error": "method_not_allowed"})

        def do_DELETE(self) -> None:
            self._write_json(405, {"error": "method_not_allowed"})

        def do_PATCH(self) -> None:
            self._write_json(405, {"error": "method_not_allowed"})

        def do_OPTIONS(self) -> None:
            self._write_json(405, {"error": "method_not_allowed"})

        def log_message(self, format: str, *args: object) -> None:
            return

        def _write_workbench_artifact(self, route: str) -> None:
            kind = _kind_from_workbench_route(route)
            query = self._query_values()
            work_item_id = query.get("work_item", "")
            try:
                artifact = render_workbench_artifact(config, kind, work_item_id)
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_json(404, {"error": "not_found", "message": str(error)})
                return
            if query.get("download") == "1":
                self._write_download(artifact)
                return
            self._write_text(
                200,
                "text/html; charset=utf-8",
                render_workbench_artifact_page(artifact),
            )

        def _write_workbench_artifact_head(self, route: str) -> None:
            kind = _kind_from_workbench_route(route)
            query = self._query_values()
            work_item_id = query.get("work_item", "")
            try:
                artifact = render_workbench_artifact(config, kind, work_item_id)
            except (FileNotFoundError, OSError, ValueError):
                self._write_head(404, "application/json; charset=utf-8")
                return
            if query.get("download") == "1":
                self._write_download_head(artifact)
                return
            self._write_head(200, "text/html; charset=utf-8")

        def _write_workbench_artifact_json(self, route: str) -> None:
            kind = _kind_from_workbench_route(route)
            query = self._query_values()
            work_item_id = query.get("work_item", "")
            try:
                artifact = render_workbench_artifact(config, kind, work_item_id)
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_json(404, {"error": "not_found", "message": str(error)})
                return
            self._write_json(200, _artifact_payload(artifact))

        def _write_workbench_artifact_json_head(self, route: str) -> None:
            kind = _kind_from_workbench_route(route)
            query = self._query_values()
            work_item_id = query.get("work_item", "")
            try:
                render_workbench_artifact(config, kind, work_item_id)
            except (FileNotFoundError, OSError, ValueError):
                self._write_head(404, "application/json; charset=utf-8")
                return
            self._write_head(200, "application/json; charset=utf-8")

        def _add_security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                content_security_policy(config),
            )

        def _write_download(self, artifact: WorkbenchArtifact) -> None:
            filename = f"{artifact.work_item_id}-{artifact.kind}.md"
            body = artifact.markdown.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self._add_security_headers()
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"',
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_download_head(self, artifact: WorkbenchArtifact) -> None:
            filename = f"{artifact.work_item_id}-{artifact.kind}.md"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self._add_security_headers()
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"',
            )
            self.send_header(
                "Content-Length", str(len(artifact.markdown.encode("utf-8")))
            )
            self.end_headers()

        def _write_head(self, status_code: int, content_type: str) -> None:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self._add_security_headers()
            self.end_headers()

        def _query_values(self) -> dict[str, str]:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            return {key: values[0] for key, values in query.items() if values}

        def _route_path(self) -> str:
            return urllib.parse.urlsplit(self.path).path

        def _bound_address(self) -> tuple[object, ...] | None:
            address = getattr(self.server, "server_address", None)
            if isinstance(address, tuple):
                return address
            return None

        def _write_static(self, name: str, *, head: bool = False) -> None:
            # The script exists only for --interactive servers.
            body = (
                None
                if name in _INTERACTIVE_SCRIPTS and not config.interactive
                else frame.read_static(name)
            )
            if body is None:
                if head:
                    self._write_head(404, "application/json; charset=utf-8")
                else:
                    self._write_json(404, {"error": "not_found"})
                return
            self.send_response(200)
            self.send_header("Content-Type", frame.STATIC_FILES[name])
            # Assets ship with the package, so an hour of caching is safe.
            # Scripts must not outlive an upgrade; fonts and images may.
            self.send_header(
                "Cache-Control",
                "no-cache" if name.endswith(".js") else "max-age=3600",
            )
            self._add_security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)

        def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self._add_security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_text(
            self,
            status_code: int,
            content_type: str,
            text: str,
        ) -> None:
            if content_type.startswith("text/html"):
                text = frame.apply_frame(
                    text,
                    frame.FrameContext(
                        path=self._route_path(),
                        query=self._query_values(),
                        projects=_frame_projects(config),
                    ),
                )
                text = apply_theme(text, config.theme)
                text = apply_interactive(text, config.interactive)
            body = text.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self._add_security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return LrhServeHandler


def create_http_server(config: ServeConfig) -> ThreadingHTTPServer:
    """Create but do not start the configured HTTP server."""

    validate_host(config)
    server_class: type[ThreadingHTTPServer]
    if _address_family_for_host(config.host) == socket.AF_INET6:
        server_class = ThreadingIPv6HTTPServer
    else:
        server_class = ThreadingHTTPServer
    return server_class((config.host, config.port), make_handler(config))


def build_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Start the safe-default LRH local read-only viewer. The server is "
            "a read-only local viewer entrypoint, not an autonomous runner."
        ),
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="bind host (default: 127.0.0.1; non-local hosts require opt-in)",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help=f"bind port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="project repository root used for read-only viewer summaries (default: .)",
    )
    parser.add_argument(
        "--codex-archive-root",
        action="append",
        default=[],
        help=(
            "explicit Codex conversation export archive root to list in the "
            "local viewer; may be supplied more than once"
        ),
    )
    parser.add_argument(
        "--allow-nonlocal-host",
        action="store_true",
        help=(
            "explicitly allow binding beyond localhost; this can expose the "
            "read-only viewer on your network"
        ),
    )
    parser.add_argument(
        "--theme",
        choices=THEMES,
        default=DEFAULT_THEME,
        help=(
            "page theme: light, dark, or system to follow the OS appearance "
            "(default: system)"
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help=(
            "add packaged same-origin scripts for tracing, filters, and the "
            "in-page theme switch (CSP script-src 'self'); pages still work "
            "without them"
        ),
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="validate and print deterministic JSON configuration without serving",
    )
    parser.add_argument(
        "--desktop-protocol",
        action="store_true",
        help=(
            "run under a desktop supervisor: read a versioned JSON start "
            "request on stdin, bind 127.0.0.1 on an OS-assigned port, and "
            "report ready/failed as JSON on stdout (see "
            "docs/reference/desktop-server-protocol.md); cannot be combined "
            "with other serve options except --theme and --interactive"
        ),
    )
    parser.add_argument(
        "--desktop-start-timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help=(
            "with --desktop-protocol, seconds to wait for the start request "
            f"(default: {desktop_protocol.DEFAULT_START_REQUEST_TIMEOUT_SECONDS:g})"
        ),
    )
    return parser


def config_from_args(args: argparse.Namespace) -> ServeConfig:
    return ServeConfig(
        host=args.host,
        port=args.port,
        project_root=Path(args.project_root),
        allow_nonlocal_host=args.allow_nonlocal_host,
        codex_archive_roots=tuple(Path(root) for root in args.codex_archive_root),
        theme=args.theme,
        interactive=args.interactive,
    )


# Serve options that desktop-protocol mode refuses, keyed by argparse dest.
_DESKTOP_PROTOCOL_CONFLICTS = {
    "host": "--host",
    "port": "--port",
    "project_root": "--project-root",
    "codex_archive_root": "--codex-archive-root",
    "allow_nonlocal_host": "--allow-nonlocal-host",
    "show_config": "--show-config",
}


def _desktop_protocol_conflicts(prog: str, argv: list[str] | None) -> list[str]:
    """Return conflicting serve options given explicitly, even at defaults."""

    # Re-parse with None defaults so explicitly supplied default values (for
    # example ``--port 8765``) are still detected. None is used rather than
    # argparse.SUPPRESS because argparse type-converts string defaults.
    probe = build_parser(prog)
    probe.set_defaults(**{dest: None for dest in _DESKTOP_PROTOCOL_CONFLICTS})
    explicit = probe.parse_args(argv)
    return [
        flag
        for dest, flag in _DESKTOP_PROTOCOL_CONFLICTS.items()
        if getattr(explicit, dest) is not None
    ]


def _desktop_server_factory(
    project_root: Path, theme: str = DEFAULT_THEME, interactive: bool = False
) -> ThreadingHTTPServer:
    """Create a loopback server on an OS-assigned port for desktop mode."""

    return create_http_server(
        ServeConfig(
            host=desktop_protocol.LOOPBACK_HOST,
            port=0,
            project_root=project_root,
            theme=theme,
            interactive=interactive,
        )
    )


def _run_desktop_protocol_cli(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    argv: list[str] | None,
) -> int:
    conflicts = _desktop_protocol_conflicts(parser.prog, argv)
    if conflicts:
        parser.error(
            "--desktop-protocol takes its workspace from the start request and "
            "always binds 127.0.0.1 on an OS-assigned port; remove "
            + ", ".join(conflicts)
        )
    timeout = args.desktop_start_timeout
    if timeout is None:
        timeout = desktop_protocol.DEFAULT_START_REQUEST_TIMEOUT_SECONDS
    if not (
        desktop_protocol.MIN_START_REQUEST_TIMEOUT_SECONDS
        <= timeout
        <= desktop_protocol.MAX_START_REQUEST_TIMEOUT_SECONDS
    ):
        parser.error(
            "--desktop-start-timeout must be between "
            f"{desktop_protocol.MIN_START_REQUEST_TIMEOUT_SECONDS:g} and "
            f"{desktop_protocol.MAX_START_REQUEST_TIMEOUT_SECONDS:g} seconds"
        )
    return desktop_protocol.run_desktop_protocol(
        lambda project_root: _desktop_server_factory(
            project_root, theme=args.theme, interactive=args.interactive
        ),
        start_request_timeout=timeout,
    )


def run_serve_cli(argv: list[str] | None = None, prog: str = "lrh serve") -> int:
    parser = build_parser(prog)
    args = parser.parse_args(argv)
    if args.desktop_protocol:
        return _run_desktop_protocol_cli(parser, args, argv)
    if args.desktop_start_timeout is not None:
        parser.error("--desktop-start-timeout requires --desktop-protocol")
    config = config_from_args(args)
    try:
        validate_host(config)
    except ValueError as err:
        parser.error(str(err))

    if args.show_config:
        print(json.dumps(status_payload(config), indent=2, sort_keys=True))
        return 0

    httpd = create_http_server(config)
    actual_host, actual_port = httpd.server_address[:2]
    url_host = _format_url_host(actual_host)
    print(
        "lrh serve listening on "
        f"http://{url_host}:{actual_port} "
        "(read-only safe-default viewer)",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nlrh serve stopped", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0

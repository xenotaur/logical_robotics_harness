"""Safe-default local read-only HTTP viewer for ``lrh serve``."""

from __future__ import annotations

import argparse
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

from lrh import core_state
from lrh.assist import run_packet, run_report, work_item_prompt_core
from lrh.control import loader as control_loader
from lrh.meta import workspace as meta_workspace
from lrh.ux import dashboard

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
UNSAFE_HOSTS = frozenset({"0.0.0.0", "::", ""})
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
    "/meta",
    "/meta/project",
    "/project/<project_id>",
    "/project/<project_id>/designs/<design_id>",
    "/project/<project_id>/workstreams/<workstream_id>",
    "/project/<project_id>/work-items/<work_item_id>",
    "/project/<project_id>/work-items/<work_item_id>/prompt",
    "/health",
    "/api/status",
    "/api/project",
    "/api/workbench",
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
    return {
        "service": "lrh serve",
        "status": "ok",
        "mode": "safe-default-read-only-viewer",
        "host": host,
        "port": port,
        "project_root_name": project_root.name,
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
<html lang=\"en\" data-theme=\"light\">
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
    return {
        "mode": "safe-default-read-only-meta-triage",
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
    """Render the read-only registered-project swimlane dashboard."""

    payload = meta_dashboard_payload(config)
    workspace = payload["workspace"]
    workspace_note = "Meta workspace available."
    if isinstance(workspace, dict) and workspace.get("error"):
        workspace_note = f"Meta workspace unavailable: {workspace['error']}"
    lane_html = "".join(_meta_lane_html(lane) for lane in payload["lanes"])
    if payload["total_projects"] == 0:
        empty_note = (
            '<p class="lrh-muted">No registered projects are available in the '
            "active meta workspace.</p>"
        )
    else:
        empty_note = ""
    return """<!doctype html>
<html lang=\"en\" data-theme=\"light\">
<head>
  <meta charset=\"utf-8\">
  <title>LRH Meta Operational Triage</title>
  {styles}
</head>
<body>
  <div class=\"lrh-app-shell\">
    <header class=\"lrh-page-header\">
      <p class=\"lrh-eyebrow\">LRH Console preview</p>
      <h1>Meta Operational Triage</h1>
      <p><a href=\"/\">Back to project viewer</a></p>
      <aside class=\"lrh-guardrail-callout\" aria-label=\"Meta dashboard guardrails\">
        This safe-default, read-only dashboard summarizes registered projects from
        the LRH meta workspace. It does not inspect arbitrary files, expose secrets,
        dispatch agents, create branches, commit, open pull requests, merge, release,
        publish, or provide write routes. Meta workspace state is informative only;
        project-local project/ control planes remain authoritative.
      </aside>
    </header>
    <main id=\"main-content\" class=\"lrh-main-content\">
      <section class=\"lrh-console-region\" aria-labelledby=\"meta-summary-heading\">
        <h2 id=\"meta-summary-heading\">Registered project swimlanes</h2>
        <p>{workspace_note}</p>
        <p>Total registered projects shown: {total_projects}</p>
        {empty_note}
      </section>
      {lane_html}
      <section class=\"lrh-console-region\" aria-labelledby=\"meta-api-heading\">
        <h2 id=\"meta-api-heading\">Read-only API</h2>
        <ul><li><a href=\"/api/meta\">/api/meta</a></li></ul>
      </section>
    </main>
  </div>
</body>
</html>
""".format(
        styles=_base_styles(),
        workspace_note=html.escape(workspace_note),
        total_projects=html.escape(str(payload["total_projects"])),
        empty_note=empty_note,
        lane_html=lane_html,
    )


def render_meta_project_placeholder(project_selector: str) -> str:
    """Render a deterministic placeholder for future project detail pages."""

    selector = html.escape(project_selector or "unknown")
    return """<!doctype html>
<html lang=\"en\" data-theme=\"light\">
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
<html lang=\"en\" data-theme=\"light\">
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
    workspace = meta_workspace.resolve_meta_workspace(
        cwd=config.resolved_project_root(),
        options=meta_workspace.MetaWorkspaceResolveOptions(),
    )
    for result in meta_workspace.list_registered_project_loads_in_workspace(workspace):
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
    loaded = control_loader.load_project(project_root)
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
    loaded = control_loader.load_project(project_root)
    return [{"id": item.id, "title": item.title} for item in loaded.workstreams]


def render_design_detail_page(
    config: ServeConfig, project_selector: str, design_id: str
) -> tuple[int, str]:
    _record, project_root = _project_from_meta_selector(config, project_selector)
    if project_root is None:
        return 404, json.dumps(
            {"error": "not_found", "project": project_selector}, indent=2
        )
    loaded = control_loader.load_project(project_root)
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
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
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
    loaded = control_loader.load_project(project_root)
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
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
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
            field="source_state",
            state="not_implemented",
            message=(
                "Live/cache inspection is not implemented for registered "
                "projects yet."
            ),
        ),
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
    inspect_result = _inspect_registered_project(workspace, result.registry_name)
    if inspect_result is not None:
        source_state = _source_state_from_inspect_result(inspect_result)
        diagnostics = _diagnostics_for_source_state(inspect_result, source_state)
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
        if (isinstance(blocked_by, list) and blocked_by) or status in {
            "blocked",
            "stalled",
        }:
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
        "source_state": project.source_state,
        "validation_status": project.validation_status,
        "validation_error_count": project.validation_error_count,
        "validation_warning_count": project.validation_warning_count,
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
        "capability_gaps": [
            {"field": gap.field, "state": gap.state, "message": gap.message}
            for gap in project.capability_gaps
        ],
        "diagnostics": list(project.diagnostics),
    }


def _meta_lane_html(lane: object) -> str:
    if not isinstance(lane, dict):
        return ""
    cards = lane.get("projects", [])
    card_html = "".join(
        _meta_card_html(card) for card in cards if isinstance(card, dict)
    )
    if not card_html:
        card_html = '<p class="lrh-muted">No projects in this lane.</p>'
    label = html.escape(str(lane["label"]))
    status = html.escape(str(lane["status"]), quote=True)
    count = html.escape(str(lane["count"]))
    description = html.escape(str(lane["description"]))
    return (
        f'<section class="lrh-console-region lrh-meta-lane" '
        f'aria-labelledby="meta-lane-{status}-heading">'
        f'<h2 id="meta-lane-{status}-heading">{label} ({count})</h2>'
        f"<p>{description}</p>{card_html}</section>"
    )


def _meta_card_html(card: dict[str, object]) -> str:
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
    fields = (
        ("Project ID", "project_id"),
        ("Short name", "short_name"),
        ("Locator", "locator"),
        ("Source state", "source_state"),
        ("Validation status", "validation_status"),
        ("Current focus", "current_focus_summary"),
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
    setup_guidance = _meta_card_setup_guidance_html(card)
    return (
        f'<article class="lrh-project-card" id="meta-project-{registry_anchor}">'
        f'<h3><a href="{detail_url}">{name}</a></h3>'
        f'<dl class="lrh-summary-grid">{field_html}</dl>'
        f"{setup_guidance}"
        f"<h4>Capability gaps</h4>{gap_html}"
        f"<h4>Diagnostics</h4>{diagnostic_html}</article>"
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
<html lang=\"en\" data-theme=\"light\">
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
<html lang=\"en\" data-theme=\"light\">
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


def _config_for_project_selector(
    config: ServeConfig, project_selector: str
) -> ServeConfig:
    """Return project-scoped config for a project selector when possible."""

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
    ):
        return config
    resolved_path = selection.resolved_project_path
    if resolved_path is None:
        return config
    return ServeConfig(
        host=config.host,
        port=config.port,
        project_root=resolved_path,
        allow_nonlocal_host=config.allow_nonlocal_host,
    )


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
    }


def _base_styles() -> str:
    """Return small semantic token scaffolding for package-owned serve pages."""

    return """<style>
  :root {
    --lrh-color-surface-page: #f7f5ef;
    --lrh-color-surface-panel: #fffdf8;
    --lrh-color-text-primary: #18212f;
    --lrh-color-text-muted: #5f6b7a;
    --lrh-color-border-subtle: #d9d2c4;
    --lrh-color-status-needs-attention-bg: #ffe8e8;
    --lrh-color-status-needs-attention-text: #7f1d1d;
    --lrh-color-status-active-work-bg: #e8f1ff;
    --lrh-color-status-active-work-text: #16396b;
    --lrh-color-status-awaiting-review-bg: #fff4d6;
    --lrh-color-status-awaiting-review-text: #614600;
    --lrh-color-status-stable-bg: #e4f7ec;
    --lrh-color-status-stable-text: #14532d;
    --lrh-color-status-unknown-bg: #eceff3;
    --lrh-color-status-unknown-text: #3f4856;
    --lrh-focus-ring: 0 0 0 3px rgba(59, 130, 246, 0.45);
  }

  [data-theme="dark"] {
    --lrh-color-surface-page: #101722;
    --lrh-color-surface-panel: #172131;
    --lrh-color-text-primary: #f7f5ef;
    --lrh-color-text-muted: #b8c1cc;
    --lrh-color-border-subtle: #334155;
    --lrh-color-status-needs-attention-bg: #4a1f24;
    --lrh-color-status-needs-attention-text: #ffd7d7;
    --lrh-color-status-active-work-bg: #1e3a5f;
    --lrh-color-status-active-work-text: #d8e9ff;
    --lrh-color-status-awaiting-review-bg: #453514;
    --lrh-color-status-awaiting-review-text: #ffe9a8;
    --lrh-color-status-stable-bg: #173b29;
    --lrh-color-status-stable-text: #c9f7d9;
    --lrh-color-status-unknown-bg: #2b3544;
    --lrh-color-status-unknown-text: #e2e8f0;
  }

  body {
    background: var(--lrh-color-surface-page);
    color: var(--lrh-color-text-primary);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
    border-radius: 1rem;
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
    border-radius: 999px;
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


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server with daemon request threads for clean shutdown."""

    daemon_threads = True


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
            if route == "/meta":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_meta_dashboard(config),
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
                    if status_code == 200:
                        self._write_text(200, "text/html; charset=utf-8", body)
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
            if route == "/api/workbench":
                self._write_json(200, workbench_payload(config))
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
            if route in _WORKBENCH_ARTIFACT_ROUTES:
                self._write_workbench_artifact_head(route)
                return
            if route in _WORKBENCH_API_ROUTES:
                self._write_workbench_artifact_json_head(route)
                return
            if route in {
                "/",
                "/workbench",
                "/meta",
                "/meta/project",
                "/health",
                "/api/status",
                "/api/project",
                "/api/workbench",
                "/api/meta",
            }:
                content_type = "application/json; charset=utf-8"
                if route in {
                    "/",
                    "/workbench",
                    "/meta",
                    "/meta/project",
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

        def _write_download(self, artifact: WorkbenchArtifact) -> None:
            filename = f"{artifact.work_item_id}-{artifact.kind}.md"
            body = artifact.markdown.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
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

        def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_text(
            self,
            status_code: int,
            content_type: str,
            text: str,
        ) -> None:
            body = text.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
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
        "--allow-nonlocal-host",
        action="store_true",
        help=(
            "explicitly allow binding beyond localhost; this can expose the "
            "read-only viewer on your network"
        ),
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="validate and print deterministic JSON configuration without serving",
    )
    return parser


def config_from_args(args: argparse.Namespace) -> ServeConfig:
    return ServeConfig(
        host=args.host,
        port=args.port,
        project_root=Path(args.project_root),
        allow_nonlocal_host=args.allow_nonlocal_host,
    )


def run_serve_cli(argv: list[str] | None = None, prog: str = "lrh serve") -> int:
    parser = build_parser(prog)
    args = parser.parse_args(argv)
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

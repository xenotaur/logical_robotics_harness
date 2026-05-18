"""Safe-default local read-only HTTP viewer for ``lrh serve``."""

from __future__ import annotations

import argparse
import html
import http.server
import json
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
    "/health",
    "/api/status",
    "/api/project",
    "/api/workbench",
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
            if route in _WORKBENCH_API_ROUTES:
                self._write_workbench_artifact_json(route)
                return
            self._write_json(404, {"error": "not_found"})

        def do_HEAD(self) -> None:
            route = self._route_path()
            if route in _WORKBENCH_ARTIFACT_ROUTES:
                self._write_workbench_artifact_head(route)
                return
            if route in _WORKBENCH_API_ROUTES:
                self._write_workbench_artifact_json_head(route)
                return
            if route in {
                "/",
                "/workbench",
                "/health",
                "/api/status",
                "/api/project",
                "/api/workbench",
            }:
                content_type = "application/json; charset=utf-8"
                if route in {"/", "/workbench"}:
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

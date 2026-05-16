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
from lrh.control import loader as control_loader

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
UNSAFE_HOSTS = frozenset({"0.0.0.0", "::", ""})


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
        "routes": ["/", "/health", "/api/status", "/api/project"],
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
    focus_text = "None loaded"
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
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>LRH Serve</title>
</head>
<body>
  <main>
    <h1>Logical Robotics Harness</h1>
    <p>Safe-default read-only project viewer.</p>
    <p>This viewer summarizes existing LRH project-control state. It does not
    serve arbitrary files, dispatch agents, mutate branches, create pull
    requests, make external network calls, or provide write routes.</p>
    <dl>
      <dt>Project</dt><dd>{project_name}</dd>
      <dt>Bind</dt><dd>{host}:{port}</dd>
      <dt>Validation</dt><dd>{validation_status} ({error_count} errors,
      {warning_count} warnings)</dd>
      <dt>Current focus</dt><dd>{focus_text}</dd>
      <dt>Work items</dt><dd>{work_item_count}</dd>
      <dt>Workstreams</dt><dd>{workstream_count}</dd>
    </dl>
    <section>
      <h2>Active workstreams</h2>
      {active_workstreams}
    </section>
    <section>
      <h2>Active leaf work items</h2>
      {active_leaves}
    </section>
    <section>
      <h2>Execution-ready leaves</h2>
      <p>Run-packet and run-report surfaces are references only; this page does
      not generate packets or reports.</p>
      {ready_items}
    </section>
    <section>
      <h2>Diagnostics</h2>
      {diagnostics}
    </section>
    <section>
      <h2>Read-only API</h2>
      <ul>
        <li><a href=\"/health\">/health</a></li>
        <li><a href=\"/api/status\">/api/status</a></li>
        <li><a href=\"/api/project\">/api/project</a></li>
      </ul>
    </section>
  </main>
</body>
</html>
""".format(
        project_name=project_name,
        host=host,
        port=port,
        validation_status=html.escape(str(validation["status"])),
        error_count=validation["error_count"],
        warning_count=validation["warning_count"],
        focus_text=html.escape(focus_text),
        work_item_count=payload["work_items"]["total"],
        workstream_count=payload["workstreams"]["total"],
        active_workstreams=active_workstreams,
        active_leaves=active_leaves,
        ready_items=ready_items,
        diagnostics=diagnostics,
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
    }


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
            self._write_json(404, {"error": "not_found"})

        def do_HEAD(self) -> None:
            route = self._route_path()
            if route in {"/", "/health", "/api/status", "/api/project"}:
                self.send_response(200)
                self.send_header("Cache-Control", "no-store")
                if route == "/":
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                else:
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                return
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

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

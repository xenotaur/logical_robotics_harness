"""Safe-default local HTTP skeleton for ``lrh serve``."""

from __future__ import annotations

import argparse
import html
import http.server
import json
import socket
import socketserver
import sys
from dataclasses import dataclass
from pathlib import Path

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
    """Return deterministic skeleton status data without exposing file contents."""

    project_root = config.resolved_project_root()
    host, port = _host_port_from_address(config, bound_address)
    return {
        "service": "lrh serve",
        "status": "ok",
        "mode": "safe-default-local-skeleton",
        "host": host,
        "port": port,
        "project_root_name": project_root.name,
        "routes": ["/", "/health", "/api/status"],
        "capabilities": {
            "write_routes": False,
            "agent_dispatch": False,
            "branch_mutation": False,
            "pull_request_mutation": False,
            "arbitrary_file_serving": False,
            "external_network_calls": False,
        },
    }


def render_index(
    config: ServeConfig,
    bound_address: tuple[object, ...] | None = None,
) -> str:
    """Render a minimal package-owned HTML index page."""

    payload = status_payload(config, bound_address=bound_address)
    project_name = html.escape(str(payload["project_root_name"]))
    host = html.escape(str(payload["host"]))
    port = html.escape(str(payload["port"]))
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>LRH Serve</title>
</head>
<body>
  <main>
    <h1>Logical Robotics Harness</h1>
    <p>Safe-default local server skeleton.</p>
    <dl>
      <dt>Project</dt><dd>{project_name}</dd>
      <dt>Bind</dt><dd>{host}:{port}</dd>
    </dl>
    <p>This skeleton exposes read-only health/status routes only. It does not
    serve arbitrary files, dispatch agents, mutate branches, create pull
    requests, or provide write routes.</p>
    <ul>
      <li><a href=\"/health\">/health</a></li>
      <li><a href=\"/api/status\">/api/status</a></li>
    </ul>
  </main>
</body>
</html>
""".format(project_name=project_name, host=host, port=port)


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
            if self.path == "/":
                self._write_text(
                    200,
                    "text/html; charset=utf-8",
                    render_index(config, bound_address=self._bound_address()),
                )
                return
            if self.path == "/health":
                self._write_json(200, {"status": "ok"})
                return
            if self.path == "/api/status":
                self._write_json(
                    200,
                    status_payload(config, bound_address=self._bound_address()),
                )
                return
            self._write_json(404, {"error": "not_found"})

        def do_HEAD(self) -> None:
            if self.path in {"/", "/health", "/api/status"}:
                self.send_response(200)
                self.send_header("Cache-Control", "no-store")
                if self.path == "/":
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
            "Start the safe-default LRH local server skeleton. The server is "
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
        help="project repository root used for skeleton status labels (default: .)",
    )
    parser.add_argument(
        "--allow-nonlocal-host",
        action="store_true",
        help=(
            "explicitly allow binding beyond localhost; this can expose the "
            "read-only skeleton on your network"
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
        "(read-only safe-default skeleton)",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nlrh serve stopped", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0

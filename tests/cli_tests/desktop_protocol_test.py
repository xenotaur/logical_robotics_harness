import contextlib
import http.client
import http.server
import io
import os
import pathlib
import queue
import tempfile
import threading
import unittest
import unittest.mock
from typing import Any

from lrh import desktop_protocol, serve
from lrh.cli import main as cli_main

_WAIT_SECONDS = 10.0


def _make_lrh_project(root: pathlib.Path) -> pathlib.Path:
    (root / "project" / "focus").mkdir(parents=True)
    (root / "project" / "work_items").mkdir(parents=True)
    return root


def _start_request(project_root: str, **overrides: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "protocol": desktop_protocol.PROTOCOL_NAME,
        "protocol_version": desktop_protocol.PROTOCOL_VERSION,
        "type": "start",
        "launch_id": "launch-1",
        "workspace": {"project_root": project_root},
    }
    message.update(overrides)
    return message


def _control(message_type: str, **overrides: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "protocol": desktop_protocol.PROTOCOL_NAME,
        "protocol_version": desktop_protocol.PROTOCOL_VERSION,
        "type": message_type,
        "launch_id": "launch-1",
    }
    message.update(overrides)
    return message


class _NotFoundHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


class _ListStatusHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = b"[]"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _Session:
    """Run ``desktop_protocol.run_session`` on in-process pipes."""

    def __init__(
        self,
        test: unittest.TestCase,
        server_factory: desktop_protocol.ServerFactory = serve._desktop_server_factory,
        read_output: bool = True,
        **session_kwargs: Any,
    ) -> None:
        self._input_read, self._input_write = os.pipe()
        self._output_read, self._output_write = os.pipe()
        self.stderr = io.StringIO()
        self.writer = desktop_protocol.MessageWriter(self._output_write)
        self.result: desktop_protocol.SessionResult | None = None
        self._output = desktop_protocol.FrameReader(self._output_read)
        if read_output:
            self._output.start()
        else:
            # Simulate a parent that has already closed its read end.
            os.close(self._output_read)
            self._output_read = -1
        session_kwargs.setdefault("poll_interval", 0.02)
        self._thread = threading.Thread(
            target=self._run,
            args=(server_factory, session_kwargs),
            daemon=True,
        )
        self._thread.start()
        test.addCleanup(self.close)

    def _run(
        self,
        server_factory: desktop_protocol.ServerFactory,
        session_kwargs: dict[str, Any],
    ) -> None:
        try:
            self.result = desktop_protocol.run_session(
                self._input_read,
                self.writer,
                server_factory,
                stderr=self.stderr,
                **session_kwargs,
            )
        finally:
            os.close(self._output_write)

    def send(self, message: dict[str, Any]) -> None:
        self.send_raw(desktop_protocol.encode_message(message))

    def send_raw(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            view = view[os.write(self._input_write, view) :]

    def close_input(self) -> None:
        if self._input_write >= 0:
            os.close(self._input_write)
            self._input_write = -1

    def receive(self) -> dict[str, Any]:
        item = self._output.items.get(timeout=_WAIT_SECONDS)
        if not isinstance(item, dict):
            raise AssertionError(f"expected a message, got {item!r}")
        return item

    def assert_no_more_messages(self, test: unittest.TestCase) -> None:
        item = self._output.items.get(timeout=_WAIT_SECONDS)
        test.assertNotIsInstance(item, dict)

    def wait(self) -> desktop_protocol.SessionResult:
        self._thread.join(_WAIT_SECONDS)
        if self._thread.is_alive() or self.result is None:
            raise AssertionError("session did not finish within the test bound")
        return self.result

    def close(self) -> None:
        self.close_input()
        self._thread.join(_WAIT_SECONDS)
        for fd in (self._input_read, self._output_read):
            if fd >= 0:
                with contextlib.suppress(OSError):
                    os.close(fd)
        self._input_read = self._output_read = -1


def _get_status(port: int, path: str = "/health") -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


class DesktopProtocolFramingTest(unittest.TestCase):
    def test_encode_and_decode_round_trip_one_line(self) -> None:
        frame = desktop_protocol.encode_message({"type": "ping", "n": 1})

        self.assertTrue(frame.endswith(b"\n"))
        self.assertEqual(frame.count(b"\n"), 1)
        self.assertEqual(
            desktop_protocol.decode_message(frame[:-1]), {"type": "ping", "n": 1}
        )

    def test_decode_rejects_non_object_and_invalid_json(self) -> None:
        for frame in (b"[1, 2]", b"not json", b"\xff\xfe"):
            with self.subTest(frame=frame):
                with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
                    desktop_protocol.decode_message(frame)
                self.assertEqual(ctx.exception.code, "malformed_message")

    def test_messages_over_size_limit_are_rejected(self) -> None:
        too_big = {"pad": "x" * desktop_protocol.MAX_MESSAGE_BYTES}

        with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
            desktop_protocol.encode_message(too_big)
        self.assertEqual(ctx.exception.code, "message_too_large")
        with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
            desktop_protocol.decode_message(b"x" * desktop_protocol.MAX_MESSAGE_BYTES)
        self.assertEqual(ctx.exception.code, "message_too_large")


class DesktopProtocolStartRequestTest(unittest.TestCase):
    def test_valid_start_request_is_parsed(self) -> None:
        request = desktop_protocol.parse_start_request(_start_request("/abs/path"))

        self.assertEqual(request.launch_id, "launch-1")
        self.assertEqual(request.protocol_version, 1)
        self.assertEqual(request.requested_project_root, "/abs/path")

    def test_invalid_start_requests_have_stable_codes(self) -> None:
        cases = {
            "unsupported_protocol": _start_request("/p", protocol="other"),
            "malformed_request": _start_request("/p", type="ping"),
            "unsupported_protocol_version": _start_request("/p", protocol_version=2),
            "invalid_launch_id": _start_request("/p", launch_id="has space"),
        }
        for code, message in cases.items():
            with self.subTest(code=code):
                with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
                    desktop_protocol.parse_start_request(message)
                self.assertEqual(ctx.exception.code, code)

    def test_overlong_workspace_path_is_rejected_before_ready(self) -> None:
        # A path this long could still exist ("/./././..."), but its echo in
        # ready would approach the message size limit.
        path = "/" + "./" * desktop_protocol.MAX_WORKSPACE_PATH_BYTES

        with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
            desktop_protocol.parse_start_request(_start_request(path))

        self.assertEqual(ctx.exception.code, "invalid_workspace")
        self.assertIn("(truncated)", ctx.exception.details["requested_project_root"])

    def test_boolean_protocol_version_is_not_accepted_as_one(self) -> None:
        with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
            desktop_protocol.parse_start_request(
                _start_request("/p", protocol_version=True)
            )
        self.assertEqual(ctx.exception.code, "unsupported_protocol_version")
        self.assertEqual(ctx.exception.details, {"supported_versions": [1]})

    def test_missing_workspace_is_malformed(self) -> None:
        message = _start_request("/p")
        del message["workspace"]

        with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
            desktop_protocol.parse_start_request(message)
        self.assertEqual(ctx.exception.code, "malformed_request")


class DesktopProtocolWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = pathlib.Path(temp_dir.name).resolve()

    def test_repo_root_resolves_to_effective_identity(self) -> None:
        repo = _make_lrh_project(self.root / "repo")

        identity = desktop_protocol.resolve_workspace(str(repo))

        self.assertEqual(identity.project_root, repo)
        self.assertEqual(identity.project_dir, repo / "project")
        self.assertEqual(identity.to_message()["name"], "repo")

    def test_project_control_dir_resolves_to_its_repo_root(self) -> None:
        repo = _make_lrh_project(self.root / "repo")

        identity = desktop_protocol.resolve_workspace(str(repo / "project"))

        self.assertEqual(identity.project_root, repo)
        self.assertEqual(
            serve.ServeConfig(project_root=identity.project_root)
            .resolved_project_root()
            .as_posix(),
            repo.as_posix(),
        )

    def test_unusable_paths_are_workspace_errors_not_internal(self) -> None:
        cases = {
            "component_too_long": "/" + "a" * 300,
            "embedded_nul": "/tmp/bad\x00path",
        }
        for name, path in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
                    desktop_protocol.resolve_workspace(path)
                self.assertEqual(ctx.exception.code, "invalid_workspace")

    def test_long_resolved_workspace_path_is_rejected(self) -> None:
        repo = _make_lrh_project(self.root / "a-much-longer-repository-name")
        link = self.root / "link"
        link.symlink_to(repo)

        with unittest.mock.patch.object(
            desktop_protocol, "MAX_WORKSPACE_PATH_BYTES", len(str(link)) + 1
        ):
            with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
                desktop_protocol.resolve_workspace(str(link))

        # The requested path fits the cap; only its resolution exceeds it.
        self.assertGreater(len(str(repo)), len(str(link)) + 1)
        self.assertEqual(ctx.exception.code, "invalid_workspace")
        self.assertIn("resolved", ctx.exception.message)

    def test_invalid_workspaces_are_rejected_without_fallback(self) -> None:
        repo = _make_lrh_project(self.root / "repo")
        (repo / "src").mkdir()
        plain_file = self.root / "file.txt"
        plain_file.write_text("x", encoding="utf-8")
        cases = {
            "relative": ("repo", "invalid_workspace"),
            "missing": (str(self.root / "missing"), "invalid_workspace"),
            "file": (str(plain_file), "invalid_workspace"),
            "not_project": (str(self.root), "workspace_not_lrh_project"),
            # A subdirectory must not silently select its enclosing project.
            "subdirectory": (str(repo / "src"), "workspace_not_lrh_project"),
        }
        for name, (path, code) in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(desktop_protocol.ProtocolError) as ctx:
                    desktop_protocol.resolve_workspace(path)
                self.assertEqual(ctx.exception.code, code)
                self.assertEqual(ctx.exception.details["requested_project_root"], path)


class DesktopProtocolSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.repo = _make_lrh_project(pathlib.Path(temp_dir.name).resolve() / "repo")

    def _ready_session(self, **kwargs: Any) -> tuple[_Session, dict[str, Any]]:
        session = _Session(self, **kwargs)
        session.send(_start_request(str(self.repo)))
        ready = session.receive()
        self.assertEqual(ready["type"], "ready", ready)
        return session, ready

    def test_ready_handshake_reports_endpoint_versions_and_identity(self) -> None:
        session, ready = self._ready_session()

        self.assertEqual(ready["protocol"], "lrh-desktop-server")
        self.assertEqual(ready["protocol_version"], 1)
        self.assertEqual(ready["launch_id"], "launch-1")
        self.assertEqual(ready["backend"]["name"], "lrh")
        self.assertIn("version", ready["backend"])
        self.assertEqual(ready["pid"], os.getpid())
        self.assertEqual(ready["workspace"]["project_root"], str(self.repo))
        self.assertEqual(ready["workspace"]["requested_project_root"], str(self.repo))
        endpoint = ready["endpoint"]
        self.assertEqual(endpoint["host"], "127.0.0.1")
        self.assertGreater(endpoint["port"], 0)
        self.assertEqual(endpoint["url"], f"http://127.0.0.1:{endpoint['port']}/")
        self.assertIs(ready["read_only"], True)
        self.assertIs(ready["execution_authority"], False)
        self.assertEqual(_get_status(endpoint["port"]), 200)

    def test_ready_server_keeps_read_only_routes_and_security_headers(self) -> None:
        session, ready = self._ready_session()
        connection = http.client.HTTPConnection(
            "127.0.0.1", ready["endpoint"]["port"], timeout=5
        )
        self.addCleanup(connection.close)

        connection.request("POST", "/api/status")
        response = connection.getresponse()
        response.read()

        self.assertEqual(response.status, 405)
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertIn(
            "default-src 'none'", response.getheader("Content-Security-Policy")
        )
        self.assertEqual(_get_status(ready["endpoint"]["port"], "/shutdown"), 404)

    def test_shutdown_stops_server_and_reports_lifecycle(self) -> None:
        session, ready = self._ready_session()
        port = ready["endpoint"]["port"]

        session.send(_control("shutdown"))

        self.assertEqual(
            session.receive(),
            {
                "launch_id": "launch-1",
                "protocol": "lrh-desktop-server",
                "protocol_version": 1,
                "reason": "shutdown_requested",
                "type": "stopping",
            },
        )
        self.assertEqual(session.receive()["type"], "stopped")
        result = session.wait()
        self.assertEqual(result.exit_code, desktop_protocol.EXIT_STOPPED)
        self.assertEqual(result.reason, "shutdown_requested")
        with self.assertRaises(OSError):
            _get_status(port)

    def test_ping_echoes_request_id(self) -> None:
        session, _ = self._ready_session()

        session.send(_control("ping", request_id="r-1"))

        pong = session.receive()
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["request_id"], "r-1")
        self.assertEqual(pong["launch_id"], "launch-1")

    def test_stale_launch_id_is_rejected_and_server_keeps_running(self) -> None:
        session, ready = self._ready_session()

        session.send(_control("shutdown", launch_id="launch-0"))

        error = session.receive()
        self.assertEqual(error["type"], "error")
        self.assertEqual(error["error"]["code"], "launch_id_mismatch")
        self.assertEqual(_get_status(ready["endpoint"]["port"]), 200)
        session.send(_control("ping", request_id="still-running"))
        self.assertEqual(session.receive()["type"], "pong")

    def test_unknown_type_and_repeated_start_are_non_fatal_errors(self) -> None:
        session, _ = self._ready_session()

        session.send(_control("reload", request_id="a"))
        session.send(_start_request(str(self.repo)))
        session.send(_control("shutdown", protocol_version=2))
        session.send(_control("shutdown", protocol_version=True))

        unknown = session.receive()
        self.assertEqual(unknown["error"]["code"], "unknown_message_type")
        self.assertEqual(unknown["request_id"], "a")
        self.assertEqual(session.receive()["error"]["code"], "already_started")
        self.assertEqual(
            session.receive()["error"]["code"], "unsupported_protocol_version"
        )
        # JSON true must not be accepted as version 1.
        self.assertEqual(
            session.receive()["error"]["code"], "unsupported_protocol_version"
        )
        session.send(_control("ping"))
        self.assertEqual(session.receive()["type"], "pong")

    def test_oversized_echo_after_ready_stays_a_bounded_error(self) -> None:
        session, _ = self._ready_session()

        # Backslashes double through repr and again through JSON escaping.
        session.send(_control("\\" * 20000, request_id="big"))

        error = session.receive()
        self.assertEqual(error["error"]["code"], "unknown_message_type")
        self.assertIn("(truncated)", error["error"]["message"])
        session.send(_control("ping"))
        self.assertEqual(session.receive()["type"], "pong")

    def test_unexpected_error_after_ready_stops_without_failed(self) -> None:
        calls = []

        def parent_alive() -> bool:
            calls.append(1)
            if len(calls) > 2:
                raise RuntimeError("probe broke")
            return True

        session, ready = self._ready_session(parent_alive=parent_alive)

        stopping = session.receive()
        self.assertEqual(stopping["type"], "stopping")
        self.assertEqual(stopping["reason"], "internal_error")
        self.assertEqual(session.receive()["type"], "stopped")
        session.assert_no_more_messages(self)
        self.assertEqual(session.wait().exit_code, desktop_protocol.EXIT_INTERNAL_ERROR)
        with self.assertRaises(OSError):
            _get_status(ready["endpoint"]["port"])

    def test_malformed_control_message_after_ready_is_fatal(self) -> None:
        session, _ = self._ready_session()

        session.send_raw(b"{not json}\n")

        error = session.receive()
        self.assertEqual(error["type"], "error")
        self.assertEqual(error["error"]["code"], "malformed_message")
        self.assertEqual(session.receive()["reason"], "protocol_error")
        self.assertEqual(session.receive()["type"], "stopped")
        self.assertEqual(session.wait().exit_code, desktop_protocol.EXIT_PROTOCOL_ERROR)

    def test_parent_channel_eof_after_ready_stops_server(self) -> None:
        session, ready = self._ready_session()

        session.close_input()

        self.assertEqual(session.receive()["reason"], "parent_channel_closed")
        self.assertEqual(session.receive()["type"], "stopped")
        self.assertEqual(session.wait().exit_code, desktop_protocol.EXIT_PARENT_LOST)
        with self.assertRaises(OSError):
            _get_status(ready["endpoint"]["port"])

    def test_parent_process_exit_stops_server(self) -> None:
        parent_alive = threading.Event()
        parent_alive.set()
        session, _ = self._ready_session(parent_alive=parent_alive.is_set)

        parent_alive.clear()

        self.assertEqual(session.receive()["reason"], "parent_process_exited")
        self.assertEqual(session.receive()["type"], "stopped")
        self.assertEqual(session.wait().exit_code, desktop_protocol.EXIT_PARENT_LOST)

    def test_stop_signal_stops_gracefully(self) -> None:
        stop_signal = desktop_protocol.StopSignal()
        session, _ = self._ready_session(stop_signal=stop_signal)

        stop_signal.request()

        self.assertEqual(session.receive()["reason"], "signal")
        self.assertEqual(session.receive()["type"], "stopped")
        self.assertEqual(session.wait().exit_code, desktop_protocol.EXIT_STOPPED)

    def test_broken_output_channel_before_ready_stops_without_serving(self) -> None:
        session = _Session(self, read_output=False)

        session.send(_start_request(str(self.repo)))

        result = session.wait()
        self.assertEqual(result.exit_code, desktop_protocol.EXIT_PARENT_LOST)
        self.assertTrue(session.writer.broken)


class DesktopProtocolStartupFailureTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = pathlib.Path(temp_dir.name).resolve()
        self.repo = _make_lrh_project(self.root / "repo")

    def _assert_failed(
        self,
        session: _Session,
        code: str,
        exit_code: int = desktop_protocol.EXIT_STARTUP_FAILED,
        launch_id: str | None = None,
    ) -> dict[str, Any]:
        failed = session.receive()
        self.assertEqual(failed["type"], "failed")
        self.assertEqual(failed["error"]["code"], code)
        self.assertEqual(failed["launch_id"], launch_id)
        self.assertIn("backend", failed)
        session.assert_no_more_messages(self)
        self.assertEqual(session.wait().exit_code, exit_code)
        return failed

    def test_malformed_start_request_fails_without_ready(self) -> None:
        session = _Session(self)

        session.send_raw(b"hello\n")

        self._assert_failed(session, "malformed_request")

    def test_oversized_start_request_fails(self) -> None:
        session = _Session(self)

        session.send_raw(b"x" * (desktop_protocol.MAX_MESSAGE_BYTES + 10))

        self._assert_failed(session, "message_too_large")

    def test_unsupported_version_reports_supported_versions(self) -> None:
        session = _Session(self)

        session.send(_start_request(str(self.repo), protocol_version=99))

        failed = self._assert_failed(
            session, "unsupported_protocol_version", launch_id="launch-1"
        )
        self.assertEqual(failed["error"]["details"], {"supported_versions": [1]})

    def test_oversized_version_echo_still_fails_cleanly(self) -> None:
        session = _Session(self)

        session.send(_start_request(str(self.repo), protocol_version="\\" * 20000))

        failed = self._assert_failed(
            session, "unsupported_protocol_version", launch_id="launch-1"
        )
        self.assertIn("(truncated)", failed["error"]["message"])

    def test_invalid_workspace_fails_with_correlated_launch_id(self) -> None:
        session = _Session(self)

        session.send(_start_request(str(self.root / "missing")))

        self._assert_failed(session, "invalid_workspace", launch_id="launch-1")

    def test_unusable_workspace_path_fails_with_correlated_launch_id(self) -> None:
        session = _Session(self)

        session.send(_start_request("/" + "a" * 300))

        self._assert_failed(session, "invalid_workspace", launch_id="launch-1")

    def test_unexpected_pre_ready_error_keeps_launch_id(self) -> None:
        session = _Session(self)

        with unittest.mock.patch.object(
            desktop_protocol, "resolve_workspace", side_effect=RuntimeError("boom")
        ):
            session.send(_start_request(str(self.repo)))
            self._assert_failed(
                session,
                "internal_error",
                exit_code=desktop_protocol.EXIT_INTERNAL_ERROR,
                launch_id="launch-1",
            )

    def test_non_project_workspace_fails(self) -> None:
        session = _Session(self)

        session.send(_start_request(str(self.root)))

        self._assert_failed(session, "workspace_not_lrh_project", launch_id="launch-1")

    def test_bind_failure_is_reported(self) -> None:
        def failing_factory(project_root: pathlib.Path) -> Any:
            raise OSError("address unavailable")

        session = _Session(self, server_factory=failing_factory)

        session.send(_start_request(str(self.repo)))

        self._assert_failed(session, "bind_failed", launch_id="launch-1")

    def test_self_check_failure_is_reported_and_server_closed(self) -> None:
        created: list[http.server.HTTPServer] = []

        def wrong_server_factory(project_root: pathlib.Path) -> Any:
            server = serve.ThreadingHTTPServer(("127.0.0.1", 0), _NotFoundHandler)
            created.append(server)
            return server

        session = _Session(self, server_factory=wrong_server_factory)

        session.send(_start_request(str(self.repo)))

        self._assert_failed(session, "startup_self_check_failed", launch_id="launch-1")
        with self.assertRaises(OSError):
            _get_status(created[0].server_address[1])

    def test_non_object_status_payload_fails_self_check_and_closes(self) -> None:
        created: list[http.server.HTTPServer] = []

        def list_server_factory(project_root: pathlib.Path) -> Any:
            server = serve.ThreadingHTTPServer(("127.0.0.1", 0), _ListStatusHandler)
            created.append(server)
            return server

        session = _Session(self, server_factory=list_server_factory)

        session.send(_start_request(str(self.repo)))

        self._assert_failed(session, "startup_self_check_failed", launch_id="launch-1")
        with self.assertRaises(OSError):
            _get_status(created[0].server_address[1])

    def test_start_request_timeout_fails(self) -> None:
        session = _Session(self, start_request_timeout=0.05)

        self._assert_failed(session, "start_request_timeout")

    def test_input_closed_before_start_request_reports_parent_lost(self) -> None:
        session = _Session(self)

        session.close_input()

        self._assert_failed(
            session,
            "parent_channel_closed",
            exit_code=desktop_protocol.EXIT_PARENT_LOST,
        )

    def test_stop_signal_before_start_request_cancels_startup(self) -> None:
        stop_signal = desktop_protocol.StopSignal()
        stop_signal.request()
        session = _Session(self, stop_signal=stop_signal)

        self._assert_failed(session, "startup_cancelled")


class DesktopProtocolCliTest(unittest.TestCase):
    def _run_cli_error(self, argv: list[str]) -> str:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                serve.run_serve_cli(argv)
        self.assertEqual(ctx.exception.code, 2)
        return stderr.getvalue()

    def test_help_documents_desktop_protocol_flag(self) -> None:
        stdout = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "serve", "--help"]):
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit):
                    cli_main.main()

        output = " ".join(stdout.getvalue().split())
        self.assertIn("--desktop-protocol", output)
        self.assertIn("--desktop-start-timeout", output)
        # argparse may wrap the doc path at its hyphens; match a stable prefix.
        self.assertIn("see docs/reference/desktop", output)

    def test_desktop_protocol_rejects_conflicting_serve_options(self) -> None:
        message = self._run_cli_error(
            ["--desktop-protocol", "--port", "9000", "--project-root", "/x"]
        )

        self.assertIn("--port", message)
        self.assertIn("--project-root", message)

    def test_explicit_default_values_still_conflict(self) -> None:
        message = self._run_cli_error(
            ["--desktop-protocol", "--host", "127.0.0.1", "--port", "8765"]
        )

        self.assertIn("--host", message)
        self.assertIn("--port", message)

    def test_desktop_start_timeout_requires_desktop_protocol(self) -> None:
        message = self._run_cli_error(["--desktop-start-timeout", "5"])

        self.assertIn("requires --desktop-protocol", message)

    def test_desktop_start_timeout_is_bounded(self) -> None:
        message = self._run_cli_error(
            ["--desktop-protocol", "--desktop-start-timeout", "0"]
        )

        self.assertIn("must be between", message)

    def test_desktop_protocol_dispatches_with_timeout(self) -> None:
        with unittest.mock.patch.object(
            desktop_protocol, "run_desktop_protocol", return_value=0
        ) as run:
            exit_code = serve.run_serve_cli(
                ["--desktop-protocol", "--desktop-start-timeout", "2.5"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(run.call_args.kwargs["start_request_timeout"], 2.5)

    def test_desktop_server_factory_binds_loopback_os_assigned_port(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            server = serve._desktop_server_factory(pathlib.Path(temp_dir))
            try:
                host, port = server.server_address[:2]
            finally:
                server.server_close()

        self.assertEqual(host, "127.0.0.1")
        self.assertNotEqual(port, serve.DEFAULT_PORT)
        self.assertGreater(port, 0)


class FrameReaderTest(unittest.TestCase):
    def test_reader_splits_frames_skips_blank_lines_and_reports_eof(self) -> None:
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        reader = desktop_protocol.FrameReader(read_fd)
        reader.start()

        os.write(write_fd, b'{"a": 1}\r\n\n{"b"')
        os.write(write_fd, b": 2}\n")
        os.close(write_fd)

        items = [reader.items.get(timeout=_WAIT_SECONDS) for _ in range(3)]
        self.assertEqual(items[0], {"a": 1})
        self.assertEqual(items[1], {"b": 2})
        self.assertNotIsInstance(items[2], dict)
        with self.assertRaises(queue.Empty):
            reader.items.get(timeout=0.05)


if __name__ == "__main__":
    unittest.main()

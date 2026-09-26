"""Bounded real-process smoke tests for ``lrh serve --desktop-protocol``.

Every child is started from this checkout (``PYTHONPATH`` points at ``src``),
bound to an OS-assigned loopback port, and cleaned up through the handle the
test created. Every wait has an explicit deadline.

Run with ``scripts/smoke`` or::

    PYTHONPATH=src python -m unittest tests.smoke.desktop_protocol_smoke -v
"""

import http.client
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from typing import Any

from lrh import desktop_protocol, desktop_supervisor

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PROCESS_TIMEOUT_SECONDS = 30.0
# Parent-loss deadline: poll interval + server stop bound + process exit slack.
_PARENT_LOSS_DEADLINE_SECONDS = (
    desktop_protocol.PARENT_POLL_INTERVAL_SECONDS
    + desktop_protocol.SERVER_STOP_TIMEOUT_SECONDS
    + 2.0
)
_LISTENING_PATTERN = re.compile(rb"listening on http://127\.0\.0\.1:(\d+) ")

# Intermediate "parent" that owns the child's pipes, relays one start request
# in and one handshake line out, then idles until killed by the test.
_OWNING_PARENT = """
import subprocess, sys, time
child = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
child.stdin.write(sys.stdin.buffer.readline())
child.stdin.flush()
sys.stdout.buffer.write(child.stdout.readline())
sys.stdout.flush()
time.sleep(120)
"""

# Intermediate parent that lets the child inherit its own stdin, so the stdin
# write end stays open (held by the test) after this parent dies. Only the
# child's parent-process watchdog can notice the loss in this case.
_LEAKY_PARENT = """
import subprocess, sys, time
child = subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE)
sys.stdout.buffer.write(child.stdout.readline())
sys.stdout.flush()
time.sleep(120)
"""

# Runs desktop mode with a server factory that writes stray output to stdout
# through both sys.stdout and the raw descriptor 1.
_STRAY_OUTPUT_CHILD = """
import os, sys
from lrh import serve
original = serve._desktop_server_factory
def noisy_factory(project_root):
    print("stray print to sys.stdout")
    os.write(1, b"stray write to fd 1\\n")
    return original(project_root)
serve._desktop_server_factory = noisy_factory
sys.exit(serve.run_serve_cli(["--desktop-protocol"]))
"""


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    src = str(_REPO_ROOT / "src")
    env["PYTHONPATH"] = f"{src}{os.pathsep}{existing}" if existing else src
    return env


def _lrh_command() -> list[str]:
    return [sys.executable, "-m", "lrh.cli.main"]


def _encode(message: dict[str, Any]) -> bytes:
    return desktop_protocol.encode_message(message)


def _start_request(project_root: pathlib.Path, **overrides: Any) -> dict[str, Any]:
    message = desktop_supervisor.build_start_request("smoke-launch", project_root)
    message.update(overrides)
    return message


def _http_status(port: int, path: str = "/health") -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


def _readline(stream: Any, timeout: float = _PROCESS_TIMEOUT_SECONDS) -> bytes:
    """Read one line from a child pipe, failing instead of blocking forever."""

    lines: list[bytes] = []
    reader = threading.Thread(
        target=lambda: lines.append(stream.readline()), daemon=True
    )
    reader.start()
    reader.join(timeout)
    if reader.is_alive() or not lines:
        raise AssertionError(f"no line from child within {timeout:g} seconds")
    return lines[0]


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_pid_exit(pid: int, deadline_seconds: float) -> float | None:
    """Return seconds until ``pid`` vanished, or None if it outlived the bound."""

    started = time.monotonic()
    while time.monotonic() - started < deadline_seconds:
        if not _pid_exists(pid):
            return time.monotonic() - started
        time.sleep(0.05)
    return None


class DesktopProtocolSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.temp_root = pathlib.Path(temp_dir.name).resolve()
        self.workspace = self.temp_root / "workspace"
        (self.workspace / "project" / "focus").mkdir(parents=True)
        (self.workspace / "project" / "work_items").mkdir(parents=True)

    # -- helpers ---------------------------------------------------------

    def _popen(self, args: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(
            args,
            stdin=kwargs.pop("stdin", subprocess.PIPE),
            stdout=kwargs.pop("stdout", subprocess.PIPE),
            stderr=kwargs.pop("stderr", subprocess.PIPE),
            env=_child_env(),
            **kwargs,
        )
        self.addCleanup(self._reap, process)
        return process

    def _reap(self, process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.kill()
        try:
            process.communicate(timeout=_PROCESS_TIMEOUT_SECONDS)
        except (subprocess.TimeoutExpired, ValueError, OSError):
            pass

    def _kill_pid_on_cleanup(self, pid: int) -> None:
        def cleanup() -> None:
            if _pid_exists(pid):
                os.kill(pid, signal.SIGKILL)

        self.addCleanup(cleanup)

    def _owned(self, **kwargs: Any) -> desktop_supervisor.OwnedServer:
        owned = desktop_supervisor.OwnedServer(
            kwargs.pop("command_prefix", _lrh_command()),
            kwargs.pop("project_root", self.workspace),
            env=_child_env(),
            **kwargs,
        )

        def cleanup() -> None:
            if owned.process is not None and owned.process.poll() is None:
                owned.process.kill()
                owned.process.wait(_PROCESS_TIMEOUT_SECONDS)

        self.addCleanup(cleanup)
        return owned

    def _run_raw(
        self, stdin: bytes, extra_args: list[str] | None = None
    ) -> tuple[int, list[dict[str, Any]], str]:
        process = self._popen(
            [*_lrh_command(), "serve", "--desktop-protocol", *(extra_args or [])]
        )
        stdout, stderr = process.communicate(stdin, timeout=_PROCESS_TIMEOUT_SECONDS)
        messages = [json.loads(line) for line in stdout.decode().splitlines()]
        return process.returncode, messages, stderr.decode("utf-8", "replace")

    def _start_unrelated_server(self) -> tuple[subprocess.Popen[bytes], int]:
        process = self._popen(
            [
                *_lrh_command(),
                "serve",
                "--port",
                "0",
                "--project-root",
                str(self.workspace),
            ],
            stdin=subprocess.DEVNULL,
        )
        assert process.stdout is not None
        line = _readline(process.stdout)
        match = _LISTENING_PATTERN.search(line)
        self.assertIsNotNone(match, line)
        assert match is not None
        return process, int(match.group(1))

    # -- happy path and channel separation ---------------------------------

    def test_start_handshake_health_and_graceful_stop(self) -> None:
        owned = self._owned()

        handshake = owned.start()
        health = _http_status(handshake.port)
        pong = owned.ping()
        result = owned.stop()

        self.assertEqual(handshake.host, "127.0.0.1")
        self.assertEqual(handshake.workspace["project_root"], str(self.workspace))
        self.assertEqual(handshake.protocol_version, 1)
        self.assertEqual(health, 200)
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(result.exit_code, desktop_protocol.EXIT_STOPPED)
        self.assertEqual(result.escalation, "none")
        self.assertEqual(result.reason, "shutdown_requested")
        self.assertEqual(
            [event["type"] for event in result.events],
            ["ready", "pong", "stopping", "stopped"],
        )
        with self.assertRaises(OSError):
            _http_status(handshake.port)

    def test_stdout_carries_only_protocol_messages(self) -> None:
        shutdown = desktop_supervisor.build_control_message("shutdown", "smoke-launch")

        exit_code, messages, stderr = self._run_raw(
            _encode(_start_request(self.workspace)) + _encode(shutdown)
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [message["type"] for message in messages],
            ["ready", "stopping", "stopped"],
        )
        for message in messages:
            self.assertEqual(message["protocol"], "lrh-desktop-server")
            self.assertEqual(message["launch_id"], "smoke-launch")
        self.assertIn("lrh serve (desktop protocol): ready", stderr)

    def test_stray_output_is_diverted_to_stderr(self) -> None:
        process = self._popen([sys.executable, "-c", _STRAY_OUTPUT_CHILD])
        shutdown = desktop_supervisor.build_control_message("shutdown", "smoke-launch")

        stdout, stderr = process.communicate(
            _encode(_start_request(self.workspace)) + _encode(shutdown),
            timeout=_PROCESS_TIMEOUT_SECONDS,
        )

        self.assertEqual(process.returncode, 0, stderr)
        types = [json.loads(line)["type"] for line in stdout.decode().splitlines()]
        self.assertEqual(types, ["ready", "stopping", "stopped"])
        self.assertIn(b"stray print to sys.stdout", stderr)
        self.assertIn(b"stray write to fd 1", stderr)

    # -- startup failures --------------------------------------------------

    def test_malformed_start_request_fails(self) -> None:
        exit_code, messages, _ = self._run_raw(b"hello\n")

        self.assertEqual(exit_code, desktop_protocol.EXIT_STARTUP_FAILED)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["type"], "failed")
        self.assertEqual(messages[0]["error"]["code"], "malformed_request")

    def test_unsupported_protocol_version_fails_with_supported_list(self) -> None:
        exit_code, messages, _ = self._run_raw(
            _encode(_start_request(self.workspace, protocol_version=2))
        )

        self.assertEqual(exit_code, desktop_protocol.EXIT_STARTUP_FAILED)
        self.assertEqual(messages[0]["error"]["code"], "unsupported_protocol_version")
        self.assertEqual(messages[0]["error"]["details"]["supported_versions"], [1])
        self.assertEqual(messages[0]["launch_id"], "smoke-launch")

    def test_invalid_workspace_selection_fails(self) -> None:
        cases = {
            "invalid_workspace": self.temp_root / "missing",
            "workspace_not_lrh_project": self.temp_root,
        }
        for code, project_root in cases.items():
            with self.subTest(code=code):
                owned = self._owned(project_root=project_root)

                with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
                    owned.start()

                self.assertEqual(ctx.exception.code, "backend_failed")
                self.assertEqual(ctx.exception.details["error"]["code"], code)
                self.assertEqual(
                    ctx.exception.details["exit_code"],
                    desktop_protocol.EXIT_STARTUP_FAILED,
                )

    def test_conflicting_cli_options_are_a_usage_error(self) -> None:
        process = self._popen(
            # 8765 is the default port: explicit defaults still conflict.
            [*_lrh_command(), "serve", "--desktop-protocol", "--port", "8765"]
        )

        stdout, stderr = process.communicate(b"", timeout=_PROCESS_TIMEOUT_SECONDS)

        self.assertEqual(process.returncode, 2)
        self.assertEqual(stdout, b"")
        self.assertIn(b"--desktop-protocol", stderr)

    def test_child_start_request_timeout(self) -> None:
        process = self._popen(
            [
                *_lrh_command(),
                "serve",
                "--desktop-protocol",
                "--desktop-start-timeout",
                "0.5",
            ]
        )
        assert process.stdout is not None

        # Keep stdin open (no EOF) so only the deadline can end startup.
        line = _readline(process.stdout)
        exit_code = process.wait(timeout=_PROCESS_TIMEOUT_SECONDS)

        self.assertEqual(json.loads(line)["error"]["code"], "start_request_timeout")
        self.assertEqual(exit_code, desktop_protocol.EXIT_STARTUP_FAILED)

    def test_wrong_executable_exits_before_ready(self) -> None:
        owned = self._owned(command_prefix=[sys.executable, "-c", "pass"])

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            owned.start()

        self.assertEqual(ctx.exception.code, "exited_before_ready")

    def test_child_closing_stdout_but_alive_is_terminated(self) -> None:
        owned = self._owned(
            command_prefix=[
                sys.executable,
                "-c",
                "import os, time; os.close(1); time.sleep(60)",
            ],
            terminate_timeout=2.0,
        )

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            owned.start()

        self.assertEqual(ctx.exception.code, "exited_before_ready")
        assert owned.process is not None
        self.assertIsNotNone(owned.process.poll())

    def test_ready_for_another_launch_fails_fast(self) -> None:
        fake_ready = json.dumps(
            {
                "protocol": "lrh-desktop-server",
                "protocol_version": 1,
                "type": "ready",
                "launch_id": "someone-else",
            }
        )
        owned = self._owned(
            command_prefix=[
                sys.executable,
                "-c",
                f"import time; print({fake_ready!r}, flush=True); time.sleep(60)",
            ],
            startup_timeout=20.0,
        )

        started = time.monotonic()
        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            owned.start()

        self.assertEqual(ctx.exception.code, "launch_id_mismatch")
        self.assertLess(time.monotonic() - started, 10.0)
        assert owned.process is not None
        self.assertIsNotNone(owned.process.poll())

    def test_project_control_dir_workspace_is_verified(self) -> None:
        owned = self._owned(project_root=self.workspace / "project")

        handshake = owned.start()
        owned.stop()

        self.assertEqual(handshake.workspace["project_root"], str(self.workspace))
        self.assertEqual(
            handshake.workspace["project_dir"], str(self.workspace / "project")
        )

    def test_non_protocol_stdout_is_rejected_and_owned_child_terminated(self) -> None:
        owned = self._owned(
            command_prefix=[
                sys.executable,
                "-c",
                "import time; print('hello', flush=True); time.sleep(60)",
            ],
            terminate_timeout=5.0,
        )

        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            owned.start()

        self.assertEqual(ctx.exception.code, "malformed_handshake")
        assert owned.process is not None
        self.assertIsNotNone(owned.process.poll())

    def test_supervisor_startup_timeout_escalates_owned_child(self) -> None:
        owned = self._owned(
            command_prefix=[sys.executable, "-c", "import time; time.sleep(60)"],
            startup_timeout=1.0,
            terminate_timeout=5.0,
        )

        started = time.monotonic()
        with self.assertRaises(desktop_supervisor.SupervisorError) as ctx:
            owned.start()
        elapsed = time.monotonic() - started

        self.assertEqual(ctx.exception.code, "startup_timeout")
        assert owned.process is not None
        self.assertIsNotNone(owned.process.poll())
        self.assertLess(elapsed, 1.0 + 2 * 5.0)

    # -- parent-channel loss -------------------------------------------------

    def test_parent_channel_close_stops_child(self) -> None:
        owned = self._owned()
        handshake = owned.start()

        result = owned.close_channel()

        self.assertEqual(result.exit_code, desktop_protocol.EXIT_PARENT_LOST)
        self.assertEqual(result.reason, "parent_channel_closed")
        self.assertEqual(result.escalation, "none")
        with self.assertRaises(OSError):
            _http_status(handshake.port)

    @unittest.skipUnless(hasattr(signal, "SIGKILL"), "POSIX parent-kill check")
    def test_killed_parent_closes_channel_and_child_exits(self) -> None:
        parent = self._popen(
            [
                sys.executable,
                "-c",
                _OWNING_PARENT,
                *_lrh_command(),
                "serve",
                "--desktop-protocol",
            ]
        )
        assert parent.stdin is not None and parent.stdout is not None
        parent.stdin.write(_encode(_start_request(self.workspace)))
        parent.stdin.flush()
        ready = json.loads(_readline(parent.stdout))
        self._kill_pid_on_cleanup(ready["pid"])
        self.assertEqual(_http_status(ready["endpoint"]["port"]), 200)

        parent.kill()
        parent.wait(_PROCESS_TIMEOUT_SECONDS)
        exited_after = _wait_for_pid_exit(ready["pid"], _PARENT_LOSS_DEADLINE_SECONDS)

        self.assertIsNotNone(exited_after, "backend outlived its killed parent")
        with self.assertRaises(OSError):
            _http_status(ready["endpoint"]["port"])

    @unittest.skipUnless(os.name == "posix", "POSIX reparenting watchdog")
    def test_killed_parent_with_leaked_stdin_uses_parent_watchdog(self) -> None:
        parent = self._popen(
            [
                sys.executable,
                "-c",
                _LEAKY_PARENT,
                *_lrh_command(),
                "serve",
                "--desktop-protocol",
            ]
        )
        assert parent.stdin is not None and parent.stdout is not None
        parent.stdin.write(_encode(_start_request(self.workspace)))
        parent.stdin.flush()
        ready = json.loads(_readline(parent.stdout))
        self._kill_pid_on_cleanup(ready["pid"])

        parent.kill()
        parent.wait(_PROCESS_TIMEOUT_SECONDS)
        # This test still holds the stdin write end, so no EOF can arrive.
        exited_after = _wait_for_pid_exit(ready["pid"], _PARENT_LOSS_DEADLINE_SECONDS)

        self.assertIsNotNone(exited_after, "backend outlived its killed parent")
        self.assertFalse(parent.stdin.closed)

    @unittest.skipUnless(hasattr(signal, "SIGTERM"), "POSIX signal check")
    def test_sigterm_stops_gracefully(self) -> None:
        owned = self._owned()
        owned.start()
        assert owned.process is not None

        owned.process.send_signal(signal.SIGTERM)
        exit_code = owned.process.wait(_PROCESS_TIMEOUT_SECONDS)
        result = owned.close_channel()

        self.assertEqual(exit_code, desktop_protocol.EXIT_STOPPED)
        self.assertEqual(result.reason, "signal")

    # -- ownership, restart, and isolation -----------------------------------

    def test_restart_waits_for_previous_child_and_start_is_idempotent(self) -> None:
        supervisor = desktop_supervisor.DesktopSupervisor(
            _lrh_command(), self.workspace, env=_child_env()
        )
        self.addCleanup(supervisor.stop)

        first = supervisor.start()
        first_owned = supervisor.current
        again = supervisor.start()
        second = supervisor.restart()

        assert first_owned is not None and first_owned.process is not None
        self.assertEqual(first, again)
        self.assertEqual(first_owned.process.returncode, 0)
        self.assertNotEqual(first.launch_id, second.launch_id)
        self.assertEqual(_http_status(second.port), 200)
        stop_result = supervisor.stop()
        assert stop_result is not None
        self.assertEqual(stop_result.exit_code, 0)
        self.assertEqual(first_owned.stale_events, [])

    def test_start_after_child_crash_relaunches(self) -> None:
        supervisor = desktop_supervisor.DesktopSupervisor(
            _lrh_command(), self.workspace, env=_child_env()
        )
        self.addCleanup(supervisor.stop)
        first = supervisor.start()
        crashed = supervisor.current
        assert crashed is not None and crashed.process is not None

        crashed.process.kill()
        crashed.process.wait(_PROCESS_TIMEOUT_SECONDS)
        second = supervisor.start()

        self.assertNotEqual(first.launch_id, second.launch_id)
        self.assertIsNot(supervisor.current, crashed)
        self.assertEqual(_http_status(second.port), 200)

    def test_unrelated_server_is_untouched_by_owned_lifecycle(self) -> None:
        unrelated, unrelated_port = self._start_unrelated_server()

        owned = self._owned()
        handshake = owned.start()
        owned.stop()
        failing = self._owned(
            command_prefix=[sys.executable, "-c", "import time; time.sleep(60)"],
            startup_timeout=0.5,
        )
        with self.assertRaises(desktop_supervisor.SupervisorError):
            failing.start()
        crashing = self._owned()
        crashing.start()
        crashing.close_channel()

        self.assertNotEqual(handshake.port, unrelated_port)
        self.assertIsNone(unrelated.poll())
        self.assertEqual(_http_status(unrelated_port), 200)


if __name__ == "__main__":
    unittest.main()

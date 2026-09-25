"""Minimal reference supervisor for the LRH desktop server protocol.

This is the parent side of ``docs/reference/desktop-server-protocol.md``,
written in Python so the contract can be exercised without a Tauri build. The
desktop shell is expected to implement the same responsibilities natively:

- spawn one child from an explicitly configured executable and hold its
  stdin/stdout pipes privately;
- send one ``start`` request with a fresh launch ID and an explicit workspace;
- accept only a verified ``ready`` handshake as proof of a usable server;
- stop by ``shutdown`` message, escalating only against the owned child
  handle; never by process name or port.

Try it (see the protocol reference for more commands)::

    python -m lrh.desktop_supervisor --lrh-executable "$(command -v lrh)" \\
        --project-root .
"""

from __future__ import annotations

import argparse
import collections
import http.client
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lrh import desktop_protocol

DEFAULT_STARTUP_TIMEOUT_SECONDS = 20.0
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 10.0
DEFAULT_TERMINATE_TIMEOUT_SECONDS = 5.0
STDERR_TAIL_BYTES = 64 * 1024

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})

STATE_STOPPED = "stopped"
STATE_STARTING = "starting"
STATE_RUNNING = "running"
STATE_STOPPING = "stopping"
STATE_FAILED = "failed"


class SupervisorError(Exception):
    """A supervisor-side failure with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


@dataclass(frozen=True)
class Handshake:
    """A verified ``ready`` handshake."""

    launch_id: str
    protocol_version: int
    backend: dict[str, Any]
    pid: int
    workspace: dict[str, Any]
    host: str
    port: int
    url: str


@dataclass(frozen=True)
class StopResult:
    """How an owned child ended."""

    exit_code: int | None
    escalation: str
    reason: str | None
    events: list[dict[str, Any]] = field(default_factory=list)


def new_launch_id() -> str:
    """Return a fresh launch ID; it correlates messages, it is not a secret."""

    return uuid.uuid4().hex


def build_start_request(launch_id: str, project_root: Path) -> dict[str, Any]:
    return {
        "protocol": desktop_protocol.PROTOCOL_NAME,
        "protocol_version": desktop_protocol.PROTOCOL_VERSION,
        "type": "start",
        "launch_id": launch_id,
        "workspace": {"project_root": str(project_root)},
    }


def build_control_message(
    message_type: str, launch_id: str, request_id: str | None = None
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "protocol": desktop_protocol.PROTOCOL_NAME,
        "protocol_version": desktop_protocol.PROTOCOL_VERSION,
        "type": message_type,
        "launch_id": launch_id,
    }
    if request_id is not None:
        message["request_id"] = request_id
    return message


def verify_ready(
    message: dict[str, Any], launch_id: str, sent_project_root: Path
) -> Handshake:
    """Accept a ``ready`` message only if every identity check passes.

    ``sent_project_root`` is exactly the ``workspace.project_root`` this
    supervisor put in its ``start`` request. The backend must echo it, and its
    canonical form must be the reported repository root or control directory.
    """

    if message.get("protocol") != desktop_protocol.PROTOCOL_NAME:
        raise SupervisorError("incompatible_backend", "unexpected protocol name")
    version = message.get("protocol_version")
    if version not in desktop_protocol.SUPPORTED_PROTOCOL_VERSIONS:
        raise SupervisorError(
            "incompatible_backend",
            f"unsupported protocol_version {version!r}",
            {"backend": message.get("backend")},
        )
    if message.get("launch_id") != launch_id:
        raise SupervisorError("launch_id_mismatch", "ready is for another launch")
    workspace = message.get("workspace")
    if not isinstance(workspace, dict):
        raise SupervisorError("malformed_handshake", "ready lacks workspace")
    if workspace.get("requested_project_root") != str(sent_project_root):
        raise SupervisorError(
            "workspace_mismatch",
            "backend did not echo the requested workspace",
            {
                "expected": str(sent_project_root),
                "actual": workspace.get("requested_project_root"),
            },
        )
    expected = str(sent_project_root.resolve())
    if expected not in (workspace.get("project_root"), workspace.get("project_dir")):
        raise SupervisorError(
            "workspace_mismatch",
            "backend reports a different effective workspace",
            {"expected": expected, "actual": workspace.get("project_root")},
        )
    endpoint = message.get("endpoint")
    if not isinstance(endpoint, dict):
        raise SupervisorError("malformed_handshake", "ready lacks endpoint")
    host = endpoint.get("host")
    port = endpoint.get("port")
    if host not in LOOPBACK_HOSTS:
        raise SupervisorError("non_loopback_endpoint", f"endpoint host {host!r}")
    if not isinstance(port, int) or isinstance(port, bool) or not 0 < port < 65536:
        raise SupervisorError("malformed_handshake", f"invalid port {port!r}")
    pid = message.get("pid")
    backend = message.get("backend")
    url_host = f"[{host}]" if ":" in host else host
    return Handshake(
        launch_id=launch_id,
        protocol_version=version,
        backend=backend if isinstance(backend, dict) else {},
        pid=pid if isinstance(pid, int) else -1,
        workspace=workspace,
        host=host,
        port=port,
        url=f"http://{url_host}:{port}/",
    )


class _Eof:
    pass


_EOF = _Eof()


class OwnedServer:
    """One owned child launch. Create a new instance for each launch."""

    def __init__(
        self,
        command_prefix: Sequence[str],
        project_root: Path,
        *,
        startup_timeout: float = DEFAULT_STARTUP_TIMEOUT_SECONDS,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
        terminate_timeout: float = DEFAULT_TERMINATE_TIMEOUT_SECONDS,
        extra_args: Sequence[str] = (),
        env: dict[str, str] | None = None,
    ) -> None:
        self.command = [*command_prefix, "serve", "--desktop-protocol", *extra_args]
        self.project_root = project_root.resolve()
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.terminate_timeout = terminate_timeout
        self.env = env
        self.launch_id = new_launch_id()
        self.state = STATE_STOPPED
        self.handshake: Handshake | None = None
        self.events: list[dict[str, Any]] = []
        self.stale_events: list[dict[str, Any]] = []
        self.process: subprocess.Popen[bytes] | None = None
        self._messages: queue.Queue[object] = queue.Queue()
        self._stderr_tail: collections.deque[bytes] = collections.deque()
        self._stderr_size = 0
        self._threads: list[threading.Thread] = []

    # -- lifecycle -------------------------------------------------------

    def start(self) -> Handshake:
        """Spawn the child and wait (bounded) for a verified handshake."""

        if self.state != STATE_STOPPED or self.process is not None:
            raise SupervisorError("already_launched", "create a new OwnedServer")
        self.state = STATE_STARTING
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                env=self.env,
            )
        except OSError as err:
            self.state = STATE_FAILED
            raise SupervisorError(
                "spawn_failed", f"could not start {self.command[0]!r}: {err}"
            ) from err
        self._start_thread(self._read_stdout, "stdout")
        self._start_thread(self._drain_stderr, "stderr")
        self._send(build_start_request(self.launch_id, self.project_root))
        try:
            return self._await_handshake()
        except SupervisorError:
            # A failed start never leaves a running child behind.
            self._close_stdin()
            if self._wait_exit(0.0) is None:
                self._escalate()
            self._release()
            self.state = STATE_FAILED
            raise

    def _await_handshake(self) -> Handshake:
        deadline = time.monotonic() + self.startup_timeout
        while True:
            item = self._next_item(deadline)
            if item is None:
                raise SupervisorError(
                    "startup_timeout",
                    f"no handshake within {self.startup_timeout:g} seconds",
                    {"stderr_tail": self.stderr_tail()},
                )
            if item is _EOF:
                exit_code = self._wait_exit(self.terminate_timeout)
                raise SupervisorError(
                    "exited_before_ready",
                    "backend exited without a handshake",
                    {"exit_code": exit_code, "stderr_tail": self.stderr_tail()},
                )
            if isinstance(item, SupervisorError):
                raise item
            assert isinstance(item, dict)
            if item.get("launch_id") not in (self.launch_id, None):
                # This handle's own child answered for another launch: that is
                # a failed launch, not a stale event to wait past.
                raise SupervisorError(
                    "launch_id_mismatch", "handshake is for another launch"
                )
            message_type = item.get("type")
            if message_type == "failed":
                exit_code = self._wait_exit(self.terminate_timeout)
                raise SupervisorError(
                    "backend_failed",
                    "backend reported a startup failure",
                    {"error": item.get("error"), "exit_code": exit_code},
                )
            if message_type != "ready":
                raise SupervisorError(
                    "malformed_handshake",
                    f"expected ready or failed, got {message_type!r}",
                )
            self.handshake = verify_ready(item, self.launch_id, self.project_root)
            self.state = STATE_RUNNING
            return self.handshake

    def ping(self, timeout: float = 5.0) -> dict[str, Any]:
        """Round-trip a ``ping`` over the private channel."""

        request_id = new_launch_id()
        self._send(build_control_message("ping", self.launch_id, request_id))
        deadline = time.monotonic() + timeout
        while True:
            item = self._next_item(deadline)
            if not isinstance(item, dict):
                raise SupervisorError("ping_failed", "no pong received")
            if item.get("type") == "pong" and item.get("request_id") == request_id:
                return item

    def stop(self) -> StopResult:
        """Graceful stop, then terminate/kill of the owned child only."""

        return self._finish(send_shutdown=True)

    def close_channel(self) -> StopResult:
        """Close stdin without a message, as a crashed parent would."""

        return self._finish(send_shutdown=False)

    def stderr_tail(self) -> str:
        return b"".join(self._stderr_tail).decode("utf-8", "replace")

    # -- internals -------------------------------------------------------

    def _finish(self, *, send_shutdown: bool) -> StopResult:
        if self.process is None:
            return StopResult(None, "none", None)
        self.state = STATE_STOPPING
        if send_shutdown:
            self._send(build_control_message("shutdown", self.launch_id))
        self._close_stdin()
        escalation = "none"
        exit_code = self._wait_exit(self.shutdown_timeout)
        if exit_code is None:
            escalation = self._escalate()
            exit_code = self.process.returncode
        self._release()
        reason = None
        for event in self.events:
            if event.get("type") == "stopped":
                reason = event.get("reason")
        self.state = STATE_STOPPED
        return StopResult(exit_code, escalation, reason, list(self.events))

    def _release(self) -> None:
        """After exit: collect remaining output and close pipe handles."""

        assert self.process is not None
        for thread in self._threads:
            thread.join(self.terminate_timeout)
        self._drain_queue()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass

    def _escalate(self) -> str:
        """Terminate, then kill, the owned child handle. Never by name/port."""

        assert self.process is not None
        self.process.terminate()
        if self._wait_exit(self.terminate_timeout) is not None:
            return "terminate"
        self.process.kill()
        self._wait_exit(self.terminate_timeout)
        return "kill"

    def _wait_exit(self, timeout: float) -> int | None:
        assert self.process is not None
        try:
            return self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None

    def _send(self, message: dict[str, Any]) -> bool:
        assert self.process is not None and self.process.stdin is not None
        try:
            self.process.stdin.write(desktop_protocol.encode_message(message))
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            return False
        return True

    def _close_stdin(self) -> None:
        assert self.process is not None
        if self.process.stdin is not None and not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except OSError:
                pass

    def _next_item(self, deadline: float) -> object | None:
        """Return the next item; after ready, skip stale-launch messages."""

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                item = self._messages.get(timeout=remaining)
            except queue.Empty:
                return None
            if isinstance(item, dict):
                stale = item.get("launch_id") not in (self.launch_id, None)
                if stale and self.state != STATE_STARTING:
                    self.stale_events.append(item)
                    continue
                if not stale:
                    self.events.append(item)
            return item

    def _drain_queue(self) -> None:
        while True:
            try:
                item = self._messages.get_nowait()
            except queue.Empty:
                return
            if isinstance(item, dict):
                if item.get("launch_id") not in (self.launch_id, None):
                    self.stale_events.append(item)
                else:
                    self.events.append(item)

    def _start_thread(self, target: Any, name: str) -> None:
        thread = threading.Thread(
            target=target, name=f"lrh-supervisor-{name}", daemon=True
        )
        thread.start()
        self._threads.append(thread)

    def _read_stdout(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        stream = self.process.stdout
        limit = desktop_protocol.MAX_MESSAGE_BYTES
        while True:
            line = stream.readline(limit + 1)
            if not line:
                self._messages.put(_EOF)
                return
            if not line.endswith(b"\n") and len(line) > limit:
                self._messages.put(
                    SupervisorError("malformed_handshake", "oversized message")
                )
                return
            frame = line.rstrip(b"\r\n")
            if not frame.strip():
                continue
            try:
                self._messages.put(desktop_protocol.decode_message(frame))
            except desktop_protocol.ProtocolError as err:
                self._messages.put(
                    SupervisorError(
                        "malformed_handshake",
                        f"backend wrote a non-protocol line: {err.message}",
                    )
                )

    def _drain_stderr(self) -> None:
        assert self.process is not None and self.process.stderr is not None
        stream = self.process.stderr
        while True:
            chunk = stream.read1(8192)
            if not chunk:
                return
            self._stderr_tail.append(chunk)
            self._stderr_size += len(chunk)
            while self._stderr_size > STDERR_TAIL_BYTES and len(self._stderr_tail) > 1:
                self._stderr_size -= len(self._stderr_tail.popleft())


class DesktopSupervisor:
    """Serialize start/stop/restart for at most one owned child."""

    def __init__(
        self,
        command_prefix: Sequence[str],
        project_root: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> None:
        self.command_prefix = list(command_prefix)
        self.project_root = project_root
        self.env = env
        self._lock = threading.Lock()
        self.current: OwnedServer | None = None

    def start(self) -> Handshake:
        """Idempotent: return the running handshake instead of relaunching."""

        with self._lock:
            if self.current is not None and self.current.state == STATE_RUNNING:
                assert self.current.handshake is not None
                return self.current.handshake
            self._stop_locked()
            self.current = OwnedServer(
                self.command_prefix, self.project_root, env=self.env
            )
            return self.current.start()

    def stop(self) -> StopResult | None:
        with self._lock:
            return self._stop_locked()

    def restart(self) -> Handshake:
        """Wait for the previous owned child to exit before a new launch."""

        with self._lock:
            self._stop_locked()
            self.current = OwnedServer(
                self.command_prefix, self.project_root, env=self.env
            )
            return self.current.start()

    def _stop_locked(self) -> StopResult | None:
        if self.current is None or self.current.process is None:
            return None
        result = self.current.stop()
        self.current = None
        return result


def fetch_health(handshake: Handshake, timeout: float = 5.0) -> int:
    """GET /health from the verified endpoint; return the HTTP status."""

    connection = http.client.HTTPConnection(
        handshake.host, handshake.port, timeout=timeout
    )
    try:
        connection.request("GET", "/health")
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


def _emit(event: str, **fields: Any) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def build_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Reference supervisor for the LRH desktop server protocol: start an "
            "owned lrh serve child, verify its handshake, check /health, stop it."
        ),
    )
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument(
        "--lrh-executable",
        help="explicit path to the lrh executable to supervise",
    )
    command.add_argument(
        "--use-current-python",
        action="store_true",
        help="supervise '<this python> -m lrh.cli.main' instead",
    )
    parser.add_argument(
        "--project-root", required=True, help="explicit LRH workspace to serve"
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="keep the server running this long before stopping (default: 0)",
    )
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=DEFAULT_STARTUP_TIMEOUT_SECONDS,
        metavar="SECONDS",
    )
    return parser


def main(argv: list[str] | None = None, prog: str = "lrh.desktop_supervisor") -> int:
    args = build_parser(prog).parse_args(argv)
    if args.use_current_python:
        command_prefix = [sys.executable, "-m", "lrh.cli.main"]
    else:
        command_prefix = [os.fspath(args.lrh_executable)]
    owned = OwnedServer(
        command_prefix,
        Path(args.project_root),
        startup_timeout=args.startup_timeout,
    )
    try:
        handshake = owned.start()
    except SupervisorError as err:
        _emit("failed", error=err.to_dict())
        return 1
    try:
        _emit(
            "ready",
            launch_id=handshake.launch_id,
            url=handshake.url,
            pid=handshake.pid,
            backend=handshake.backend,
            workspace=handshake.workspace,
        )
        _emit("health", status=fetch_health(handshake))
        _emit("ping", ok=owned.ping().get("type") == "pong")
        if args.hold > 0:
            _emit("holding", seconds=args.hold, url=handshake.url)
            time.sleep(args.hold)
    except KeyboardInterrupt:
        pass
    finally:
        result = owned.stop()
        _emit(
            "stopped",
            exit_code=result.exit_code,
            escalation=result.escalation,
            reason=result.reason,
        )
    return 0 if result.exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Versioned desktop-supervisor protocol for ``lrh serve --desktop-protocol``.

This module owns the child side of the LRH desktop server protocol: message
framing, startup-request validation, strict workspace identity resolution, and
the owned-server lifecycle (ready/failed handshake, graceful stop, and exit on
parent-channel loss). The normative contract is documented in
``docs/reference/desktop-server-protocol.md``.

Transport summary: the supervising parent owns the child's stdin and stdout
pipes. Each machine message is one UTF-8 JSON object terminated by ``\\n``
(NDJSON). Human diagnostics go to stderr only. Closing stdin (for example, when
the parent process dies) is the parent-loss signal.

The HTTP server itself is injected through ``ServerFactory`` so this module
stays independent of ``lrh.serve`` and can be unit-tested in-process.
"""

from __future__ import annotations

import http.client
import json
import os
import platform
import queue
import re
import signal
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from lrh import version as lrh_version
from lrh.control import loader as control_loader

PROTOCOL_NAME = "lrh-desktop-server"
PROTOCOL_VERSION = 1
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION,)

# One framed message (including its trailing newline) may not exceed this.
MAX_MESSAGE_BYTES = 64 * 1024

LOOPBACK_HOST = "127.0.0.1"

# Child-side deadlines, in seconds. Parent-side deadlines are documented in the
# protocol reference and implemented by ``lrh.desktop_supervisor``.
DEFAULT_START_REQUEST_TIMEOUT_SECONDS = 10.0
MIN_START_REQUEST_TIMEOUT_SECONDS = 0.1
MAX_START_REQUEST_TIMEOUT_SECONDS = 120.0
SELF_CHECK_TIMEOUT_SECONDS = 5.0
SERVER_STOP_TIMEOUT_SECONDS = 5.0
PARENT_POLL_INTERVAL_SECONDS = 0.25

# Process exit codes in desktop-protocol mode. Exit code 2 remains argparse's
# CLI usage error, reported on stderr without any machine message.
EXIT_STOPPED = 0
EXIT_INTERNAL_ERROR = 1
EXIT_STARTUP_FAILED = 3
EXIT_PARENT_LOST = 4
EXIT_PROTOCOL_ERROR = 5

# Stop reasons reported in ``stopping``/``stopped`` messages.
REASON_SHUTDOWN_REQUESTED = "shutdown_requested"
REASON_PARENT_CHANNEL_CLOSED = "parent_channel_closed"
REASON_PARENT_PROCESS_EXITED = "parent_process_exited"
REASON_SIGNAL = "signal"
REASON_PROTOCOL_ERROR = "protocol_error"
REASON_INTERNAL_ERROR = "internal_error"

_EXIT_CODE_BY_REASON = {
    REASON_SHUTDOWN_REQUESTED: EXIT_STOPPED,
    REASON_SIGNAL: EXIT_STOPPED,
    REASON_PARENT_CHANNEL_CLOSED: EXIT_PARENT_LOST,
    REASON_PARENT_PROCESS_EXITED: EXIT_PARENT_LOST,
    REASON_PROTOCOL_ERROR: EXIT_PROTOCOL_ERROR,
    REASON_INTERNAL_ERROR: EXIT_INTERNAL_ERROR,
}

_LAUNCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REQUEST_ID_MAX_LENGTH = 128
# Values copied from untrusted input into replies are truncated to this many
# characters so no reply can approach MAX_MESSAGE_BYTES.
_ECHO_MAX_CHARS = 256


class ProtocolError(Exception):
    """A protocol-level failure with a stable machine-readable code."""

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


class ServerHandle(Protocol):
    """The subset of ``socketserver.BaseServer`` the lifecycle relies on."""

    server_address: Any

    def serve_forever(self, poll_interval: float = 0.5) -> None: ...

    def shutdown(self) -> None: ...

    def server_close(self) -> None: ...


ServerFactory = Callable[[Path], ServerHandle]


@dataclass(frozen=True)
class WorkspaceIdentity:
    """Effective workspace identity resolved without any fallback."""

    requested_project_root: str
    project_root: Path
    project_dir: Path

    def to_message(self) -> dict[str, str]:
        return {
            "requested_project_root": self.requested_project_root,
            "project_root": str(self.project_root),
            "project_dir": str(self.project_dir),
            "name": self.project_root.name,
        }


@dataclass(frozen=True)
class StartRequest:
    """A validated ``start`` request from the supervising parent."""

    launch_id: str
    protocol_version: int
    requested_project_root: str


@dataclass(frozen=True)
class SessionResult:
    """Outcome of one desktop-protocol session."""

    exit_code: int
    reason: str
    launch_id: str | None


def encode_message(message: dict[str, Any]) -> bytes:
    """Serialize one machine message as a single NDJSON frame."""

    # ensure_ascii=False keeps non-ASCII paths at their UTF-8 byte length
    # instead of inflating them with \\uXXXX escapes.
    body = json.dumps(
        message, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    frame = body.encode("utf-8") + b"\n"
    if len(frame) > MAX_MESSAGE_BYTES:
        raise ProtocolError(
            "message_too_large",
            f"outgoing message exceeds {MAX_MESSAGE_BYTES} bytes",
        )
    return frame


def decode_message(frame: bytes) -> dict[str, Any]:
    """Parse one NDJSON frame (without its newline) into a JSON object."""

    if len(frame) + 1 > MAX_MESSAGE_BYTES:
        raise ProtocolError(
            "message_too_large",
            f"message exceeds {MAX_MESSAGE_BYTES} bytes",
        )
    try:
        text = frame.decode("utf-8")
    except UnicodeDecodeError as err:
        raise ProtocolError("malformed_message", "message is not UTF-8") from err
    try:
        value = json.loads(text)
    except json.JSONDecodeError as err:
        raise ProtocolError(
            "malformed_message", f"message is not valid JSON: {err.msg}"
        ) from err
    if not isinstance(value, dict):
        raise ProtocolError("malformed_message", "message must be a JSON object")
    return value


def _echo(value: object) -> str:
    """Return a bounded ``repr`` of an untrusted value for an error reply."""

    text = repr(value)
    if len(text) > _ECHO_MAX_CHARS:
        return text[:_ECHO_MAX_CHARS] + "...(truncated)"
    return text


def _echo_path(path: str) -> str:
    """Return an untrusted path, truncated for inclusion in an error reply."""

    if len(path) > _ECHO_MAX_CHARS * 4:
        return path[: _ECHO_MAX_CHARS * 4] + "...(truncated)"
    return path


def extract_launch_id(message: dict[str, Any]) -> str | None:
    """Return the message's launch ID when it is well formed, else None."""

    launch_id = message.get("launch_id")
    if isinstance(launch_id, str) and _LAUNCH_ID_PATTERN.fullmatch(launch_id):
        return launch_id
    return None


def parse_start_request(message: dict[str, Any]) -> StartRequest:
    """Validate a decoded ``start`` request.

    Raises:
        ProtocolError: with a stable code describing the first problem found.
    """

    if message.get("protocol") != PROTOCOL_NAME:
        raise ProtocolError(
            "unsupported_protocol",
            f"expected protocol {PROTOCOL_NAME!r}",
            {"protocol": PROTOCOL_NAME},
        )
    if message.get("type") != "start":
        raise ProtocolError(
            "malformed_request",
            "the first message must have type 'start'",
        )
    version = message.get("protocol_version")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version not in SUPPORTED_PROTOCOL_VERSIONS
    ):
        raise ProtocolError(
            "unsupported_protocol_version",
            f"protocol_version {_echo(version)} is not supported",
            {"supported_versions": list(SUPPORTED_PROTOCOL_VERSIONS)},
        )
    launch_id = extract_launch_id(message)
    if launch_id is None:
        raise ProtocolError(
            "invalid_launch_id",
            "launch_id must be 1-128 characters from [A-Za-z0-9._:-]",
        )
    workspace = message.get("workspace")
    if not isinstance(workspace, dict):
        raise ProtocolError(
            "malformed_request", "workspace must be an object with project_root"
        )
    project_root = workspace.get("project_root")
    if not isinstance(project_root, str) or not project_root:
        raise ProtocolError(
            "malformed_request", "workspace.project_root must be a non-empty string"
        )
    return StartRequest(
        launch_id=launch_id,
        protocol_version=version,
        requested_project_root=project_root,
    )


def resolve_workspace(requested_project_root: str) -> WorkspaceIdentity:
    """Resolve the explicitly requested workspace, refusing any fallback.

    The path must be absolute and name either an LRH repository root (one that
    contains ``project/``) or an LRH ``project/`` control directory itself. No
    parent-directory search, current-directory default, or Meta registry lookup
    is performed.
    """

    requested = Path(requested_project_root)
    details = {"requested_project_root": _echo_path(requested_project_root)}
    if not requested.is_absolute():
        raise ProtocolError(
            "invalid_workspace",
            "workspace.project_root must be an absolute path",
            details,
        )
    if not requested.exists():
        raise ProtocolError(
            "invalid_workspace", "workspace.project_root does not exist", details
        )
    if not requested.is_dir():
        raise ProtocolError(
            "invalid_workspace", "workspace.project_root is not a directory", details
        )
    resolved = requested.resolve()
    try:
        project_dir = control_loader.find_project_dir(resolved)
    except FileNotFoundError as err:
        raise ProtocolError(
            "workspace_not_lrh_project",
            "workspace.project_root does not contain an LRH project control "
            "directory (expected project/focus and project/work_items)",
            details,
        ) from err
    # Mirror ServeConfig.resolved_project_root so Serve uses this exact root.
    project_root = project_dir.parent if project_dir.name == "project" else project_dir
    return WorkspaceIdentity(
        requested_project_root=requested_project_root,
        project_root=project_root,
        project_dir=project_dir,
    )


def backend_identity() -> dict[str, Any]:
    """Return backend version information reported in the handshake."""

    return {
        "name": lrh_version.DISTRIBUTION_NAME,
        "version": lrh_version.get_installed_version(),
        "python": platform.python_version(),
    }


def _envelope(message_type: str, launch_id: str | None) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "type": message_type,
        "launch_id": launch_id,
    }


def ready_message(
    launch_id: str,
    workspace: WorkspaceIdentity,
    host: str,
    port: int,
) -> dict[str, Any]:
    """Build the ``ready`` handshake emitted after bind and self-check."""

    message = _envelope("ready", launch_id)
    message.update(
        {
            "backend": backend_identity(),
            "pid": os.getpid(),
            "workspace": workspace.to_message(),
            "endpoint": {
                "scheme": "http",
                "host": host,
                "port": port,
                "url": f"http://{host}:{port}/",
            },
            "read_only": True,
            "execution_authority": False,
        }
    )
    return message


def failed_message(launch_id: str | None, error: ProtocolError) -> dict[str, Any]:
    """Build the ``failed`` startup response."""

    message = _envelope("failed", launch_id)
    message["backend"] = backend_identity()
    message["error"] = {
        "code": error.code,
        "message": error.message,
        "details": error.details,
    }
    return message


def error_message(
    launch_id: str | None,
    error: ProtocolError,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build a non-fatal (or pre-exit) ``error`` event after startup."""

    message = _envelope("error", launch_id)
    message["error"] = {
        "code": error.code,
        "message": error.message,
        "details": error.details,
    }
    if request_id is not None:
        message["request_id"] = request_id
    return message


def lifecycle_message(message_type: str, launch_id: str, reason: str) -> dict[str, Any]:
    """Build a ``stopping`` or ``stopped`` lifecycle event."""

    message = _envelope(message_type, launch_id)
    message["reason"] = reason
    return message


class _Sentinel:
    """Named sentinel for reader and startup-wait outcomes."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<{self.name}>"


# Queued by the reader when the parent channel reaches EOF.
_EOF = _Sentinel("eof")
# Returned by the startup wait when a stop signal or parent exit arrives first.
_CANCELLED = _Sentinel("cancelled")


class FrameReader:
    """Read NDJSON frames from a raw file descriptor on a daemon thread.

    Reads use ``os.read`` on the raw descriptor rather than a buffered Python
    stream so a reader blocked at interpreter shutdown holds no stream lock.
    Items placed on ``items`` are decoded message dicts, ``ProtocolError``
    instances for bad frames, or the EOF sentinel.
    """

    def __init__(self, fd: int) -> None:
        self._fd = fd
        self.items: queue.Queue[object] = queue.Queue()
        self._thread = threading.Thread(
            target=self._run, name="lrh-desktop-reader", daemon=True
        )

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        buffer = b""
        while True:
            try:
                chunk = os.read(self._fd, 8192)
            except OSError:
                chunk = b""
            if not chunk:
                self.items.put(_EOF)
                return
            buffer += chunk
            while b"\n" in buffer:
                frame, buffer = buffer.split(b"\n", 1)
                frame = frame.rstrip(b"\r")
                if not frame.strip():
                    continue
                try:
                    self.items.put(decode_message(frame))
                except ProtocolError as err:
                    self.items.put(err)
                    if err.code == "message_too_large":
                        return
            if len(buffer) >= MAX_MESSAGE_BYTES:
                self.items.put(
                    ProtocolError(
                        "message_too_large",
                        f"message exceeds {MAX_MESSAGE_BYTES} bytes",
                    )
                )
                return


class MessageWriter:
    """Write NDJSON frames to a raw file descriptor, serialized by a lock."""

    def __init__(self, fd: int) -> None:
        self._fd = fd
        self._lock = threading.Lock()
        self.broken = False

    def send(self, message: dict[str, Any]) -> bool:
        """Write one message; return False when the parent channel is gone."""

        frame = encode_message(message)
        with self._lock:
            if self.broken:
                return False
            view = memoryview(frame)
            try:
                while view:
                    written = os.write(self._fd, view)
                    view = view[written:]
            except OSError:
                self.broken = True
                return False
        return True


class StopSignal:
    """Thread-safe flag a signal handler can set to request graceful stop."""

    def __init__(self) -> None:
        self.requested = False

    def request(self) -> None:
        self.requested = True


def _log(stderr: Any, text: str) -> None:
    try:
        stderr.write(f"lrh serve (desktop protocol): {text}\n")
        stderr.flush()
    except (OSError, ValueError):
        pass


def _self_check(host: str, port: int, timeout: float) -> None:
    """Confirm the bound server answers its read-only status route."""

    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request("GET", "/api/status")
        response = connection.getresponse()
        body = response.read()
    except (OSError, http.client.HTTPException) as err:
        raise ProtocolError(
            "startup_self_check_failed",
            f"server did not answer its status route: {err}",
        ) from err
    finally:
        connection.close()
    if response.status != 200:
        raise ProtocolError(
            "startup_self_check_failed",
            f"status route returned HTTP {response.status}",
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ProtocolError(
            "startup_self_check_failed", "status route returned invalid JSON"
        ) from err
    if payload.get("service") != "lrh serve" or payload.get("port") != port:
        raise ProtocolError(
            "startup_self_check_failed",
            "status route did not identify this lrh serve instance",
        )


def _stop_server(
    server: ServerHandle, thread: threading.Thread, timeout: float
) -> None:
    """Stop the HTTP server, bounded by ``timeout`` seconds in total."""

    deadline = time.monotonic() + timeout
    stopper = threading.Thread(
        target=server.shutdown, name="lrh-desktop-stop", daemon=True
    )
    stopper.start()
    stopper.join(timeout)
    thread.join(max(0.0, deadline - time.monotonic()))
    try:
        server.server_close()
    except OSError:
        pass


def run_session(
    input_fd: int,
    writer: MessageWriter,
    server_factory: ServerFactory,
    *,
    stderr: Any = None,
    start_request_timeout: float = DEFAULT_START_REQUEST_TIMEOUT_SECONDS,
    self_check_timeout: float = SELF_CHECK_TIMEOUT_SECONDS,
    stop_timeout: float = SERVER_STOP_TIMEOUT_SECONDS,
    poll_interval: float = PARENT_POLL_INTERVAL_SECONDS,
    parent_alive: Callable[[], bool] | None = None,
    stop_signal: StopSignal | None = None,
) -> SessionResult:
    """Run one owned-server session over an already-established channel.

    Args:
        input_fd: raw descriptor carrying parent-to-child messages.
        writer: writer for child-to-parent messages.
        server_factory: builds (but does not start) a loopback HTTP server
            for a validated project root with an OS-assigned port.
        stderr: text stream for human diagnostics (default ``sys.stderr``).
        start_request_timeout: seconds to wait for the ``start`` request.
        self_check_timeout: seconds allowed for the readiness self-check.
        stop_timeout: seconds allowed for the HTTP server to stop.
        poll_interval: seconds between parent-liveness/stop-signal checks.
        parent_alive: optional probe; returning False triggers shutdown.
        stop_signal: optional flag set by a signal handler.

    Returns:
        The session outcome, including the process exit code to use.
    """

    log_stream = stderr if stderr is not None else sys.stderr
    reader = FrameReader(input_fd)
    reader.start()

    def fail(
        launch_id: str | None, error: ProtocolError, exit_code: int
    ) -> SessionResult:
        _log(log_stream, f"startup failed: {error.code}: {error.message}")
        writer.send(failed_message(launch_id, error))
        return SessionResult(exit_code, error.code, launch_id)

    item = _wait_for_start_item(
        reader,
        start_request_timeout,
        poll_interval=poll_interval,
        parent_alive=parent_alive,
        stop_signal=stop_signal,
    )
    if item is None:
        return fail(
            None,
            ProtocolError(
                "start_request_timeout",
                f"no start request within {start_request_timeout:g} seconds",
            ),
            EXIT_STARTUP_FAILED,
        )
    if item is _CANCELLED:
        return fail(
            None,
            ProtocolError(
                "startup_cancelled",
                "stop signal or parent exit before a start request",
            ),
            EXIT_STARTUP_FAILED,
        )
    if item is _EOF:
        return fail(
            None,
            ProtocolError(
                "parent_channel_closed", "input closed before a start request"
            ),
            EXIT_PARENT_LOST,
        )
    if isinstance(item, ProtocolError):
        code = item.code if item.code == "message_too_large" else "malformed_request"
        return fail(None, ProtocolError(code, item.message), EXIT_STARTUP_FAILED)

    assert isinstance(item, dict)
    correlated_launch_id = extract_launch_id(item)
    try:
        request = parse_start_request(item)
        workspace = resolve_workspace(request.requested_project_root)
    except ProtocolError as err:
        return fail(correlated_launch_id, err, EXIT_STARTUP_FAILED)

    launch_id = request.launch_id
    try:
        server = server_factory(workspace.project_root)
    except (OSError, ValueError) as err:
        return fail(
            launch_id,
            ProtocolError("bind_failed", f"could not bind loopback server: {err}"),
            EXIT_STARTUP_FAILED,
        )
    host, port = server.server_address[:2]
    host = str(host)
    port = int(port)
    serve_thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": min(0.5, max(0.05, poll_interval))},
        name="lrh-desktop-serve",
        daemon=True,
    )
    serve_thread.start()

    if host != LOOPBACK_HOST:
        _stop_server(server, serve_thread, stop_timeout)
        return fail(
            launch_id,
            ProtocolError("bind_failed", f"server bound to non-loopback host {host!r}"),
            EXIT_STARTUP_FAILED,
        )
    try:
        _self_check(host, port, self_check_timeout)
    except ProtocolError as err:
        _stop_server(server, serve_thread, stop_timeout)
        return fail(launch_id, err, EXIT_STARTUP_FAILED)

    if not writer.send(ready_message(launch_id, workspace, host, port)):
        _stop_server(server, serve_thread, stop_timeout)
        return SessionResult(EXIT_PARENT_LOST, REASON_PARENT_CHANNEL_CLOSED, launch_id)
    _log(
        log_stream,
        f"ready launch_id={launch_id} endpoint=http://{host}:{port}/ "
        f"project_root={workspace.project_root}",
    )

    try:
        reason = _serve_until_stop(
            reader,
            writer,
            launch_id,
            poll_interval=poll_interval,
            parent_alive=parent_alive,
            stop_signal=stop_signal,
        )
    except Exception as err:  # noqa: BLE001 - never report failed after ready
        # Once ready has been sent the only terminal messages are
        # stopping/stopped, so an unexpected error still stops the server.
        _log(log_stream, f"internal error: {type(err).__name__}: {err}")
        reason = REASON_INTERNAL_ERROR
    _log(log_stream, f"stopping launch_id={launch_id} reason={reason}")
    writer.send(lifecycle_message("stopping", launch_id, reason))
    _stop_server(server, serve_thread, stop_timeout)
    writer.send(lifecycle_message("stopped", launch_id, reason))
    return SessionResult(_EXIT_CODE_BY_REASON[reason], reason, launch_id)


def _wait_for_start_item(
    reader: FrameReader,
    timeout: float,
    *,
    poll_interval: float,
    parent_alive: Callable[[], bool] | None,
    stop_signal: StopSignal | None,
) -> object | None:
    """Wait for the first reader item; None on timeout, _CANCELLED on stop."""

    deadline = time.monotonic() + timeout
    while True:
        if stop_signal is not None and stop_signal.requested:
            return _CANCELLED
        if parent_alive is not None and not parent_alive():
            return _CANCELLED
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return reader.items.get(timeout=min(poll_interval, remaining))
        except queue.Empty:
            continue


def _serve_until_stop(
    reader: FrameReader,
    writer: MessageWriter,
    launch_id: str,
    *,
    poll_interval: float,
    parent_alive: Callable[[], bool] | None,
    stop_signal: StopSignal | None,
) -> str:
    """Process control messages until a stop condition; return the reason."""

    while True:
        if stop_signal is not None and stop_signal.requested:
            return REASON_SIGNAL
        if parent_alive is not None and not parent_alive():
            return REASON_PARENT_PROCESS_EXITED
        if writer.broken:
            return REASON_PARENT_CHANNEL_CLOSED
        try:
            item = reader.items.get(timeout=poll_interval)
        except queue.Empty:
            continue
        if item is _EOF:
            return REASON_PARENT_CHANNEL_CLOSED
        if isinstance(item, ProtocolError):
            # Framing may be desynchronized; fail closed rather than guess.
            writer.send(error_message(launch_id, item))
            return REASON_PROTOCOL_ERROR
        assert isinstance(item, dict)
        request_id = _request_id(item)
        error = _control_message_error(item, launch_id)
        if error is not None:
            writer.send(error_message(launch_id, error, request_id))
            continue
        message_type = item.get("type")
        if message_type == "shutdown":
            return REASON_SHUTDOWN_REQUESTED
        if message_type == "start":
            writer.send(
                error_message(
                    launch_id,
                    ProtocolError("already_started", "this server has already started"),
                    request_id,
                )
            )
            continue
        if message_type == "ping":
            pong = _envelope("pong", launch_id)
            if request_id is not None:
                pong["request_id"] = request_id
            writer.send(pong)
            continue
        writer.send(
            error_message(
                launch_id,
                ProtocolError(
                    "unknown_message_type",
                    f"unsupported control message type {_echo(message_type)}",
                    {"supported_types": ["ping", "shutdown"]},
                ),
                request_id,
            )
        )


def _request_id(message: dict[str, Any]) -> str | None:
    request_id = message.get("request_id")
    if isinstance(request_id, str) and 0 < len(request_id) <= _REQUEST_ID_MAX_LENGTH:
        return request_id
    return None


def _control_message_error(
    message: dict[str, Any], launch_id: str
) -> ProtocolError | None:
    if message.get("protocol") != PROTOCOL_NAME:
        return ProtocolError(
            "unsupported_protocol", f"expected protocol {PROTOCOL_NAME!r}"
        )
    if message.get("protocol_version") != PROTOCOL_VERSION:
        return ProtocolError(
            "unsupported_protocol_version",
            "control messages must use the negotiated protocol_version",
            {"supported_versions": list(SUPPORTED_PROTOCOL_VERSIONS)},
        )
    if message.get("launch_id") != launch_id:
        # Correlation only: a mismatch means a stale or misrouted message,
        # not an authentication failure. The pipe itself is the owner.
        return ProtocolError(
            "launch_id_mismatch",
            "control message launch_id does not match this server",
        )
    return None


def run_desktop_protocol(
    server_factory: ServerFactory,
    *,
    start_request_timeout: float = DEFAULT_START_REQUEST_TIMEOUT_SECONDS,
) -> int:
    """Run desktop-protocol mode on this process's stdin/stdout.

    Reserves the original stdout descriptor for machine messages and points
    descriptor 1 (and ``sys.stdout``) at stderr, so any stray print or library
    output lands in human diagnostics instead of corrupting the channel.
    """

    sys.stdout.flush()
    protocol_fd = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    writer = MessageWriter(protocol_fd)

    stop_signal = StopSignal()

    def _handle_signal(signum: int, frame: object) -> None:
        stop_signal.request()

    for name in ("SIGTERM", "SIGINT", "SIGHUP"):
        signum = getattr(signal, name, None)
        if signum is not None:
            signal.signal(signum, _handle_signal)

    initial_parent_pid = os.getppid()

    def _parent_alive() -> bool:
        # POSIX reparents an orphan, changing getppid(); this catches parent
        # death even if the stdin write end leaked into another process.
        return os.getppid() == initial_parent_pid

    try:
        result = run_session(
            0,
            writer,
            server_factory,
            start_request_timeout=start_request_timeout,
            parent_alive=_parent_alive,
            stop_signal=stop_signal,
        )
    except Exception as err:  # noqa: BLE001 - only reachable before ready
        _log(sys.stderr, f"internal error: {type(err).__name__}: {err}")
        writer.send(
            failed_message(None, ProtocolError("internal_error", "internal error"))
        )
        return EXIT_INTERNAL_ERROR
    finally:
        sys.stderr.flush()
    return result.exit_code

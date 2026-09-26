"""Private, single-writer store for packets and attempt records.

Layout under the store root (directories 0700, files 0600)::

    packets/<packet_sha256>/manifest.json
    packets/<packet_sha256>/packet.md
    runs/<run_id>/run.json          # atomically replaced manifest + outcome
    runs/<run_id>/events.jsonl      # append-only, one JSON event per line
    runs/<run_id>/output.json       # raw model text and parsed briefing
    runs/<run_id>/evaluation.json   # human scores, when recorded

These are experimental attempt logs, not canonical LRH run or work-item state.
The store refuses to live inside a Git worktree so raw content stays out of Git.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import secrets
from collections.abc import Callable

from local_agent import settings
from lrh import atomic_write

_DIR_MODE = 0o700
_FILE_MODE = 0o600


class StoreError(ValueError):
    """Raised for an unsafe store location or a missing record."""


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def default_store_root(environ: dict[str, str] | None = None) -> pathlib.Path:
    env = os.environ if environ is None else environ
    override = env.get(settings.STORE_ENV_VAR)
    if override:
        return pathlib.Path(override).expanduser()
    return pathlib.Path.home().joinpath(*settings.DEFAULT_STORE_RELATIVE)


def _inside_git_worktree(path: pathlib.Path) -> pathlib.Path | None:
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _write_private(path: pathlib.Path, content: str) -> None:
    atomic_write.atomic_write(path, content)
    os.chmod(path, _FILE_MODE)


def _dump(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def read_events(path: pathlib.Path) -> tuple[list[dict[str, object]], bool]:
    """Read JSONL events, tolerating one truncated final line.

    Returns ``(events, truncated_tail)``. A malformed line anywhere other than
    the end is corruption and raises ``StoreError``.
    """
    if not path.exists():
        return [], False
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    events: list[dict[str, object]] = []
    truncated = False
    for index, line in enumerate(lines):
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as error:
            is_last = all(not rest for rest in lines[index + 1 :])
            if is_last:
                truncated = True
                break
            raise StoreError(f"corrupt event log {path} line {index + 1}") from error
    return events, truncated


class Store:
    """Filesystem store rooted outside any Git worktree."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        clock: Callable[[], str] = utc_now,
        token: Callable[[], str] = lambda: secrets.token_hex(3),
    ) -> None:
        resolved = root.expanduser().resolve()
        worktree = _inside_git_worktree(resolved)
        if worktree is not None:
            raise StoreError(
                f"store root {resolved} is inside Git worktree {worktree}; "
                "raw logs must stay out of Git"
            )
        self.root = resolved
        self._clock = clock
        self._token = token

    def _ensure_dir(self, path: pathlib.Path) -> pathlib.Path:
        self.root.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
        for directory in reversed((path, *path.parents)):
            if directory == self.root or self.root in directory.parents:
                if not directory.exists():
                    directory.mkdir(mode=_DIR_MODE)
                os.chmod(directory, _DIR_MODE)
        return path

    # Packets -----------------------------------------------------------

    def packet_dir(self, packet_sha256: str) -> pathlib.Path:
        if len(packet_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in packet_sha256
        ):
            raise StoreError(f"invalid packet sha256 {packet_sha256!r}")
        return self.root / "packets" / packet_sha256

    def save_packet(
        self, packet_sha256: str, manifest: dict[str, object], text: str
    ) -> pathlib.Path:
        directory = self._ensure_dir(self.packet_dir(packet_sha256))
        _write_private(directory / "manifest.json", _dump(manifest))
        _write_private(directory / "packet.md", text)
        return directory

    def load_packet(self, packet_sha256: str) -> tuple[dict[str, object], str]:
        directory = self.packet_dir(packet_sha256)
        if not (directory / "manifest.json").exists():
            raise StoreError(f"no stored packet {packet_sha256}")
        manifest = json.loads((directory / "manifest.json").read_text("utf-8"))
        text = (directory / "packet.md").read_text(encoding="utf-8")
        return manifest, text

    # Runs --------------------------------------------------------------

    def new_run_id(self) -> str:
        stamp = self._clock().replace(":", "").replace("-", "").replace("+", "Z")
        return f"{stamp[:15]}-{self._token()}"

    def run_dir(self, run_id: str) -> pathlib.Path:
        if "/" in run_id or run_id.startswith("."):
            raise StoreError(f"invalid run id {run_id!r}")
        return self.root / "runs" / run_id

    def start_run(self, run_manifest: dict[str, object]) -> str:
        run_id = self.new_run_id()
        directory = self._ensure_dir(self.run_dir(run_id))
        run_manifest = {**run_manifest, "run_id": run_id, "created_at": self._clock()}
        _write_private(directory / "run.json", _dump(run_manifest))
        return run_id

    def load_run(self, run_id: str) -> dict[str, object]:
        path = self.run_dir(run_id) / "run.json"
        if not path.exists():
            raise StoreError(f"no stored run {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def update_run(self, run_id: str, **fields: object) -> dict[str, object]:
        manifest = {**self.load_run(run_id), **fields, "updated_at": self._clock()}
        _write_private(self.run_dir(run_id) / "run.json", _dump(manifest))
        return manifest

    def append_event(self, run_id: str, event_type: str, **payload: object) -> None:
        path = self.run_dir(run_id) / "events.jsonl"
        events, truncated = read_events(path)
        if truncated:
            raise StoreError(f"event log {path} has a truncated tail; recover first")
        event = {"seq": len(events) + 1, "at": self._clock(), "type": event_type}
        event.update(payload)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        fd = os.open(path, flags, _FILE_MODE)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def events(self, run_id: str) -> tuple[list[dict[str, object]], bool]:
        return read_events(self.run_dir(run_id) / "events.jsonl")

    def write_json(self, run_id: str, name: str, data: object) -> None:
        _write_private(self.run_dir(run_id) / name, _dump(data))

    def read_json(self, run_id: str, name: str) -> object | None:
        path = self.run_dir(run_id) / name
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[str]:
        runs = self.root / "runs"
        if not runs.is_dir():
            return []
        return sorted(entry.name for entry in runs.iterdir() if entry.is_dir())

    def recover_run(self, run_id: str) -> dict[str, object]:
        """Reconcile a run whose manifest lacks a terminal outcome.

        If the event log holds a valid terminal ``outcome`` event (the process
        stopped after logging it but before updating ``run.json``), that
        outcome is restored. Otherwise the run is marked ``incomplete``. A
        truncated final event is preserved as evidence (moved to
        ``events.truncated_tail``) rather than silently dropped, and is never
        treated as success.
        """
        path = self.run_dir(run_id) / "events.jsonl"
        events, truncated = read_events(path)
        manifest = self.load_run(run_id)
        if truncated:
            raw = path.read_text(encoding="utf-8")
            keep, _, tail = raw.rstrip("\n").rpartition("\n")
            kept_text = keep + "\n" if keep else ""
            _write_private(self.run_dir(run_id) / "events.truncated_tail", tail)
            _write_private(path, kept_text)
        logged = [event for event in events if event.get("type") == "outcome"]
        if manifest.get("outcome") is None and logged:
            manifest = self.update_run(
                run_id,
                outcome=logged[-1].get("outcome"),
                outcome_detail=logged[-1].get("detail"),
                recovered_from_event_log=True,
                recovered_truncated_tail=truncated,
            )
            self.append_event(
                run_id, "recovered", truncated_tail=truncated, restored_outcome=True
            )
        elif manifest.get("outcome") is None:
            manifest = self.update_run(
                run_id,
                outcome="incomplete",
                outcome_detail="recovered: no terminal outcome was recorded",
                recovered_truncated_tail=truncated,
            )
            self.append_event(run_id, "recovered", truncated_tail=truncated)
        return manifest

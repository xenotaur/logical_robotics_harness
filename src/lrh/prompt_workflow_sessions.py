"""Minimal project/sessions/ index: host<->child session identity capture.

Stage 1 of PROP-LRH-SESSION-ARCHIVE-SYNC. This module owns only identity
capture (host id, child id aliases, title, PRs, branch/writtenBranches[]
fields reserved for later fork stitching). It does not archive transcript
content, reconcile against /export metadata, or implement lrh sessions
sync/discover/link/report -- those are later stages.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import typing


@dataclasses.dataclass(frozen=True)
class SessionRecord:
    """One session's identity, keyed by its host id."""

    host_id: str
    child_ids: tuple[str, ...] = ()
    title: str | None = None
    prs: tuple[str, ...] = ()
    branch: str | None = None
    written_branches: tuple[str, ...] = ()
    updated_at: str | None = None

    def to_json_dict(self) -> dict[str, typing.Any]:
        return {
            "host_id": self.host_id,
            "child_ids": list(self.child_ids),
            "title": self.title,
            "prs": list(self.prs),
            "branch": self.branch,
            "written_branches": list(self.written_branches),
            "updated_at": self.updated_at,
        }


def index_path(project_root: str | pathlib.Path) -> pathlib.Path:
    return pathlib.Path(project_root) / "project" / "sessions" / "index.jsonl"


def load_session_index(
    project_root: str | pathlib.Path,
) -> dict[str, SessionRecord]:
    """Load the committed index. Missing file is not an error -- empty index."""

    path = index_path(project_root)
    records: dict[str, SessionRecord] = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        host_id = data["host_id"]
        records[host_id] = SessionRecord(
            host_id=host_id,
            child_ids=tuple(data.get("child_ids") or ()),
            title=data.get("title"),
            prs=tuple(data.get("prs") or ()),
            branch=data.get("branch"),
            written_branches=tuple(data.get("written_branches") or ()),
            updated_at=data.get("updated_at"),
        )
    return records


def _merge(
    existing: SessionRecord | None,
    *,
    host_id: str,
    child_id: str | None,
    title: str | None,
    pr: str | None,
    branch: str | None,
    written_branches: typing.Sequence[str] | None,
    updated_at: str,
) -> SessionRecord:
    child_ids = set(existing.child_ids) if existing else set()
    if child_id:
        child_ids.add(child_id)
    prs = set(existing.prs) if existing else set()
    if pr:
        prs.add(pr)
    written = set(existing.written_branches) if existing else set()
    if written_branches:
        written.update(written_branches)
    return SessionRecord(
        host_id=host_id,
        child_ids=tuple(sorted(child_ids)),
        title=title if title is not None else (existing.title if existing else None),
        prs=tuple(sorted(prs)),
        branch=(
            branch if branch is not None else (existing.branch if existing else None)
        ),
        written_branches=tuple(sorted(written)),
        updated_at=updated_at,
    )


def record_session_observation(
    project_root: str | pathlib.Path,
    *,
    host_id: str,
    updated_at: str,
    child_id: str | None = None,
    title: str | None = None,
    pr: str | None = None,
    branch: str | None = None,
    written_branches: typing.Sequence[str] | None = None,
) -> pathlib.Path:
    """Merge one observation into the session identity for ``host_id``.

    Idempotent and dedup-by-host-id, latest-wins for scalar fields
    (title/branch), union for set-valued fields (child_ids/prs/
    written_branches). Rewrites the whole index sorted by host_id so the
    file is byte-stable across repeated observations and diffs cleanly.
    """

    if not host_id:
        raise ValueError("host_id is required")
    records = load_session_index(project_root)
    records[host_id] = _merge(
        records.get(host_id),
        host_id=host_id,
        child_id=child_id,
        title=title,
        pr=pr,
        branch=branch,
        written_branches=written_branches,
        updated_at=updated_at,
    )
    path = index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(records[key].to_json_dict(), sort_keys=True)
        for key in sorted(records)
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path

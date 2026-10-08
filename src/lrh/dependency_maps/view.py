"""Dependency-map view declarations: ``project/views/dependency_maps/<name>.md``.

A declaration holds the view's identity, ordered lanes and phases, and
placement by canonical ID. It never copies work items or edges:

    ---
    id: "lrh-console-l1"
    title: "LRH Console L1"
    lanes:
    - workstream: "WS-EXAMPLE"
      title: "Example"            # optional; defaults to the workstream title
    phases:
    - id: "foundation"
      title: "Foundation"
      work_items: ["WI-ONE", "WI-TWO"]
    lane_overrides:               # optional
    - work_item: "WI-THREE"
      lane: "WS-EXAMPLE"
      reason: "Listed in two workstreams; tracked here."
    ---

Lanes are canonical workstreams. An item belongs to a lane when that
workstream lists it in ``work_items`` or is its ``parent_id``.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Any

from lrh.control.parser import parse_markdown_file

VIEWS_DIR = pathlib.Path("project") / "views" / "dependency_maps"
_VIEW_ID = re.compile(r"[a-z0-9][a-z0-9-]*")


class ViewDeclarationError(ValueError):
    """A view declaration that cannot be used; ``problems`` lists every issue."""

    def __init__(self, path: str, problems: list[str]) -> None:
        super().__init__(f"{path}: " + "; ".join(problems))
        self.path = path
        self.problems = tuple(problems)


@dataclasses.dataclass(frozen=True)
class Lane:
    workstream: str
    title: str | None = None


@dataclasses.dataclass(frozen=True)
class Phase:
    id: str
    title: str
    work_items: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class LaneOverride:
    work_item: str
    lane: str
    reason: str


@dataclasses.dataclass(frozen=True)
class ViewDeclaration:
    id: str
    title: str
    lanes: tuple[Lane, ...]
    phases: tuple[Phase, ...]
    lane_overrides: tuple[LaneOverride, ...] = ()
    source: str = ""


def view_path(repo_root: pathlib.Path, view_id: str) -> pathlib.Path:
    """Return where a view declaration lives, rejecting unsafe names."""

    if not _VIEW_ID.fullmatch(view_id):
        raise ViewDeclarationError(view_id, ["view ids are lowercase, digits, -"])
    return repo_root / VIEWS_DIR / f"{view_id}.md"


def discover_views(repo_root: pathlib.Path) -> tuple[pathlib.Path, ...]:
    """Return every declaration file under ``project/views/dependency_maps``."""

    directory = repo_root / VIEWS_DIR
    if not directory.is_dir():
        return ()
    return tuple(sorted(path for path in directory.glob("*.md") if path.is_file()))


def load_view(repo_root: pathlib.Path, view_id: str) -> ViewDeclaration:
    """Load one declaration by id; FileNotFoundError if it does not exist."""

    path = view_path(repo_root, view_id)
    if not path.is_file():
        raise FileNotFoundError(f"no dependency-map view named {view_id!r}")
    return parse_view(path, repo_root)


def parse_view(path: pathlib.Path, repo_root: pathlib.Path) -> ViewDeclaration:
    """Parse and check a declaration's shape (not its references)."""

    source = path.relative_to(repo_root).as_posix()
    try:
        data = parse_markdown_file(path).frontmatter
    except (OSError, ValueError) as err:
        raise ViewDeclarationError(source, [str(err)]) from err
    problems: list[str] = []

    view_id = data.get("id")
    if not isinstance(view_id, str) or view_id != path.stem:
        problems.append(f"id must be {path.stem!r}, matching the file name")
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("title must be a non-empty string")

    lanes = _lanes(data.get("lanes"), problems)
    phases = _phases(data.get("phases"), problems)
    overrides = _overrides(data.get("lane_overrides", []), problems)
    unknown = sorted(set(data) - {"id", "title", "lanes", "phases", "lane_overrides"})
    if unknown:
        problems.append(f"unknown fields: {', '.join(unknown)}")
    if problems:
        raise ViewDeclarationError(source, problems)
    return ViewDeclaration(
        id=str(view_id),
        title=str(title),
        lanes=lanes,
        phases=phases,
        lane_overrides=overrides,
        source=source,
    )


def reference_problems(
    view: ViewDeclaration,
    work_item_ids: set[str],
    workstream_ids: set[str],
) -> list[str]:
    """Return every canonical ID the view names that the project lacks."""

    problems = [
        f"lane workstream {lane.workstream} does not exist"
        for lane in view.lanes
        if lane.workstream not in workstream_ids
    ]
    for phase in view.phases:
        problems.extend(
            f"phase {phase.id} lists {item}, which does not exist"
            for item in phase.work_items
            if item not in work_item_ids
        )
    lanes = {lane.workstream for lane in view.lanes}
    for override in view.lane_overrides:
        if override.work_item not in work_item_ids:
            problems.append(
                f"lane override names {override.work_item}, which does not exist"
            )
        if override.lane not in lanes:
            problems.append(
                f"lane override for {override.work_item} names {override.lane}, "
                "which is not a lane of this view"
            )
    return problems


def _string_list(value: Any) -> tuple[str, ...] | None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    return None


def _lanes(value: Any, problems: list[str]) -> tuple[Lane, ...]:
    if not isinstance(value, list) or not value:
        problems.append("lanes must be a non-empty list")
        return ()
    lanes: list[Lane] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict) or not isinstance(entry.get("workstream"), str):
            problems.append(f"lanes[{index}] needs a workstream id")
            continue
        title = entry.get("title")
        if title is not None and not isinstance(title, str):
            problems.append(f"lanes[{index}].title must be a string")
            continue
        lanes.append(Lane(workstream=entry["workstream"], title=title))
    seen = [lane.workstream for lane in lanes]
    if len(set(seen)) != len(seen):
        problems.append("lanes must not repeat a workstream")
    return tuple(lanes)


def _phases(value: Any, problems: list[str]) -> tuple[Phase, ...]:
    if not isinstance(value, list) or not value:
        problems.append("phases must be a non-empty list")
        return ()
    phases: list[Phase] = []
    for index, entry in enumerate(value):
        items = (
            _string_list(entry.get("work_items")) if isinstance(entry, dict) else None
        )
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("id"), str)
            or not isinstance(entry.get("title"), str)
            or items is None
        ):
            problems.append(
                f"phases[{index}] needs an id, a title, and a work_items list"
            )
            continue
        if entry["id"] == "unplaced":
            problems.append("phase id 'unplaced' is reserved")
        phases.append(Phase(id=entry["id"], title=entry["title"], work_items=items))
    ids = [phase.id for phase in phases]
    if len(set(ids)) != len(ids):
        problems.append("phase ids must be unique")
    return tuple(phases)


def _overrides(value: Any, problems: list[str]) -> tuple[LaneOverride, ...]:
    if not isinstance(value, list):
        problems.append("lane_overrides must be a list")
        return ()
    overrides: list[LaneOverride] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(key), str) and entry.get(key)
            for key in ("work_item", "lane", "reason")
        ):
            problems.append(
                f"lane_overrides[{index}] needs a work_item, a lane, and a reason"
            )
            continue
        overrides.append(
            LaneOverride(
                work_item=entry["work_item"], lane=entry["lane"], reason=entry["reason"]
            )
        )
    return tuple(overrides)

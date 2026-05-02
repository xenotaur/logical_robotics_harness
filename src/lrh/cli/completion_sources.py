"""Framework-neutral completion providers for LRH CLI workflows."""

from __future__ import annotations

import pathlib

from lrh.assist import request_templates
from lrh.control import parser as control_parser

_WORK_ITEM_BUCKETS = ("proposed", "active", "resolved", "abandoned")


def request_template_names(prefix: str = "") -> list[str]:
    """Return sorted request-template names from package resources."""
    names: list[str] = []
    try:
        for candidate in request_templates.get_template_root().iterdir():
            if candidate.is_file() and candidate.name.endswith(".md"):
                names.append(candidate.name[: -len(".md")])
    except (FileNotFoundError, OSError):
        return []
    return _filter_sorted(names, prefix)


def work_item_ids(project_root: pathlib.Path, prefix: str = "") -> list[str]:
    """Return sorted work-item IDs from known project/work_items buckets."""
    work_items_root = project_root / "project" / "work_items"
    identifiers: set[str] = set()
    for bucket in _WORK_ITEM_BUCKETS:
        bucket_dir = work_items_root / bucket
        if not bucket_dir.is_dir():
            continue
        for work_item_path in sorted(bucket_dir.glob("*.md")):
            work_item_id = _read_frontmatter_id(work_item_path)
            if work_item_id:
                identifiers.add(work_item_id)
    return _filter_sorted(identifiers, prefix)


def _read_frontmatter_id(path: pathlib.Path) -> str:
    """Read work-item `id` from YAML frontmatter using canonical parser."""
    try:
        parsed = control_parser.parse_markdown_file(path)
    except (FileNotFoundError, OSError, ValueError):
        return ""
    work_item_id = parsed.frontmatter.get("id")
    return work_item_id if isinstance(work_item_id, str) else ""


def _filter_sorted(values: list[str] | set[str], prefix: str) -> list[str]:
    needle = (prefix or "").strip()
    return sorted(value for value in values if value.startswith(needle))

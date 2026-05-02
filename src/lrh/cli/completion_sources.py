"""Framework-neutral completion providers for LRH CLI workflows."""

from __future__ import annotations

import pathlib

from lrh.assist import request_templates

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
    """Read `id` from a markdown file's top YAML frontmatter block."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""

    if not text.startswith("---\n"):
        return ""
    lines = text.splitlines()
    for line in lines[1:]:
        if line.strip() == "---":
            return ""
        stripped = line.strip()
        if stripped.startswith("id:"):
            value = stripped[len("id:") :].strip()
            return value.strip("\"'")
    return ""


def _filter_sorted(values: list[str] | set[str], prefix: str) -> list[str]:
    needle = (prefix or "").strip()
    return sorted(value for value in values if value.startswith(needle))

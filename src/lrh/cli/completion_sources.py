"""Framework-neutral completion providers for LRH CLI workflows."""

from __future__ import annotations

import pathlib
import re

from lrh.assist import request_templates
from lrh.control import parser as control_parser
from lrh.work_items import validate as work_items_validate

_WORK_ITEM_ID_PATTERN = re.compile(r"^WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*$")
_WORK_ITEM_H1_ID_PATTERN = re.compile(
    r"^#\s*(WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)(?:\s|:|$)"
)


def request_template_names(
    prefix: str = "",
    *,
    project_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
    environ: dict[str, str] | None = None,
) -> list[str]:
    """Return sorted request-template names from overrides and package resources."""
    try:
        names = request_templates.request_template_names(
            project_root=project_root,
            template_dirs=template_dirs,
            environ=environ,
        )
    except (FileNotFoundError, OSError):
        return []
    return _filter_sorted(names, prefix)


def work_item_ids(project_root: pathlib.Path, prefix: str = "") -> list[str]:
    """Return sorted work-item IDs discovered under project/work_items."""
    work_items_root = project_root / "project" / "work_items"
    if not work_items_root.is_dir():
        return []
    identifiers: set[str] = set()
    for work_item_path in _discover_work_item_paths(work_items_root):
        work_item_id = _read_frontmatter_id(work_item_path)
        if work_item_id:
            identifiers.add(work_item_id)
            continue
        heading_id = _read_h1_work_item_id(work_item_path)
        if heading_id:
            identifiers.add(heading_id)
            continue
        filename_id = _read_filename_work_item_id(work_item_path)
        if filename_id:
            identifiers.add(filename_id)
    return _filter_sorted(identifiers, prefix)


def _discover_work_item_paths(work_items_root: pathlib.Path) -> list[pathlib.Path]:
    return work_items_validate.discover_work_item_paths(work_items_root)


def _read_frontmatter_id(path: pathlib.Path) -> str:
    """Read work-item `id` from YAML frontmatter using canonical parser."""
    try:
        parsed = control_parser.parse_markdown_file(path)
    except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError):
        return ""
    work_item_id = parsed.frontmatter.get("id")
    if not isinstance(work_item_id, str):
        return ""
    candidate = work_item_id.strip()
    return candidate if _looks_like_work_item_id(candidate) else ""


def _read_h1_work_item_id(path: pathlib.Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ""
    content_lines = lines
    if content_lines and content_lines[0].strip() == "---":
        for index in range(1, len(content_lines)):
            if content_lines[index].strip() == "---":
                content_lines = content_lines[index + 1 :]
                break
    for line in content_lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = _WORK_ITEM_H1_ID_PATTERN.match(stripped)
        if match is not None:
            candidate = match.group(1)
            return candidate if _looks_like_work_item_id(candidate) else ""
    return ""


def _read_filename_work_item_id(path: pathlib.Path) -> str:
    candidate = path.stem.strip()
    return candidate if _looks_like_work_item_id(candidate) else ""


def _looks_like_work_item_id(value: str) -> bool:
    return bool(_WORK_ITEM_ID_PATTERN.fullmatch(value))


def _filter_sorted(values: list[str] | set[str], prefix: str) -> list[str]:
    needle = (prefix or "").strip()
    return sorted(value for value in values if value.startswith(needle))

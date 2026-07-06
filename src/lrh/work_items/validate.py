"""Validation for project work-item hygiene and organization."""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re
from typing import Any

from lrh.control import parser as control_parser

_ALLOWED_STATUSES = ("proposed", "active", "resolved", "abandoned")
_REFERENCE_FIELDS_TO_DIRS = {
    "related_roadmap": ("roadmap",),
    "related_focus": ("focus",),
    "related_workstream": ("workstreams",),
    "related_workstreams": ("workstreams",),
    "related_design": ("design",),
}
_DEPENDENCY_FIELDS = ("depends_on", "blocked_by")
_WORK_ITEM_ID_PATTERN = re.compile(r"^WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*$")
_WORK_ITEM_H1_ID_PATTERN = re.compile(
    r"^#\s*(WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)(?:\s|:|$)"
)


@dataclasses.dataclass(frozen=True)
class WorkItemDiagnostic:
    severity: str
    code: str
    path: str
    message: str


@dataclasses.dataclass(frozen=True)
class WorkItemValidationResult:
    diagnostics: tuple[WorkItemDiagnostic, ...]

    @property
    def errors(self) -> int:
        return sum(1 for item in self.diagnostics if item.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for item in self.diagnostics if item.severity == "warning")


def discover_work_item_paths(work_items_root: pathlib.Path) -> list[pathlib.Path]:
    paths = set(work_items_root.glob("*.md"))
    paths.update(work_items_root.glob("**/*.md"))
    return sorted(
        path for path in paths if path.is_file() and path.name.lower() != "readme.md"
    )


def validate_work_items(project_root: pathlib.Path) -> WorkItemValidationResult:
    work_items_root = project_root / "project" / "work_items"
    if not work_items_root.exists() or not work_items_root.is_dir():
        return WorkItemValidationResult(diagnostics=())

    diagnostics: list[WorkItemDiagnostic] = []
    ids_to_paths: dict[str, list[pathlib.Path]] = {}
    records_by_id: dict[str, tuple[pathlib.Path, dict[str, Any]]] = {}
    for path in discover_work_item_paths(work_items_root):
        rel = path.relative_to(project_root).as_posix()
        bucket = _bucket_for(path=path, work_items_root=work_items_root)
        if bucket == "flat":
            diagnostics.append(
                WorkItemDiagnostic(
                    "warning",
                    "flat-work-item",
                    rel,
                    "Work item is discoverable but not organized into a status bucket.",
                )
            )
        elif bucket == "unknown":
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "unknown-bucket-directory",
                    rel,
                    "File is under an unknown nested directory in project/work_items/.",
                )
            )

        record = _inspect(path)
        if record["frontmatter_invalid_type"]:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "frontmatter-not-mapping",
                    rel,
                    "YAML frontmatter must be a mapping/object.",
                )
            )
            continue
        if record["malformed"]:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "malformed-frontmatter",
                    rel,
                    "YAML frontmatter is malformed.",
                )
            )
            continue

        fm_id = record["frontmatter_id"]
        h1_id = record["h1_id"]
        filename_id = record["filename_id"]
        reliable_id = fm_id or h1_id or filename_id

        if not record["has_frontmatter"] and reliable_id:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "missing-frontmatter",
                    rel,
                    "Work-item-like file is missing YAML frontmatter.",
                )
            )
        if reliable_id is None:
            diagnostics.append(
                WorkItemDiagnostic(
                    "warning",
                    "non-work-item-markdown",
                    rel,
                    (
                        "Markdown file under project/work_items does not "
                        "appear to be a work item."
                    ),
                )
            )
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "missing-reliable-id",
                    rel,
                    (
                        "No reliable WI-* identifier found in frontmatter, H1, "
                        "or filename."
                    ),
                )
            )
            continue
        if fm_id is None:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "missing-frontmatter-id",
                    rel,
                    "Work item is missing frontmatter id.",
                )
            )
            diagnostics.append(
                WorkItemDiagnostic(
                    "warning",
                    "fallback-id-source",
                    rel,
                    (
                        "Work item ID was discovered from H1/filename "
                        "fallback; add frontmatter id."
                    ),
                )
            )
        else:
            ids_to_paths.setdefault(fm_id, []).append(path)
            parsed_frontmatter = _parse_frontmatter(path)
            if parsed_frontmatter is not None:
                records_by_id[fm_id] = (path, parsed_frontmatter)

        if record["has_frontmatter"] and record["frontmatter_status"] is None:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "missing-frontmatter-status",
                    rel,
                    "Work item is missing frontmatter status.",
                )
            )

        status = record["status_value"]
        if status and status not in _ALLOWED_STATUSES:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "invalid-status",
                    rel,
                    (
                        "Work item status must be one of proposed, active, "
                        "resolved, abandoned."
                    ),
                )
            )
        if (
            status in _ALLOWED_STATUSES
            and bucket in _ALLOWED_STATUSES
            and status != bucket
        ):
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "bucket-status-mismatch",
                    rel,
                    f"Bucket '{bucket}' does not match frontmatter status '{status}'.",
                )
            )

        if fm_id and filename_id and fm_id != filename_id:
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "filename-id-mismatch",
                    rel,
                    "Filename stem does not match frontmatter id.",
                )
            )
        if fm_id and h1_id and fm_id != h1_id:
            diagnostics.append(
                WorkItemDiagnostic(
                    "warning",
                    "h1-id-mismatch",
                    rel,
                    "H1 work item ID does not match frontmatter id.",
                )
            )

    diagnostics.extend(_validate_metadata_references(project_root, records_by_id))

    for wi, wi_paths in sorted(ids_to_paths.items()):
        if len(wi_paths) <= 1:
            continue
        for dup in sorted(wi_paths):
            diagnostics.append(
                WorkItemDiagnostic(
                    "error",
                    "duplicate-id",
                    dup.relative_to(project_root).as_posix(),
                    f"Duplicate frontmatter id {wi}.",
                )
            )

    diagnostics = sorted(
        diagnostics, key=lambda d: (d.severity, d.code, d.path, d.message)
    )
    return WorkItemValidationResult(diagnostics=tuple(diagnostics))


def format_text(result: WorkItemValidationResult) -> str:
    lines = [
        f"Work item validation: {result.errors} error(s), {result.warnings} warning(s)"
    ]
    for item in result.diagnostics:
        lines.append(f"\n{item.severity.upper()} {item.code}")
        lines.append(f"  {item.path}")
        lines.append(f"  {item.message}")
    return "\n".join(lines)


def format_json(result: WorkItemValidationResult) -> str:
    payload = {
        "schema_version": "1.0",
        "errors": result.errors,
        "warnings": result.warnings,
        "diagnostics": [dataclasses.asdict(d) for d in result.diagnostics],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _inspect(path: pathlib.Path) -> dict[str, str | bool | None]:
    text = path.read_text(encoding="utf-8")
    has_frontmatter = text.startswith("---\n")
    malformed = False
    frontmatter_invalid_type = False
    frontmatter_id = None
    frontmatter_status = None
    status_value = None
    body = text

    if has_frontmatter:
        frontmatter_text, body = _split_frontmatter_for_inspect(text)
        if frontmatter_text is None:
            malformed = True
        else:
            if frontmatter_text.lstrip().startswith("- "):
                frontmatter_invalid_type = True
            try:
                parsed = control_parser.parse_markdown_text(text)
            except ValueError:
                malformed = True
                parsed = None
            if parsed is not None:
                val = parsed.frontmatter.get("id")
                if isinstance(val, str) and _looks_like_work_item_id(val.strip()):
                    frontmatter_id = val.strip()
                status_raw = parsed.frontmatter.get("status")
                if isinstance(status_raw, str):
                    status_value = status_raw.strip()
                    if status_value:
                        frontmatter_status = status_value

    h1_id = _read_h1_work_item_id(body)
    filename_id = (
        path.stem.strip() if _looks_like_work_item_id(path.stem.strip()) else None
    )
    return {
        "has_frontmatter": has_frontmatter,
        "malformed": malformed,
        "frontmatter_invalid_type": frontmatter_invalid_type,
        "frontmatter_id": frontmatter_id,
        "frontmatter_status": frontmatter_status,
        "status_value": status_value,
        "h1_id": h1_id,
        "filename_id": filename_id,
    }


def _split_frontmatter_for_inspect(text: str) -> tuple[str | None, str]:
    # Use str.find() instead of line-by-line slicing to avoid O(N^2) behavior
    # on very large files missing closing frontmatter delimiters.
    start = 4
    while True:
        idx = text.find("---", start)
        if idx == -1:
            break

        line_start = text.rfind("\n", 0, idx) + 1
        line_end = text.find("\n", idx)
        if line_end == -1:
            line_end = len(text)

        line = text[line_start:line_end]
        if line.strip() == "---":
            body_start = line_end + 1 if line_end < len(text) else line_end
            return text[4:line_start], text[body_start:]

        start = line_end + 1
    return None, text


def _read_h1_work_item_id(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _WORK_ITEM_H1_ID_PATTERN.match(stripped)
        if match is not None:
            candidate = match.group(1)
            return candidate if _looks_like_work_item_id(candidate) else None
    return None


def _looks_like_work_item_id(value: str) -> bool:
    return bool(_WORK_ITEM_ID_PATTERN.fullmatch(value))


def _bucket_for(path: pathlib.Path, work_items_root: pathlib.Path) -> str | None:
    rel = path.relative_to(work_items_root)
    if len(rel.parts) == 1:
        return "flat"
    first = rel.parts[0]
    if first in _ALLOWED_STATUSES:
        return first
    return "unknown"


def _validate_metadata_references(
    project_root: pathlib.Path,
    records_by_id: dict[str, tuple[pathlib.Path, dict[str, Any]]],
) -> list[WorkItemDiagnostic]:
    diagnostics: list[WorkItemDiagnostic] = []
    known_work_item_ids = set(records_by_id)
    artifact_ids = _artifact_ids_by_directory(project_root)

    dependency_graph: dict[str, tuple[str, ...]] = {}
    for work_item_id, (path, frontmatter) in sorted(records_by_id.items()):
        rel = path.relative_to(project_root).as_posix()
        dependencies: list[str] = []
        for field in _DEPENDENCY_FIELDS:
            for target in _metadata_values(frontmatter.get(field)):
                if not _looks_like_work_item_id(target):
                    diagnostics.append(
                        WorkItemDiagnostic(
                            "warning",
                            "unstructured-work-item-reference",
                            rel,
                            (
                                f"Metadata field '{field}' contains non-WI "
                                f"reference {target!r}."
                            ),
                        )
                    )
                    continue
                dependencies.append(target)
                if target not in known_work_item_ids:
                    diagnostics.append(
                        WorkItemDiagnostic(
                            "error",
                            "missing-work-item-reference",
                            rel,
                            (
                                f"Metadata field '{field}' references unknown "
                                f"work item {target}."
                            ),
                        )
                    )

        dependency_graph[work_item_id] = tuple(dependencies)

        for field, directories in _REFERENCE_FIELDS_TO_DIRS.items():
            allowed_ids = set().union(
                *(artifact_ids.get(name, set()) for name in directories)
            )
            for target in _metadata_values(frontmatter.get(field)):
                if target not in allowed_ids:
                    diagnostics.append(
                        WorkItemDiagnostic(
                            "warning",
                            "unresolved-metadata-reference",
                            rel,
                            (
                                f"Metadata field '{field}' references unresolved "
                                f"artifact {target}."
                            ),
                        )
                    )

    for cycle in _dependency_cycles(dependency_graph):
        if not cycle:
            continue
        cycle_text = " -> ".join((*cycle, cycle[0]))
        first = cycle[0]
        path = records_by_id[first][0].relative_to(project_root).as_posix()
        diagnostics.append(
            WorkItemDiagnostic(
                "error",
                "work-item-dependency-cycle",
                path,
                f"Work-item dependency cycle detected: {cycle_text}.",
            )
        )

    return diagnostics


def _artifact_ids_by_directory(project_root: pathlib.Path) -> dict[str, set[str]]:
    project_dir = project_root / "project"
    result: dict[str, set[str]] = {}
    for directory in _REFERENCE_FIELDS_TO_DIRS.values():
        for directory_name in directory:
            if directory_name in result:
                continue
            root = project_dir / directory_name
            ids: set[str] = set()
            if root.exists():
                for path in sorted(root.glob("**/*.md")):
                    if not path.is_file() or path.name.lower() == "readme.md":
                        continue
                    ids.add(path.stem)
                    ids.add(path.relative_to(project_root).as_posix())
                    ids.add(path.relative_to(project_dir).as_posix())
                    parsed = _parse_frontmatter(path)
                    if parsed is None:
                        continue
                    value = parsed.get("id")
                    if isinstance(value, str) and value.strip():
                        ids.add(value.strip())
            result[directory_name] = ids
    return result


def _parse_frontmatter(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        return control_parser.parse_markdown_file(path).frontmatter
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _metadata_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else ()
    if isinstance(value, list):
        return tuple(
            item.strip() for item in value if isinstance(item, str) and item.strip()
        )
    return ()


def _dependency_cycles(graph: dict[str, tuple[str, ...]]) -> list[tuple[str, ...]]:
    cycles: list[tuple[str, ...]] = []
    visited: set[str] = set()
    visiting: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            cycle = tuple(visiting[visiting.index(node) :])
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.append(node)
        for target in graph.get(node, ()):  # missing targets are validated separately
            if target in graph:
                visit(target)
        visiting.pop()
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return cycles

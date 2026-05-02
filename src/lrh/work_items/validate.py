"""Validation for project work-item hygiene and organization."""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re

from lrh.control import parser as control_parser

_ALLOWED_STATUSES = ("proposed", "active", "resolved", "abandoned")
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
    return sorted(path for path in paths if path.is_file())


def validate_work_items(project_root: pathlib.Path) -> WorkItemValidationResult:
    work_items_root = project_root / "project" / "work_items"
    if not work_items_root.exists() or not work_items_root.is_dir():
        return WorkItemValidationResult(diagnostics=())

    diagnostics: list[WorkItemDiagnostic] = []
    ids_to_paths: dict[str, list[pathlib.Path]] = {}
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
                    "warning",
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
                    "warning",
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
        if fm_id is None and h1_id is None and filename_id is None:
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
        split_index = text.find("\n---\n", 4)
        if split_index == -1:
            malformed = True
        else:
            body = text[split_index + 5 :]
            frontmatter_text = text[4:split_index]
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

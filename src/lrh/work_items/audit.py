"""Deterministic work-item lifecycle audit reporting."""

from __future__ import annotations

import dataclasses
import json
import pathlib
from typing import Any

from lrh.control import parser as control_parser
from lrh.work_items import validate as work_items_validate

_SCHEMA_VERSION = "1.0"
_TRACEABILITY_FIELDS = (
    "related_workstream",
    "related_workstreams",
    "related_design",
    "related_focus",
    "related_roadmap",
    "required_evidence",
    "artifacts_expected",
)
_TERMINAL_STATUSES = ("resolved", "abandoned")


@dataclasses.dataclass(frozen=True)
class WorkItemAuditFinding:
    code: str
    severity: str
    kind: str
    message: str
    evidence: tuple[str, ...] = ()
    recommendation: str | None = None


@dataclasses.dataclass(frozen=True)
class WorkItemAuditItem:
    work_item_id: str
    path: str
    status: str | None
    bucket: str | None
    title: str | None
    findings: tuple[WorkItemAuditFinding, ...]


@dataclasses.dataclass(frozen=True)
class WorkItemAuditReport:
    project_root: pathlib.Path
    validation_result: work_items_validate.WorkItemValidationResult
    items: tuple[WorkItemAuditItem, ...]
    warnings: tuple[str, ...] = ()

    @property
    def summary(self) -> dict[str, int]:
        counts = {
            "items": len(self.items),
            "validation_errors": self.validation_result.errors,
            "validation_warnings": self.validation_result.warnings,
            "findings": 0,
            "candidate_stale": 0,
            "missing_traceability": 0,
            "terminal_missing_resolution": 0,
        }
        for item in self.items:
            counts["findings"] += len(item.findings)
            for finding in item.findings:
                if finding.code == "candidate-stale-semantic-review":
                    counts["candidate_stale"] += 1
                if finding.code == "missing-traceability-links":
                    counts["missing_traceability"] += 1
                if finding.code == "terminal-missing-resolution":
                    counts["terminal_missing_resolution"] += 1
        return counts


def audit_work_items(project_root: pathlib.Path) -> WorkItemAuditReport:
    """Build a deterministic, non-mutating lifecycle audit report."""
    work_items_root = project_root / "project" / "work_items"
    validation_result = work_items_validate.validate_work_items(project_root)
    if not work_items_root.exists() or not work_items_root.is_dir():
        return WorkItemAuditReport(
            project_root=project_root,
            validation_result=validation_result,
            items=(),
            warnings=("project/work_items does not exist",),
        )

    items: list[WorkItemAuditItem] = []
    for path in work_items_validate.discover_work_item_paths(work_items_root):
        parsed = _parse_frontmatter(path)
        if parsed is None:
            continue
        work_item_id = _string_or_none(parsed.get("id")) or path.stem
        status = _string_or_none(parsed.get("status"))
        bucket = _bucket_for(path, work_items_root)
        title = _string_or_none(parsed.get("title"))
        findings = _findings_for_item(project_root, path, parsed)
        items.append(
            WorkItemAuditItem(
                work_item_id=work_item_id,
                path=path.relative_to(project_root).as_posix(),
                status=status,
                bucket=bucket,
                title=title,
                findings=tuple(findings),
            )
        )

    return WorkItemAuditReport(
        project_root=project_root,
        validation_result=validation_result,
        items=tuple(sorted(items, key=lambda item: item.path)),
    )


def format_json(report: WorkItemAuditReport) -> str:
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "root": str(report.project_root),
        "summary": report.summary,
        "items": [
            {
                "id": item.work_item_id,
                "path": item.path,
                "status": item.status,
                "bucket": item.bucket,
                "title": item.title,
                "findings": [dataclasses.asdict(finding) for finding in item.findings],
            }
            for item in report.items
        ],
        "validation": json.loads(
            work_items_validate.format_json(report.validation_result)
        ),
        "warnings": list(report.warnings),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def format_markdown(report: WorkItemAuditReport) -> str:
    summary = report.summary
    lines = [
        "# Work Item Lifecycle Audit",
        "",
        "## Summary",
        "",
        f"- Project root: `{report.project_root}`",
        f"- Work items inspected: {summary['items']}",
        (
            "- Validation diagnostics: "
            f"{summary['validation_errors']} error(s), "
            f"{summary['validation_warnings']} warning(s)"
        ),
        f"- Lifecycle findings: {summary['findings']}",
        (
            "- Candidate stale items requiring semantic review: "
            f"{summary['candidate_stale']}"
        ),
        f"- Items missing traceability links: {summary['missing_traceability']}",
        "",
        "## Deterministic validation diagnostics",
        "",
    ]
    if report.validation_result.diagnostics:
        for diagnostic in report.validation_result.diagnostics:
            lines.append(
                f"- **{diagnostic.severity}** `{diagnostic.code}` "
                f"in `{diagnostic.path}`: {diagnostic.message}"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Lifecycle findings", ""])
    finding_items = [item for item in report.items if item.findings]
    if not finding_items:
        lines.append("- No lifecycle findings.")
    for item in finding_items:
        title = f" — {item.title}" if item.title else ""
        lines.append(f"### {item.work_item_id}{title}")
        lines.append("")
        lines.append(f"- Path: `{item.path}`")
        lines.append(f"- Status: `{item.status}`")
        lines.append(f"- Bucket: `{item.bucket}`")
        for finding in item.findings:
            lines.append("")
            lines.append(f"#### {finding.code}")
            lines.append("")
            lines.append(f"- Severity: `{finding.severity}`")
            lines.append(f"- Type: `{finding.kind}`")
            lines.append(f"- Finding: {finding.message}")
            for evidence in finding.evidence:
                lines.append(f"- Fact: {evidence}")
            if finding.recommendation:
                lines.append(f"- Recommendation: {finding.recommendation}")
        lines.append("")

    lines.extend(
        [
            "## Semantic review guidance",
            "",
            (
                "This audit is deterministic and non-mutating. It reports facts and "
                "conservative recommendations; it does not decide whether acceptance "
                "criteria are complete. Use the semantic work-item audit request "
                "template for any closure, abandonment, split, or supersession "
                "recommendation that requires repository interpretation."
            ),
        ]
    )
    return "\n".join(lines)


def _findings_for_item(
    project_root: pathlib.Path,
    path: pathlib.Path,
    frontmatter: dict[str, Any],
) -> list[WorkItemAuditFinding]:
    findings: list[WorkItemAuditFinding] = []
    work_item_id = _string_or_none(frontmatter.get("id")) or path.stem
    status = _string_or_none(frontmatter.get("status"))

    if status in _TERMINAL_STATUSES and frontmatter.get("resolution") in (None, ""):
        findings.append(
            WorkItemAuditFinding(
                code="terminal-missing-resolution",
                severity="warning",
                kind="fact",
                message="Terminal work item lacks resolution metadata.",
                recommendation=(
                    "Add concise resolution metadata with evidence before relying "
                    "on terminal status."
                ),
            )
        )

    if status in ("proposed", "active") and not _has_traceability(frontmatter):
        findings.append(
            WorkItemAuditFinding(
                code="missing-traceability-links",
                severity="info",
                kind="fact",
                message=(
                    "Work item lacks obvious roadmap, focus, design, workstream, "
                    "evidence, artifact, or execution-record linkage in frontmatter."
                ),
                recommendation=(
                    "Add deterministic metadata where possible, or include this item "
                    "in a semantic audit before lifecycle changes."
                ),
            )
        )

    execution_dir = project_root / "project" / "executions" / work_item_id
    if status in ("proposed", "active") and execution_dir.is_dir():
        findings.append(
            WorkItemAuditFinding(
                code="execution-records-present",
                severity="info",
                kind="fact",
                message="Execution records exist for this non-terminal work item.",
                evidence=(execution_dir.relative_to(project_root).as_posix(),),
                recommendation=(
                    "Review execution records before changing lifecycle status."
                ),
            )
        )

    if work_item_id == "WI-ASSIST-TEMPLATES-PACKAGING" and status == "proposed":
        stale_finding = _assist_template_packaging_finding(project_root)
        if stale_finding is not None:
            findings.append(stale_finding)

    return findings


def _assist_template_packaging_finding(
    project_root: pathlib.Path,
) -> WorkItemAuditFinding | None:
    facts: list[str] = []
    template_dir = project_root / "src" / "lrh" / "assist" / "templates" / "request"
    loader = project_root / "src" / "lrh" / "assist" / "request_templates.py"
    pyproject = project_root / "pyproject.toml"
    tests = project_root / "tests" / "assist_tests" / "request_templates_test.py"

    if template_dir.is_dir():
        facts.append("src/lrh/assist/templates/request/ exists")
    if loader.is_file() and "importlib.resources" in loader.read_text(encoding="utf-8"):
        facts.append("src/lrh/assist/request_templates.py uses package resources")
    if pyproject.is_file() and "lrh.assist" in pyproject.read_text(encoding="utf-8"):
        facts.append("pyproject.toml includes lrh.assist package data")
    if tests.is_file() and "package_resources" in tests.read_text(encoding="utf-8"):
        facts.append("tests cover package-resource template loading")

    if len(facts) < 3:
        return None
    return WorkItemAuditFinding(
        code="candidate-stale-semantic-review",
        severity="warning",
        kind="recommendation",
        message=(
            "Repository facts indicate the assist-template packaging capability may "
            "already be present."
        ),
        evidence=tuple(facts),
        recommendation=(
            "Review acceptance criteria against the cited facts; if satisfied, move "
            "the work item to resolved with resolution evidence."
        ),
    )


def _parse_frontmatter(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        parsed = control_parser.parse_markdown_file(path)
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return parsed.frontmatter


def _has_traceability(frontmatter: dict[str, Any]) -> bool:
    return any(
        bool(_as_string_tuple(frontmatter.get(field))) for field in _TRACEABILITY_FIELDS
    )


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else ()
    if isinstance(value, list):
        return tuple(
            item.strip() for item in value if isinstance(item, str) and item.strip()
        )
    return ()


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _bucket_for(path: pathlib.Path, work_items_root: pathlib.Path) -> str | None:
    rel = path.relative_to(work_items_root)
    return rel.parts[0] if len(rel.parts) > 1 else None

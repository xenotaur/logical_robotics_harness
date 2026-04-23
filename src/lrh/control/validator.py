"""Validation for LRH control-plane bootstrap artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lrh.control import work_item_policy

CONTRIBUTOR_REQUIRED_FIELDS = {"id", "type", "roles", "display_name", "status"}
CONTRIBUTOR_TYPES = {"human", "agent"}
CONTRIBUTOR_ROLES = {"admin", "editor", "reviewer", "viewer"}
CONTRIBUTOR_STATUS = {"active", "inactive", "archived"}
AGENT_EXECUTION_MODES = {"human_orchestrated", "autonomous", "disabled"}

FOCUS_REQUIRED_FIELDS = {"id", "title", "status"}
FOCUS_STATUS = {"proposed", "active", "paused", "blocked", "completed", "abandoned"}

WORK_ITEM_REQUIRED_FIELDS = {"id", "title", "type", "status"}
WORK_ITEM_TYPES = {"deliverable", "investigation", "evaluation", "operation"}
WORK_ITEM_STATUS = {
    "proposed",
    "active",
    "resolved",
    "abandoned",
}
WORK_ITEM_POLICY_REQUIRED_FIELDS = {
    "id",
    "status",
    "blocked",
    "blocked_reason",
    "resolution",
}

WORK_ITEM_LIST_FIELDS = {
    "contributors",
    "assigned_agents",
    "related_focus",
    "related_roadmap",
    "depends_on",
    "blocked_by",
    "expected_actions",
    "forbidden_actions",
    "acceptance",
    "required_evidence",
    "artifacts_expected",
}


@dataclass(frozen=True)
class ValidationIssue:
    file: str
    severity: str
    code: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class _ParsedArtifact:
    path: Path
    data: dict[str, Any] | None


def validate_project(
    project_root: Path,
    work_items_only: bool = False,
) -> ValidationReport:
    project_root = project_root.resolve()
    issues: list[ValidationIssue] = []

    work_item_files = sorted((project_root / "work_items").glob("**/WI-*.md"))
    work_items = _parse_many(project_root, work_item_files, issues)
    work_item_map: dict[str, _ParsedArtifact] = {}
    work_item_policy_items: list[tuple[Path, dict[str, Any]]] = []
    for artifact in work_items:
        if artifact.data is None:
            continue
        _validate_work_item_schema(project_root, artifact, issues)
        _validate_work_item_policy_required_fields(project_root, artifact, issues)
        work_item_id = artifact.data.get("id")
        if isinstance(work_item_id, str):
            work_item_map[work_item_id] = artifact
        work_item_policy_items.append((artifact.path, artifact.data))

    for policy_issue in work_item_policy.validate_work_item_collection(
        project_root, work_item_policy_items
    ).issues:
        issues.append(
            ValidationIssue(
                file=str(Path(policy_issue.file).resolve().relative_to(project_root)),
                severity=policy_issue.severity,
                code=policy_issue.code,
                message=policy_issue.message,
            )
        )

    if work_items_only:
        return ValidationReport(issues=issues)

    contributor_files = sorted((project_root / "contributors").glob("**/*.md"))
    contributors = _parse_many(project_root, contributor_files, issues)
    contributor_map: dict[str, _ParsedArtifact] = {}

    for artifact in contributors:
        if artifact.data is None:
            continue
        _validate_contributor_schema(project_root, artifact, issues)
        contributor_id = artifact.data.get("id")
        if isinstance(contributor_id, str):
            if contributor_id in contributor_map:
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "error",
                        "DUPLICATE_CONTRIBUTOR_ID",
                        f"duplicate contributor id '{contributor_id}'",
                    )
                )
            else:
                contributor_map[contributor_id] = artifact

    focus_file = project_root / "focus" / "current_focus.md"
    focus_artifacts = _parse_many(project_root, [focus_file], issues)
    focus_ids: set[str] = set()
    for artifact in focus_artifacts:
        if artifact.data is None:
            continue
        _validate_focus_schema(project_root, artifact, issues)
        focus_id = artifact.data.get("id")
        if isinstance(focus_id, str):
            focus_ids.add(focus_id)
        active_contributors = artifact.data.get("active_contributors")
        if active_contributors is not None:
            if not isinstance(active_contributors, list):
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "error",
                        "FOCUS_ACTIVE_CONTRIBUTORS_NOT_LIST",
                        "active_contributors must be a list",
                    )
                )
            else:
                for contributor_id in active_contributors:
                    if not isinstance(contributor_id, str):
                        continue
                    if contributor_id not in contributor_map:
                        issues.append(
                            _issue(
                                project_root,
                                artifact.path,
                                "warning",
                                "FOCUS_UNKNOWN_ACTIVE_CONTRIBUTOR",
                                "active_contributors references unknown contributor "
                                f"'{contributor_id}'",
                            )
                        )

    for artifact in work_items:
        if artifact.data is None:
            continue
        _validate_work_item_references(
            project_root,
            artifact,
            contributor_map,
            work_item_map,
            focus_ids,
            issues,
        )

    return ValidationReport(issues=issues)


def _parse_many(
    project_root: Path,
    files: list[Path],
    issues: list[ValidationIssue],
) -> list[_ParsedArtifact]:
    artifacts: list[_ParsedArtifact] = []
    for path in files:
        data = _parse_markdown_frontmatter(project_root, path, issues)
        artifacts.append(_ParsedArtifact(path=path, data=data))
    return artifacts


def _parse_markdown_frontmatter(
    project_root: Path,
    path: Path,
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "FILE_NOT_FOUND",
                f"required file not found: {path.name}",
            )
        )
        return None

    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "MISSING_FRONTMATTER",
                "markdown file must begin with YAML frontmatter",
            )
        )
        return None

    closing_index = raw.find("\n---\n", 4)
    if closing_index == -1:
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "MALFORMED_FRONTMATTER",
                "could not find closing frontmatter delimiter '---'",
            )
        )
        return None

    frontmatter_text = raw[4:closing_index]
    try:
        data = _parse_simple_yaml(frontmatter_text)
    except ValueError as exc:
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "YAML_PARSE_ERROR",
                f"invalid YAML in frontmatter: {exc}",
            )
        )
        return None

    if not isinstance(data, dict):
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "FRONTMATTER_NOT_OBJECT",
                "frontmatter must parse to a mapping object",
            )
        )
        return None

    return data


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    folded_key: str | None = None
    folded_lines: list[str] = []

    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue

        if folded_key is not None:
            if line.startswith("  ") or line.startswith("\t"):
                folded_lines.append(stripped)
                continue
            data[folded_key] = " ".join(folded_lines).strip()
            folded_key = None
            folded_lines = []

        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValueError("list item found without a list field")
            data[current_list_key].append(stripped[2:].strip())
            continue

        if ":" not in stripped:
            raise ValueError(f"malformed line: {stripped}")

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_list_key = None

        if not key:
            raise ValueError("empty key in frontmatter")

        if value == "":
            data[key] = []
            current_list_key = key
            continue
        if value == ">":
            folded_key = key
            folded_lines = []
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                data[key] = []
            else:
                data[key] = [part.strip() for part in inner.split(",")]
            continue

        parsed_scalar = value.strip("'\"")
        if parsed_scalar in {"null", "Null", "NULL", "~"}:
            data[key] = None
            continue
        if parsed_scalar in {"true", "True", "TRUE"}:
            data[key] = True
            continue
        if parsed_scalar in {"false", "False", "FALSE"}:
            data[key] = False
            continue
        data[key] = parsed_scalar

    if folded_key is not None:
        data[folded_key] = " ".join(folded_lines).strip()

    return data


def _validate_contributor_schema(
    project_root: Path,
    artifact: _ParsedArtifact,
    issues: list[ValidationIssue],
) -> None:
    data = artifact.data or {}
    _require_fields(
        project_root, artifact.path, data, CONTRIBUTOR_REQUIRED_FIELDS, issues
    )

    _validate_enum(
        project_root,
        artifact.path,
        data,
        "type",
        CONTRIBUTOR_TYPES,
        "CONTRIBUTOR_TYPE_INVALID",
        issues,
    )
    _validate_enum(
        project_root,
        artifact.path,
        data,
        "status",
        CONTRIBUTOR_STATUS,
        "CONTRIBUTOR_STATUS_INVALID",
        issues,
    )

    roles = data.get("roles")
    if (
        not isinstance(roles, list)
        or not roles
        or not all(isinstance(role, str) for role in roles)
    ):
        issues.append(
            _issue(
                project_root,
                artifact.path,
                "error",
                "CONTRIBUTOR_ROLES_INVALID",
                "roles must be a non-empty list of strings",
            )
        )
    else:
        invalid_roles = sorted(set(roles) - CONTRIBUTOR_ROLES)
        if invalid_roles:
            issues.append(
                _issue(
                    project_root,
                    artifact.path,
                    "error",
                    "CONTRIBUTOR_ROLE_INVALID",
                    f"invalid role(s): {', '.join(invalid_roles)}",
                )
            )

    if data.get("type") == "agent":
        execution_mode = data.get("execution_mode")
        if execution_mode is None:
            issues.append(
                _issue(
                    project_root,
                    artifact.path,
                    "warning",
                    "AGENT_EXECUTION_MODE_MISSING",
                    "agent contributor is missing execution_mode",
                )
            )
        elif execution_mode not in AGENT_EXECUTION_MODES:
            issues.append(
                _issue(
                    project_root,
                    artifact.path,
                    "error",
                    "AGENT_EXECUTION_MODE_INVALID",
                    f"invalid execution_mode '{execution_mode}'",
                )
            )


def _validate_focus_schema(
    project_root: Path,
    artifact: _ParsedArtifact,
    issues: list[ValidationIssue],
) -> None:
    data = artifact.data or {}
    _require_fields(project_root, artifact.path, data, FOCUS_REQUIRED_FIELDS, issues)
    _validate_enum(
        project_root,
        artifact.path,
        data,
        "status",
        FOCUS_STATUS,
        "FOCUS_STATUS_INVALID",
        issues,
    )


def _validate_work_item_schema(
    project_root: Path,
    artifact: _ParsedArtifact,
    issues: list[ValidationIssue],
) -> None:
    data = artifact.data or {}
    _require_fields(
        project_root, artifact.path, data, WORK_ITEM_REQUIRED_FIELDS, issues
    )
    _validate_enum(
        project_root,
        artifact.path,
        data,
        "type",
        WORK_ITEM_TYPES,
        "WORK_ITEM_TYPE_INVALID",
        issues,
    )
    _validate_enum(
        project_root,
        artifact.path,
        data,
        "status",
        WORK_ITEM_STATUS,
        "WORK_ITEM_STATUS_INVALID",
        issues,
    )

    for field in sorted(WORK_ITEM_LIST_FIELDS):
        if field in data and not isinstance(data[field], list):
            issues.append(
                _issue(
                    project_root,
                    artifact.path,
                    "error",
                    "WORK_ITEM_LIST_FIELD_INVALID",
                    f"{field} must be a list",
                )
            )


def _validate_work_item_policy_required_fields(
    project_root: Path,
    artifact: _ParsedArtifact,
    issues: list[ValidationIssue],
) -> None:
    data = artifact.data or {}
    _require_fields(
        project_root,
        artifact.path,
        data,
        WORK_ITEM_POLICY_REQUIRED_FIELDS,
        issues,
    )


def _validate_work_item_references(
    project_root: Path,
    artifact: _ParsedArtifact,
    contributor_map: dict[str, _ParsedArtifact],
    work_item_map: dict[str, _ParsedArtifact],
    focus_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    data = artifact.data or {}

    owner = data.get("owner")
    owner_data = None
    if owner is not None:
        owner_data = _contributor_data(
            project_root,
            artifact.path,
            contributor_map,
            owner,
            "owner",
            issues,
        )
        if owner_data and owner_data.get("type") != "human":
            issues.append(
                _issue(
                    project_root,
                    artifact.path,
                    "error",
                    "OWNER_NOT_HUMAN",
                    f"owner '{owner}' refers to a non-human contributor",
                )
            )
        if owner_data:
            owner_roles = owner_data.get("roles")
            if isinstance(owner_roles, list) and not (
                {"admin", "editor"} & set(owner_roles)
            ):
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "warning",
                        "OWNER_ROLE_INSUFFICIENT",
                        f"owner '{owner}' lacks a typical ownership role "
                        "(admin/editor)",
                    )
                )

    contributors = data.get("contributors")
    if contributors is not None and isinstance(contributors, list):
        for contributor_id in contributors:
            _contributor_data(
                project_root,
                artifact.path,
                contributor_map,
                contributor_id,
                "contributors",
                issues,
            )

    assigned_agents = data.get("assigned_agents")
    if assigned_agents is not None and isinstance(assigned_agents, list):
        for contributor_id in assigned_agents:
            contributor_data = _contributor_data(
                project_root,
                artifact.path,
                contributor_map,
                contributor_id,
                "assigned_agents",
                issues,
            )
            if not contributor_data:
                continue
            if contributor_data.get("type") != "agent":
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "error",
                        "ASSIGNED_AGENT_NOT_AGENT",
                        "assigned_agents references non-agent contributor "
                        f"'{contributor_id}'",
                    )
                )
                continue
            roles = contributor_data.get("roles")
            if isinstance(roles, list) and "editor" not in roles:
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "warning",
                        "ASSIGNED_AGENT_ROLE_INSUFFICIENT",
                        f"assigned agent '{contributor_id}' lacks a typical "
                        "execution role (editor)",
                    )
                )
            if contributor_data.get("execution_mode") == "human_orchestrated":
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "warning",
                        "ASSIGNED_AGENT_HUMAN_ORCHESTRATED",
                        f"assigned agent '{contributor_id}' is human_orchestrated",
                    )
                )
            if contributor_data.get("status") == "inactive":
                issues.append(
                    _issue(
                        project_root,
                        artifact.path,
                        "warning",
                        "ASSIGNED_AGENT_INACTIVE",
                        f"assigned agent '{contributor_id}' is inactive",
                    )
                )

    if (
        owner is not None
        and isinstance(contributors, list)
        and owner not in contributors
    ):
        issues.append(
            _issue(
                project_root,
                artifact.path,
                "warning",
                "OWNER_NOT_IN_CONTRIBUTORS",
                f"owner '{owner}' is not listed in contributors",
            )
        )

    _validate_relation_field(
        project_root,
        artifact.path,
        data,
        "depends_on",
        set(work_item_map),
        "UNKNOWN_DEPENDENCY",
        issues,
    )
    _validate_relation_field(
        project_root,
        artifact.path,
        data,
        "blocked_by",
        set(work_item_map),
        "UNKNOWN_BLOCKER",
        issues,
    )
    _validate_relation_field(
        project_root,
        artifact.path,
        data,
        "related_focus",
        focus_ids,
        "UNKNOWN_RELATED_FOCUS",
        issues,
    )


def _validate_relation_field(
    project_root: Path,
    path: Path,
    data: dict[str, Any],
    field: str,
    known_values: set[str],
    issue_code: str,
    issues: list[ValidationIssue],
) -> None:
    values = data.get(field)
    if not isinstance(values, list):
        return
    for value in values:
        if isinstance(value, str) and value not in known_values:
            issues.append(
                _issue(
                    project_root,
                    path,
                    "error",
                    issue_code,
                    f"{field} references unknown id '{value}'",
                )
            )


def _contributor_data(
    project_root: Path,
    path: Path,
    contributor_map: dict[str, _ParsedArtifact],
    contributor_id: Any,
    field_name: str,
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    if not isinstance(contributor_id, str):
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                "CONTRIBUTOR_REFERENCE_INVALID",
                f"{field_name} contains a non-string contributor reference",
            )
        )
        return None

    contributor = contributor_map.get(contributor_id)
    if contributor is None:
        code = {
            "owner": "UNKNOWN_OWNER",
            "contributors": "UNKNOWN_CONTRIBUTOR",
            "assigned_agents": "UNKNOWN_ASSIGNED_AGENT",
        }.get(field_name, "UNKNOWN_CONTRIBUTOR_REFERENCE")
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                code,
                f"{field_name} references unknown contributor '{contributor_id}'",
            )
        )
        return None
    return contributor.data


def _require_fields(
    project_root: Path,
    path: Path,
    data: dict[str, Any],
    required_fields: set[str],
    issues: list[ValidationIssue],
) -> None:
    for field in sorted(required_fields):
        if field not in data:
            issues.append(
                _issue(
                    project_root,
                    path,
                    "error",
                    "MISSING_REQUIRED_FIELD",
                    f"missing required field '{field}'",
                )
            )


def _validate_enum(
    project_root: Path,
    path: Path,
    data: dict[str, Any],
    field: str,
    valid_values: set[str],
    issue_code: str,
    issues: list[ValidationIssue],
) -> None:
    value = data.get(field)
    if value is None:
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                issue_code,
                f"invalid value 'null' for {field}",
            )
        )
        return
    if value not in valid_values:
        issues.append(
            _issue(
                project_root,
                path,
                "error",
                issue_code,
                f"invalid value '{value}' for {field}",
            )
        )


def _issue(
    project_root: Path,
    path: Path,
    severity: str,
    code: str,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        file=str(path.resolve().relative_to(project_root.resolve())),
        severity=severity,
        code=code,
        message=message,
    )


def format_report(report: ValidationReport) -> str:
    lines = [
        "Validation completed: "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
    ]

    if report.errors:
        lines.append("\nErrors:")
        for issue in report.errors:
            lines.append(f"- [{issue.code}] {issue.file}: {issue.message}")

    if report.warnings:
        lines.append("\nWarnings:")
        for issue in report.warnings:
            lines.append(f"- [{issue.code}] {issue.file}: {issue.message}")

    return "\n".join(lines)

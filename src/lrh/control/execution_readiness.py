"""Typed interpretation and validation for opt-in execution readiness metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

READINESS_FIELDS = {
    "execution_ready",
    "autonomy_level",
    "operation_risk",
    "allowed_paths",
    "forbidden_paths",
    "validation_commands",
    "required_evidence",
    "expected_artifacts",
    "max_review_rounds",
    "max_ci_rounds",
    "requires_human_approval",
    "requires_human_merge",
    "requires_human_closeout",
    "policy_gates",
    "agent_constraints",
}
OPT_IN_FIELDS = READINESS_FIELDS - {"required_evidence"}
REQUIRED_READY_FIELDS = {
    "execution_ready",
    "autonomy_level",
    "operation_risk",
    "allowed_paths",
    "validation_commands",
    "required_evidence",
}
LIST_FIELDS = {
    "allowed_paths",
    "forbidden_paths",
    "validation_commands",
    "required_evidence",
    "expected_artifacts",
    "policy_gates",
    "agent_constraints",
}
BOOLEAN_FIELDS = {
    "execution_ready",
    "requires_human_approval",
    "requires_human_merge",
    "requires_human_closeout",
}
INTEGER_FIELDS = {
    "max_review_rounds",
    "max_ci_rounds",
}
AUTONOMY_LEVELS = {
    "manual",
    "human_gated",
    "bounded_auto",
    "sequential_bounded",
}
OPERATION_RISKS = {
    "read_only",
    "safe_local",
    "branch_mutating",
    "repo_mutating",
    "external_side_effect",
    "destructive",
}


@dataclass(frozen=True)
class ExecutionReadiness:
    """Safe-default readiness interpretation for one work item."""

    execution_ready: bool
    autonomy_level: str | None
    operation_risk: str | None
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    validation_commands: tuple[str, ...]
    required_evidence: tuple[str, ...]
    expected_artifacts: tuple[str, ...]
    max_review_rounds: int | None
    max_ci_rounds: int | None
    requires_human_approval: bool
    requires_human_merge: bool
    requires_human_closeout: bool
    policy_gates: tuple[str, ...]
    agent_constraints: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionReadinessIssue:
    """Deterministic readiness validation issue."""

    path: Path
    severity: str
    code: str
    message: str


def has_readiness_metadata(frontmatter: dict[str, Any]) -> bool:
    """Return whether frontmatter opted into readiness interpretation."""

    return any(field in frontmatter for field in OPT_IN_FIELDS)


def from_frontmatter(frontmatter: dict[str, Any]) -> ExecutionReadiness | None:
    """Build typed readiness from source frontmatter when explicitly present.

    Missing human gates default to ``True`` so consumers remain safe by default
    even before strict validation reports missing or malformed fields.
    """

    if not has_readiness_metadata(frontmatter):
        return None

    return ExecutionReadiness(
        execution_ready=_bool_value(frontmatter, "execution_ready", default=False),
        autonomy_level=_str_value(frontmatter, "autonomy_level"),
        operation_risk=_str_value(frontmatter, "operation_risk"),
        allowed_paths=_string_tuple(frontmatter, "allowed_paths"),
        forbidden_paths=_string_tuple(frontmatter, "forbidden_paths"),
        validation_commands=_string_tuple(frontmatter, "validation_commands"),
        required_evidence=_string_tuple(frontmatter, "required_evidence"),
        expected_artifacts=_string_tuple(frontmatter, "expected_artifacts"),
        max_review_rounds=_int_value(frontmatter, "max_review_rounds"),
        max_ci_rounds=_int_value(frontmatter, "max_ci_rounds"),
        requires_human_approval=_bool_value(
            frontmatter, "requires_human_approval", default=True
        ),
        requires_human_merge=_bool_value(
            frontmatter, "requires_human_merge", default=True
        ),
        requires_human_closeout=_bool_value(
            frontmatter, "requires_human_closeout", default=True
        ),
        policy_gates=_string_tuple(frontmatter, "policy_gates"),
        agent_constraints=_string_tuple(frontmatter, "agent_constraints"),
    )


def validate_frontmatter(
    path: Path,
    frontmatter: dict[str, Any],
    *,
    require_ready: bool = False,
) -> tuple[ExecutionReadinessIssue, ...]:
    """Validate readiness metadata when a work item opts in.

    Ordinary work items with no readiness fields return no diagnostics. Passing
    ``require_ready=True`` lets future packet generation validate a selected leaf
    as executable even when no readiness fields have been declared yet.
    """

    if not require_ready and not has_readiness_metadata(frontmatter):
        return ()

    issues: list[ExecutionReadinessIssue] = []
    readiness = from_frontmatter(frontmatter)
    if readiness is None:
        readiness = from_frontmatter({"execution_ready": False})

    _validate_field_types(path, frontmatter, issues)

    if frontmatter.get("execution_ready") is not True:
        issues.append(
            ExecutionReadinessIssue(
                path=path,
                severity="error",
                code="EXECUTION_READINESS_NOT_READY",
                message="execution_ready must be true for an executable leaf",
            )
        )
        return _sorted_issues(issues)

    for field in sorted(REQUIRED_READY_FIELDS - {"execution_ready"}):
        if field not in frontmatter:
            issues.append(
                ExecutionReadinessIssue(
                    path=path,
                    severity="error",
                    code="EXECUTION_READINESS_REQUIRED_FIELD_MISSING",
                    message=f"missing execution-readiness field '{field}'",
                )
            )

    _validate_enum(
        path,
        frontmatter,
        "autonomy_level",
        AUTONOMY_LEVELS,
        "EXECUTION_READINESS_AUTONOMY_LEVEL_INVALID",
        issues,
    )
    _validate_enum(
        path,
        frontmatter,
        "operation_risk",
        OPERATION_RISKS,
        "EXECUTION_READINESS_OPERATION_RISK_INVALID",
        issues,
    )
    _validate_non_empty_string_list(
        path,
        readiness.allowed_paths,
        "allowed_paths",
        issues,
    )
    _validate_non_empty_string_list(
        path,
        readiness.validation_commands,
        "validation_commands",
        issues,
    )
    _validate_non_empty_string_list(
        path,
        readiness.required_evidence,
        "required_evidence",
        issues,
    )
    _validate_positive_integer(path, frontmatter, "max_review_rounds", issues)
    _validate_positive_integer(path, frontmatter, "max_ci_rounds", issues)

    return _sorted_issues(issues)


def _validate_field_types(
    path: Path,
    frontmatter: dict[str, Any],
    issues: list[ExecutionReadinessIssue],
) -> None:
    for field in sorted(LIST_FIELDS):
        if field in frontmatter and not _is_string_list(frontmatter[field]):
            issues.append(
                ExecutionReadinessIssue(
                    path=path,
                    severity="error",
                    code="EXECUTION_READINESS_LIST_FIELD_INVALID",
                    message=f"{field} must be a list of strings",
                )
            )
    for field in sorted(BOOLEAN_FIELDS):
        if field in frontmatter and not isinstance(frontmatter[field], bool):
            issues.append(
                ExecutionReadinessIssue(
                    path=path,
                    severity="error",
                    code="EXECUTION_READINESS_BOOLEAN_FIELD_INVALID",
                    message=f"{field} must be true or false",
                )
            )
    for field in sorted(INTEGER_FIELDS):
        if field in frontmatter and not _is_integer(frontmatter[field]):
            issues.append(
                ExecutionReadinessIssue(
                    path=path,
                    severity="error",
                    code="EXECUTION_READINESS_INTEGER_FIELD_INVALID",
                    message=f"{field} must be an integer",
                )
            )


def _validate_enum(
    path: Path,
    frontmatter: dict[str, Any],
    field: str,
    allowed_values: set[str],
    code: str,
    issues: list[ExecutionReadinessIssue],
) -> None:
    if field not in frontmatter:
        return
    value = frontmatter[field]
    if not isinstance(value, str) or value not in allowed_values:
        issues.append(
            ExecutionReadinessIssue(
                path=path,
                severity="error",
                code=code,
                message=f"{field} must be one of {', '.join(sorted(allowed_values))}",
            )
        )


def _validate_non_empty_string_list(
    path: Path,
    values: tuple[str, ...],
    field: str,
    issues: list[ExecutionReadinessIssue],
) -> None:
    if values:
        return
    issues.append(
        ExecutionReadinessIssue(
            path=path,
            severity="error",
            code="EXECUTION_READINESS_REQUIRED_LIST_EMPTY",
            message=f"{field} must contain at least one string",
        )
    )


def _validate_positive_integer(
    path: Path,
    frontmatter: dict[str, Any],
    field: str,
    issues: list[ExecutionReadinessIssue],
) -> None:
    if field not in frontmatter:
        return
    value = frontmatter[field]
    if not _is_integer(value):
        return
    if value >= 1:
        return
    issues.append(
        ExecutionReadinessIssue(
            path=path,
            severity="error",
            code="EXECUTION_READINESS_INTEGER_FIELD_INVALID",
            message=f"{field} must be an integer greater than or equal to 1",
        )
    )


def _sorted_issues(
    issues: list[ExecutionReadinessIssue],
) -> tuple[ExecutionReadinessIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.severity,
                issue.code,
                issue.path.as_posix(),
                issue.message,
            ),
        )
    )


def _str_value(frontmatter: dict[str, Any], field: str) -> str | None:
    value = frontmatter.get(field)
    if isinstance(value, str):
        return value
    return None


def _bool_value(frontmatter: dict[str, Any], field: str, *, default: bool) -> bool:
    value = frontmatter.get(field)
    if isinstance(value, bool):
        return value
    return default


def _int_value(frontmatter: dict[str, Any], field: str) -> int | None:
    value = frontmatter.get(field)
    if _is_integer(value):
        return value
    return None


def _string_tuple(frontmatter: dict[str, Any], field: str) -> tuple[str, ...]:
    value = frontmatter.get(field)
    if not _is_string_list(value):
        return ()
    return tuple(value)


def _is_integer(value: Any) -> bool:
    return type(value) is int


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)

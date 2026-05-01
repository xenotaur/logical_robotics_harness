"""Project bootstrap diagnostics for LRH prompt-workflow readiness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class Diagnosis:
    findings: list[Finding]

    def has_errors(self) -> bool:
        return any(finding.severity == "error" for finding in self.findings)

    def has_warnings(self) -> bool:
        return any(finding.severity == "warning" for finding in self.findings)


def _check_path(findings: list[Finding], root: Path, relative_path: str) -> bool:
    target = root / relative_path
    exists = target.exists()
    if exists:
        findings.append(
            Finding(
                severity="info",
                code="present",
                path=relative_path,
                message=f"present: {relative_path}",
            )
        )
    else:
        findings.append(
            Finding(
                severity="error",
                code="missing_required",
                path=relative_path,
                message=f"missing required path: {relative_path}",
            )
        )
    return exists


def _check_optional_path(findings: list[Finding], root: Path, relative_path: str) -> None:
    target = root / relative_path
    if target.exists():
        findings.append(
            Finding(
                severity="info",
                code="present",
                path=relative_path,
                message=f"present: {relative_path}",
            )
        )
    else:
        findings.append(
            Finding(
                severity="warning",
                code="missing_recommended",
                path=relative_path,
                message=f"missing recommended path: {relative_path}",
            )
        )


def diagnose_project(project_root: Path) -> Diagnosis:
    root = project_root.expanduser().resolve()
    findings: list[Finding] = []

    required_paths = [
        "project",
        "project/principles",
        "project/goal",
        "project/roadmap",
        "project/focus",
        "project/work_items",
        "project/evidence",
        "project/status",
        "project/executions",
        "project/executions/README.md",
        "PROMPTS.md",
    ]
    for relative_path in required_paths:
        _check_path(findings, root, relative_path)

    recommended_paths = [
        "AGENTS.md",
        "STYLE.md",
        "scripts/test",
        "scripts/lint",
        "scripts/format",
    ]
    for relative_path in recommended_paths:
        _check_optional_path(findings, root, relative_path)

    missing_required_paths = {
        finding.path
        for finding in findings
        if finding.code == "missing_required"
    }
    if missing_required_paths:
        common_paths = {
            "project",
            "project/principles",
            "project/goal",
            "project/roadmap",
            "project/focus",
            "project/work_items",
            "project/evidence",
            "project/status",
        }
        prompt_workflow_paths = {
            "PROMPTS.md",
            "project/executions",
            "project/executions/README.md",
        }

        missing_common = bool(common_paths & missing_required_paths)
        missing_prompt_workflow = bool(prompt_workflow_paths & missing_required_paths)

        if missing_common and missing_prompt_workflow:
            profile = "full"
        elif missing_common:
            profile = "minimal"
        else:
            profile = "prompt-workflow"

        findings.append(
            Finding(
                severity="info",
                code="recommended_next_step",
                path=".",
                message=(
                    "scaffolding is incomplete; run: "
                    f"lrh project init --profile {profile} "
                    f"--project-root {root}"
                ),
            )
        )

    return Diagnosis(findings=findings)


def format_text_report(diagnosis: Diagnosis) -> str:
    lines = ["lrh project doctor report"]
    for finding in diagnosis.findings:
        lines.append(
            f"{finding.severity.upper():7} [{finding.code}] "
            f"{finding.path} :: {finding.message}"
        )
    return "\n".join(lines)


def format_json_report(diagnosis: Diagnosis) -> str:
    payload = {
        "findings": [
            {
                "severity": finding.severity,
                "code": finding.code,
                "path": finding.path,
                "message": finding.message,
            }
            for finding in diagnosis.findings
        ]
    }
    return json.dumps(payload, indent=2, sort_keys=True)

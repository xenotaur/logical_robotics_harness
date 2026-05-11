"""CLI adapter for snapshot context packet workflows."""

from __future__ import annotations

import argparse
import pathlib
import sys

from lrh import version as lrh_version
from lrh.control import loader as control_loader
from lrh.control import models as control_models
from lrh.control import planning_tree as control_planning_tree
from lrh.control import validator as control_validator


def build_parser(*, prog: str = "snapshot") -> argparse.ArgumentParser:
    """Build the snapshot CLI parser."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project-root",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="Repository root or project directory (default: current directory).",
    )
    common.add_argument(
        "--output",
        type=pathlib.Path,
        help="Write output to this file path.",
    )
    common.add_argument(
        "--stdout",
        action="store_true",
        help="Also print generated context packet to stdout.",
    )
    common.add_argument(
        "--include-status",
        action="store_true",
        help="Include project/status/current_status.md when it exists.",
    )
    common.add_argument(
        "--include-guardrails",
        action="store_true",
        help="Include summaries from project/guardrails/ when files exist.",
    )
    common.add_argument(
        "--include-design",
        action="store_true",
        help="Include project/design/design.md when it exists.",
    )

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Generate Markdown context packets from project control files.",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="scope", required=True)
    subparsers.add_parser(
        "project", parents=[common], help="Generate project-wide context."
    )
    subparsers.add_parser(
        "current_focus", parents=[common], help="Generate current-focus context."
    )

    work_item_parser = subparsers.add_parser(
        "work_item", parents=[common], help="Generate context for a specific work item."
    )
    work_item_parser.add_argument(
        "work_item_id", help="Work item identifier (for example WI-0003)."
    )
    return parser


_DESIGN_PROPOSAL_IMPLEMENTATION_ORDER = (
    "implemented",
    "partial",
    "not_started",
    "deferred",
    "obsolete",
)


def _canonical_design_proposal_status(status: str) -> str:
    if status == "accepted":
        return "adopted"
    return status


def _proposal_label(proposal: control_models.DesignProposal) -> str:
    title = proposal.title
    if title:
        return f"{proposal.id} {title}"
    return proposal.id


def _format_traceability_line(label: str, references: tuple[str, ...]) -> str | None:
    if not references:
        return None
    return f"    - {label}: {', '.join(sorted(references))}"


def _format_design_proposal_item(
    proposal: control_models.DesignProposal,
    *,
    include_traceability: bool,
) -> list[str]:
    lines = [f"  - {_proposal_label(proposal)}"]
    if include_traceability:
        implemented_by = _format_traceability_line(
            "implemented_by", proposal.implemented_by
        )
        evidence = _format_traceability_line("evidence", proposal.evidence)
        if implemented_by is not None:
            lines.append(implemented_by)
        if evidence is not None:
            lines.append(evidence)
    return lines


_WORKSTREAM_STATUS_ORDER = ("proposed", "active", "resolved", "abandoned")


def summarize_workstreams(project_dir: pathlib.Path) -> str:
    """Summarize workstream lifecycle state for read-only snapshots."""
    try:
        workstreams = control_loader.load_workstreams(project_dir)
    except (FileNotFoundError, ValueError) as error:
        return "\n".join(
            [
                "Workstreams:",
                *[f"  {status}: 0" for status in _WORKSTREAM_STATUS_ORDER],
                "",
                "Warnings:",
                f"  - Could not load workstreams: {error}",
            ]
        )

    work_items = _load_snapshot_work_items(project_dir)
    relationship_index = control_planning_tree.build_planning_tree_from_artifacts(
        workstreams=workstreams,
        work_items=work_items,
    )

    counts = {status: 0 for status in _WORKSTREAM_STATUS_ORDER}
    other_statuses: dict[str, int] = {}
    for workstream in workstreams:
        if workstream.status in counts:
            counts[workstream.status] += 1
        else:
            other_statuses[workstream.status] = (
                other_statuses.get(workstream.status, 0) + 1
            )

    lines = ["Workstreams:"]
    lines.extend(f"  {status}: {counts[status]}" for status in _WORKSTREAM_STATUS_ORDER)
    for status in sorted(other_statuses):
        lines.append(f"  {status}: {other_statuses[status]}")

    active_workstreams = sorted(
        (workstream for workstream in workstreams if workstream.status == "active"),
        key=lambda workstream: workstream.id,
    )
    if active_workstreams:
        lines.extend(["", "Active workstreams:"])
        for workstream in active_workstreams:
            lines.extend(_format_active_workstream(workstream, relationship_index))

    diagnostics = _workstream_snapshot_diagnostics(project_dir, relationship_index)
    if diagnostics:
        lines.extend(["", "Warnings:"])
        lines.extend(f"  - {diagnostic}" for diagnostic in diagnostics)

    return "\n".join(lines)


def _load_snapshot_work_items(
    project_dir: pathlib.Path,
) -> tuple[control_models.WorkItem, ...]:
    work_items: list[control_models.WorkItem] = []
    for path in list_work_items(project_dir):
        text = read_text_if_exists(path)
        if text is None:
            continue
        frontmatter, body = parse_frontmatter(text)
        work_item_id = frontmatter.get("id")
        title = frontmatter.get("title")
        item_type = frontmatter.get("type")
        status = frontmatter.get("status")
        if not all(
            isinstance(value, str) for value in (work_item_id, title, item_type, status)
        ):
            continue
        work_items.append(
            control_models.WorkItem(
                path=path,
                id=work_item_id,
                title=title,
                type=item_type,
                status=status,
                priority=_optional_frontmatter_str(frontmatter, "priority"),
                owner=_optional_frontmatter_str(frontmatter, "owner"),
                parent_id=_optional_frontmatter_str(frontmatter, "parent_id"),
                body=body,
                frontmatter=frontmatter,
            )
        )
    return tuple(work_items)


def _optional_frontmatter_str(
    frontmatter: dict[str, object],
    field: str,
) -> str | None:
    value = frontmatter.get(field)
    if isinstance(value, str):
        return value
    return None


def _format_active_workstream(
    workstream: control_models.Workstream,
    relationship_index: control_planning_tree.PlanningTreeIndex,
) -> list[str]:
    lines = [f"  {workstream.id} — {workstream.title}"]
    lines.append(f"    stage: {workstream.stage}")
    lines.append(f"    status: {workstream.status}")

    children = relationship_index.children_of(workstream.id)
    if children:
        work_item_count = sum(
            1
            for child_id in children
            if relationship_index.artifacts_by_id[child_id].kind
            == control_planning_tree.ARTIFACT_WORK_ITEM
        )
        lines.append(f"    children: {len(children)}")
        lines.append(f"    work_items: {work_item_count}")
    return lines


def _workstream_snapshot_diagnostics(
    project_dir: pathlib.Path,
    relationship_index: control_planning_tree.PlanningTreeIndex,
) -> list[str]:
    diagnostics: list[str] = []
    for diagnostic in relationship_index.diagnostics:
        diagnostics.append(
            f"{diagnostic.code}: {diagnostic.path}: {diagnostic.message}"
        )

    validation_report = control_validator.validate_project(project_dir)
    for issue in validation_report.issues:
        if issue.code.startswith("WORKSTREAM_") or issue.code.startswith("PLANNING_"):
            diagnostics.append(f"{issue.code}: {issue.file}: {issue.message}")

    return sorted(dict.fromkeys(diagnostics))


def summarize_design_proposals(project_dir: pathlib.Path) -> str:
    """Summarize design proposal lifecycle and implementation state."""
    loaded_proposals, load_warnings = (
        control_loader.load_design_proposals_from_project_dir_permissive(project_dir)
    )
    proposals = sorted(
        loaded_proposals,
        key=lambda proposal: proposal.id,
    )
    if not proposals:
        if load_warnings:
            warning_lines = ["- Warnings:"]
            warning_lines.extend(f"  - {warning}" for warning in load_warnings)
            return "\n".join(warning_lines)
        return "- No design proposals found."

    lines: list[str] = []
    for implementation_status in _DESIGN_PROPOSAL_IMPLEMENTATION_ORDER:
        matching = [
            proposal
            for proposal in proposals
            if _canonical_design_proposal_status(proposal.status) == "adopted"
            and proposal.implementation_status == implementation_status
        ]
        if not matching:
            continue
        if lines:
            lines.append("")
        lines.append(f"- Adopted / {implementation_status}:")
        include_traceability = implementation_status in {"partial", "implemented"}
        for proposal in matching:
            lines.extend(
                _format_design_proposal_item(
                    proposal,
                    include_traceability=include_traceability,
                )
            )

    unspecified = [
        proposal
        for proposal in proposals
        if _canonical_design_proposal_status(proposal.status) == "adopted"
        and proposal.implementation_status is None
    ]
    if unspecified:
        if lines:
            lines.append("")
        lines.append("- Adopted / unspecified:")
        for proposal in unspecified:
            lines.extend(
                _format_design_proposal_item(
                    proposal,
                    include_traceability=False,
                )
            )

    superseded = [
        proposal
        for proposal in proposals
        if _canonical_design_proposal_status(proposal.status) == "superseded"
    ]
    if superseded:
        if lines:
            lines.append("")
        lines.append("- Superseded:")
        for proposal in superseded:
            line = f"  - {_proposal_label(proposal)}"
            if proposal.superseded_by:
                line = f"{line} -> {proposal.superseded_by}"
            lines.append(line)

    warnings = [
        *load_warnings,
        *_design_proposal_traceability_warnings(proposals),
    ]
    if warnings:
        if lines:
            lines.append("")
        lines.append("- Warnings:")
        lines.extend(f"  - {warning}" for warning in warnings)

    if not lines:
        return "- No adopted or superseded design proposals found."
    return "\n".join(lines)


def _design_proposal_traceability_warnings(
    proposals: list[control_models.DesignProposal],
) -> list[str]:
    warnings: list[str] = []
    for proposal in proposals:
        status = _canonical_design_proposal_status(proposal.status)
        if status == "adopted" and proposal.implementation_status is None:
            warnings.append(
                f"{proposal.id} is adopted but has no implementation_status."
            )
        if (
            proposal.implementation_status == "implemented"
            and not proposal.implemented_by
            and not proposal.evidence
        ):
            warnings.append(
                f"{proposal.id} claims implementation_status=implemented "
                "but has no evidence or implemented_by references."
            )
        if status == "superseded" and proposal.superseded_by is None:
            warnings.append(f"{proposal.id} is superseded but has no superseded_by.")
    return warnings


def find_project_dir(project_root: pathlib.Path) -> pathlib.Path:
    root = project_root.resolve()
    if (root / "project").is_dir():
        return root / "project"
    if root.name == "project" and root.is_dir():
        return root
    raise FileNotFoundError(f"Missing required project directory under: {root}")


def read_text_if_exists(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("\n---\n", maxsplit=1)
    if len(parts) != 2:
        return {}, text

    header, body = parts
    frontmatter_lines = header.splitlines()[1:]
    data: dict[str, object] = {}
    current_key: str | None = None

    for line in frontmatter_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("  - ") and current_key:
            existing = data.get(current_key)
            if not isinstance(existing, list):
                existing = []
                data[current_key] = existing
            existing.append(stripped[2:].strip())
            continue
        if ":" in line:
            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_key = None
            else:
                data[key] = []
                current_key = key

    return data, body.strip()


def first_body_lines(text: str, max_lines: int = 8) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "(No body content.)"
    sample = lines[:max_lines]
    if len(lines) > max_lines:
        sample.append("...")
    return "\n".join(sample)


def list_markdown_files(path: pathlib.Path) -> list[pathlib.Path]:
    if not path.is_dir():
        return []
    return sorted(path.glob("*.md"))


def summarize_file(path: pathlib.Path, required: bool = False) -> str:
    text = read_text_if_exists(path)
    if text is None:
        if required:
            raise FileNotFoundError(f"Missing required file: {path}")
        return f"- `{path}`: not found."

    frontmatter, body = parse_frontmatter(text)
    lines = [f"- `{path}`"]
    for key in ("id", "title", "status", "priority", "owner"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value:
            lines.append(f"  - {key}: {value}")
    lines.append("  - summary:")
    for body_line in first_body_lines(body).splitlines():
        lines.append(f"    {body_line}")
    return "\n".join(lines)


def list_work_items(project_dir: pathlib.Path) -> list[pathlib.Path]:
    work_items_dir = project_dir / "work_items"
    if not work_items_dir.is_dir():
        return []
    return sorted(work_items_dir.glob("**/WI-*.md"))


def current_focus_frontmatter(
    project_dir: pathlib.Path,
) -> tuple[dict[str, object], str]:
    focus_path = project_dir / "focus" / "current_focus.md"
    focus_text = read_text_if_exists(focus_path)
    if focus_text is None:
        raise FileNotFoundError(f"Missing required file: {focus_path}")
    return parse_frontmatter(focus_text)


def relevant_work_items(project_dir: pathlib.Path) -> tuple[list[pathlib.Path], str]:
    focus_meta, _ = current_focus_frontmatter(project_dir)
    focus_id = focus_meta.get("id")
    items = list_work_items(project_dir)

    if not isinstance(focus_id, str):
        return items, "Focus id not detected; including all work items."

    matching: list[pathlib.Path] = []
    for item_path in items:
        text = read_text_if_exists(item_path) or ""
        meta, _ = parse_frontmatter(text)
        related_focus = meta.get("related_focus")
        if isinstance(related_focus, list) and focus_id in related_focus:
            matching.append(item_path)

    if matching:
        return (
            matching,
            f"Filtered work items by related_focus containing `{focus_id}`.",
        )

    return items, (
        f"No work item related_focus match for `{focus_id}`; including all work items "
        "(version 1 fallback)."
    )


def resolve_work_item(project_dir: pathlib.Path, work_item_id: str) -> pathlib.Path:
    work_items = list_work_items(project_dir)
    for path in work_items:
        if path.stem == work_item_id:
            return path

    for path in work_items:
        text = read_text_if_exists(path) or ""
        meta, _ = parse_frontmatter(text)
        if meta.get("id") == work_item_id:
            return path

    raise FileNotFoundError(
        f"Work item '{work_item_id}' not found under {project_dir / 'work_items'}"
    )


def summarize_directory(path: pathlib.Path) -> str:
    files = list_markdown_files(path)
    if not files:
        return f"- `{path}`: no markdown files found."
    return "\n\n".join(summarize_file(file_path) for file_path in files)


def maybe_optional_section(enabled: bool, title: str, content: str) -> str:
    if not enabled:
        return f"## {title}\n\n- Not included (flag not set)."
    return f"## {title}\n\n{content}"


def resolve_harness_version() -> str:
    """Resolve installed package version for snapshot metadata."""
    version = lrh_version.get_installed_version()
    if version is None:
        return "unknown"
    return version


def harness_metadata_lines() -> list[str]:
    """Return additive harness metadata block lines."""
    return [
        "```yaml",
        "harness:",
        "  name: lrh",
        f"  version: {resolve_harness_version()}",
        "```",
    ]


def generate_project_context(
    project_dir: pathlib.Path, args: argparse.Namespace
) -> str:
    sections = [
        "# Project Context Packet",
        "",
        "## Scope",
        "",
        "- Scope: `project`",
        f"- Project directory: `{project_dir}`",
        "",
        "Harness metadata:",
        "",
        *harness_metadata_lines(),
        "",
        "## Principles",
        "",
        summarize_directory(project_dir / "principles"),
        "",
        "## Project Goal",
        "",
        summarize_file(project_dir / "goal" / "project_goal.md"),
        "",
        "## Design",
        "",
        summarize_file(project_dir / "design" / "design.md"),
        "",
        "## Design Proposals",
        "",
        summarize_design_proposals(project_dir),
        "",
        "## Roadmap",
        "",
        summarize_file(project_dir / "roadmap" / "roadmap.md"),
        "",
        "## Current Focus",
        "",
        summarize_file(project_dir / "focus" / "current_focus.md"),
        "",
        "## Workstreams",
        "",
        summarize_workstreams(project_dir),
        "",
        maybe_optional_section(
            args.include_guardrails,
            "Guardrails",
            summarize_directory(project_dir / "guardrails"),
        ),
        "",
        "## Contributors",
        "",
        summarize_directory(project_dir / "contributors"),
        "",
        maybe_optional_section(
            args.include_status,
            "Current Status",
            summarize_file(project_dir / "status" / "current_status.md"),
        ),
    ]
    return "\n".join(sections).strip() + "\n"


def generate_current_focus_context(
    project_dir: pathlib.Path, args: argparse.Namespace
) -> str:
    focus_path = project_dir / "focus" / "current_focus.md"
    if not focus_path.exists():
        raise FileNotFoundError(f"Missing required file: {focus_path}")

    items, filter_note = relevant_work_items(project_dir)
    item_content = "\n\n".join(summarize_file(item) for item in items)
    if not item_content:
        item_content = "- No work items found."

    sections = [
        "# Current Focus Context Packet",
        "",
        "## Scope",
        "",
        "- Scope: `current_focus`",
        f"- Project directory: `{project_dir}`",
        "",
        "Harness metadata:",
        "",
        *harness_metadata_lines(),
        "",
        "## Project Goal",
        "",
        summarize_file(project_dir / "goal" / "project_goal.md"),
        "",
        maybe_optional_section(
            args.include_design,
            "Design",
            summarize_file(project_dir / "design" / "design.md"),
        ),
        "",
        "## Roadmap",
        "",
        summarize_file(project_dir / "roadmap" / "roadmap.md"),
        "",
        "## Current Focus",
        "",
        summarize_file(focus_path, required=True),
        "",
        "## Relevant Work Items",
        "",
        f"- Filtering note: {filter_note}",
        "",
        item_content,
        "",
        maybe_optional_section(
            args.include_guardrails,
            "Guardrails",
            summarize_directory(project_dir / "guardrails"),
        ),
        "",
        "## Contributors",
        "",
        summarize_directory(project_dir / "contributors"),
        "",
        maybe_optional_section(
            args.include_status,
            "Current Status",
            summarize_file(project_dir / "status" / "current_status.md"),
        ),
    ]
    return "\n".join(sections).strip() + "\n"


def generate_work_item_context(
    project_dir: pathlib.Path, args: argparse.Namespace, work_item_id: str
) -> str:
    work_item_path = resolve_work_item(project_dir, work_item_id)
    work_text = read_text_if_exists(work_item_path) or ""
    work_meta, _ = parse_frontmatter(work_text)

    dependency_lines: list[str] = []
    depends_on = work_meta.get("depends_on")
    if isinstance(depends_on, list) and depends_on:
        for dependency_id in depends_on:
            if not isinstance(dependency_id, str):
                continue
            try:
                dep_path = resolve_work_item(project_dir, dependency_id)
                dependency_lines.append(summarize_file(dep_path))
            except FileNotFoundError:
                dependency_lines.append(f"- `{dependency_id}`: dependency not found.")
    else:
        dependency_lines.append("- No dependencies declared.")

    evidence_lines: list[str] = []
    evidence_dir = project_dir / "evidence"
    if evidence_dir.is_dir():
        wi_token = work_item_id.lower()
        for evidence_path in list_markdown_files(evidence_dir):
            content = (read_text_if_exists(evidence_path) or "").lower()
            if wi_token in content:
                evidence_lines.append(summarize_file(evidence_path))
    if not evidence_lines:
        evidence_lines.append(
            "- No trivial evidence links detected for this work item."
        )

    sections = [
        "# Work Item Context Packet",
        "",
        "## Scope",
        "",
        "- Scope: `work_item`",
        f"- Requested work item: `{work_item_id}`",
        f"- Project directory: `{project_dir}`",
        "",
        "Harness metadata:",
        "",
        *harness_metadata_lines(),
        "",
        "## Target Work Item",
        "",
        summarize_file(work_item_path, required=True),
        "",
        "## Current Focus",
        "",
        summarize_file(project_dir / "focus" / "current_focus.md"),
        "",
        "## Workstreams",
        "",
        summarize_workstreams(project_dir),
        "",
        maybe_optional_section(
            args.include_design,
            "Design",
            summarize_file(project_dir / "design" / "design.md"),
        ),
        "",
        "## Resolved Dependencies",
        "",
        "\n\n".join(dependency_lines),
        "",
        "## Relevant Evidence (Trivial Detection)",
        "",
        "\n\n".join(evidence_lines),
        "",
        maybe_optional_section(
            args.include_guardrails,
            "Guardrails",
            summarize_directory(project_dir / "guardrails"),
        ),
        "",
        "## Contributors",
        "",
        summarize_directory(project_dir / "contributors"),
        "",
        maybe_optional_section(
            args.include_status,
            "Current Status",
            summarize_file(project_dir / "status" / "current_status.md"),
        ),
    ]
    return "\n".join(sections).strip() + "\n"


def write_output(
    text: str, output_path: pathlib.Path | None, force_stdout: bool
) -> None:
    should_stdout = force_stdout or output_path is None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    if should_stdout:
        sys.stdout.write(text)


def run_snapshot_cli(argv: list[str], *, prog: str) -> int:
    """Parse args and render snapshot context output."""
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    try:
        project_dir = find_project_dir(args.project_root)
        if args.scope == "project":
            output = generate_project_context(project_dir, args)
        elif args.scope == "current_focus":
            output = generate_current_focus_context(project_dir, args)
        else:
            output = generate_work_item_context(project_dir, args, args.work_item_id)
        write_output(output, args.output, args.stdout)
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0

#!/usr/bin/env python3
"""Generate Markdown context packets from a project's control-plane files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root or project root (defaults to current directory).",
    )
    common.add_argument("--output", type=Path, help="Optional output path.")
    common.add_argument(
        "--stdout",
        action="store_true",
        help="Also print generated context to stdout.",
    )
    common.add_argument(
        "--include-status",
        action="store_true",
        help="Include project/status/current_status.md when available.",
    )
    common.add_argument(
        "--include-guardrails",
        action="store_true",
        help="Include project/guardrails/ summaries when available.",
    )
    common.add_argument(
        "--include-design",
        action="store_true",
        help="Include project/design/design.md when available.",
    )

    parser = argparse.ArgumentParser(description=__doc__, parents=[common])
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
    work_item_parser.add_argument("work_item_id", help="Work item identifier (for example WI-0003).")
    return parser.parse_args()


def find_project_dir(project_root: Path) -> Path:
    root = project_root.resolve()
    if (root / "project").is_dir():
        return root / "project"
    if root.name == "project" and root.is_dir():
        return root
    raise FileNotFoundError(f"Missing required project directory under: {root}")


def read_text_if_exists(path: Path) -> str | None:
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


def list_markdown_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(path.glob("*.md"))


def summarize_file(path: Path, required: bool = False) -> str:
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


def list_work_items(project_dir: Path) -> list[Path]:
    return list_markdown_files(project_dir / "work_items")


def current_focus_frontmatter(project_dir: Path) -> tuple[dict[str, object], str]:
    focus_path = project_dir / "focus" / "current_focus.md"
    focus_text = read_text_if_exists(focus_path)
    if focus_text is None:
        raise FileNotFoundError(f"Missing required file: {focus_path}")
    return parse_frontmatter(focus_text)


def relevant_work_items(project_dir: Path) -> tuple[list[Path], str]:
    focus_meta, _ = current_focus_frontmatter(project_dir)
    focus_id = focus_meta.get("id")
    items = list_work_items(project_dir)

    if not isinstance(focus_id, str):
        return items, "Focus id not detected; including all work items."

    matching: list[Path] = []
    for item_path in items:
        text = read_text_if_exists(item_path) or ""
        meta, _ = parse_frontmatter(text)
        related_focus = meta.get("related_focus")
        if isinstance(related_focus, list) and focus_id in related_focus:
            matching.append(item_path)

    if matching:
        return matching, f"Filtered work items by related_focus containing `{focus_id}`."

    return items, (
        f"No work item related_focus match for `{focus_id}`; including all work items "
        "(version 1 fallback)."
    )


def resolve_work_item(project_dir: Path, work_item_id: str) -> Path:
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


def summarize_directory(path: Path) -> str:
    files = list_markdown_files(path)
    if not files:
        return f"- `{path}`: no markdown files found."
    return "\n\n".join(summarize_file(file_path) for file_path in files)


def maybe_optional_section(enabled: bool, title: str, content: str) -> str:
    if not enabled:
        return f"## {title}\n\n- Not included (flag not set)."
    return f"## {title}\n\n{content}"


def generate_project_context(project_dir: Path, args: argparse.Namespace) -> str:
    sections = [
        "# Project Context Packet",
        "",
        "## Scope",
        "",
        "- Scope: `project`",
        f"- Project directory: `{project_dir}`",
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
        "## Roadmap",
        "",
        summarize_file(project_dir / "roadmap" / "roadmap.md"),
        "",
        "## Current Focus",
        "",
        summarize_file(project_dir / "focus" / "current_focus.md"),
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


def generate_current_focus_context(project_dir: Path, args: argparse.Namespace) -> str:
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
    project_dir: Path, args: argparse.Namespace, work_item_id: str
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
        evidence_lines.append("- No trivial evidence links detected for this work item.")

    sections = [
        "# Work Item Context Packet",
        "",
        "## Scope",
        "",
        "- Scope: `work_item`",
        f"- Requested work item: `{work_item_id}`",
        f"- Project directory: `{project_dir}`",
        "",
        "## Target Work Item",
        "",
        summarize_file(work_item_path, required=True),
        "",
        "## Current Focus",
        "",
        summarize_file(project_dir / "focus" / "current_focus.md"),
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


def write_output(text: str, output_path: Path | None, force_stdout: bool) -> None:
    should_stdout = force_stdout or output_path is None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    if should_stdout:
        sys.stdout.write(text)


def main() -> int:
    args = parse_args()
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


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI adapter for request generation workflows."""

import argparse
import pathlib
import sys

from lrh.assist import request_service


def build_parser(*, prog: str = "request") -> argparse.ArgumentParser:
    """Build the request CLI parser."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Render an assist request from a template and input options.",
    )
    parser.add_argument(
        "template_name",
        help=(
            "Template base name (e.g. improve_coverage, bootstrap_project, "
            "work_items_from_audit, codex_prompt_from_work_item)."
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Optional target path or identifier. For coverage-style templates, "
            "this is usually a module path such as "
            "src/lrh/analysis/llm_extractor.py."
        ),
    )
    parser.add_argument(
        "--target",
        dest="target_option",
        help=(
            "Optional named target identifier or path. For assessment work-item "
            "scope, use the work-item ID (for example WI-0003)."
        ),
    )
    parser.add_argument(
        "--scope",
        choices=["project", "current_focus", "work_item"],
        help=(
            "Scope for assessment request generation. "
            "Required when template_name is assessment."
        ),
    )
    parser.add_argument(
        "--repo-name",
        help="Repository name for bootstrap-oriented templates.",
    )
    parser.add_argument(
        "--project-goal",
        help="Project goal text to inject into the template.",
    )
    background_group = parser.add_mutually_exclusive_group()
    background_group.add_argument(
        "--background-file",
        help="Path to a UTF-8 text/markdown file for background context.",
    )
    background_group.add_argument(
        "--background-text",
        help="Literal background context text.",
    )
    parser.add_argument(
        "--project-type",
        help="Optional project type, such as library, app, or research.",
    )
    parser.add_argument(
        "--bootstrap-mode",
        choices=["minimal", "full"],
        default="minimal",
        help="Bootstrap scope hint for bootstrap-oriented templates.",
    )
    parser.add_argument(
        "--audit-file",
        help="Path to a UTF-8 audit report injected as {{AUDIT_REPORT}}.",
    )
    parser.add_argument(
        "--work-item-file",
        help=(
            "Path to a UTF-8 work item file injected as {{WORK_ITEM}} and "
            "{{WORK_ITEM_CONTENT}}, with path available as {{WORK_ITEM_PATH}}."
        ),
    )
    parser.add_argument(
        "--style-file",
        help=(
            "Path to a UTF-8 style guide file injected as {{STYLE_GUIDE_CONTEXT}} "
            "and {{STYLE_GUIDE_CONTENT}}, with path available as "
            "{{STYLE_GUIDE_PATH}}."
        ),
    )
    parser.add_argument(
        "--patch-file",
        help="Path to a UTF-8 patch or diff file injected as {{PATCH}}.",
    )
    parser.add_argument(
        "--show-vars",
        action="store_true",
        help="Print computed variables to stderr for debugging.",
    )
    return parser


def run_request_cli(
    argv: list[str],
    *,
    template_root: pathlib.Path | None = None,
    prog: str,
) -> int:
    """Parse args and render a request."""
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)

    error = request_service.validate_args(args)
    if error:
        print(error, file=sys.stderr)
        return 2

    try:
        rendered, variables = request_service.generate_request(
            args,
            template_root=template_root,
        )
    except (FileNotFoundError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.show_vars:
        for key in sorted(variables.keys()):
            print(f"{key}={variables[key]}", file=sys.stderr)

    sys.stdout.write(rendered)
    if not rendered.endswith("\n"):
        sys.stdout.write("\n")
    return 0

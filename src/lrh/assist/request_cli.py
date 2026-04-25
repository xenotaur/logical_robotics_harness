"""CLI adapter for request generation workflows."""

import argparse
import datetime
import pathlib
import re
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
            "src/lrh/analysis/llm_extractor.py. For "
            "codex_prompt_from_work_item, this may be a work-item ID, stem, "
            "or file path."
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
            " When provided for codex_prompt_from_work_item, this explicit path "
            "takes precedence over any positional target."
        ),
    )
    parser.add_argument(
        "--style-file",
        help=(
            "Path to a UTF-8 style guide file injected as {{STYLE_GUIDE_CONTEXT}} "
            "and {{STYLE_GUIDE_CONTENT}}, with path available as "
            "{{STYLE_GUIDE_PATH}}. codex_prompt_from_work_item defaults to "
            "STYLE.md when omitted."
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
    parser.add_argument(
        "--prompt-id",
        help=(
            "Optional explicit prompt ID for codex_prompt_from_work_item. "
            "When omitted, a prompt ID is generated from work-item metadata and "
            "the current timestamp."
        ),
    )
    return parser


def build_codex_prompt_from_work_item_parser(
    *, prog: str = "request codex-prompt-from-work-item"
) -> argparse.ArgumentParser:
    """Build parser for the structured codex_prompt_from_work_item CLI command."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Generate a Codex implementation prompt from a structured LRH work item."
        ),
    )
    parser.add_argument(
        "--work-item",
        required=True,
        help="Path to the source work item markdown file.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Prompt slug used to build prompt ID metadata.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output markdown path for the generated prompt.",
    )
    parser.add_argument(
        "--style-file",
        help="Optional style guide path (defaults to STYLE.md discovery rules).",
    )
    parser.add_argument(
        "--show-vars",
        action="store_true",
        help="Print computed variables to stderr for debugging.",
    )
    return parser


def _build_prompt_id_from_slug(slug: str) -> str:
    """Create a prompt ID from a slug using prompt workflow conventions."""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", slug.strip()).strip("_").upper()
    if not normalized:
        raise ValueError("error: --slug must include at least one letter or number.")
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    timestamp = now.isoformat(timespec="seconds")
    return f"PROMPT(AD_HOC:{normalized})[{timestamp}]"


def run_request_cli(
    argv: list[str],
    *,
    template_root: pathlib.Path | None = None,
    prog: str,
) -> int:
    """Parse args and render a request."""
    if argv and argv[0] == "codex-prompt-from-work-item":
        command_parser = build_codex_prompt_from_work_item_parser(
            prog=f"{prog} codex-prompt-from-work-item"
        )
        command_args = command_parser.parse_args(argv[1:])
        mapped_args = argparse.Namespace(
            template_name="codex_prompt_from_work_item",
            target=None,
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text=None,
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file=command_args.work_item,
            style_file=command_args.style_file,
            patch_file=None,
            show_vars=command_args.show_vars,
            prompt_id=_build_prompt_id_from_slug(command_args.slug),
        )
        args = mapped_args
        output_path = pathlib.Path(command_args.out)
    else:
        output_path = None
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
    except (FileNotFoundError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.show_vars:
        for key in sorted(variables.keys()):
            print(f"{key}={variables[key]}", file=sys.stderr)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            rendered if rendered.endswith("\n") else f"{rendered}\n",
            encoding="utf-8",
        )
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")
    return 0

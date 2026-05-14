"""CLI adapter for request generation workflows."""

import argparse
import datetime
import pathlib
import re
import sys

from lrh.assist import (
    request_catalog,
    request_service,
    request_templates,
    request_variables,
)
from lrh.cli import argcomplete_adapter


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach request CLI arguments to an existing parser."""
    template_name_arg = parser.add_argument(
        "template_name",
        help=(
            "Request name (e.g. improve-coverage, bootstrap-project, "
            "work-items-from-audit, prompt-from-work-item, "
            "assess-continuous-integration-status). Legacy template names "
            "remain supported. Use 'lrh request list' to discover cataloged "
            "requests. Use 'lrh request templates list' and "
            "'lrh request templates where' for template diagnostics."
        ),
    )
    target_arg = parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Optional target path or identifier. For coverage-style requests, "
            "this is usually a module path such as "
            "src/lrh/analysis/llm_extractor.py. For "
            "prompt-from-work-item, this may be a work-item ID, stem, "
            "or file path."
        ),
    )
    template_name_arg.completer = argcomplete_adapter.request_template_completer
    target_arg.completer = argcomplete_adapter.codex_work_item_target_completer
    parser.add_argument(
        "--target",
        dest="target_option",
        help=(
            "Optional named target identifier or path. For assessment work-item "
            "scope, use the work-item ID (for example WI-0003)."
        ),
    )
    parser.add_argument(
        "--template-dir",
        help=(
            "Template override root containing logical paths such as "
            "request/review_response.md."
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
        "--force",
        action="store_true",
        help=(
            "For review_response, emit the full prompt even when no "
            "unresolved review threads are found."
        ),
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


def build_parser(*, prog: str = "request") -> argparse.ArgumentParser:
    """Build the request CLI parser."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Render an assist request from a template and input options. "
            "Optional completion is available via argcomplete; "
            "run scripts/install-completion for setup guidance."
        ),
    )
    return configure_parser(parser)


def build_request_catalog_parser(*, prog: str = "request") -> argparse.ArgumentParser:
    """Build parser for request-catalog discoverability commands."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Discover cataloged LRH assist requests.",
    )
    subparsers = parser.add_subparsers(dest="catalog_command")

    list_parser = subparsers.add_parser(
        "list",
        help="List cataloged request names grouped by category.",
    )
    list_parser.add_argument(
        "--category",
        help="Limit output to one request category.",
    )

    describe_parser = subparsers.add_parser(
        "describe",
        help="Describe one cataloged request by canonical or legacy name.",
    )
    describe_parser.add_argument(
        "request_name",
        help="Canonical or legacy request name to describe.",
    )
    return parser


def _group_requests_by_category(
    requests: tuple[request_catalog.RequestMetadata, ...],
) -> dict[str, list[request_catalog.RequestMetadata]]:
    """Return request metadata grouped by category in catalog order."""
    grouped: dict[str, list[request_catalog.RequestMetadata]] = {}
    for metadata in requests:
        grouped.setdefault(metadata.category, []).append(metadata)
    return grouped


def _format_legacy_names(legacy_names: tuple[str, ...]) -> str:
    """Format legacy request names for user-facing output."""
    if not legacy_names:
        return "none"
    return ", ".join(legacy_names)


def _format_catalog_list(
    requests: tuple[request_catalog.RequestMetadata, ...],
) -> str:
    """Format cataloged requests grouped by category."""
    lines: list[str] = []
    for category, category_requests in _group_requests_by_category(requests).items():
        lines.append(f"{category}:")
        for metadata in category_requests:
            lines.append(f"  {metadata.canonical_name:<48} {metadata.description}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_catalog_description(
    metadata: request_catalog.RequestMetadata,
    *,
    requested_name: str,
) -> str:
    """Format detailed metadata for one cataloged request."""
    lines = [
        f"canonical name: {metadata.canonical_name}",
        f"category: {metadata.category}",
        f"description: {metadata.description}",
        f"legacy names: {_format_legacy_names(metadata.legacy_names)}",
        f"template: request/{metadata.template_name}.md",
        f"implementation: {metadata.implementation_target}",
        "usage: lrh request " + metadata.canonical_name + " [options]",
    ]
    if requested_name != metadata.canonical_name:
        lines.append(f"resolved from: {requested_name}")
    return "\n".join(lines)


def run_catalog_cli(
    argv: list[str],
    *,
    prog: str,
) -> int:
    """Run request-catalog discoverability subcommands."""
    parser = build_request_catalog_parser(prog=prog)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code) if isinstance(error.code, int) else 2

    if args.catalog_command is None:
        print(
            "error: request catalog requires a subcommand (try: list or describe)",
            file=sys.stderr,
        )
        return 2

    if args.catalog_command == "list":
        requests = request_catalog.all_requests()
        if args.category:
            requests = tuple(
                metadata for metadata in requests if metadata.category == args.category
            )
            if not requests:
                print(
                    f"error: unknown request category: {args.category}",
                    file=sys.stderr,
                )
                return 2
        output = _format_catalog_list(requests)
        if output:
            print(output)
        return 0

    metadata = request_catalog.resolve(args.request_name)
    if metadata is None:
        print(f"error: unknown request name: {args.request_name}", file=sys.stderr)
        return 2
    print(_format_catalog_description(metadata, requested_name=args.request_name))
    return 0


def build_templates_parser(
    *, prog: str = "request templates"
) -> argparse.ArgumentParser:
    """Build parser for request-template diagnostics."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Inspect request assist template override resolution.",
    )
    parser.add_argument(
        "--template-dir",
        action="append",
        dest="template_dirs",
        help=(
            "Template override root containing logical paths such as "
            "request/review_response.md. May be passed more than once; "
            "earlier values have higher precedence."
        ),
    )
    subparsers = parser.add_subparsers(dest="templates_command")
    subparsers.add_parser(
        "list",
        help="List request templates and the source that would be used.",
    )
    where_parser = subparsers.add_parser(
        "where",
        help="Show the source that would be used for one request template.",
    )
    where_parser.add_argument(
        "logical_template_name",
        help=(
            "Request name or template name, such as review-response, "
            "review_response, request/review_response.md, or "
            "request/review_response."
        ),
    )
    return parser


def _request_logical_name(template_name: str) -> str:
    """Normalize a request-template diagnostic argument to a logical name."""
    normalized_name = (
        template_name[: -len(".md")] if template_name.endswith(".md") else template_name
    )
    if "/" not in normalized_name:
        normalized_name = f"request/{normalized_name}"
    return f"{normalized_name}.md"


def _request_template_base_name(logical_name: str) -> str:
    """Return the CLI-facing request template name for a request logical name."""
    return logical_name[len("request/") : -len(".md")]


def _format_template_resolution(name: str, resolution) -> str:
    """Format one template-resolution diagnostic line."""
    source_label = (
        "package fallback" if resolution.source == "package" else "filesystem override"
    )
    return f"{name}	{resolution.source}	{source_label}	{resolution.origin}"


def run_templates_cli(
    argv: list[str],
    *,
    prog: str,
) -> int:
    """Run request-template diagnostic subcommands."""
    parser = build_templates_parser(prog=prog)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code) if isinstance(error.code, int) else 2

    if args.templates_command is None:
        print(
            "error: templates requires a subcommand (try: list or where)",
            file=sys.stderr,
        )
        return 2

    project_root = request_variables.find_repo_root()
    template_dirs = args.template_dirs

    if args.templates_command == "list":
        names = request_templates.request_template_names(
            project_root=project_root,
            template_dirs=template_dirs,
        )
        for name in names:
            resolution = request_templates.resolve_template(
                name,
                project_root=project_root,
                template_dirs=template_dirs,
            )
            print(_format_template_resolution(name, resolution))
        return 0

    logical_name = _request_logical_name(args.logical_template_name)
    request_name = (
        _request_template_base_name(logical_name)
        if logical_name.startswith("request/") and logical_name.endswith(".md")
        else logical_name
    )
    request_metadata = request_catalog.resolve(request_name)
    if request_metadata is not None:
        request_name = request_metadata.template_name
    try:
        resolution = request_templates.resolve_template(
            request_name,
            project_root=project_root,
            template_dirs=template_dirs,
        )
    except (FileNotFoundError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    print(_format_template_resolution(resolution.logical_name, resolution))
    return 0


def build_codex_prompt_from_work_item_parser(
    *, prog: str = "request codex-prompt-from-work-item"
) -> argparse.ArgumentParser:
    """Build parser for the structured codex_prompt_from_work_item CLI command."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Generate a Codex Cloud-ready implementation prompt "
            "from a structured LRH work item."
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
        help=(
            "Output markdown path for the generated prompt "
            "(submit this file to Codex Cloud)."
        ),
    )
    parser.add_argument(
        "--style-file",
        help="Optional style guide path (defaults to STYLE.md discovery rules).",
    )
    parser.add_argument(
        "--template-dir",
        help=(
            "Template override root containing logical paths such as "
            "request/codex_prompt_from_work_item.md."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "For review_response, emit the full prompt even when no "
            "unresolved review threads are found."
        ),
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
    if argv and argv[0] in {"list", "describe"}:
        return run_catalog_cli(
            argv,
            prog=prog,
        )

    if argv and argv[0] == "templates":
        return run_templates_cli(
            argv[1:],
            prog=f"{prog} templates",
        )

    if argv and argv[0] == "codex-prompt-from-work-item":
        command_parser = build_codex_prompt_from_work_item_parser(
            prog=f"{prog} {argv[0]}"
        )
        try:
            command_args = command_parser.parse_args(argv[1:])
        except SystemExit as error:
            return int(error.code) if isinstance(error.code, int) else 2
        try:
            prompt_id = _build_prompt_id_from_slug(command_args.slug)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
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
            force=False,
            prompt_id=prompt_id,
            template_dir=command_args.template_dir,
        )
        args = mapped_args
        output_path = pathlib.Path(command_args.out) if command_args.out else None
    else:
        output_path = None
        parser = build_parser(prog=prog)
        try:
            args = parser.parse_args(argv)
        except SystemExit as error:
            return int(error.code) if isinstance(error.code, int) else 2
        request_metadata = request_catalog.resolve(args.template_name)
        if request_metadata is not None:
            args.request_name = args.template_name
            args.template_name = request_metadata.template_name

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
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                rendered if rendered.endswith("\n") else f"{rendered}\n",
                encoding="utf-8",
            )
        except OSError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")
    return 0

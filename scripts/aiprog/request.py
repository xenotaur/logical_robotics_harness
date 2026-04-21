#!/usr/bin/env python
"""
Create a filled-out request from a template.

Examples:
    scripts/aiprog/request.py improve_coverage src/lrh/analysis/llm_extractor.py

    scripts/aiprog/request.py bootstrap_project \
        --repo-name taurworks \
        --project-goal "Turn taurworks into a robust project bootstrap CLI" \
        --background-file notes/taurworks_background.md

    scripts/aiprog/request.py work_items_from_audit \
        --audit-file audits/style_audit_2026_04_10.md \
        --style-file STYLE.md

    scripts/aiprog/request.py codex_prompt_from_work_item \
        --work-item-file project/work_items/WI-STYLE-0001.md \
        --style-file STYLE.md \
        --background-file notes/context.md

    scripts/aiprog/request.py pr_against_work_item \
        --work-item-file project/work_items/WI-STYLE-0001.md \
        --patch-file patches/WI-STYLE-0001.diff \
        --style-file STYLE.md

Templates live in:
    scripts/aiprog/templates/request/<template_name>.md

Interpolation variables use the form:
    {{VARIABLE_NAME}}
"""

import argparse
import pathlib
import sys

from lrh.assist import request_service


def _default_template_root() -> pathlib.Path:
    """Resolve request templates relative to this script location."""
    return pathlib.Path(__file__).resolve().parent / "templates" / "request"


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="request.py",
        description="Fill a request template with computed variables.",
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
            "this is usually a module path like src/lrh/analysis/llm_extractor.py."
        ),
    )
    parser.add_argument(
        "--target",
        dest="target_option",
        help=(
            "Optional named target identifier/path. For assessment work-item scope, "
            "this should be the work-item ID (for example WI-0003)."
        ),
    )
    parser.add_argument(
        "--scope",
        choices=["project", "current_focus", "work_item"],
        help=(
            "Scope for assessment template generation. "
            "Required for template_name=assessment."
        ),
    )
    parser.add_argument(
        "--repo-name",
        help="Repository name for repository/bootstrap-oriented templates.",
    )
    parser.add_argument(
        "--project-goal",
        help="Human-readable project goal to inject into the template.",
    )
    background_group = parser.add_mutually_exclusive_group()
    background_group.add_argument(
        "--background-file",
        help="Path to a UTF-8 text/markdown file to inject as background context.",
    )
    background_group.add_argument(
        "--background-text",
        help="Literal background context to inject directly.",
    )
    parser.add_argument(
        "--project-type",
        help="Optional project classification, such as library, app, or research.",
    )
    parser.add_argument(
        "--bootstrap-mode",
        choices=["minimal", "full"],
        default="minimal",
        help="Optional bootstrap scope hint for bootstrap-oriented templates.",
    )
    parser.add_argument(
        "--audit-file",
        help="Path to a UTF-8 audit report to inject as {{AUDIT_REPORT}}.",
    )
    parser.add_argument(
        "--work-item-file",
        help="Path to a UTF-8 work item file to inject as {{WORK_ITEM}}.",
    )
    parser.add_argument(
        "--style-file",
        help="Path to a UTF-8 style guide file to inject as {{STYLE_GUIDE_CONTEXT}}.",
    )
    parser.add_argument(
        "--patch-file",
        help="Path to a UTF-8 patch or diff file to inject as {{PATCH}}.",
    )
    parser.add_argument(
        "--show-vars",
        action="store_true",
        help="Print computed variables to stderr (debugging).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    error = request_service.validate_args(args)
    if error:
        print(error, file=sys.stderr)
        return 2

    try:
        rendered, variables = request_service.generate_request(
            args,
            template_root=_default_template_root(),
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


if __name__ == "__main__":
    raise SystemExit(main())

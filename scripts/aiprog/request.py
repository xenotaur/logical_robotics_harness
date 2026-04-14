#!/usr/bin/env python3
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
import re
import sys

from lrh.assist import request_variables

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _script_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent


def _templates_dir() -> pathlib.Path:
    return _script_dir() / "templates" / "request"


def _load_template(template_name: str) -> tuple[pathlib.Path, str]:
    template_path = _templates_dir() / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected: scripts/aiprog/templates/request/{template_name}.md"
        )
    return template_path, template_path.read_text(encoding="utf-8")


def _render_template(template_text: str, variables: dict[str, str]) -> str:
    """
    Simple, deterministic interpolation:
      - Replaces {{VARNAME}} with variables[VARNAME] if present.
      - Leaves unknown placeholders intact (so you can notice missing vars).
    """

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _TEMPLATE_VAR_RE.sub(repl, template_text)


def _build_variables(args: argparse.Namespace) -> dict[str, str]:
    target_input = _resolve_target_input(args)
    target_module_gha = request_variables.normalize_target_for_gha(target_input)
    module_name = pathlib.Path(target_module_gha).stem if target_module_gha else ""
    suggested_test_path = request_variables.compute_suggested_test_path(
        target_module_gha
    )

    background_context = args.background_text or request_variables.read_optional_text(
        args.background_file
    )
    repo_name = request_variables.infer_repo_name(target_input, args.repo_name)

    audit_report = request_variables.read_optional_text(args.audit_file)
    work_item = request_variables.read_optional_text(args.work_item_file)
    style_guide_context = request_variables.read_optional_text(args.style_file)
    patch_text = request_variables.read_optional_text(args.patch_file)

    # Keep names stable and ALL CAPS to match {{...}} usage
    return {
        "TEMPLATE_NAME": args.template_name,
        "TARGET_INPUT": target_input,
        "TARGET_MODULE_GHA": target_module_gha,
        "MODULE_NAME": module_name,
        "SUGGESTED_TEST_PATH": suggested_test_path,
        "REPO_NAME": repo_name,
        "PROJECT_GOAL": args.project_goal or "",
        "BACKGROUND_CONTEXT": background_context,
        "BACKGROUND_FILE": args.background_file or "",
        "PROJECT_TYPE": args.project_type or "",
        "BOOTSTRAP_SCOPE": args.bootstrap_mode or "",
        "ASSESSMENT_SCOPE": args.scope or "",
        "ASSESSMENT_TARGET": target_input,
        "AUDIT_REPORT": audit_report,
        "AUDIT_FILE": args.audit_file or "",
        "WORK_ITEM": work_item,
        "WORK_ITEM_FILE": args.work_item_file or "",
        "STYLE_GUIDE_CONTEXT": style_guide_context,
        "STYLE_FILE": args.style_file or "",
        "PATCH": patch_text,
        "PATCH_FILE": args.patch_file or "",
    }


def _resolve_target_input(args: argparse.Namespace) -> str:
    if args.target_option:
        return args.target_option
    if args.target:
        return args.target
    return ""


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


def _validate_args(args: argparse.Namespace) -> int:
    """
    Return 0 if arguments are valid, otherwise print an error and return a
    non-zero exit code.
    """
    # Preserve existing behavior for target-centric templates.
    target_input = _resolve_target_input(args)

    if args.template_name == "improve_coverage" and not target_input:
        print(
            "error: improve_coverage requires a target module path.",
            file=sys.stderr,
        )
        return 2

    # Helpful validation for the bootstrap workflow.
    if args.template_name == "bootstrap_project":
        if not args.repo_name and not target_input:
            print(
                "error: bootstrap_project requires --repo-name or a target value "
                "that can be used as the repository identifier.",
                file=sys.stderr,
            )
            return 2

    if args.template_name == "assessment":
        if not args.scope:
            print(
                "error: assessment requires --scope "
                "(project, current_focus, or work_item).",
                file=sys.stderr,
            )
            return 2
        if args.scope == "work_item" and not target_input:
            print(
                "error: assessment --scope work_item requires --target "
                "(for example --target WI-0003).",
                file=sys.stderr,
            )
            return 2

    if args.template_name == "work_items_from_audit":
        if not args.audit_file:
            print(
                "error: work_items_from_audit requires --audit-file.",
                file=sys.stderr,
            )
            return 2
        if not args.style_file:
            print(
                "error: work_items_from_audit requires --style-file.",
                file=sys.stderr,
            )
            return 2

    if args.template_name == "codex_prompt_from_work_item":
        if not args.work_item_file:
            print(
                "error: codex_prompt_from_work_item requires --work-item-file.",
                file=sys.stderr,
            )
            return 2
        if not args.style_file:
            print(
                "error: codex_prompt_from_work_item requires --style-file.",
                file=sys.stderr,
            )
            return 2

    if args.template_name == "pr_against_work_item":
        if not args.work_item_file:
            print(
                "error: pr_against_work_item requires --work-item-file.",
                file=sys.stderr,
            )
            return 2
        if not args.patch_file:
            print(
                "error: pr_against_work_item requires --patch-file.",
                file=sys.stderr,
            )
            return 2
        if not args.style_file:
            print(
                "error: pr_against_work_item requires --style-file.",
                file=sys.stderr,
            )
            return 2

    return 0


def main(argv=None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    validation_code = _validate_args(args)
    if validation_code != 0:
        return validation_code

    try:
        _, template_text = _load_template(args.template_name)
        variables = _build_variables(args)
    except (FileNotFoundError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2

    if args.show_vars:
        for k in sorted(variables.keys()):
            print(f"{k}={variables[k]}", file=sys.stderr)

    rendered = _render_template(template_text, variables)
    sys.stdout.write(rendered)
    if not rendered.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

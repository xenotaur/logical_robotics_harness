"""Request generation orchestration for the compatibility request script."""

import argparse
import pathlib
import re

from lrh.assist import request_templates, request_variables

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def validate_args(args: argparse.Namespace) -> str | None:
    """Validate request arguments and return an error message if invalid."""
    target_input = resolve_target_input(args)

    if args.template_name == "improve_coverage" and not target_input:
        return "error: improve_coverage requires a target module path."

    if args.template_name == "bootstrap_project":
        if not args.repo_name and not target_input:
            return (
                "error: bootstrap_project requires --repo-name or a target value "
                "that can be used as the repository identifier."
            )

    if args.template_name == "assessment":
        if not args.scope:
            return (
                "error: assessment requires --scope "
                "(project, current_focus, or work_item)."
            )
        if args.scope == "work_item" and not target_input:
            return (
                "error: assessment --scope work_item requires --target "
                "(for example --target WI-0003)."
            )

    if args.template_name == "work_items_from_audit":
        if not args.audit_file:
            return "error: work_items_from_audit requires --audit-file."
        if not args.style_file:
            return "error: work_items_from_audit requires --style-file."

    if args.template_name == "codex_prompt_from_work_item":
        if not args.work_item_file:
            return "error: codex_prompt_from_work_item requires --work-item-file."
        if not args.style_file:
            return "error: codex_prompt_from_work_item requires --style-file."

    if args.template_name == "pr_against_work_item":
        if not args.work_item_file:
            return "error: pr_against_work_item requires --work-item-file."
        if not args.patch_file:
            return "error: pr_against_work_item requires --patch-file."
        if not args.style_file:
            return "error: pr_against_work_item requires --style-file."

    return None


def generate_request(
    args: argparse.Namespace,
    *,
    template_root: pathlib.Path | None = None,
) -> tuple[str, dict[str, str]]:
    """Load template and render it using computed request variables."""
    template_text = request_templates.load_template_text(
        args.template_name,
        template_root=template_root,
    )
    variables = build_variables(args)
    return render_template(template_text, variables), variables


def render_template(template_text: str, variables: dict[str, str]) -> str:
    """Interpolate ``{{VARNAME}}`` tokens, preserving unknown placeholders."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _TEMPLATE_VAR_RE.sub(repl, template_text)


def resolve_target_input(args: argparse.Namespace) -> str:
    """Resolve optional target value from positional/named CLI arguments."""
    if args.target_option:
        return args.target_option
    if args.target:
        return args.target
    return ""


def build_variables(args: argparse.Namespace) -> dict[str, str]:
    """Build template interpolation variables from parsed request arguments."""
    target_input = resolve_target_input(args)
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

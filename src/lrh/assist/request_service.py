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
    variables = build_variables(args)

    if args.template_name == "codex_prompt_from_work_item":
        return transform_codex_prompt_from_work_item(variables), variables

    template_text = request_templates.load_template_text(
        args.template_name,
        template_root=template_root,
    )
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


def transform_codex_prompt_from_work_item(variables: dict[str, str]) -> str:
    """Generate a concrete Codex implementation prompt from a work item."""
    work_item = variables.get("WORK_ITEM", "")
    objective = _extract_section_text(work_item, "Problem")
    scope = _extract_section_text(work_item, "Scope")
    out_of_scope = _extract_section_text(work_item, "Out of Scope")
    likely_files = _extract_bullets(work_item, "Likely files")
    validation_steps = _extract_bullets(work_item, "Validation")
    acceptance_criteria = _extract_bullets(work_item, "Acceptance criteria")
    risk_level = _extract_field_value(work_item, "Risk level")
    execution_suitability = _extract_field_value(work_item, "Execution suitability")

    required_changes = (
        scope or "- Implement only what is explicitly described in the work item."
    )
    if likely_files:
        likely_file_lines = "\n".join(f"  - {path}" for path in likely_files)
        required_changes = (
            f"{required_changes}\n- Limit edits to likely files:\n{likely_file_lines}"
        )

    do_not = (
        out_of_scope
        or "- Do not expand scope beyond the selected work item.\n"
        "- Do not perform unrelated cleanup or refactors."
    )

    edge_case_rules = (
        "- If requirements are ambiguous, choose the smallest safe interpretation "
        "and report uncertainty."
    )
    if risk_level:
        edge_case_rules += f"\n- Treat this change as risk level: {risk_level}."
    if execution_suitability:
        edge_case_rules += (
            "\n- Respect execution suitability guidance from the work item: "
            f"{execution_suitability}."
        )

    validation_block = (
        "\n".join(f"- {step}" for step in validation_steps)
        if validation_steps
        else "- scripts/test\n- scripts/validate"
    )
    success_criteria = (
        "\n".join(f"- {criterion}" for criterion in acceptance_criteria)
        if acceptance_criteria
        else "- Work item scope is implemented without unrelated changes."
    )

    return f"""# ROLE

You are a senior Python engineer making a single, tightly scoped repository change.

# AUTHORITATIVE REFERENCES

- STYLE.md
- {variables.get("WORK_ITEM_FILE", "approved work item file")}

# OBJECTIVE

{objective or "Implement the approved work item exactly as written."}

# STRICT SCOPE

{scope or "Only the approved work item is in scope."}

# REQUIRED CHANGES

{required_changes}

# DO NOT

{do_not}

# EDGE CASE RULES

{edge_case_rules}

# VALIDATION

{validation_block}

# OUTPUT REQUIREMENTS

- Summarize changed files and why each change is needed.
- List validation commands run and results.
- Explicitly list what was intentionally not changed.

# SUCCESS CRITERIA

{success_criteria}

# FINAL CHECK

- Confirm changes are minimal and reviewable.
- Confirm no unrelated files were modified.
- Confirm requested validations were run or limitations were reported.

# BEGIN
"""


def _extract_section_text(markdown_text: str, section_name: str) -> str:
    """Extract body text beneath a markdown heading."""
    pattern = re.compile(
        rf"(?im)^##\s+{re.escape(section_name)}\s*$\n(?P<body>.*?)(?=^\s*##\s+|\Z)",
        re.DOTALL,
    )
    match = pattern.search(markdown_text)
    if not match:
        return ""
    return match.group("body").strip()


def _extract_bullets(markdown_text: str, section_name: str) -> list[str]:
    """Extract bullet-line content from a section."""
    section = _extract_section_text(markdown_text, section_name)
    if not section:
        return []
    bullets = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _extract_field_value(markdown_text: str, field_name: str) -> str:
    """Extract a short field value from `- **Field:** value` style lines."""
    pattern = re.compile(
        rf"(?im)^\s*-\s*\*\*{re.escape(field_name)}:\*\*\s*(?P<value>.+?)\s*$"
    )
    match = pattern.search(markdown_text)
    if not match:
        return ""
    return match.group("value").strip()

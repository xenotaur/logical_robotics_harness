#!/usr/bin/env python3
"""
Create a filled-out PR request from a template.

Examples:
    scripts/aiprog/create_request.py improve_coverage src/lrh/analysis/llm_extractor.py

    scripts/aiprog/create_request.py bootstrap_project \
        --repo-name taurworks \
        --project-goal "Turn taurworks into a robust project bootstrap CLI" \
        --background-file notes/taurworks_background.md

Templates live in:
    scripts/aiprog/templates/<template_name>.md

Interpolation variables use the form:
    {{VARIABLE_NAME}}
"""

import argparse
import pathlib
import re
import sys

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _script_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent


def _templates_dir() -> pathlib.Path:
    return _script_dir() / "templates"


def _load_template(template_name: str) -> tuple[pathlib.Path, str]:
    template_path = _templates_dir() / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected: scripts/aiprog/templates/{template_name}.md"
        )
    return template_path, template_path.read_text(encoding="utf-8")


def _normalize_target_for_gha(target_input: str | None) -> str:
    """
    Normalize an input path into repo-root style module path:
        src/lrh/<...>.py

    Accepts inputs like:
        src/lrh/analysis/foo.py -> src/lrh/analysis/foo.py
        lrh/analysis/foo.py     -> src/lrh/analysis/foo.py
        analysis/foo.py         -> src/lrh/analysis/foo.py
                                   (assumed relative to src/lrh/)

    If target_input is empty or None, returns an empty string.
    """
    if not target_input:
        return ""

    s = target_input.strip().replace("\\", "/")
    s = s.lstrip("./")

    # If user passes a path relative to src/lrh/ (common local usage)
    if not s.startswith("src/lrh/"):
        if s.startswith("lrh/"):
            s = f"src/{s}"
        else:
            s = f"src/lrh/{s}"

    # If already includes src/lrh, keep as-is
    if s.startswith("src/lrh/"):
        return s

    # If starts with src/ but not src/lrh/, insert lrh/
    if s.startswith("src/"):
        return "src/lrh/" + s[len("src/") :]

    # Should be unreachable, but keep safe
    return s


def _compute_suggested_test_path(target_module_gha: str) -> str:
    """
    Given:
        src/lrh/<subdir>/<...>/<name>.py
    Suggest:
        tests/<subdir>/<...>/<name>_test.py

    Example:
        src/lrh/analysis/llm_extractor.py
            -> tests/analysis/llm_extractor_test.py

        src/lrh/analysis/nlp/foo.py
            -> tests/analysis/nlp/foo_test.py
    """
    if not target_module_gha:
        return ""

    p = pathlib.Path(target_module_gha)

    # Expect: src / lrh / <subdir> / ... / <file>
    parts = p.parts
    if len(parts) < 3 or parts[0] != "src" or parts[1] != "lrh":
        # Fall back: place in tests/
        stem = p.stem
        return str(pathlib.Path("tests") / f"{stem}_test.py").replace("\\", "/")

    subdir = parts[2]
    rest_dirs = parts[3:-1]  # dirs after subdir, before file
    stem = p.stem

    test_dir = pathlib.Path("tests") / subdir
    if rest_dirs:
        test_dir = test_dir.joinpath(*rest_dirs)

    return str(test_dir / f"{stem}_test.py").replace("\\", "/")


def _read_optional_text(path_str: str | None) -> str:
    """
    Read a UTF-8 text file if provided, otherwise return an empty string.
    """
    if not path_str:
        return ""

    path = pathlib.Path(path_str)
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Background file not found: {path}")
    except OSError as e:
        raise OSError(f"Could not read background file {path}: {e}") from e


def _infer_repo_name(target_input: str | None, repo_name: str | None) -> str:
    """
    Prefer explicit repo_name. Otherwise infer a reasonable repository name.
    """
    if repo_name:
        return repo_name

    if target_input:
        candidate = pathlib.Path(target_input).name
        if candidate:
            return candidate

    return pathlib.Path.cwd().name


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
    target_module_gha = _normalize_target_for_gha(args.target)
    module_name = pathlib.Path(target_module_gha).stem if target_module_gha else ""
    suggested_test_path = _compute_suggested_test_path(target_module_gha)

    background_context = args.background_text or _read_optional_text(
        args.background_file
    )
    repo_name = _infer_repo_name(args.target, args.repo_name)

    # Keep names stable and ALL CAPS to match {{...}} usage
    return {
        "TEMPLATE_NAME": args.template_name,
        "TARGET_INPUT": args.target or "",
        "TARGET_MODULE_GHA": target_module_gha,
        "MODULE_NAME": module_name,
        "SUGGESTED_TEST_PATH": suggested_test_path,
        "REPO_NAME": repo_name,
        "PROJECT_GOAL": args.project_goal or "",
        "BACKGROUND_CONTEXT": background_context,
        "BACKGROUND_FILE": args.background_file or "",
        "PROJECT_TYPE": args.project_type or "",
        "BOOTSTRAP_SCOPE": args.bootstrap_mode or "",
    }


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="create_request.py",
        description="Fill a PR request template with computed variables.",
    )
    parser.add_argument(
        "template_name",
        help=(
            "Template base name (e.g. improve_coverage or bootstrap_project) "
            "corresponding to scripts/aiprog/templates/<name>.md"
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
    if args.template_name == "improve_coverage" and not args.target:
        print(
            "error: improve_coverage requires a target module path.",
            file=sys.stderr,
        )
        return 2

    # Helpful validation for the bootstrap workflow.
    if args.template_name == "bootstrap_project":
        if not args.repo_name and not args.target:
            print(
                "error: bootstrap_project requires --repo-name or a target value "
                "that can be used as the repository identifier.",
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

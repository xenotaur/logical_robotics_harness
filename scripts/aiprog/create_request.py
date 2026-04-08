#!/usr/bin/env python3
"""
Create a filled-out PR request from a template.

Usage:
    scripts/aiprog/create_request.py improve_coverage src/lrh/analysis/llm_extractor.py

Templates live in:
    scripts/aiprog/templates/<template_name>.md

Interpolation variables use the form:
    {{VARIABLE_NAME}}
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _templates_dir() -> Path:
    return _script_dir() / "templates"


def _load_template(template_name: str) -> Tuple[Path, str]:
    template_path = _templates_dir() / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected: scripts/aiprog/templates/{template_name}.md"
        )
    return template_path, template_path.read_text(encoding="utf-8")


def _normalize_target_for_gha(target_input: str) -> str:
    """
    Normalize an input path into repo-root style module path:
        src/lrh/<...>.py

    Accepts inputs like:
        src/lrh/analysis/foo.py      -> src/lrh/analysis/foo.py
        src/lrh/analysis/foo.py      -> src/lrh/analysis/foo.py
        analysis/foo.py             -> src/lrh/analysis/foo.py  (assumed relative to src/lrh/)
    """
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
    p = Path(target_module_gha)

    # Expect: src / lrh / <subdir> / ... / <file>
    parts = p.parts
    if len(parts) < 3 or parts[0] != "src" or parts[1] != "lrh":
        # Fall back: place in tests/
        stem = p.stem
        return str(Path("tests") / f"{stem}_test.py").replace(
            "\\", "/"
        )

    subdir = parts[2]
    rest_dirs = parts[3:-1]  # dirs after subdir, before file
    stem = p.stem

    test_dir = Path("tests") / subdir
    if rest_dirs:
        test_dir = test_dir.joinpath(*rest_dirs)

    return str(test_dir / f"{stem}_test.py").replace("\\", "/")


def _render_template(template_text: str, variables: Dict[str, str]) -> str:
    """
    Simple, deterministic interpolation:
      - Replaces {{VARNAME}} with variables[VARNAME] if present.
      - Leaves unknown placeholders intact (so you can notice missing vars).
    """

    def repl(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _TEMPLATE_VAR_RE.sub(repl, template_text)


def _build_variables(template_name: str, target_input: str) -> Dict[str, str]:
    target_module_gha = _normalize_target_for_gha(target_input)
    module_name = Path(target_module_gha).stem
    suggested_test_path = _compute_suggested_test_path(target_module_gha)

    # Keep names stable and ALL CAPS to match {{...}} usage
    return {
        "TEMPLATE_NAME": template_name,
        "TARGET_INPUT": target_input,
        "TARGET_MODULE_GHA": target_module_gha,
        "MODULE_NAME": module_name,
        "SUGGESTED_TEST_PATH": suggested_test_path,
    }


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="create_request.py",
        description="Fill a PR request template with computed variables.",
    )
    parser.add_argument(
        "template_name",
        help="Template base name (e.g. improve_coverage) corresponding to scripts/aiprog/templates/<name>.md",
    )
    parser.add_argument(
        "target",
        help="Target module path (e.g. src/lrh/analysis/llm_extractor.py)",
    )
    parser.add_argument(
        "--show-vars",
        action="store_true",
        help="Print computed variables to stderr (debugging).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # print('hello from create_request.py with template "%s" and target "%s"' % (args.template_name, args.target), file=sys.stderr)
    try:
        _, template_text = _load_template(args.template_name)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    variables = _build_variables(args.template_name, args.target)

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

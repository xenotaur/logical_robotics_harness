"""Inventory a Python source tree for assist planning workflows.

Examples:
  python -m lrh.assist.sourcetree_surveyor src/lrh --format md
  python -m lrh.assist.sourcetree_surveyor src/lrh --format json
  python -m lrh.assist.sourcetree_surveyor src/lrh --tests-root tests --format md
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import json
import pathlib
import sys
import tomllib
import typing


@dataclasses.dataclass(frozen=True)
class Symbol:
    name: str
    kind: str  # "function" | "class" | "async_function"
    lineno: int
    is_private: bool
    doc: typing.Optional[str]


@dataclasses.dataclass(frozen=True)
class FileReport:
    path: str
    relpath: str
    module: str
    syntax_error: typing.Optional[str]
    functions: list[Symbol]
    classes: list[Symbol]
    has_main_guard: bool
    top_level_imports: int
    test_file_guess: typing.Optional[str]  # if tests-root provided, best guess name
    test_file_exists: typing.Optional[bool]


@dataclasses.dataclass(frozen=True)
class SurveyReport:
    schema_version: str
    survey_root: str
    tests_root: typing.Optional[str]
    tests_root_inferred: bool
    pyproject_toml_present: bool
    readme_files: list[str]
    documentation_files: list[str]
    cli_candidate_files: list[str]
    console_scripts: list[str]
    discovered_python_files: list[str]
    discovered_test_files: list[str]
    files: list[FileReport]


def _is_private(name: str) -> bool:
    # Treat dunder names and leading underscore as "private-ish".
    # NOTE: you may want to consider single-underscore as "semi-public" in your project.
    return name.startswith("_")


def _first_line(doc: typing.Optional[str]) -> typing.Optional[str]:
    if not doc:
        return None
    line = doc.strip().splitlines()[0].strip()
    return line if line else None


def _module_name_from_path(root: pathlib.Path, path: pathlib.Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    # If root is a package dir, we can treat it as module prefix "utils.foo"
    return ".".join(rel.parts)


def _guess_test_filename(src_path: pathlib.Path) -> str:
    """
    Given names.py -> names_test.py (matching your current convention)
    """
    stem = src_path.stem
    return f"{stem}_test.py"


def _count_top_level_imports(tree: ast.AST) -> int:
    n = 0
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            n += 1
    return n


def _has_main_guard(text: str) -> bool:
    # Simple string heuristic; avoids false negatives from AST formatting
    return 'if __name__ == "__main__"' in text or "if __name__=='__main__'" in text


def _should_skip_path(path: pathlib.Path) -> bool:
    return any(
        part in (".venv", "venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache")
        for part in path.parts
    )


def _infer_tests_root(root: pathlib.Path) -> typing.Optional[pathlib.Path]:
    inferred = root / "tests"
    if inferred.is_dir():
        return inferred
    return None


def _looks_like_test_file(path: pathlib.Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py")


def _read_console_scripts(pyproject_path: pathlib.Path) -> list[str]:
    if not pyproject_path.exists():
        return []
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return []
    project = data.get("project", {})
    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict):
        return []
    return sorted(str(key) for key in scripts.keys())


def _is_cli_candidate_relpath(relpath: str) -> bool:
    normalized_relpath = relpath.replace("\\", "/")
    return normalized_relpath == "cli.py" or normalized_relpath.endswith("/cli.py")


def analyze_file(
    root: pathlib.Path, path: pathlib.Path, tests_root: typing.Optional[pathlib.Path]
) -> FileReport:
    relpath = str(path.relative_to(root))
    module = _module_name_from_path(root, path)

    text = path.read_text(encoding="utf-8")
    syntax_error: typing.Optional[str] = None
    funcs: list[Symbol] = []
    clss: list[Symbol] = []
    top_level_imports = 0

    try:
        tree = ast.parse(text)
        top_level_imports = _count_top_level_imports(tree)
        for node in tree.body:  # type: ignore[attr-defined]
            if isinstance(node, ast.FunctionDef):
                funcs.append(
                    Symbol(
                        name=node.name,
                        kind="function",
                        lineno=getattr(node, "lineno", 0),
                        is_private=_is_private(node.name),
                        doc=_first_line(ast.get_docstring(node)),
                    )
                )
            elif isinstance(node, ast.AsyncFunctionDef):
                funcs.append(
                    Symbol(
                        name=node.name,
                        kind="async_function",
                        lineno=getattr(node, "lineno", 0),
                        is_private=_is_private(node.name),
                        doc=_first_line(ast.get_docstring(node)),
                    )
                )
            elif isinstance(node, ast.ClassDef):
                clss.append(
                    Symbol(
                        name=node.name,
                        kind="class",
                        lineno=getattr(node, "lineno", 0),
                        is_private=_is_private(node.name),
                        doc=_first_line(ast.get_docstring(node)),
                    )
                )
    except SyntaxError as e:
        syntax_error = f"{e.msg} (line {e.lineno}:{e.offset})"
    except UnicodeDecodeError as e:
        syntax_error = f"UnicodeDecodeError: {e}"

    test_file_guess: typing.Optional[str] = None
    test_file_exists: typing.Optional[bool] = None
    if tests_root is not None:
        test_file_guess = _guess_test_filename(path)
        test_path = tests_root / test_file_guess
        test_file_exists = test_path.exists()

    return FileReport(
        path=str(path),
        relpath=relpath,
        module=module,
        syntax_error=syntax_error,
        functions=sorted(funcs, key=lambda s: (s.is_private, s.name)),
        classes=sorted(clss, key=lambda s: (s.is_private, s.name)),
        has_main_guard=_has_main_guard(text),
        top_level_imports=top_level_imports,
        test_file_guess=test_file_guess,
        test_file_exists=test_file_exists,
    )


def scan_tree(
    root: pathlib.Path, tests_root: typing.Optional[pathlib.Path]
) -> list[FileReport]:
    reports: list[FileReport] = []
    for path in sorted(root.rglob("*.py")):
        # Skip common junk dirs
        if _should_skip_path(path):
            continue
        reports.append(analyze_file(root, path, tests_root))
    return reports


def survey_python_tree(
    root: pathlib.Path, tests_root: typing.Optional[pathlib.Path]
) -> SurveyReport:
    effective_tests_root = tests_root
    tests_root_inferred = False
    if effective_tests_root is None:
        effective_tests_root = _infer_tests_root(root)
        tests_root_inferred = effective_tests_root is not None

    reports = scan_tree(root, effective_tests_root)
    discovered_python_files = [report.relpath for report in reports]

    discovered_test_files: list[str] = []
    if effective_tests_root is not None:
        for test_path in sorted(effective_tests_root.rglob("*.py")):
            if _should_skip_path(test_path):
                continue
            if _looks_like_test_file(test_path):
                discovered_test_files.append(
                    str(test_path.relative_to(effective_tests_root))
                )

    readme_files = sorted(
        str(path.relative_to(root))
        for path in root.rglob("README.md")
        if not _should_skip_path(path)
    )
    documentation_files = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.md")
        if path.name != "README.md" and not _should_skip_path(path)
    )
    cli_candidate_files = sorted(
        report.relpath
        for report in reports
        if report.has_main_guard or _is_cli_candidate_relpath(report.relpath)
    )

    pyproject_path = root / "pyproject.toml"
    console_scripts = _read_console_scripts(pyproject_path)

    return SurveyReport(
        schema_version="1.0",
        survey_root=str(root),
        tests_root=(
            str(effective_tests_root) if effective_tests_root is not None else None
        ),
        tests_root_inferred=tests_root_inferred,
        pyproject_toml_present=pyproject_path.exists(),
        readme_files=readme_files,
        documentation_files=documentation_files,
        cli_candidate_files=cli_candidate_files,
        console_scripts=console_scripts,
        discovered_python_files=discovered_python_files,
        discovered_test_files=discovered_test_files,
        files=reports,
    )


def to_markdown(
    survey: SurveyReport,
) -> str:
    lines: list[str] = []
    lines.append(f"# Surface inventory: `{survey.survey_root}`")
    if survey.tests_root is not None:
        suffix = " (inferred)" if survey.tests_root_inferred else ""
        lines.append(f"- Tests root: `{survey.tests_root}`{suffix}")
    lines.append(f"- Files: {len(survey.files)}")
    lines.append(f"- pyproject.toml present: `{survey.pyproject_toml_present}`")
    lines.append("")

    for r in survey.files:
        lines.append(f"## `{r.relpath}`")
        lines.append(f"- module: `{r.module}`")
        if r.syntax_error:
            lines.append(f"- ⚠️ syntax error: `{r.syntax_error}`")
            lines.append("")
            continue

        if r.test_file_guess is not None:
            status = "✅ present" if r.test_file_exists else "❌ missing"
            lines.append(f"- test file: `{r.test_file_guess}` ({status})")

        flags: list[str] = []
        if r.has_main_guard:
            flags.append("has __main__ guard")
        if r.top_level_imports > 0:
            flags.append(f"{r.top_level_imports} top-level imports")
        if flags:
            lines.append(f"- notes: {', '.join(flags)}")

        pub_funcs = [s for s in r.functions if not s.is_private]
        priv_funcs = [s for s in r.functions if s.is_private]
        pub_clss = [s for s in r.classes if not s.is_private]
        priv_clss = [s for s in r.classes if s.is_private]

        def sym_line(s: Symbol) -> str:
            doc = f" — {s.doc}" if s.doc else ""
            return f"  - `{s.name}` (line {s.lineno}){doc}"

        if pub_funcs:
            lines.append("")
            lines.append("### Public functions")
            lines.extend(sym_line(s) for s in pub_funcs)

        if pub_clss:
            lines.append("")
            lines.append("### Public classes")
            lines.extend(sym_line(s) for s in pub_clss)

        if priv_funcs or priv_clss:
            lines.append("")
            lines.append("<details><summary>Private-ish symbols</summary>")
            lines.append("")
            if priv_funcs:
                lines.append("**Functions**")
                lines.extend(sym_line(s) for s in priv_funcs)
                lines.append("")
            if priv_clss:
                lines.append("**Classes**")
                lines.extend(sym_line(s) for s in priv_clss)
                lines.append("")
            lines.append("</details>")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def to_json(survey: SurveyReport) -> str:
    payload: dict[str, typing.Any] = dataclasses.asdict(survey)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _parse_args(argv: list[str], prog: str | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog=prog)
    p.add_argument("root", help="Root directory to scan (e.g., src/lrh)")
    p.add_argument(
        "--tests-root",
        default=None,
        help="Optional tests dir (e.g., tests/utils_tests)",
    )
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--out", default="-", help="Output file path, or '-' for stdout")
    return p.parse_args(argv)


def main(argv: list[str], prog: str | None = None) -> int:
    args = _parse_args(argv, prog=prog)

    root = pathlib.Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: root not found or not a directory: {root}", file=sys.stderr)
        return 2

    tests_root: typing.Optional[pathlib.Path] = None
    if args.tests_root:
        tests_root = pathlib.Path(args.tests_root).resolve()
        if not tests_root.exists() or not tests_root.is_dir():
            print(
                f"ERROR: tests-root not found or not a directory: {tests_root}",
                file=sys.stderr,
            )
            return 2

    survey = survey_python_tree(root, tests_root)
    if args.format == "md":
        out_txt = to_markdown(survey)
    else:
        out_txt = to_json(survey)

    if args.out == "-" or args.out.strip() == "":
        sys.stdout.write(out_txt)
    else:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_txt, encoding="utf-8")
        print(f"Wrote {args.format} to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

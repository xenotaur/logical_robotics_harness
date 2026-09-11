"""AST-based guardrails verifying test files comply with STYLE.md Rule 5 (unittest)."""

from __future__ import annotations

import ast
import pathlib
import sys
from typing import Sequence

PYTEST_FIXTURE_NAMES = frozenset(
    {"tmp_path", "monkeypatch", "capsys", "capfd", "caplog", "pytestconfig"}
)


class TestGuardrailViolation:
    """Represents a violation of test framework guardrails."""

    def __init__(self, path: pathlib.Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def check_test_ast(tree: ast.AST, path: pathlib.Path) -> list[TestGuardrailViolation]:
    """Check an AST tree for test framework violations."""
    violations: list[TestGuardrailViolation] = []

    for node in tree.body if isinstance(tree, ast.Module) else []:
        # Check 1: Top-level test_* functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_") or node.name.endswith("_test"):
                violations.append(
                    TestGuardrailViolation(
                        path,
                        node.lineno,
                        f"Standalone test function '{node.name}' violates "
                        "STYLE.md Rule 5. All unit tests must be methods inside a "
                        "unittest.TestCase subclass.",
                    )
                )

            for arg in node.args.args:
                if arg.arg in PYTEST_FIXTURE_NAMES:
                    violations.append(
                        TestGuardrailViolation(
                            path,
                            node.lineno,
                            f"Pytest fixture parameter '{arg.arg}' in function "
                            f"'{node.name}' is prohibited by STYLE.md Rule 5. "
                            "Use standard library unittest fixtures.",
                        )
                    )

        # Check 2: Top-level classes containing test methods
        elif isinstance(node, ast.ClassDef):
            has_test_methods = any(
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name.startswith("test_")
                for item in node.body
            )

            is_named_test = node.name.startswith("Test") or node.name.endswith("Test")
            if has_test_methods or is_named_test:
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)

                inherits_testcase = any(
                    "TestCase" in b or "Test" in b for b in base_names
                )
                if not inherits_testcase:
                    violations.append(
                        TestGuardrailViolation(
                            path,
                            node.lineno,
                            f"Test class '{node.name}' must inherit from "
                            "unittest.TestCase. Bare test classes are skipped by "
                            "unittest discover.",
                        )
                    )

            # Check methods for pytest fixtures
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in item.args.args:
                        if arg.arg in PYTEST_FIXTURE_NAMES:
                            violations.append(
                                TestGuardrailViolation(
                                    path,
                                    item.lineno,
                                    f"Pytest fixture parameter '{arg.arg}' in method "
                                    f"'{item.name}' is prohibited by STYLE.md Rule 5.",
                                )
                            )

    return violations


def check_test_file(path: pathlib.Path) -> list[TestGuardrailViolation]:
    """Parse and check a test file for guardrail violations."""
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
    except Exception as exc:
        return [TestGuardrailViolation(path, 1, f"Failed to parse test file: {exc}")]

    return check_test_ast(tree, path)


def scan_test_files(
    target_dirs: Sequence[pathlib.Path],
) -> list[TestGuardrailViolation]:
    """Scan directories for test files and return all violations."""
    all_violations: list[TestGuardrailViolation] = []

    for target in target_dirs:
        if target.is_file() and target.name.endswith("_test.py"):
            all_violations.extend(check_test_file(target))
        elif target.is_dir():
            for test_file in sorted(target.rglob("*_test.py")):
                all_violations.extend(check_test_file(test_file))

    return all_violations


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for checking test files."""
    args = list(argv if argv is not None else sys.argv[1:])
    targets = [pathlib.Path(a) for a in args] if args else [pathlib.Path("tests")]

    violations = scan_test_files(targets)
    if violations:
        print("Test framework guardrail violations (STYLE.md Rule 5):")
        for v in violations:
            print(f"  {v}")
        print(f"\nFound {len(violations)} violation(s).")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

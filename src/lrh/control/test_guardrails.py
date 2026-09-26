"""AST-based guardrails verifying test files comply with STYLE.md Rule 5
(unittest) and the Output Hygiene section (WI-TEST-OUTPUT-SUPPRESSION-AUDIT).

Output Hygiene check scope, deliberately narrow (see that work item's Risk
Notes): this only flags an uncaptured `subprocess.run`/`check_call`/`call`
invocation -- calling one of those three methods on a name literally bound
to `subprocess` (i.e. `import subprocess; subprocess.run(...)`), with none
of `capture_output`/`stdout`/`stderr` among its keyword arguments, and not
lexically nested inside a `with testing_support.suppress_output(...,
suppress_file_descriptors=True):` block (matched by name only, not by
verifying the import actually resolves to `tests.testing_support`).

That specific form -- `suppress_output` with `suppress_file_descriptors=True`
-- is required, not merely `suppress_output()` or `capture_output()`: a
real child process writes to the file descriptors it inherited from the
parent, bypassing Python's `sys.stdout`/`sys.stderr` objects entirely, so
only the `os.dup2`-based fd redirect those two helpers *don't* use by
default actually silences it (verified empirically during this work item's
self-review: a plain `capture_output()`/`suppress_output()` wrap left a
real subprocess's print output on the real terminal). A caller that needs
to assert on in-process output still uses plain `capture_output()` -- this
check never flags anything but a real subprocess call, so that usage is
unaffected.

Known limitations, accepted for this first pass rather than generalized
further:
- Does not flag unwrapped in-process calls to CLI/library entry points
  (e.g. `cli_main.main()`) -- that is a much broader, harder-to-bound
  heuristic (see the work item's Risk Notes on why this was deferred).
- Does not verify the `subprocess`/`testing_support` names actually refer
  to those modules (e.g. a local variable shadowing `subprocess` would
  produce a false positive; not observed in this repo's test tree).
- A `capture_output=False` (or `stdout=None`) keyword is still treated as
  "captured" -- this check only looks for the *keyword's presence*, not
  its value, to keep the check purely syntactic and dependency-free.
- Only covers `subprocess.run`/`.check_call`/`.call`, not `Popen` or
  other lower-level subprocess APIs.
"""

from __future__ import annotations

import ast
import pathlib
import sys
from typing import Sequence

PYTEST_FIXTURE_NAMES = frozenset(
    {"tmp_path", "monkeypatch", "capsys", "capfd", "caplog", "pytestconfig"}
)

SUBPROCESS_OUTPUT_METHODS = frozenset({"run", "check_call", "call"})
OUTPUT_CAPTURE_KEYWORDS = frozenset({"capture_output", "stdout", "stderr"})


class TestGuardrailViolation:
    """Represents a violation of test framework guardrails."""

    def __init__(self, path: pathlib.Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _is_uncaptured_subprocess_call(node: ast.Call) -> str | None:
    """Return the subprocess method name if `node` is an uncaptured
    `subprocess.run`/`.check_call`/`.call` invocation, else None."""
    func = node.func
    if not (isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_OUTPUT_METHODS):
        return None
    if not (isinstance(func.value, ast.Name) and func.value.id == "subprocess"):
        return None
    if any(kw.arg in OUTPUT_CAPTURE_KEYWORDS for kw in node.keywords):
        return None
    return func.attr


def _call_has_true_keyword(call: ast.Call, keyword_name: str) -> bool:
    """True if `call` passes `keyword_name=True` as a literal keyword."""
    return any(
        kw.arg == keyword_name
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in call.keywords
    )


def _with_provides_fd_level_suppression(with_node: ast.With | ast.AsyncWith) -> bool:
    """True if any context manager in `with_node` is a call to
    `testing_support.suppress_output(..., suppress_file_descriptors=True)`
    -- the only form that actually redirects a real subprocess's inherited
    file descriptors. `capture_output()` and a bare `suppress_output()`
    only redirect Python's own `sys.stdout`/`sys.stderr` objects via
    `contextlib.redirect_stdout`/`redirect_stderr`; a child process writes
    straight to the fds it inherited from the parent, bypassing those
    objects entirely, so neither actually silences a real subprocess
    (matched by name only, not by verifying the import resolves to
    `tests.testing_support`)."""
    for item in with_node.items:
        expr = item.context_expr
        if not isinstance(expr, ast.Call):
            continue
        func = expr.func
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            continue
        if name == "suppress_output" and _call_has_true_keyword(
            expr, "suppress_file_descriptors"
        ):
            return True
    return False


def _check_output_hygiene(
    node: ast.AST,
    path: pathlib.Path,
    *,
    captured: bool,
    violations: list[TestGuardrailViolation],
) -> None:
    """Recursively flag uncaptured subprocess calls (Output Hygiene check).

    `captured` tracks whether the node currently being visited is lexically
    nested inside a `with testing_support.suppress_output()/capture_output()`
    block -- see the module docstring for the exact scope and limits.
    """
    if isinstance(node, (ast.With, ast.AsyncWith)):
        body_captured = captured or _with_provides_fd_level_suppression(node)
        for item in node.items:
            _check_output_hygiene(
                item.context_expr, path, captured=captured, violations=violations
            )
        for child in node.body:
            _check_output_hygiene(
                child, path, captured=body_captured, violations=violations
            )
        return

    if isinstance(node, ast.Call):
        method = _is_uncaptured_subprocess_call(node)
        if method is not None and not captured:
            violations.append(
                TestGuardrailViolation(
                    path,
                    node.lineno,
                    f"Uncaptured subprocess.{method}(...) call. Wrap it in "
                    "`with tests.testing_support.suppress_output("
                    "suppress_file_descriptors=True):` (a bare "
                    "suppress_output()/capture_output() does not redirect "
                    "a real child process's inherited file descriptors), "
                    "or pass capture_output=True, per STYLE.md's Output "
                    "Hygiene section -- otherwise its output leaks into "
                    "scripts/test.",
                )
            )

    for child in ast.iter_child_nodes(node):
        _check_output_hygiene(child, path, captured=captured, violations=violations)


def check_test_ast(tree: ast.AST, path: pathlib.Path) -> list[TestGuardrailViolation]:
    """Check an AST tree for test framework violations."""
    violations: list[TestGuardrailViolation] = []

    _check_output_hygiene(tree, path, captured=False, violations=violations)

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

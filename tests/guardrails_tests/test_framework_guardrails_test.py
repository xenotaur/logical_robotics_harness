"""Unit tests for test framework guardrails (STYLE.md Rule 5)."""

from __future__ import annotations

import ast
import pathlib
import unittest

from lrh.control import test_guardrails


class TestFrameworkGuardrailsTest(unittest.TestCase):
    """Test suite verifying AST-based test framework guardrails."""

    def test_all_repository_tests_comply_with_guardrails(self) -> None:
        """Verify all existing test files in tests/ satisfy STYLE.md Rule 5."""
        repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
        tests_dir = repo_root / "tests"
        self.assertTrue(tests_dir.exists(), f"Tests dir not found: {tests_dir}")

        violations = test_guardrails.scan_test_files([tests_dir])
        if violations:
            violation_msgs = "\n".join(f"  {v}" for v in violations)
            self.fail(
                f"Repository test files violate STYLE.md Rule 5:\n{violation_msgs}"
            )

    def test_detects_standalone_test_function(self) -> None:
        """Verify standalone def test_* functions are detected."""
        source = """
import unittest

def test_standalone():
    assert True
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertIn(
            "Standalone test function 'test_standalone'",
            violations[0].message,
        )
        self.assertIn("STYLE.md Rule 5", violations[0].message)

    def test_detects_pytest_fixture_parameters(self) -> None:
        """Verify pytest fixture parameters like tmp_path are detected."""
        source = """
import unittest

class SampleTest(unittest.TestCase):
    def test_with_fixture(self, tmp_path):
        pass
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("Pytest fixture parameter 'tmp_path'", violations[0].message)

    def test_detects_unclassed_test_class(self) -> None:
        """Verify test classes that do not inherit from TestCase are detected."""
        source = """
class TestBare:
    def test_method(self):
        pass
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("must inherit from unittest.TestCase", violations[0].message)

    def test_detects_uncaptured_subprocess_call(self) -> None:
        """Verify an unwrapped subprocess.run(...) call is flagged
        (WI-TEST-OUTPUT-SUPPRESSION-AUDIT Output Hygiene check)."""
        source = """
import subprocess
import unittest

class SampleTest(unittest.TestCase):
    def test_runs_git(self) -> None:
        subprocess.run(["git", "init", "-q"], check=True)
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("Uncaptured subprocess.run(...)", violations[0].message)

    def test_subprocess_call_wrapped_in_fd_level_suppress_output_passes(
        self,
    ) -> None:
        """Verify a subprocess.run(...) wrapped in
        testing_support.suppress_output(suppress_file_descriptors=True) is
        not flagged -- that is the only form that actually redirects a
        real child process's inherited file descriptors."""
        source = """
import subprocess
import unittest

from tests import testing_support

class SampleTest(unittest.TestCase):
    def test_runs_git(self) -> None:
        with testing_support.suppress_output(suppress_file_descriptors=True):
            subprocess.run(["git", "init", "-q"], check=True)
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 0)

    def test_subprocess_call_wrapped_in_bare_suppress_output_still_flagged(
        self,
    ) -> None:
        """Verify a subprocess.run(...) wrapped in a bare
        testing_support.suppress_output() (no suppress_file_descriptors)
        is still flagged -- that form only redirects sys.stdout/sys.stderr,
        which a real child process's own fds bypass entirely."""
        source = """
import subprocess
import unittest

from tests import testing_support

class SampleTest(unittest.TestCase):
    def test_runs_git(self) -> None:
        with testing_support.suppress_output():
            subprocess.run(["git", "init", "-q"], check=True)
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 1)
        self.assertIn("Uncaptured subprocess.run(...)", violations[0].message)

    def test_subprocess_call_wrapped_in_capture_output_still_flagged(self) -> None:
        """Verify a subprocess.run(...) wrapped in
        testing_support.capture_output() is still flagged -- that helper
        has no file-descriptor-level option at all, so it never actually
        silences a real subprocess."""
        source = """
import subprocess
import unittest

from tests import testing_support

class SampleTest(unittest.TestCase):
    def test_runs_git(self) -> None:
        with testing_support.capture_output():
            subprocess.run(["git", "init", "-q"], check=True)
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 1)

    def test_subprocess_call_with_capture_output_kwarg_passes(self) -> None:
        """Verify a subprocess.run(..., capture_output=True) call is not
        flagged even when unwrapped."""
        source = """
import subprocess
import unittest

class SampleTest(unittest.TestCase):
    def test_runs_git(self) -> None:
        subprocess.run(["git", "init", "-q"], check=True, capture_output=True)
"""
        tree = ast.parse(source, filename="test_sample.py")
        violations = test_guardrails.check_test_ast(
            tree, pathlib.Path("test_sample.py")
        )
        self.assertEqual(len(violations), 0)

    def test_compliant_unittest_passes(self) -> None:
        """Verify standard compliant unittest.TestCase passes with zero violations."""
        source = """
import tempfile
import unittest

class ValidTest(unittest.TestCase):
    def test_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertTrue(True)
"""
        tree = ast.parse(source, filename="test_valid.py")
        violations = test_guardrails.check_test_ast(tree, pathlib.Path("test_valid.py"))
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()

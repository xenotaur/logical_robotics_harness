"""Unit tests for the output capture utilities in tests.testing_support."""

import contextlib
import io
import os
import subprocess
import sys
import unittest

from tests import testing_support


class CaptureUtilsTests(unittest.TestCase):
    """Unit tests for the capture utilities in tests.testing_support."""

    def test_capture_output_captures_stdout_and_stderr(self) -> None:
        outer_out = io.StringIO()
        outer_err = io.StringIO()

        with (
            contextlib.redirect_stdout(outer_out),
            contextlib.redirect_stderr(outer_err),
        ):
            with testing_support.capture_output() as inner:
                print("hello stdout")
                print("hello stderr", file=sys.stderr)

            self.assertIn("hello stdout", inner.stdout.getvalue())
            self.assertIn("hello stderr", inner.stderr.getvalue())

        self.assertEqual(outer_out.getvalue(), "")
        self.assertEqual(outer_err.getvalue(), "")

    def test_capture_output_can_leave_stderr_uncaptured(self) -> None:
        outer_out = io.StringIO()
        outer_err = io.StringIO()

        with (
            contextlib.redirect_stdout(outer_out),
            contextlib.redirect_stderr(outer_err),
        ):
            with testing_support.capture_output(capture_stderr=False) as inner:
                print("hello stdout")
                print("hello stderr", file=sys.stderr)

            self.assertIn("hello stdout", inner.stdout.getvalue())
            self.assertEqual(inner.stderr.getvalue(), "")

        self.assertEqual(outer_out.getvalue(), "")
        self.assertIn("hello stderr", outer_err.getvalue())

    def test_suppress_output_suppresses_stdout_and_stderr(self) -> None:
        outer_out = io.StringIO()
        outer_err = io.StringIO()

        with (
            contextlib.redirect_stdout(outer_out),
            contextlib.redirect_stderr(outer_err),
        ):
            with testing_support.suppress_output():
                print("noisy stdout")
                print("noisy stderr", file=sys.stderr)

        self.assertEqual(outer_out.getvalue(), "")
        self.assertEqual(outer_err.getvalue(), "")

    def test_suppress_output_can_leave_stderr_unsuppressed(self) -> None:
        outer_out = io.StringIO()
        outer_err = io.StringIO()

        with (
            contextlib.redirect_stdout(outer_out),
            contextlib.redirect_stderr(outer_err),
        ):
            with testing_support.suppress_output(suppress_stderr=False):
                print("noisy stdout")
                print("noisy stderr", file=sys.stderr)

        self.assertEqual(outer_out.getvalue(), "")
        self.assertIn("noisy stderr", outer_err.getvalue())

    def test_suppress_output_can_silence_child_processes(self) -> None:
        with testing_support.capture_output() as outer:
            with testing_support.suppress_output(suppress_file_descriptors=True):
                subprocess.run(
                    [sys.executable, "-c", "print('child output')"], check=True
                )

        self.assertEqual(outer.stdout.getvalue(), "")
        self.assertEqual(outer.stderr.getvalue(), "")

    def test_suppress_output_restores_file_descriptors(self) -> None:
        read_fd, write_fd = os.pipe()
        saved_stdout = os.dup(1)
        try:
            os.dup2(write_fd, 1)
            with testing_support.suppress_output(suppress_file_descriptors=True):
                os.write(1, b"suppressed")
            os.write(1, b"restored")
        finally:
            os.dup2(saved_stdout, 1)
            os.close(saved_stdout)
            os.close(write_fd)

        try:
            self.assertEqual(os.read(read_fd, 1024), b"restored")
        finally:
            os.close(read_fd)


if __name__ == "__main__":
    unittest.main()

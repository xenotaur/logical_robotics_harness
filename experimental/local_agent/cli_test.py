import contextlib
import io
import pathlib
import tempfile
import unittest

from local_agent import cli


class CliTest(unittest.TestCase):
    def test_unknown_packet_reports_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(
                    [
                        "--store",
                        str(pathlib.Path(tmp) / "store"),
                        "run",
                        "--packet",
                        "0" * 64,
                        "--approve",
                        "0" * 64,
                        "--backend",
                        "fake",
                    ]
                )
        self.assertEqual(code, 2)
        self.assertIn("no stored packet", stderr.getvalue())

    def test_malformed_packet_id_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(
                    ["--store", str(pathlib.Path(tmp) / "s"), "inspect", "../x"]
                )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

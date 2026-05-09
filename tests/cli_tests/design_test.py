import contextlib
import io
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh.cli import main as cli_main


class DesignCliTest(unittest.TestCase):
    def test_design_organize_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "DP-CLI.md", "adopted")

            stdout = io.StringIO()
            with unittest.mock.patch(
                "sys.argv",
                ["lrh", "design", "organize", "--project-root", str(root)],
            ):
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as err:
                        cli_main.main()

            self.assertEqual(err.exception.code, 0)
            self.assertIn("Would move:", stdout.getvalue())
            self.assertTrue((root / "project/design/proposals/DP-CLI.md").exists())

    def test_design_organize_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_proposal(root, "DP-CLI.md", "adopted")

            stdout = io.StringIO()
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "design",
                    "organize",
                    "--project-root",
                    str(root),
                    "--apply",
                ],
            ):
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as err:
                        cli_main.main()

            self.assertEqual(err.exception.code, 0)
            self.assertIn("Moved:", stdout.getvalue())
            self.assertTrue(
                (root / "project/design/proposals/adopted/DP-CLI.md").exists()
            )


def _write_proposal(
    root: pathlib.Path, relative_path: str, status: str
) -> pathlib.Path:
    path = root / "project/design/proposals" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    proposal_id = pathlib.Path(relative_path).stem
    path.write_text(
        f"---\nid: {proposal_id}\ntype: design_proposal\nstatus: {status}\n---\n\n"
        f"# {proposal_id}\n",
        encoding="utf-8",
    )
    return path

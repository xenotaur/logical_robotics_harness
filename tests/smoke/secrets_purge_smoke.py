import pathlib
import shutil
import subprocess
import tempfile
import unittest

from lrh.secrets import purge
from lrh.secrets.review import MARKER_LINE

_SECRET = "sk-purge-smoke-ab+c-test"


def _run(cmd: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)


@unittest.skipUnless(shutil.which("git-filter-repo"), "git-filter-repo not installed")
class SecretsPurgeSmokeTest(unittest.TestCase):
    def test_real_mirror_clone_rewrite_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            source_repo = tmp_path / "source"
            source_repo.mkdir()
            _run(["git", "init", "-b", "main"], source_repo)
            _run(["git", "config", "user.email", "smoke@example.com"], source_repo)
            _run(["git", "config", "user.name", "Smoke Test"], source_repo)
            secret_file = source_repo / "config.txt"
            secret_file.write_text(f"API_KEY={_SECRET}\n")
            _run(["git", "add", "config.txt"], source_repo)
            _run(["git", "commit", "-m", "add secret"], source_repo)

            refs_file = tmp_path / "refs.txt"
            refs_file.write_text("refs/heads/main\n")

            replacements_path = tmp_path / "replacements.reviewed.txt"
            replacements_path.write_text(
                f"{MARKER_LINE}\n{_SECRET}==>***REMOVED-smoke***\n"
            )

            mirror_dir = tmp_path / "mirror"

            output = purge.run_purge(
                project_root=source_repo,
                source=str(source_repo),
                refs_file=refs_file,
                replacements_path=replacements_path,
                mirror_dir=mirror_dir,
                apply=True,
            )

            self.assertIn("push --force", output)
            self.assertTrue(mirror_dir.exists())

            remaining = purge.secret_still_present(mirror_dir, _SECRET)
            self.assertFalse(remaining, "secret must not remain after rewrite")


if __name__ == "__main__":
    unittest.main()

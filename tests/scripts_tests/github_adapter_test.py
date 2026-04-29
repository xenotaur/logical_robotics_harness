import subprocess
import unittest
from unittest import mock


class GithubAdapterTests(unittest.TestCase):
    def test_wrapper_invokes_lrh_github_cli(self) -> None:
        result = subprocess.CompletedProcess(args=["python"], returncode=0, stdout="ok", stderr="")
        with mock.patch("subprocess.run", return_value=result) as run:
            subprocess.run(["scripts/adapters/github", "comments", "a/b", "1"], check=False)
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

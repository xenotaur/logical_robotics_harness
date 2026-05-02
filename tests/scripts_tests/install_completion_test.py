import subprocess
import unittest


class InstallCompletionScriptTest(unittest.TestCase):
    def test_script_runs_and_prints_guidance(self) -> None:
        result = subprocess.run(
            ["scripts/install-completion"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Detected shell:", result.stdout)
        self.assertIn("To enable completion:", result.stdout)
        self.assertIn("~/.bashrc or ~/.zshrc", result.stdout)

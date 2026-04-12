import subprocess
import sys
import unittest


class TestAiprogSmoke(unittest.TestCase):
    def test_create_request_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/aiprog/request.py", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("request.py", result.stdout)


if __name__ == "__main__":
    unittest.main()

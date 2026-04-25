import unittest
import unittest.mock

from lrh import version as version_module


class VersionModuleTest(unittest.TestCase):
    def test_format_cli_version_returns_distribution_version_when_available(
        self,
    ) -> None:
        with unittest.mock.patch(
            "importlib.metadata.version", return_value="9.9.9"
        ) as version_mock:
            result = version_module.format_cli_version()

        version_mock.assert_called_once_with(version_module.DISTRIBUTION_NAME)
        self.assertEqual(result, "lrh 9.9.9")


if __name__ == "__main__":
    unittest.main()

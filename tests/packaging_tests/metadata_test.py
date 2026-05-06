import pathlib
import tomllib
import unittest

import lrh.version


class PackageMetadataTest(unittest.TestCase):
    def _pyproject(self) -> dict[str, object]:
        pyproject_path = pathlib.Path(__file__).resolve().parents[2] / "pyproject.toml"
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    def test_distribution_name_matches_runtime_lookup_name(self) -> None:
        pyproject = self._pyproject()

        self.assertEqual(pyproject["project"]["name"], "lrh")
        self.assertEqual(lrh.version.DISTRIBUTION_NAME, "lrh")

    def test_lrh_console_script_points_to_current_cli_entry_point(self) -> None:
        pyproject = self._pyproject()

        self.assertEqual(pyproject["project"]["scripts"]["lrh"], "lrh.cli.main:main")

    def test_license_uses_pep_639_expression_without_license_classifier(self) -> None:
        pyproject = self._pyproject()

        self.assertEqual(pyproject["project"]["license"], "MIT")
        self.assertNotIn(
            "License :: OSI Approved :: MIT License",
            pyproject["project"].get("classifiers", []),
        )

    def test_default_distribution_does_not_advertise_agentic_extra(self) -> None:
        pyproject = self._pyproject()
        optional_dependencies = pyproject["project"].get("optional-dependencies", {})

        self.assertNotIn("agentic", optional_dependencies)

    def test_package_data_includes_runtime_template_trees(self) -> None:
        pyproject = self._pyproject()
        package_data = pyproject["tool"]["setuptools"]["package-data"]

        self.assertIn("templates/**/*.md", package_data["lrh.assist"])
        self.assertIn("templates/project_bootstrap/**/*.md", package_data["lrh"])


if __name__ == "__main__":
    unittest.main()

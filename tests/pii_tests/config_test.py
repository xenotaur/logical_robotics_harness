import pathlib
import tempfile
import unittest

from lrh.pii import config as pii_config


class LoadConfigTest(unittest.TestCase):
    def test_returns_built_in_defaults_when_no_config_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = pii_config.load_config(pathlib.Path(tmp))

            self.assertEqual(config.path_globs, pii_config.DEFAULT_PATH_GLOBS)
            self.assertEqual(
                config.filename_keywords, pii_config.DEFAULT_FILENAME_KEYWORDS
            )
            self.assertEqual(
                config.content_scan_scope, pii_config.CONTENT_SCAN_SCOPE_FLAGGED
            )

    def test_extends_defaults_when_use_default_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'path_globs = ["*.docx"]\n'
                'filename_keywords = ["invoice"]\n\n'
                "[extend]\nuseDefault = true\n"
            )

            config = pii_config.load_config(project_root)

            self.assertIn("*.pdf", config.path_globs)
            self.assertIn("*.docx", config.path_globs)
            self.assertIn("statement", config.filename_keywords)
            self.assertIn("invoice", config.filename_keywords)

    def test_replaces_defaults_when_use_default_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'path_globs = ["*.docx"]\n\n[extend]\nuseDefault = false\n'
            )

            config = pii_config.load_config(project_root)

            self.assertEqual(config.path_globs, ("*.docx",))
            self.assertEqual(config.filename_keywords, ())

    def test_deduplicates_globs_appearing_in_both_defaults_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'path_globs = ["*.pdf"]\n'
            )

            config = pii_config.load_config(project_root)

            self.assertEqual(config.path_globs.count("*.pdf"), 1)

    def test_malformed_toml_raises_pii_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text("not [ valid toml")

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_non_table_extend_raises_pii_config_error_not_attribute_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text("extend = true\n")

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_non_bool_use_default_raises_pii_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                '[extend]\nuseDefault = "yes"\n'
            )

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_non_list_path_globs_raises_pii_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'path_globs = "*.pdf"\n'
            )

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_non_string_list_entry_raises_pii_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                "filename_keywords = [1, 2]\n"
            )

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_content_scan_scope_all_text_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'content_scan_scope = "all-text"\n'
            )

            config = pii_config.load_config(project_root)

            self.assertEqual(
                config.content_scan_scope, pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT
            )

    def test_invalid_content_scan_scope_raises_pii_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / pii_config.CONFIG_FILENAME).write_text(
                'content_scan_scope = "everything"\n'
            )

            with self.assertRaises(pii_config.PiiConfigError):
                pii_config.load_config(project_root)

    def test_config_path_overrides_project_root_auto_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            custom_config = project_root / "custom.toml"
            custom_config.write_text('path_globs = ["*.docx"]\n')

            config = pii_config.load_config(project_root, config_path=custom_config)

            self.assertIn("*.docx", config.path_globs)

    def test_config_path_missing_falls_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            missing_config = project_root / "does-not-exist.toml"

            config = pii_config.load_config(project_root, config_path=missing_config)

            self.assertEqual(config.path_globs, pii_config.DEFAULT_PATH_GLOBS)


if __name__ == "__main__":
    unittest.main()

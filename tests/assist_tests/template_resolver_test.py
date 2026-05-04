import pathlib
import tempfile
import unittest

from lrh.assist import template_resolver


class TemplateResolverTest(unittest.TestCase):
    def test_package_fallback_resolves_existing_package_template(self) -> None:
        resolver = template_resolver.TemplateResolver(environ={})

        resolution = resolver.resolve("request/codex_prompt_from_work_item.md")
        content = resolver.read_text("request/codex_prompt_from_work_item.md")

        self.assertEqual(
            resolution.logical_name, "request/codex_prompt_from_work_item.md"
        )
        self.assertEqual(resolution.source, "package")
        self.assertEqual(
            resolution.origin,
            "lrh.assist.templates/request/codex_prompt_from_work_item.md",
        )
        self.assertIn("Codex Implementation Prompt", content)

    def test_explicit_template_directory_override_wins_over_package_fallback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_dir = pathlib.Path(temp_dir)
            _write_template(
                explicit_dir,
                "request/codex_prompt_from_work_item.md",
                "explicit override\n",
            )
            resolver = template_resolver.TemplateResolver(
                template_dirs=[explicit_dir],
                environ={},
            )

            resolution = resolver.resolve("request/codex_prompt_from_work_item.md")
            content = resolver.read_text("request/codex_prompt_from_work_item.md")

            self.assertEqual(resolution.source, "explicit")
            self.assertEqual(content, "explicit override\n")

    def test_environment_template_directory_override_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_dir = pathlib.Path(temp_dir)
            _write_template(env_dir, "request/review_response.md", "env override\n")
            resolver = template_resolver.TemplateResolver(
                environ={"LRH_TEMPLATE_DIR": str(env_dir)},
            )

            resolution = resolver.resolve("request/review_response.md")
            content = resolver.read_text("request/review_response.md")

            self.assertEqual(resolution.source, "environment")
            self.assertEqual(content, "env override\n")

    def test_project_local_template_directory_override_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            _write_template(
                project_root / ".lrh" / "templates",
                "request/review_response.md",
                "project override\n",
            )
            resolver = template_resolver.TemplateResolver(
                project_root=project_root,
                environ={},
            )

            resolution = resolver.resolve("request/review_response.md")
            content = resolver.read_text("request/review_response.md")

            self.assertEqual(resolution.source, "project")
            self.assertEqual(content, "project override\n")

    def test_user_global_config_template_directory_override_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_home = pathlib.Path(temp_dir)
            _write_template(
                config_home / "lrh" / "templates",
                "request/review_response.md",
                "user override\n",
            )
            resolver = template_resolver.TemplateResolver(
                environ={"XDG_CONFIG_HOME": str(config_home)},
            )

            resolution = resolver.resolve("request/review_response.md")
            content = resolver.read_text("request/review_response.md")

            self.assertEqual(resolution.source, "user")
            self.assertEqual(content, "user override\n")

    def test_user_global_config_defaults_to_home_when_xdg_config_home_is_unset(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir)
            _write_template(
                home / ".config" / "lrh" / "templates",
                "request/review_response.md",
                "home override\n",
            )
            resolver = template_resolver.TemplateResolver(
                environ={"HOME": str(home)},
            )

            resolution = resolver.resolve("request/review_response.md")
            content = resolver.read_text("request/review_response.md")

            self.assertEqual(resolution.source, "user")
            self.assertEqual(content, "home override\n")

    def test_precedence_order_is_deterministic_when_multiple_overrides_exist(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            explicit_dir = root / "explicit"
            env_dir = root / "env"
            project_root = root / "project"
            config_home = root / "config"
            logical_name = "request/review_response.md"
            _write_template(explicit_dir, logical_name, "explicit\n")
            _write_template(env_dir, logical_name, "env\n")
            _write_template(
                project_root / ".lrh" / "templates", logical_name, "project\n"
            )
            _write_template(config_home / "lrh" / "templates", logical_name, "user\n")
            resolver = template_resolver.TemplateResolver(
                template_dirs=[explicit_dir],
                project_root=project_root,
                environ={
                    "LRH_TEMPLATE_DIR": str(env_dir),
                    "XDG_CONFIG_HOME": str(config_home),
                },
            )

            self.assertEqual(resolver.resolve(logical_name).source, "explicit")
            self.assertEqual(resolver.read_text(logical_name), "explicit\n")

    def test_precedence_continues_to_next_source_when_higher_source_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            env_dir = root / "env"
            project_root = root / "project"
            config_home = root / "config"
            logical_name = "request/review_response.md"
            _write_template(
                project_root / ".lrh" / "templates", logical_name, "project\n"
            )
            _write_template(config_home / "lrh" / "templates", logical_name, "user\n")
            resolver = template_resolver.TemplateResolver(
                template_dirs=[root / "missing-explicit"],
                project_root=project_root,
                environ={
                    "LRH_TEMPLATE_DIR": str(env_dir),
                    "XDG_CONFIG_HOME": str(config_home),
                },
            )

            self.assertEqual(resolver.resolve(logical_name).source, "project")
            self.assertEqual(resolver.read_text(logical_name), "project\n")

    def test_missing_template_raises_clear_error(self) -> None:
        resolver = template_resolver.TemplateResolver(environ={})

        with self.assertRaisesRegex(
            FileNotFoundError,
            "Template not found: request/does_not_exist.md",
        ):
            resolver.resolve("request/does_not_exist.md")

    def test_unsafe_logical_names_are_rejected(self) -> None:
        resolver = template_resolver.TemplateResolver(environ={})
        unsafe_names = [
            "",
            "/request/review_response.md",
            "request/../review_response.md",
            "request//review_response.md",
            "request/./review_response.md",
            "C:/request/review_response.md",
            "C:\\request\\review_response.md",
            "\\\\server\\share\\template.md",
        ]

        for unsafe_name in unsafe_names:
            with self.subTest(unsafe_name=unsafe_name):
                with self.assertRaises(ValueError):
                    resolver.resolve(unsafe_name)


def _write_template(
    root: pathlib.Path, logical_name: str, content: str
) -> pathlib.Path:
    template_path = root.joinpath(*logical_name.split("/"))
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(content, encoding="utf-8")
    return template_path


if __name__ == "__main__":
    unittest.main()

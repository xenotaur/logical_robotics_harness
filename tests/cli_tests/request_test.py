import subprocess
import tempfile
import unittest
from pathlib import Path


class TestLrhRequestCli(unittest.TestCase):
    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            return subprocess.run(
                ["lrh", *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

    def test_lrh_request_help(self) -> None:
        result = self._run_lrh(["request", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh request", result.stdout)

    def test_lrh_request_prompt_from_work_item_generic_help(self) -> None:
        result = self._run_lrh(["request", "prompt-from-work-item", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh request", result.stdout)
        self.assertIn("--work-item-file", result.stdout)

    def test_lrh_request_ready_work_item_help(self) -> None:
        result = self._run_lrh(["request", "ready-work-item", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("ready-work-item", result.stdout)
        self.assertIn("--work-item", result.stdout)

    def test_lrh_request_codex_prompt_from_work_item_help(self) -> None:
        result = self._run_lrh(["request", "codex-prompt-from-work-item", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--work-item", result.stdout)
        self.assertIn("--slug", result.stdout)
        self.assertIn("--out", result.stdout)

    def test_lrh_request_list(self) -> None:
        result = self._run_lrh(["request", "list"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn("work-items:\n", result.stdout)
        self.assertIn("prompt-from-work-item", result.stdout)
        self.assertIn("ready-work-item", result.stdout)
        self.assertIn("review:\n", result.stdout)
        self.assertIn("review-response", result.stdout)

    def test_lrh_request_list_category(self) -> None:
        result = self._run_lrh(["request", "list", "--category", "review"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn("review:\n", result.stdout)
        self.assertIn("review-response", result.stdout)
        self.assertNotIn("work-items:\n", result.stdout)
        self.assertNotIn("prompt-from-work-item", result.stdout)

    def test_lrh_request_describe_canonical_name(self) -> None:
        result = self._run_lrh(["request", "describe", "prompt-from-work-item"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn("canonical name: prompt-from-work-item", result.stdout)
        self.assertIn("category: work-items", result.stdout)
        self.assertIn("legacy names: codex-prompt-from-work-item", result.stdout)
        self.assertIn("template: request/codex_prompt_from_work_item.md", result.stdout)
        self.assertNotIn("resolved from:", result.stdout)

    def test_lrh_request_describe_legacy_name(self) -> None:
        result = self._run_lrh(["request", "describe", "review_response"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            "canonical name: review-response",
            result.stdout,
        )
        self.assertIn("category: review", result.stdout)
        self.assertIn("legacy names: review_response", result.stdout)
        self.assertIn("resolved from: review_response", result.stdout)

    def test_lrh_request_describe_unknown_name(self) -> None:
        result = self._run_lrh(["request", "describe", "missing-request"])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error: unknown request name: missing-request", result.stderr)

    def test_lrh_request_canonical_improve_coverage(self) -> None:
        result = self._run_lrh(
            ["request", "improve-coverage", "src/lrh/analysis/llm_extractor.py"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("TARGET MODULE:", result.stdout)
        self.assertIn("src/lrh/analysis/llm_extractor.py", result.stdout)

    def test_lrh_request_improve_coverage(self) -> None:
        result = self._run_lrh(
            ["request", "improve_coverage", "src/lrh/analysis/llm_extractor.py"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("TARGET MODULE:", result.stdout)
        self.assertIn("src/lrh/analysis/llm_extractor.py", result.stdout)

    def test_lrh_request_invalid_arguments(self) -> None:
        result = self._run_lrh(["request", "assessment", "--scope", "work_item"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --target", result.stderr)

    def test_lrh_request_dispatches_with_leading_global_flag(self) -> None:
        result = self._run_lrh(
            [
                "--version",
                "request",
                "improve_coverage",
                "src/lrh/analysis/llm_extractor.py",
            ]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("TARGET MODULE:", result.stdout)
        self.assertNotIn("logical-robotics-harness", result.stdout)

    def test_lrh_request_help_dispatches_with_leading_global_flag(self) -> None:
        result = self._run_lrh(["--version", "request", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh request", result.stdout)

    def test_lrh_project_init_not_hijacked_when_project_root_is_request(self) -> None:
        result = self._run_lrh(
            ["project", "init", "--project-root", "request", "--dry-run"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("summary:", result.stdout)

    def test_lrh_meta_inspect_not_hijacked_when_selector_is_request(self) -> None:
        result = self._run_lrh(["meta", "inspect", "request"])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("lrh request", result.stderr)

    def test_lrh_request_codex_prompt_from_work_item_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            style_file = root / "STYLE.md"
            out_file = root / "prompt.md"
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "example-implementation",
                    "--out",
                    str(out_file),
                    "--style-file",
                    str(style_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertTrue(out_file.is_file())
            self.assertIn(
                "PROMPT(AD_HOC:EXAMPLE_IMPLEMENTATION)",
                out_file.read_text(encoding="utf-8"),
            )

    def test_lrh_request_codex_prompt_from_work_item_writes_stdout_when_out_omitted(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            style_file = root / "STYLE.md"
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "example-implementation",
                    "--style-file",
                    str(style_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertIn("PROMPT(AD_HOC:EXAMPLE_IMPLEMENTATION)", result.stdout)
            self.assertIn("Approved work item:", result.stdout)

    def test_lrh_request_codex_prompt_from_work_item_invalid_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            out_file = root / "prompt.md"
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "!!!",
                    "--out",
                    str(out_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "--slug must include at least one letter or number", result.stderr
            )
            self.assertEqual(result.stdout, "")
            self.assertFalse(out_file.exists())
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_request_codex_prompt_from_work_item_output_write_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            out_dir = root / "prompt.md"
            style_file = root / "STYLE.md"
            out_dir.mkdir()
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "example-implementation",
                    "--out",
                    str(out_dir),
                    "--style-file",
                    str(style_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)
            self.assertIn("Is a directory", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("Traceback", result.stderr)

    def test_lrh_request_audit_docs_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out_file = root / "artifacts" / "audit-docs.prompt.md"
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "audit-docs",
                    "--repo-root",
                    ".",
                    "--project-root",
                    "./lcats",
                    "--docs-root",
                    "./lcats/docs",
                    "--control-root",
                    "./lcats/project",
                    "--package-root",
                    "./lcats/lcats",
                    "--package-root",
                    "./lcats/plugins",
                    "--audit-output",
                    "./lcats/project/audits/2026-05-23-docs-audit.md",
                    "--out",
                    str(out_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertTrue(out_file.is_file())
            rendered = out_file.read_text(encoding="utf-8")
            self.assertIn("Classify documentation needs using Diátaxis", rendered)
            self.assertIn("`lcats/project/audits/2026-05-23-docs-audit.md`", rendered)
            self.assertIn("  - `lcats/lcats`", rendered)
            self.assertIn("  - `lcats/plugins`", rendered)

    def test_lrh_request_organize_docs_accepts_audit_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audit_path = root / "lcats" / "project" / "audits" / "2026-05-24-docs.md"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text("# Audit\n", encoding="utf-8")
            out_file = root / "artifacts" / "organize-docs.prompt.md"
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "organize-docs",
                    "--repo-root",
                    ".",
                    "--project-root",
                    "./lcats",
                    "--docs-root",
                    "./lcats/docs",
                    "--control-root",
                    "./lcats/project",
                    "--audit",
                    str(audit_path),
                    "--out",
                    str(out_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertTrue(out_file.is_file())
            rendered = out_file.read_text(encoding="utf-8")
            self.assertIn("read the docs audit artifact first", rendered)
            self.assertIn("2026-05-24-docs.md", rendered)

    def test_lrh_request_audit_docs_audit_shorthand_is_rejected(self) -> None:
        result = self._run_lrh(["request", "audit-docs", "--audit", "audit.md"])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("ambiguous option: --audit", result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for lrh.skills.exporter."""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from lrh.skills import exporter, installer

_PORTABLE_SKILL_MD = """---
name: {name}
description: Portable test skill.
argument-hint: "[thing]"
when_to_use: Only in tests.
---

# {name}

Plain instructions with no local tooling.
"""


class _SkillTreeMixin:
    def _make_source(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)  # type: ignore[attr-defined]
        source = parent / "skills"
        source.mkdir()
        return source

    def _make_out(self) -> Path:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent, True)  # type: ignore[attr-defined]
        return parent / "out"

    def _write_skill(
        self,
        source: Path,
        name: str,
        skill_md: str | None = None,
        extra_files: dict[str, str] | None = None,
    ) -> Path:
        skill_dir = source / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            skill_md if skill_md is not None else _PORTABLE_SKILL_MD.format(name=name)
        )
        for relative_path, content in (extra_files or {}).items():
            target = skill_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        return skill_dir

    def _archive_names(self, archive_path: Path) -> list[str]:
        with zipfile.ZipFile(archive_path) as archive:
            return sorted(archive.namelist())

    def _archive_read(self, archive_path: Path, member: str) -> str:
        with zipfile.ZipFile(archive_path) as archive:
            return archive.read(member).decode("utf-8")

    def _result(
        self, report: exporter.ExportReport, name: str
    ) -> exporter.SkillExportResult:
        return next(result for result in report.results if result.name == name)

    def _notice(
        self, result: exporter.SkillExportResult, code: str
    ) -> exporter.ExportNotice:
        for notice in result.notices:
            if notice.code == code:
                return notice
        raise AssertionError(f"no {code!r} notice in {result.notices!r}")


class TestExportSkills(_SkillTreeMixin, unittest.TestCase):
    def test_package_source_exports_public_non_manual_skills(self) -> None:
        out = self._make_out()
        report = exporter.export_skills(out_dir=out)
        self.assertFalse(report.has_failures)
        self.assertEqual(report.source_label, "lrh-package")
        exported = [
            result.name
            for result in report.results
            if result.status is exporter.ExportStatus.EXPORTED
        ]
        skipped = {
            result.name
            for result in report.results
            if result.status is exporter.ExportStatus.SKIPPED_MANUAL_ONLY
        }
        self.assertIn("lrh-design", exported)
        self.assertIn("lrh-land", skipped)
        self.assertNotIn("lrh-land", exported)
        for name in exported:
            names = self._archive_names(out / f"{name}.zip")
            self.assertIn(f"{name}/SKILL.md", names)
            self.assertEqual({entry.split("/")[0] for entry in names}, {name})
        self.assertFalse((out / "lrh-land.zip").exists())

    def test_filesystem_source_exports_single_top_level_directory(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "demo-skill",
            extra_files={
                "references/guide.md": "guide",
                "references/nested/deep.md": "deep",
                "scripts/run.py": "print('hi')\n",
                "assets/template.txt": "template",
            },
        )
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        self.assertFalse(report.has_failures)
        self.assertEqual(
            self._archive_names(out / "demo-skill.zip"),
            [
                "demo-skill/SKILL.md",
                "demo-skill/assets/template.txt",
                "demo-skill/references/guide.md",
                "demo-skill/references/nested/deep.md",
                "demo-skill/scripts/run.py",
            ],
        )

    def test_rendering_keeps_only_portable_frontmatter_and_body(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "demo-skill",
            skill_md=(
                "---\n"
                "name: demo-skill\n"
                "description: Demo.\n"
                "license: MIT\n"
                "argument-hint: '[x]'\n"
                "when_to_use: Tests.\n"
                "context: fork\n"
                "disallowed-tools: Skill\n"
                "allowed-tools: Bash\n"
                "---\n"
                "\n"
                "Body text stays exactly.\n"
            ),
        )
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        skill_md = self._archive_read(out / "demo-skill.zip", "demo-skill/SKILL.md")
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(
            frontmatter,
            {"name": "demo-skill", "description": "Demo.", "license": "MIT"},
        )
        self.assertTrue(skill_md.endswith("\nBody text stays exactly.\n"))
        notice = self._notice(self._result(report, "demo-skill"), "stripped_metadata")
        for key in ("allowed-tools", "argument-hint", "context", "when_to_use"):
            self.assertIn(key, notice.message)

    def test_canonical_source_is_not_modified(self) -> None:
        source = self._make_source()
        skill_dir = self._write_skill(source, "demo-skill")
        before = (skill_dir / "SKILL.md").read_bytes()
        exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual((skill_dir / "SKILL.md").read_bytes(), before)

    def test_codex_metadata_is_excluded_from_bundle(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "demo-skill",
            extra_files={"agents/openai.yaml": "interface:\n  display_name: Demo\n"},
        )
        out = self._make_out()
        exporter.export_skills(out_dir=out, source=source)
        self.assertEqual(
            self._archive_names(out / "demo-skill.zip"), ["demo-skill/SKILL.md"]
        )

    def test_non_portable_entries_are_skipped_with_notice(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "demo-skill",
            extra_files={
                "README.md": "readme",
                "references/.DS_Store": "junk",
                "references/kept.md": "kept",
            },
        )
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        self.assertEqual(
            self._archive_names(out / "demo-skill.zip"),
            ["demo-skill/SKILL.md", "demo-skill/references/kept.md"],
        )
        notice = self._notice(self._result(report, "demo-skill"), "skipped_entry")
        self.assertIn("`README.md`", notice.message)
        self.assertIn("`references/.DS_Store`", notice.message)
        self.assertNotIn("`references`,", notice.message)

    def test_repeated_export_is_byte_identical(self) -> None:
        source = self._make_source()
        self._write_skill(
            source, "demo-skill", extra_files={"references/guide.md": "guide"}
        )
        first = self._make_out()
        second = self._make_out()
        exporter.export_skills(out_dir=first, source=source)
        os.utime(source / "demo-skill" / "SKILL.md", (1_000_000, 1_000_000))
        exporter.export_skills(out_dir=second, source=source)
        self.assertEqual(
            (first / "demo-skill.zip").read_bytes(),
            (second / "demo-skill.zip").read_bytes(),
        )

    def test_archive_metadata_is_normalized(self) -> None:
        archive = exporter.build_archive("demo", {"b.md": b"b", "a.md": b"a"})
        with zipfile.ZipFile(io.BytesIO(archive)) as opened:
            infos = opened.infolist()
        self.assertEqual([info.filename for info in infos], ["demo/a.md", "demo/b.md"])
        for info in infos:
            self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
            self.assertEqual(info.create_system, 3)
            self.assertEqual(info.external_attr >> 16, 0o100644)

    def test_explicit_selection_exports_only_named_skills(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha-skill")
        self._write_skill(source, "beta-skill")
        out = self._make_out()
        report = exporter.export_skills(
            out_dir=out, source=source, skill_names=["beta-skill"]
        )
        self.assertEqual([result.name for result in report.results], ["beta-skill"])
        self.assertTrue((out / "beta-skill.zip").exists())
        self.assertFalse((out / "alpha-skill.zip").exists())

    def test_unknown_skill_name_is_rejected_before_writing(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha-skill")
        out = self._make_out()
        with self.assertRaisesRegex(exporter.SkillExportError, "missing-skill"):
            exporter.export_skills(
                out_dir=out,
                source=source,
                skill_names=["alpha-skill", "missing-skill"],
            )
        self.assertFalse(out.exists())

    def test_bare_string_skill_names_rejected(self) -> None:
        with self.assertRaises(TypeError):
            exporter.export_skills(
                out_dir=self._make_out(), skill_names="lrh-design"  # type: ignore[arg-type]
            )


class TestManualOnlySkills(_SkillTreeMixin, unittest.TestCase):
    def _write_manual_skills(self, source: Path) -> None:
        self._write_skill(source, "auto-skill")
        self._write_skill(
            source,
            "codex-manual",
            extra_files={
                "agents/openai.yaml": "policy:\n  allow_implicit_invocation: false\n"
            },
        )
        self._write_skill(
            source,
            "claude-manual",
            skill_md=(
                "---\n"
                "name: claude-manual\n"
                "description: Manual.\n"
                "disable-model-invocation: true\n"
                "---\n"
                "Body.\n"
            ),
        )

    def test_default_export_skips_manual_only_skills(self) -> None:
        source = self._make_source()
        self._write_manual_skills(source)
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        statuses = {result.name: result.status for result in report.results}
        self.assertEqual(statuses["auto-skill"], exporter.ExportStatus.EXPORTED)
        self.assertEqual(
            statuses["codex-manual"], exporter.ExportStatus.SKIPPED_MANUAL_ONLY
        )
        self.assertEqual(
            statuses["claude-manual"], exporter.ExportStatus.SKIPPED_MANUAL_ONLY
        )
        self.assertFalse((out / "codex-manual.zip").exists())
        self.assertFalse((out / "claude-manual.zip").exists())

    def test_explicit_manual_only_export_carries_notice(self) -> None:
        source = self._make_source()
        self._write_manual_skills(source)
        out = self._make_out()
        report = exporter.export_skills(
            out_dir=out,
            source=source,
            skill_names=["codex-manual", "claude-manual"],
        )
        for name in ("codex-manual", "claude-manual"):
            result = self._result(report, name)
            self.assertEqual(result.status, exporter.ExportStatus.EXPORTED)
            self._notice(result, "manual_only")
            self.assertTrue((out / f"{name}.zip").exists())

    def test_allow_implicit_true_is_not_manual_only(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "auto-skill",
            extra_files={
                "agents/openai.yaml": "policy:\n  allow_implicit_invocation: true\n"
            },
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.EXPORTED)

    def test_default_export_warns_about_stale_manual_only_bundle(self) -> None:
        source = self._make_source()
        self._write_manual_skills(source)
        out = self._make_out()
        exporter.export_skills(out_dir=out, source=source, skill_names=["codex-manual"])
        report = exporter.export_skills(out_dir=out, source=source)
        result = self._result(report, "codex-manual")
        self.assertEqual(result.status, exporter.ExportStatus.SKIPPED_MANUAL_ONLY)
        self._notice(result, "stale_manual_only_bundle")
        self.assertIn(
            "codex-manual.zip is still in the output directory",
            exporter.format_export_report(report),
        )

    def test_unreadable_invocation_policy_fails_safe(self) -> None:
        source = self._make_source()
        self._write_skill(
            source, "bad-policy", extra_files={"agents/openai.yaml": "policy: [1, 2]\n"}
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.FAILED)


class TestCapabilityNotices(_SkillTreeMixin, unittest.TestCase):
    def test_capability_dependent_skill_gets_notices_without_rewrite(self) -> None:
        source = self._make_source()
        body = (
            "---\nname: tool-skill\ndescription: Tools.\n---\n"
            "Run this:\n\n```bash\ngit status\ngh pr view 1\nlrh validate\n```\n"
        )
        self._write_skill(source, "tool-skill", skill_md=body)
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        result = self._result(report, "tool-skill")
        self.assertEqual(result.status, exporter.ExportStatus.EXPORTED)
        codes = {notice.code for notice in result.notices}
        self.assertTrue(
            {"requires_git", "requires_gh", "requires_lrh_cli", "requires_shell"}
            <= codes
        )
        exported = self._archive_read(out / "tool-skill.zip", "tool-skill/SKILL.md")
        self.assertTrue(exported.endswith(body.split("---\n", 2)[2]))

    def test_capability_notice_scans_references(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "ref-skill",
            extra_files={"references/steps.md": "Then run `gh api repos/x/y`."},
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        codes = {notice.code for notice in report.results[0].notices}
        self.assertIn("requires_gh", codes)
        self.assertNotIn("requires_git", codes)

    def test_plain_skill_has_no_capability_notices(self) -> None:
        source = self._make_source()
        self._write_skill(source, "plain-skill")
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        codes = {notice.code for notice in report.results[0].notices}
        self.assertFalse({code for code in codes if code.startswith("requires_")})

    def test_formatted_report_groups_capability_notices(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "tool-skill",
            skill_md=(
                "---\nname: tool-skill\ndescription: Tools.\n---\n"
                "```bash\ngit status\ngh pr view 1\n```\n"
            ),
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        text = exporter.format_export_report(report)
        capability_lines = [line for line in text.splitlines() if "cannot run" in line]
        self.assertEqual(len(capability_lines), 1)
        self.assertIn("local `git`", capability_lines[0])
        self.assertIn("the GitHub `gh` CLI", capability_lines[0])


class TestExportValidation(_SkillTreeMixin, unittest.TestCase):
    def _assert_fails_without_writing(
        self, source: Path, fragment: str
    ) -> exporter.ExportReport:
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        self.assertTrue(report.has_failures)
        failed = [
            result
            for result in report.results
            if result.status is exporter.ExportStatus.FAILED
        ]
        self.assertTrue(
            any(fragment in error for result in failed for error in result.errors),
            [result.errors for result in failed],
        )
        self.assertFalse(out.exists())
        return report

    def test_missing_skill_md_fails(self) -> None:
        source = self._make_source()
        (source / "empty-skill" / "references").mkdir(parents=True)
        (source / "empty-skill" / "references" / "x.md").write_text("x")
        self._assert_fails_without_writing(source, "missing SKILL.md")

    def test_missing_frontmatter_fails(self) -> None:
        source = self._make_source()
        self._write_skill(source, "no-front", skill_md="# Just a heading\n")
        self._assert_fails_without_writing(source, "YAML frontmatter")

    def test_malformed_frontmatter_yaml_fails(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "bad-yaml",
            skill_md="---\nname: bad-yaml\ndescription: [unclosed\n---\nBody\n",
        )
        self._assert_fails_without_writing(source, "invalid YAML")

    def test_name_must_match_directory(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "right-name",
            skill_md="---\nname: other-name\ndescription: X.\n---\nBody\n",
        )
        self._assert_fails_without_writing(source, "must match the skill directory")

    def test_invalid_name_characters_fail(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "Bad_Name",
            skill_md="---\nname: Bad_Name\ndescription: X.\n---\nBody\n",
        )
        self._assert_fails_without_writing(source, "lowercase letters")

    def test_missing_description_fails(self) -> None:
        source = self._make_source()
        self._write_skill(source, "no-desc", skill_md="---\nname: no-desc\n---\nB\n")
        self._assert_fails_without_writing(source, "description must be")

    def test_overlong_description_fails(self) -> None:
        source = self._make_source()
        long_description = "x" * (exporter.MAX_DESCRIPTION_LENGTH + 1)
        self._write_skill(
            source,
            "long-desc",
            skill_md=f"---\nname: long-desc\ndescription: {long_description}\n---\n",
        )
        self._assert_fails_without_writing(source, "limit is 1024")

    def test_one_failure_blocks_all_writes(self) -> None:
        source = self._make_source()
        self._write_skill(source, "good-skill")
        self._write_skill(source, "bad-skill", skill_md="no frontmatter\n")
        report = self._assert_fails_without_writing(source, "YAML frontmatter")
        good = self._result(report, "good-skill")
        self.assertEqual(good.status, exporter.ExportStatus.EXPORTED)
        self.assertIn("not written", exporter.format_export_report(report))

    def test_file_count_limit_enforced(self) -> None:
        source = self._make_source()
        files = {
            f"references/file-{index:03d}.md": "x"
            for index in range(exporter.MAX_FILE_COUNT)
        }
        self._write_skill(source, "big-skill", extra_files=files)
        self._assert_fails_without_writing(source, "limit is 500")

    def test_output_path_that_is_a_file_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        out = self._make_out()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("not a directory")
        with self.assertRaisesRegex(exporter.SkillExportError, "not a directory"):
            exporter.export_skills(out_dir=out, source=source)


class TestExportSafety(_SkillTreeMixin, unittest.TestCase):
    def test_symlinked_file_inside_skill_is_rejected(self) -> None:
        source = self._make_source()
        skill_dir = self._write_skill(source, "link-skill")
        outside = source.parent / "secret.txt"
        outside.write_text("secret")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "leak.md").symlink_to(outside)
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        result = self._result(report, "link-skill")
        self.assertEqual(result.status, exporter.ExportStatus.FAILED)
        self.assertIn("symlink", " ".join(result.errors))
        self.assertFalse(out.exists())

    def test_symlinked_skill_directory_is_rejected(self) -> None:
        source = self._make_source()
        real = self._write_skill(source.parent, "real-skill")
        (source / "real-skill").symlink_to(real)
        with self.assertRaisesRegex(installer.SkillSourceError, "symlink"):
            exporter.export_skills(out_dir=self._make_out(), source=source)

    def test_planted_temp_symlink_is_not_followed(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        out = self._make_out()
        out.mkdir(parents=True)
        victim = out.parent / "victim.txt"
        victim.write_text("keep me")
        (out / ".demo-skill.zip.tmp").symlink_to(victim)
        exporter.export_skills(out_dir=out, source=source)
        self.assertEqual(victim.read_text(), "keep me")
        archive = out / "demo-skill.zip"
        self.assertFalse(archive.is_symlink())
        self.assertIn("demo-skill/SKILL.md", self._archive_names(archive))

    def test_escaping_and_duplicate_paths_are_rejected(self) -> None:
        errors = exporter._path_errors(
            {
                "references/../escape.md": b"x",
                "/references/abs.md": b"x",
                "references\\win.md": b"x",
                "references/Case.md": b"x",
                "references/case.md": b"x",
            }
        )
        joined = "\n".join(errors)
        self.assertIn("references/../escape.md", joined)
        self.assertIn("/references/abs.md", joined)
        self.assertIn("references\\\\win.md", joined)
        self.assertIn("duplicate archive path", joined)

    def test_safe_paths_have_no_errors(self) -> None:
        self.assertEqual(
            exporter._path_errors(
                {"SKILL.md": b"x", "references/a/b.md": b"x", "assets/c.png": b"x"}
            ),
            [],
        )


class TestChatGPTSkillRenderer(unittest.TestCase):
    def test_renderer_satisfies_skill_renderer_protocol(self) -> None:
        renderer: installer.SkillRenderer = exporter.ChatGPTSkillRenderer()
        rendered = renderer.render(
            "demo",
            {
                "SKILL.md": (
                    b"---\nname: demo\ndescription: D.\nwhen_to_use: W.\n---\nB\n"
                ),
                "agents/openai.yaml": b"policy: {}\n",
                "references/r.md": b"r",
                "notes.txt": b"n",
            },
        )
        self.assertEqual(sorted(rendered), ["SKILL.md", "references/r.md"])
        self.assertNotIn(b"when_to_use", rendered["SKILL.md"])

    def test_renderer_leaves_frontmatterless_skill_md_unchanged(self) -> None:
        rendered = exporter.ChatGPTSkillRenderer().render(
            "demo", {"SKILL.md": b"# plain\n"}
        )
        self.assertEqual(rendered["SKILL.md"], b"# plain\n")


if __name__ == "__main__":
    unittest.main()

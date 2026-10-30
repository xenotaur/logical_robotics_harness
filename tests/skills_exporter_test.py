"""Unit tests for lrh.skills.exporter."""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

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
            {"name": "demo-skill", "description": "Demo. Tests.", "license": "MIT"},
        )
        self.assertTrue(skill_md.endswith("\nBody text stays exactly.\n"))
        notice = self._notice(self._result(report, "demo-skill"), "stripped_metadata")
        for key in ("allowed-tools", "argument-hint", "context"):
            self.assertIn(key, notice.message)
        self.assertNotIn("when_to_use", notice.message)

    def test_non_string_frontmatter_key_is_stripped_without_error(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "odd-keys",
            skill_md="---\nname: odd-keys\ndescription: X.\n1: one\n---\nBody\n",
        )
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        result = self._result(report, "odd-keys")
        self.assertEqual(result.status, exporter.ExportStatus.EXPORTED)
        self.assertIn("`1`", self._notice(result, "stripped_metadata").message)

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

    def test_non_mapping_openai_yaml_root_fails_safe(self) -> None:
        source = self._make_source()
        self._write_skill(
            source, "list-root", extra_files={"agents/openai.yaml": "[]\n"}
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.FAILED)
        self.assertIn("invocation policy", report.results[0].errors[0])

    def test_quoted_manual_only_markers_fail_safe(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "quoted-claude",
            skill_md=(
                "---\nname: quoted-claude\ndescription: Q.\n"
                "disable-model-invocation: 'true'\n---\nB\n"
            ),
        )
        self._write_skill(
            source,
            "quoted-codex",
            extra_files={
                "agents/openai.yaml": 'policy:\n  allow_implicit_invocation: "false"\n'
            },
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        for name in ("quoted-claude", "quoted-codex"):
            result = self._result(report, name)
            self.assertEqual(result.status, exporter.ExportStatus.FAILED)
            self.assertIn("must be true or false", " ".join(result.errors))

    def test_blank_manual_only_markers_fail_safe(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "blank-claude",
            skill_md=(
                "---\nname: blank-claude\ndescription: Q.\n"
                "disable-model-invocation:\n---\nB\n"
            ),
        )
        self._write_skill(
            source,
            "blank-codex",
            extra_files={
                "agents/openai.yaml": "policy:\n  allow_implicit_invocation:\n"
            },
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        for name in ("blank-claude", "blank-codex"):
            result = self._result(report, name)
            self.assertEqual(result.status, exporter.ExportStatus.FAILED)
            self.assertIn("must be true or false", " ".join(result.errors))

    def test_valid_claude_marker_does_not_hide_bad_codex_policy(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "both-markers",
            skill_md=(
                "---\nname: both-markers\ndescription: Q.\n"
                "disable-model-invocation: true\n---\nB\n"
            ),
            extra_files={
                "agents/openai.yaml": "policy:\n  allow_implicit_invocation:\n"
            },
        )
        report = exporter.export_skills(
            out_dir=self._make_out(), source=source, skill_names=["both-markers"]
        )
        result = self._result(report, "both-markers")
        self.assertEqual(result.status, exporter.ExportStatus.FAILED)
        self.assertIn("allow_implicit_invocation", " ".join(result.errors))

    def test_absent_manual_only_markers_do_not_fail(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "no-markers",
            extra_files={"agents/openai.yaml": "policy:\n  other: 1\n"},
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.EXPORTED)

    def test_empty_openai_yaml_is_not_manual_only(self) -> None:
        source = self._make_source()
        self._write_skill(
            source, "empty-policy", extra_files={"agents/openai.yaml": ""}
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.EXPORTED)

    def test_unreadable_invocation_policy_fails_safe(self) -> None:
        source = self._make_source()
        self._write_skill(
            source, "bad-policy", extra_files={"agents/openai.yaml": "policy: [1, 2]\n"}
        )
        report = exporter.export_skills(out_dir=self._make_out(), source=source)
        self.assertEqual(report.results[0].status, exporter.ExportStatus.FAILED)


class TestWhenToUse(_SkillTreeMixin, unittest.TestCase):
    def _export_one(
        self, name: str, skill_md: str
    ) -> tuple[exporter.SkillExportResult, str]:
        source = self._make_source()
        self._write_skill(source, name, skill_md=skill_md)
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        result = self._result(report, name)
        self.assertEqual(result.status, exporter.ExportStatus.EXPORTED, result.errors)
        return result, self._archive_read(out / f"{name}.zip", f"{name}/SKILL.md")

    def test_short_guidance_folds_into_description_with_single_space(self) -> None:
        result, skill_md = self._export_one(
            "fold-skill",
            "---\nname: fold-skill\ndescription: >\n  Does a thing.\n"
            "when_to_use: >\n  Use it for tests.\n---\n# fold-skill\n\nBody.\n",
        )
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(frontmatter["description"], "Does a thing. Use it for tests.")
        self.assertNotIn("## When to use", skill_md)
        self.assertTrue(skill_md.endswith("# fold-skill\n\nBody.\n"))
        codes = {notice.code for notice in result.notices}
        self.assertNotIn("when_to_use_section", codes)
        self.assertNotIn("stripped_metadata", codes)

    def test_fold_exactly_at_limit_stays_folded(self) -> None:
        guidance = "g" * (exporter.MAX_DESCRIPTION_LENGTH - len("D.") - 1)
        _result, skill_md = self._export_one(
            "edge-skill",
            "---\nname: edge-skill\ndescription: D.\n"
            f"when_to_use: {guidance}\n---\nB\n",
        )
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(
            len(frontmatter["description"]), exporter.MAX_DESCRIPTION_LENGTH
        )
        self.assertNotIn("## When to use", skill_md)

    def test_over_limit_guidance_becomes_section_after_first_h1(self) -> None:
        description = "d" * 1000
        guidance = "Only when explicitly asked. Do not invoke proactively."
        result, skill_md = self._export_one(
            "long-skill",
            f"---\nname: long-skill\ndescription: {description}\n"
            f"when_to_use: {guidance}\n---\n\n# long-skill Skill\n\nOriginal body.\n",
        )
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(frontmatter["description"], description)
        self.assertNotIn("when_to_use", frontmatter)
        body = skill_md.split("---\n", 2)[2]
        self.assertEqual(
            body,
            "\n# long-skill Skill\n\n## When to use\n\n"
            f"{guidance}\n\nOriginal body.\n",
        )
        self._notice(result, "when_to_use_section")
        stripped = [n for n in result.notices if n.code == "stripped_metadata"]
        self.assertFalse(stripped)

    def test_section_without_h1_goes_to_top(self) -> None:
        _result, skill_md = self._export_one(
            "noh1-skill",
            f"---\nname: noh1-skill\ndescription: {'d' * 1020}\n"
            "when_to_use: Guidance.\n---\nPlain body.\n",
        )
        body = skill_md.split("---\n", 2)[2]
        self.assertEqual(body, "## When to use\n\nGuidance.\n\nPlain body.\n")

    def test_section_goes_to_top_when_body_does_not_open_with_h1(self) -> None:
        _result, skill_md = self._export_one(
            "fence-skill",
            f"---\nname: fence-skill\ndescription: {'d' * 1020}\n"
            "when_to_use: Guidance.\n---\n"
            "```\n# not a heading\n```\n# Real\n\nText.\n",
        )
        body = skill_md.split("---\n", 2)[2]
        self.assertEqual(
            body,
            "## When to use\n\nGuidance.\n\n"
            "```\n# not a heading\n```\n# Real\n\nText.\n",
        )

    def test_fold_one_over_limit_becomes_section(self) -> None:
        guidance = "g" * (exporter.MAX_DESCRIPTION_LENGTH - len("D."))
        result, skill_md = self._export_one(
            "over-skill",
            "---\nname: over-skill\ndescription: D.\n"
            f"when_to_use: {guidance}\n---\nB\n",
        )
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(frontmatter["description"], "D.")
        self.assertIn("## When to use", skill_md)
        self._notice(result, "when_to_use_section")

    def test_section_placement_follows_opening_title(self) -> None:
        insert = exporter._insert_when_to_use_section
        top = "## When to use\n\nG\n\n"
        cases = {
            "leading blank lines before title": (
                "\n\n# Title\nText\n",
                "\n\n# Title\n\n## When to use\n\nG\n\nText\n",
            ),
            "indented title": (
                "   # Title\nBody\n",
                "   # Title\n\n## When to use\n\nG\n\nBody\n",
            ),
            "title at end without newline": (
                "# Title",
                "# Title\n\n## When to use\n\nG\n",
            ),
            "fence before title": (
                "```\n# inside\n```\n# Real\n",
                top + "```\n# inside\n```\n# Real\n",
            ),
            "backtick info string before title": (
                "``` a`b\n# Real\n",
                top + "``` a`b\n# Real\n",
            ),
            "html comment before title": (
                "<!--\n# example\n-->\n# Real\nText\n",
                top + "<!--\n# example\n-->\n# Real\nText\n",
            ),
            "four-space indent is not a title": (
                "    # code\n",
                top + "    # code\n",
            ),
            "h2 is not a title": ("## Sub\n", top + "## Sub\n"),
            "line separator is not a line break": (
                "# Title\u2028more\nBody\n",
                "# Title\u2028more\n\n## When to use\n\nG\n\nBody\n",
            ),
        }
        for label, (body, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(insert(body, "G"), expected)

    def test_section_matches_crlf_body_line_endings(self) -> None:
        insert = exporter._insert_when_to_use_section
        self.assertEqual(
            insert("# Title\r\n\r\nBody\r\n", "one\ntwo"),
            "# Title\r\n\r\n## When to use\r\n\r\none\r\ntwo\r\n\r\nBody\r\n",
        )
        self.assertEqual(
            insert("Body\r\n", "one\ntwo"),
            "## When to use\r\n\r\none\r\ntwo\r\n\r\nBody\r\n",
        )

    def test_canonical_skills_never_drop_when_to_use(self) -> None:
        out = self._make_out()
        report = exporter.export_skills(out_dir=out)
        self.assertFalse(report.has_failures)
        sectioned = set()
        for result in report.results:
            if result.status is not exporter.ExportStatus.EXPORTED:
                continue
            for notice in result.notices:
                if notice.code == "stripped_metadata":
                    self.assertNotIn("when_to_use", notice.message)
                if notice.code == "when_to_use_section":
                    sectioned.add(result.name)
            skill_md = self._archive_read(
                out / f"{result.name}.zip", f"{result.name}/SKILL.md"
            )
            frontmatter = yaml.safe_load(skill_md.split("---")[1])
            self.assertLessEqual(
                len(frontmatter["description"]), exporter.MAX_DESCRIPTION_LENGTH
            )
            self.assertEqual(result.name in sectioned, "## When to use" in skill_md)
        self.assertIn("lrh-export-claude", sectioned)


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
        self.assertIn("against your local repository or machine", capability_lines[0])


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

    def test_malformed_optional_portable_fields_fail(self) -> None:
        cases = {
            "bad-license": ("license: 5\n", "license must be a string"),
            "bad-compat": ("compatibility: " + "c" * 501 + "\n", "limit is 500"),
            "empty-compat": (
                "compatibility: ''\n",
                "compatibility must be a non-blank",
            ),
            "blank-compat": (
                "compatibility: '   '\n",
                "compatibility must be a non-blank",
            ),
            "bad-metadata": ("metadata: [1, 2]\n", "metadata must map"),
            "bad-metadata-value": ("metadata:\n  key: 3\n", "metadata must map"),
        }
        for name, (extra, fragment) in cases.items():
            with self.subTest(name=name):
                source = self._make_source()
                self._write_skill(
                    source,
                    name,
                    skill_md=f"---\nname: {name}\ndescription: X.\n{extra}---\nB\n",
                )
                self._assert_fails_without_writing(source, fragment)

    def test_blank_or_non_string_when_to_use_fails(self) -> None:
        cases = {
            "null-wtu": "when_to_use:\n",
            "blank-wtu": "when_to_use: '   '\n",
            "list-wtu": "when_to_use: [a, b]\n",
        }
        for name, extra in cases.items():
            with self.subTest(name=name):
                source = self._make_source()
                self._write_skill(
                    source,
                    name,
                    skill_md=f"---\nname: {name}\ndescription: X.\n{extra}---\nB\n",
                )
                self._assert_fails_without_writing(
                    source, "when_to_use must be a non-blank string"
                )

    def test_valid_optional_portable_fields_are_kept(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "full-fields",
            skill_md=(
                "---\nname: full-fields\ndescription: X.\nlicense: MIT\n"
                "compatibility: Needs nothing.\nmetadata:\n  owner: lrh\n---\nB\n"
            ),
        )
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        self.assertFalse(report.has_failures)
        skill_md = self._archive_read(out / "full-fields.zip", "full-fields/SKILL.md")
        frontmatter = yaml.safe_load(skill_md.split("---")[1])
        self.assertEqual(frontmatter["metadata"], {"owner": "lrh"})
        self.assertEqual(frontmatter["compatibility"], "Needs nothing.")
        self.assertEqual(frontmatter["license"], "MIT")

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

    def test_output_inside_source_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        for out in (source, source / "exports", source / "demo-skill" / "out"):
            with self.subTest(out=out):
                with self.assertRaisesRegex(
                    exporter.SkillExportError, "inside the skill source"
                ):
                    exporter.export_skills(out_dir=out, source=source)
                self.assertFalse((out / "demo-skill.zip").exists())

    def test_output_inside_source_via_symlink_or_case_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        alias = source.parent / "alias"
        alias.symlink_to(source)
        variants = [alias / "exports"]
        upper = source.parent / source.name.upper()
        if upper.exists() and os.path.samefile(upper, source):
            # Case-insensitive filesystem: a differently-cased path is the
            # same directory and must be caught too.
            variants.append(upper / "exports")
        for out in variants:
            with self.subTest(out=out):
                with self.assertRaisesRegex(
                    exporter.SkillExportError, "inside the skill source"
                ):
                    exporter.export_skills(out_dir=out, source=source)
        self.assertFalse((source / "exports").exists())

    def test_promotion_failure_removes_remaining_temporaries(self) -> None:
        out = self._make_out()
        out.mkdir(parents=True)
        blocked = out / "beta-skill.zip"
        original_replace = os.replace

        def failing_replace(src: object, dst: object) -> None:
            if Path(dst) == blocked:
                raise PermissionError("simulated")
            original_replace(src, dst)

        with mock.patch.object(exporter.os, "replace", failing_replace):
            with self.assertRaisesRegex(exporter.SkillExportError, "could not publish"):
                exporter._publish_archives(
                    [
                        (out / "alpha-skill.zip", b"a"),
                        (blocked, b"b"),
                        (out / "gamma-skill.zip", b"c"),
                    ]
                )
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["alpha-skill.zip"])

    def test_symlinked_output_directory_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        real_out = self._make_out()
        real_out.mkdir(parents=True)
        link = real_out.parent / "linked-out"
        link.symlink_to(real_out)
        with self.assertRaisesRegex(exporter.SkillExportError, "symlink"):
            exporter.export_skills(out_dir=link, source=source)
        self.assertEqual(list(real_out.iterdir()), [])

    def test_directory_at_destination_blocks_whole_batch(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha-skill")
        self._write_skill(source, "beta-skill")
        out = self._make_out()
        (out / "beta-skill.zip").mkdir(parents=True)
        with self.assertRaisesRegex(exporter.SkillExportError, "is a directory"):
            exporter.export_skills(out_dir=out, source=source)
        self.assertEqual(
            sorted(path.name for path in out.iterdir()), ["beta-skill.zip"]
        )

    def test_staging_failure_leaves_no_partial_batch(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha-skill")
        self._write_skill(source, "beta-skill")
        out = self._make_out()
        # A directory at beta's temp path makes staging beta fail after alpha
        # has already been staged.
        (out / ".beta-skill.zip.tmp").mkdir(parents=True)
        with self.assertRaisesRegex(exporter.SkillExportError, "could not write"):
            exporter.export_skills(out_dir=out, source=source)
        self.assertEqual(
            sorted(path.name for path in out.iterdir()), [".beta-skill.zip.tmp"]
        )

    def test_output_path_that_is_a_file_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        out = self._make_out()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("not a directory")
        with self.assertRaisesRegex(exporter.SkillExportError, "not a directory"):
            exporter.export_skills(out_dir=out, source=source)


class TestHiddenSourceEntries(_SkillTreeMixin, unittest.TestCase):
    def test_hidden_directory_is_not_a_skill(self) -> None:
        source = self._make_source()
        self._write_skill(source, "demo-skill")
        (source / ".git" / "objects").mkdir(parents=True)
        (source / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        out = self._make_out()
        report = exporter.export_skills(out_dir=out, source=source)
        self.assertFalse(report.has_failures)
        self.assertEqual([r.name for r in report.results], ["demo-skill"])
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["demo-skill.zip"])


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
        self.assertIn(b"description: D. W.", rendered["SKILL.md"])

    def test_renderer_leaves_frontmatterless_skill_md_unchanged(self) -> None:
        rendered = exporter.ChatGPTSkillRenderer().render(
            "demo", {"SKILL.md": b"# plain\n"}
        )
        self.assertEqual(rendered["SKILL.md"], b"# plain\n")


_MANUAL_SKILL_MD = """---
name: {name}
description: Manual-only test skill.
argument-hint: "[pr-url]"
disable-model-invocation: true
when_to_use: Only when typed.
---

# {name}

Run $ARGUMENTS by hand.
"""


class TestClaudePluginExport(_SkillTreeMixin, unittest.TestCase):
    def _export(self, source: Path, out: Path) -> exporter.ExportReport:
        return exporter.export_skills(
            out_dir=out, source=source, target=exporter.ExportTarget.CLAUDE_PLUGIN
        )

    def _snapshot(self, root: Path) -> dict[str, bytes | str]:
        snapshot: dict[str, bytes | str] = {}
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot[relative] = f"symlink:{os.readlink(path)}"
            elif path.is_file():
                snapshot[relative] = path.read_bytes()
            else:
                snapshot[relative] = "dir"
        return snapshot

    def _plugin_skills(self, out: Path) -> list[str]:
        return sorted(
            path.name
            for path in (out / exporter.CLAUDE_PLUGIN_DIR / "skills").iterdir()
        )

    def test_writes_marketplace_and_plugin_manifests(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()

        report = self._export(source, out)

        self.assertFalse(report.has_failures)
        marketplace = json.loads((out / exporter.CLAUDE_MARKETPLACE_PATH).read_text())
        self.assertEqual(
            marketplace["plugins"],
            [
                {
                    "name": "lrh",
                    "source": "./plugins/lrh",
                    "description": marketplace["plugins"][0]["description"],
                }
            ],
        )
        self.assertIn("name", marketplace["owner"])
        plugin = json.loads(
            (
                out / exporter.CLAUDE_PLUGIN_DIR / ".claude-plugin" / "plugin.json"
            ).read_text()
        )
        self.assertEqual(plugin["name"], "lrh")
        self.assertNotIn("version", plugin)
        self.assertNotIn("version", marketplace["plugins"][0])
        self.assertEqual(
            self._result(report, "alpha").archive_path,
            out / exporter.CLAUDE_PLUGIN_DIR / "skills" / "alpha",
        )

    def test_manual_only_skills_are_included_with_frontmatter_unchanged(
        self,
    ) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        manual = self._write_skill(
            source, "manual", skill_md=_MANUAL_SKILL_MD.format(name="manual")
        )
        out = self._make_out()

        report = self._export(source, out)

        self.assertEqual(self._plugin_skills(out), ["alpha", "manual"])
        self.assertEqual(
            self._result(report, "manual").status, exporter.ExportStatus.EXPORTED
        )
        skills = out / exporter.CLAUDE_PLUGIN_DIR / "skills"
        self.assertEqual(
            (skills / "manual" / "SKILL.md").read_bytes(),
            (manual / "SKILL.md").read_bytes(),
        )
        self.assertEqual(
            (skills / "alpha" / "SKILL.md").read_bytes(),
            (source / "alpha" / "SKILL.md").read_bytes(),
        )

    def test_excludes_agents_hidden_and_non_bundle_entries(self) -> None:
        source = self._make_source()
        self._write_skill(
            source,
            "alpha",
            extra_files={
                "agents/openai.yaml": "policy:\n  allow_implicit_invocation: false\n",
                "references/guide.md": "guide\n",
                "scripts/run.py": "print('hi')\n",
                "assets/logo.txt": "logo\n",
                "references/.DS_Store": "junk",
                "examples/demo.md": "demo\n",
            },
        )
        (source / "_shared").mkdir()
        (source / "_shared" / "note.md").write_text("shared\n")
        out = self._make_out()

        report = self._export(source, out)

        skill_dir = out / exporter.CLAUDE_PLUGIN_DIR / "skills" / "alpha"
        self.assertEqual(
            sorted(installer._collect_fs_files(skill_dir)),
            [
                "SKILL.md",
                "assets/logo.txt",
                "references/guide.md",
                "scripts/run.py",
            ],
        )
        self.assertEqual(self._plugin_skills(out), ["alpha"])
        self.assertFalse((out / exporter.CLAUDE_PLUGIN_DIR / "bin").exists())
        notice = self._notice(self._result(report, "alpha"), "skipped_entry")
        self.assertIn("not included in the plugin", notice.message)
        self.assertIn("`examples`", notice.message)
        self.assertNotIn("agents", notice.message)

    def test_export_is_deterministic_and_matches_in_memory_render(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha", extra_files={"references/a.md": "a\n"})
        self._write_skill(source, "beta")
        first = self._make_out()
        second = self._make_out()

        self._export(source, first)
        self._export(source, second)
        self._export(source, second)

        self.assertEqual(self._snapshot(first), self._snapshot(second))
        tree = exporter.render_claude_plugin_tree(source)
        written = {
            path.relative_to(first).as_posix(): path.read_bytes()
            for path in first.rglob("*")
            if path.is_file()
        }
        self.assertEqual(written, tree)

    def test_canonical_source_is_not_modified(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha", extra_files={"agents/openai.yaml": "{}\n"})
        before = self._snapshot(source)

        self._export(source, self._make_out())

        self.assertEqual(self._snapshot(source), before)

    def test_reexport_removes_stale_skills_and_files(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha", extra_files={"references/old.md": "old\n"})
        self._write_skill(source, "beta")
        out = self._make_out()
        self._export(source, out)

        shutil.rmtree(source / "beta")
        (source / "alpha" / "references" / "old.md").unlink()
        self._write_skill(source, "gamma")
        report = self._export(source, out)

        self.assertEqual(self._plugin_skills(out), ["alpha", "gamma"])
        self.assertEqual(report.removed, ("beta",))
        self.assertFalse(
            (
                out / exporter.CLAUDE_PLUGIN_DIR / "skills" / "alpha" / "references"
            ).exists()
        )
        self.assertIn("removed (stale): beta", exporter.format_export_report(report))

    def test_unrelated_output_files_are_untouched(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        unrelated = {
            "README.md": "readme\n",
            ".claude-plugin/plugin.json": "{}\n",
            "plugins/other/keep.md": "other plugin\n",
            "plugins/lrh-extra.md": "sibling\n",
            "src/code.py": "pass\n",
        }
        for relative_path, content in unrelated.items():
            target = out / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        before = self._snapshot(out)

        self._export(source, out)
        self._export(source, out)

        after = self._snapshot(out)
        managed = (exporter.CLAUDE_MARKETPLACE_PATH, exporter.CLAUDE_PLUGIN_DIR)

        def unmanaged(snapshot: dict[str, bytes | str]) -> dict[str, bytes | str]:
            return {
                path: value
                for path, value in snapshot.items()
                if not any(path == m or path.startswith(f"{m}/") for m in managed)
            }

        self.assertEqual(unmanaged(after), before)

    def test_export_into_directory_containing_source(self) -> None:
        out = self._make_out()
        source = out / "src" / "lrh" / "skills"
        source.mkdir(parents=True)
        self._write_skill(source, "alpha")
        before = self._snapshot(source)

        report = self._export(source, out)

        self.assertFalse(report.has_failures)
        self.assertEqual(self._snapshot(source), before)
        self.assertEqual(self._plugin_skills(out), ["alpha"])

    def test_source_inside_plugin_directory_is_rejected(self) -> None:
        out = self._make_out()
        source = out / exporter.CLAUDE_PLUGIN_DIR / "skills"
        source.mkdir(parents=True)
        self._write_skill(source, "alpha")
        before = self._snapshot(out)

        with self.assertRaisesRegex(exporter.SkillExportError, "replaces"):
            self._export(source, out)
        self.assertEqual(self._snapshot(out), before)

    def test_source_containing_a_written_folder_is_rejected(self) -> None:
        for written in ("plugins", ".claude-plugin"):
            with self.subTest(source=written):
                out = self._make_out()
                source = out / written
                source.mkdir(parents=True)
                self._write_skill(source, "alpha")
                before = self._snapshot(out)

                with self.assertRaisesRegex(
                    exporter.SkillExportError, "inside the skill source"
                ):
                    self._export(source, out)
                self.assertEqual(self._snapshot(out), before)

    def test_symlinked_or_file_destinations_are_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        elsewhere = self._make_out()
        elsewhere.mkdir()
        for relative_path in ("plugins", ".claude-plugin", "plugins/lrh"):
            with self.subTest(path=relative_path):
                out = self._make_out()
                link = out / relative_path
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(elsewhere, target_is_directory=True)
                with self.assertRaisesRegex(exporter.SkillExportError, "symlink"):
                    self._export(source, out)
                self.assertEqual(list(elsewhere.iterdir()), [])
        out = self._make_out()
        (out / "plugins").mkdir(parents=True)
        (out / "plugins" / "lrh").write_text("not a directory\n")
        with self.assertRaisesRegex(exporter.SkillExportError, "not a directory"):
            self._export(source, out)
        out = self._make_out()
        (out / exporter.CLAUDE_MARKETPLACE_PATH).mkdir(parents=True)
        with self.assertRaisesRegex(exporter.SkillExportError, "is a directory"):
            self._export(source, out)

    def test_skill_selection_is_rejected(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        with self.assertRaisesRegex(exporter.SkillExportError, "not supported"):
            exporter.export_skills(
                out_dir=out,
                source=source,
                skill_names=["alpha"],
                target="claude-plugin",
            )
        self.assertFalse(out.exists())

    def test_validation_failure_writes_nothing_and_keeps_previous_tree(
        self,
    ) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        self._export(source, out)
        before = self._snapshot(out)
        self._write_skill(source, "broken", skill_md="no frontmatter\n")
        self._write_skill(
            source,
            "quoted",
            skill_md=_MANUAL_SKILL_MD.format(name="quoted").replace(
                "disable-model-invocation: true", 'disable-model-invocation: "true"'
            ),
        )

        report = self._export(source, out)

        self.assertTrue(report.has_failures)
        self.assertEqual(
            self._result(report, "quoted").status, exporter.ExportStatus.FAILED
        )
        self.assertEqual(self._snapshot(out), before)
        self.assertIn("no plugin written", exporter.format_export_report(report))
        with self.assertRaises(exporter.SkillExportError):
            exporter.render_claude_plugin_tree(source)

    def test_plugin_limits_fail_before_writing(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha", extra_files={"references/a.md": "a\n"})
        for constant, pattern in (
            ("MAX_PLUGIN_FILE_COUNT", "files; limit is 2"),
            ("MAX_PLUGIN_BYTES", "bytes; limit is 2"),
        ):
            with self.subTest(limit=constant):
                out = self._make_out()
                with mock.patch.object(exporter, constant, 2):
                    with self.assertRaisesRegex(exporter.SkillExportError, pattern):
                        self._export(source, out)
                self.assertFalse(out.exists())

    def test_top_level_bin_is_rejected(self) -> None:
        tree = {
            f"{exporter.CLAUDE_PLUGIN_DIR}/bin/tool": b"#!/bin/sh\n",
            f"{exporter.CLAUDE_PLUGIN_DIR}/skills/bin/SKILL.md": b"ok\n",
        }
        errors = exporter._plugin_limit_errors(tree)
        self.assertEqual(len(errors), 1)
        self.assertIn("bin/", errors[0])

    def test_staging_failure_keeps_previous_tree(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        self._export(source, out)
        before = self._snapshot(out)
        self._write_skill(source, "beta")

        with mock.patch.object(
            exporter, "_stage_archive", side_effect=OSError("disk full")
        ):
            with self.assertRaisesRegex(exporter.SkillExportError, "disk full"):
                self._export(source, out)

        self.assertEqual(self._snapshot(out), before)

    def test_staging_failure_on_fresh_output_leaves_nothing(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()

        with mock.patch.object(
            exporter, "_stage_archive", side_effect=OSError("disk full")
        ):
            with self.assertRaises(exporter.SkillExportError):
                self._export(source, out)

        self.assertFalse(out.exists())

    def test_publish_failure_restores_previous_tree(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        self._export(source, out)
        before = self._snapshot(out)
        self._write_skill(source, "beta")

        with mock.patch.object(
            exporter.os, "replace", side_effect=OSError("replace failed")
        ):
            with self.assertRaisesRegex(exporter.SkillExportError, "replace failed"):
                self._export(source, out)

        self.assertEqual(self._snapshot(out), before)

    def test_publish_failure_on_fresh_output_leaves_nothing(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()

        with mock.patch.object(
            exporter.os, "replace", side_effect=OSError("replace failed")
        ):
            with self.assertRaises(exporter.SkillExportError):
                self._export(source, out)

        self.assertFalse(out.exists())

    def test_failed_restore_reports_where_previous_plugin_is(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        self._export(source, out)
        real_rename = os.rename
        calls: list[str] = []

        def rename(src: object, dst: object) -> None:
            calls.append(Path(str(src)).name)
            # Allow moving the old plugin aside; fail the swap and the restore.
            if len(calls) == 1:
                real_rename(src, dst)
                return
            raise OSError(f"rename {len(calls)} failed")

        with mock.patch.object(exporter.os, "rename", side_effect=rename):
            with self.assertRaisesRegex(
                exporter.SkillExportError, "restoring the previous plugin also failed"
            ):
                self._export(source, out)

        plugins = out / "plugins"
        leftovers = sorted(path.name for path in plugins.iterdir())
        self.assertEqual(len(leftovers), 1)
        self.assertTrue(leftovers[0].startswith(".lrh-previous-"))
        self.assertTrue((plugins / leftovers[0] / "skills" / "alpha").is_dir())

    def test_stale_report_ignores_hidden_entries(self) -> None:
        source = self._make_source()
        self._write_skill(source, "alpha")
        out = self._make_out()
        self._export(source, out)
        (out / exporter.CLAUDE_PLUGIN_DIR / "skills" / ".DS_Store").write_text("x")

        report = self._export(source, out)

        self.assertEqual(report.removed, ())
        self.assertFalse(
            (out / exporter.CLAUDE_PLUGIN_DIR / "skills" / ".DS_Store").exists()
        )


class TestClaudePluginSkillRenderer(unittest.TestCase):
    def test_renderer_satisfies_skill_renderer_protocol(self) -> None:
        renderer: installer.SkillRenderer = exporter.ClaudePluginSkillRenderer()
        source_files = {
            "SKILL.md": _MANUAL_SKILL_MD.format(name="manual").encode("utf-8"),
            "agents/openai.yaml": b"{}\n",
            "references/a.md": b"a\n",
        }
        rendered = renderer.render("manual", source_files)
        self.assertEqual(sorted(rendered), ["SKILL.md", "references/a.md"])
        self.assertEqual(rendered["SKILL.md"], source_files["SKILL.md"])


if __name__ == "__main__":
    unittest.main()

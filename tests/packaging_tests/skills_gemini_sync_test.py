"""Regression coverage: the committed `.gemini` Antigravity skills match `src`.

`.gemini/plugins/lrh/` is a committed, generated install target
(`lrh skills install --local --target antigravity --source current-repo`).
Antigravity loads these copies directly, so a skill edited in
`src/lrh/skills/` without regenerating `.gemini` silently ships stale
instructions to Antigravity users. These tests compare every committed skill
file-by-file against the Antigravity renderer's output from the canonical
source.

To fix a failure, regenerate the target (dry-run first):

    lrh skills install --local --target antigravity --source current-repo --force
"""

from __future__ import annotations

import pathlib
import unittest

from lrh.skills import installer
from lrh.skills.installer import SkillTarget

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
PLUGIN_ROOT = REPO_ROOT / ".gemini" / "plugins" / "lrh"
GEMINI_SKILLS_ROOT = PLUGIN_ROOT / "skills"
REGEN_HINT = (
    "regenerate with `lrh skills install --local --target antigravity "
    "--source current-repo --force`"
)


def _source_skill_names() -> list[str]:
    return sorted(
        item.name
        for item in SOURCE_ROOT.iterdir()
        if item.is_dir() and not item.name.startswith("_")
    )


def _committed_files(skill_dir: pathlib.Path) -> dict[str, bytes]:
    return {
        path.relative_to(skill_dir).as_posix(): path.read_bytes()
        for path in skill_dir.rglob("*")
        if path.is_file()
    }


class GeminiSkillsSyncTest(unittest.TestCase):
    def test_committed_skill_set_matches_source(self) -> None:
        committed = sorted(
            item.name for item in GEMINI_SKILLS_ROOT.iterdir() if item.is_dir()
        )
        self.assertEqual(committed, _source_skill_names(), REGEN_HINT)

    def test_every_committed_skill_equals_antigravity_render(self) -> None:
        renderer = installer._renderer_for_target(SkillTarget.ANTIGRAVITY)
        for name in _source_skill_names():
            with self.subTest(skill=name):
                source_files = installer._collect_source_files(SOURCE_ROOT / name)
                rendered = renderer.render(name, source_files)
                committed = _committed_files(GEMINI_SKILLS_ROOT / name)
                self.assertEqual(sorted(committed), sorted(rendered), REGEN_HINT)
                for rel_path, content in rendered.items():
                    with self.subTest(skill=name, file=rel_path):
                        self.assertEqual(committed[rel_path], content, REGEN_HINT)

    def test_plugin_manifest_matches_installer(self) -> None:
        self.assertEqual(
            (PLUGIN_ROOT / "plugin.json").read_bytes(),
            installer._antigravity_plugin_manifest(),
            REGEN_HINT,
        )


if __name__ == "__main__":
    unittest.main()

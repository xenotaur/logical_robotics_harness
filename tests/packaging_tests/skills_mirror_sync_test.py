"""Regression coverage: the committed skill install targets match `src`.

`src/lrh/skills/` is canonical. Three committed, generated install targets are
rendered from it by `lrh skills install --local --source current-repo`:

- `.claude/skills/` (Claude target; byte-identical copies)
- `.agents/skills/` (Codex target)
- `.gemini/plugins/lrh/skills/` (Antigravity target, plus `plugin.json`)

Agents load these copies directly, so a skill edited in `src/lrh/skills/`
without regenerating them silently ships stale instructions. These tests
compare every committed skill file-by-file against the installer's renderer
output for each target.

To fix a failure, regenerate the targets (append `--dry-run` to preview first):

    lrh skills install --local --target all --source current-repo --force
"""

from __future__ import annotations

import pathlib
import unittest

from lrh.skills import installer

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
PLUGIN_ROOT = REPO_ROOT / ".gemini" / "plugins" / "lrh"
TARGET_ROOTS = {
    installer.SkillTarget.CLAUDE: REPO_ROOT / ".claude" / "skills",
    installer.SkillTarget.CODEX: REPO_ROOT / ".agents" / "skills",
    installer.SkillTarget.ANTIGRAVITY: PLUGIN_ROOT / "skills",
}
REGEN_HINT = (
    "regenerate with `lrh skills install --local --target all "
    "--source current-repo --force`"
)


def _source_skill_names() -> list[str]:
    return installer.resolve_skill_source(SOURCE_ROOT).skill_names()


def _label(target: installer.SkillTarget) -> str:
    return TARGET_ROOTS[target].relative_to(REPO_ROOT).as_posix()


class SkillsMirrorSyncTest(unittest.TestCase):
    def test_committed_skill_set_matches_source(self) -> None:
        for target, skills_root in TARGET_ROOTS.items():
            with self.subTest(target=_label(target)):
                committed = sorted(
                    item.name
                    for item in skills_root.iterdir()
                    if item.is_dir() or item.is_symlink()
                )
                self.assertEqual(committed, _source_skill_names(), REGEN_HINT)

    def test_every_committed_skill_equals_target_render(self) -> None:
        for target, skills_root in TARGET_ROOTS.items():
            renderer = installer._renderer_for_target(target)
            for name in _source_skill_names():
                with self.subTest(target=_label(target), skill=name):
                    source_files = installer._collect_source_files(SOURCE_ROOT / name)
                    rendered = renderer.render(name, source_files)
                    skill_dir = skills_root / name
                    # Mirror the installer: a symlinked skill dir or file is
                    # never dereferenced and counts as modified, not up to date.
                    self.assertFalse(skill_dir.is_symlink(), REGEN_HINT)
                    self.assertEqual(
                        installer._collect_fs_symlinks(skill_dir), set(), REGEN_HINT
                    )
                    committed = installer._collect_fs_files(skill_dir)
                    self.assertEqual(sorted(committed), sorted(rendered), REGEN_HINT)
                    for rel_path, content in rendered.items():
                        with self.subTest(
                            target=_label(target), skill=name, file=rel_path
                        ):
                            self.assertEqual(committed[rel_path], content, REGEN_HINT)

    def test_antigravity_plugin_manifest_matches_installer(self) -> None:
        manifest_path = PLUGIN_ROOT / "plugin.json"
        # The installer treats a symlinked manifest as modified; never follow it.
        self.assertFalse(manifest_path.is_symlink(), REGEN_HINT)
        self.assertEqual(
            manifest_path.read_bytes(),
            installer._antigravity_plugin_manifest(),
            REGEN_HINT,
        )


if __name__ == "__main__":
    unittest.main()

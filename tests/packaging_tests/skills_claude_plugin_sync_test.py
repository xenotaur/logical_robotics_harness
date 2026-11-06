"""Regression coverage: the committed Claude plugin marketplace matches `src`.

`lrh skills export --target claude-plugin --source current-repo --out .`
generates `.claude-plugin/marketplace.json` and `plugins/lrh/` at the repo
root from the canonical `src/lrh/skills/`. claude.ai accounts that add this
repo as a marketplace sync that tree from `main`, so a skill edited without
regenerating it ships stale instructions to Claude Code cloud sessions.

To fix a failure, regenerate the tree:

    lrh skills export --target claude-plugin --source current-repo --out .
"""

from __future__ import annotations

import pathlib
import unittest

from lrh.skills import exporter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "lrh" / "skills"
REGEN_HINT = (
    "regenerate with `lrh skills export --target claude-plugin"
    " --source current-repo --out .`"
)


class SkillsClaudePluginSyncTest(unittest.TestCase):
    def test_committed_plugin_tree_equals_export(self) -> None:
        expected = exporter.render_claude_plugin_tree(SOURCE_ROOT)
        plugin_dir = REPO_ROOT / exporter.CLAUDE_PLUGIN_DIR
        marketplace = REPO_ROOT / exporter.CLAUDE_MARKETPLACE_PATH
        self.assertFalse(plugin_dir.is_symlink(), REGEN_HINT)
        self.assertFalse(marketplace.is_symlink(), REGEN_HINT)
        committed = {
            path.relative_to(REPO_ROOT).as_posix(): path.read_bytes()
            for path in sorted(plugin_dir.rglob("*"))
            if path.is_file() or path.is_symlink()
        }
        committed[exporter.CLAUDE_MARKETPLACE_PATH] = marketplace.read_bytes()
        self.assertEqual(sorted(committed), sorted(expected), REGEN_HINT)
        for path, content in expected.items():
            with self.subTest(path=path):
                self.assertEqual(committed[path], content, REGEN_HINT)


if __name__ == "__main__":
    unittest.main()

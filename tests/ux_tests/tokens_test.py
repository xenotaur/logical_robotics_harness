"""Tests for the shared LRH Console token file."""

from __future__ import annotations

import inspect
import pathlib
import re
import unittest

from lrh import serve
from lrh.ux import tokens

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "src" / "lrh" / "ux" / "static" / "lrh-tokens.css"
DESKTOP_COPY = REPO_ROOT / "apps" / "desktop" / "ui" / "lrh-tokens.css"

_STATES = ("done", "progress", "unblocked", "waiting", "blocked", "review", "unknown")
_BANDS = (
    "needs-attention",
    "blocked",
    "active-work",
    "awaiting-review",
    "stable",
    "unknown",
)
_SURFACES = ("page", "panel", "sunken", "overlay")

# Text against its background: WCAG 2.2 SC 1.4.3.
_TEXT_PAIRS = (
    [
        (text, f"surface-{surface}")
        for text in ("text-primary", "text-muted", "action-accent")
        for surface in _SURFACES
    ]
    + [
        (f"status-{state}-fg", background)
        for state in _STATES
        for background in (f"status-{state}-bg",)
        + tuple(f"surface-{s}" for s in _SURFACES)
    ]
    + [
        (text, f"status-{state}-bg")
        for text in ("text-primary", "text-muted")
        for state in _STATES
    ]
    + [("action-on-accent", "action-accent"), ("text-primary", "action-accent-bg")]
    + [(f"band-{band}-fg", f"band-{band}-bg") for band in _BANDS]
)

# Lines, icons, and focus against the surfaces they sit on: SC 1.4.11.
_LINE_PAIRS = (
    [
        (line, f"surface-{surface}")
        for line in (
            ["edge", "edge-strong", "focus"]
            + [f"status-{state}-line" for state in _STATES]
        )
        for surface in _SURFACES
    ]
    + [(f"status-{state}-line", f"status-{state}-bg") for state in _STATES]
    + [("focus", "action-accent-bg")]
    + [
        (f"band-{band}-line", background)
        for band in _BANDS
        for background in (f"band-{band}-bg",)
        + tuple(f"surface-{s}" for s in _SURFACES)
    ]
)


def _blocks(css: str) -> dict[str, dict[str, str]]:
    """Split the token file into its light and two dark declaration blocks."""

    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    light = re.search(r"^:root \{(.*?)^\}", css, flags=re.S | re.M)
    media = re.search(
        r"^@media \(prefers-color-scheme: dark\) \{\s*"
        r':root:not\(\[data-theme="light"\]\)'
        r" \{(.*?)^  \}\s*^\}",
        css,
        flags=re.S | re.M,
    )
    forced = re.search(
        r'^:root\[data-theme="dark"\] \{(.*?)^\}', css, flags=re.S | re.M
    )
    if not (light and media and forced):
        raise AssertionError("token file layout changed")
    return {
        "light": _declarations(light.group(1)),
        "media": _declarations(media.group(1)),
        "forced": _declarations(forced.group(1)),
    }


def _declarations(body: str) -> dict[str, str]:
    return {
        name: value.strip()
        for name, value in re.findall(r"(--lrh-[a-z0-9-]+)\s*:\s*([^;]+);", body)
    }


def _resolve(theme: dict[str, str], name: str) -> str:
    value = theme[name]
    seen = {name}
    while match := re.fullmatch(r"var\((--lrh-[a-z0-9-]+)\)", value):
        reference = match.group(1)
        if reference in seen:
            raise AssertionError(f"token cycle at {reference}")
        seen.add(reference)
        value = theme[reference]
    return value


def _luminance(hex_color: str) -> float:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", hex_color)
    if match is None:
        raise AssertionError(f"not a 6-digit hex color: {hex_color}")
    channels = [int(match.group(1)[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class TokenFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.css = SOURCE.read_text(encoding="utf-8")
        self.blocks = _blocks(self.css)
        light = self.blocks["light"]
        self.themes = {"light": light, "dark": {**light, **self.blocks["media"]}}

    def test_desktop_copy_matches_the_source(self) -> None:
        self.assertEqual(
            DESKTOP_COPY.read_text(encoding="utf-8"),
            self.css,
            "copy src/lrh/ux/static/lrh-tokens.css to apps/desktop/ui/lrh-tokens.css",
        )

    def test_packaged_resource_is_the_source_file(self) -> None:
        self.assertEqual(tokens.token_css(), self.css)

    def test_both_dark_blocks_are_identical(self) -> None:
        self.assertEqual(self.blocks["media"], self.blocks["forced"])

    def test_dark_overrides_only_declared_light_tokens(self) -> None:
        self.assertLessEqual(set(self.blocks["media"]), set(self.blocks["light"]))

    def test_every_token_uses_the_lrh_prefix(self) -> None:
        names = re.findall(r"^\s*(--[a-z0-9-]+)\s*:", self.css, flags=re.M)
        self.assertTrue(names)
        self.assertEqual([n for n in names if not n.startswith("--lrh-")], [])

    def test_every_alias_resolves(self) -> None:
        for theme_name, theme in self.themes.items():
            for name in theme:
                with self.subTest(theme=theme_name, token=name):
                    _resolve(theme, name)

    def test_text_pairs_meet_four_and_a_half_to_one(self) -> None:
        self._check(_TEXT_PAIRS, 4.5)

    def test_line_icon_and_focus_pairs_meet_three_to_one(self) -> None:
        self._check(_LINE_PAIRS, 3.0)

    def test_checked_states_and_bands_are_every_declared_one(self) -> None:
        names = self.blocks["light"]
        states = {
            match.group(1)
            for name in names
            if (match := re.fullmatch(r"--lrh-color-status-([a-z-]+)-line", name))
        }
        bands = {
            match.group(1)
            for name in names
            if (match := re.fullmatch(r"--lrh-color-band-([a-z-]+)-line", name))
        }
        self.assertEqual(states, set(_STATES))
        self.assertEqual(bands, set(_BANDS))
        self.assertEqual(
            [key for key, _label, _icon in serve._SPECIMEN_STATES], list(_STATES)
        )
        self.assertEqual([key for key, _label in serve._SPECIMEN_BANDS], list(_BANDS))

    def test_bands_resolve_to_status_hues(self) -> None:
        light = self.themes["light"]
        self.assertEqual(
            _resolve(light, "--lrh-color-band-stable-fg"),
            _resolve(light, "--lrh-color-status-done-fg"),
        )
        self.assertEqual(
            _resolve(light, "--lrh-color-band-needs-attention-line"),
            _resolve(light, "--lrh-color-status-waiting-line"),
        )

    def _check(self, pairs: list[tuple[str, str]], minimum: float) -> None:
        for theme_name, theme in self.themes.items():
            for foreground, background in pairs:
                with self.subTest(theme=theme_name, pair=(foreground, background)):
                    ratio = _contrast(
                        _resolve(theme, f"--lrh-color-{foreground}"),
                        _resolve(theme, f"--lrh-color-{background}"),
                    )
                    self.assertGreaterEqual(ratio, minimum, f"{ratio:.2f}:1")


class ServePagesTest(unittest.TestCase):
    def test_only_the_specimen_follows_the_system_theme_for_now(self) -> None:
        # WI-LRH-CONSOLE-THEME removes these; until then Serve pages stay light.
        source = (REPO_ROOT / "src" / "lrh" / "serve.py").read_text(encoding="utf-8")
        tags = re.findall(r'<html lang=\\?"en\\?"[^>]*>', source)
        unthemed = [tag for tag in tags if "data-theme" not in tag]
        self.assertGreater(len(tags), 1)
        self.assertEqual(unthemed, ['<html lang="en">'])
        self.assertIn(
            '<html lang="en">', inspect.getsource(serve.render_style_specimen)
        )


class DesktopStylesTest(unittest.TestCase):
    def test_desktop_pages_load_tokens_before_their_styles(self) -> None:
        for page in ("index.html", "settings.html"):
            with self.subTest(page=page):
                text = (DESKTOP_COPY.parent / page).read_text(encoding="utf-8")
                self.assertLess(
                    text.index('href="lrh-tokens.css"'), text.index('href="style.css"')
                )

    def test_desktop_styles_use_tokens_not_literal_colors(self) -> None:
        styles = (DESKTOP_COPY.parent / "style.css").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", styles))

    def test_settings_highlight_honors_reduced_motion(self) -> None:
        styles = (DESKTOP_COPY.parent / "style.css").read_text(encoding="utf-8")
        script = (DESKTOP_COPY.parent / "settings.js").read_text(encoding="utf-8")
        self.assertRegex(
            styles,
            r"@media \(prefers-reduced-motion: reduce\) \{\s*\.flash \{",
        )
        self.assertIn("(prefers-reduced-motion: reduce)", script)


if __name__ == "__main__":
    unittest.main()

"""Access to the shared LRH Console design-token stylesheet."""

from __future__ import annotations

import functools
import importlib.resources

TOKENS_RESOURCE = "static/lrh-tokens.css"


@functools.cache
def token_css() -> str:
    """Return the packaged token stylesheet, ready to inline in a ``<style>``."""

    text = (
        importlib.resources.files("lrh.ux")
        .joinpath(TOKENS_RESOURCE)
        .read_text(encoding="utf-8")
    )
    if "</" in text:
        raise ValueError(f"{TOKENS_RESOURCE} must not contain '</'")
    return text

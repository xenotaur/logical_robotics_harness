"""Optional argcomplete wiring for the LRH argparse CLI."""

from __future__ import annotations

import argparse


def enable_completion(parser: argparse.ArgumentParser) -> None:
    """Enable argcomplete for a parser when the optional dependency is present."""
    try:
        import argcomplete  # type: ignore[import-not-found]
    except ImportError:
        return

    argcomplete.autocomplete(parser)

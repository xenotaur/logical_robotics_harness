"""Name-to-backend registry: the single place a new backend is wired in."""

from __future__ import annotations

import pathlib

from lrh.vcs import backend, github_backend

DEFAULT_BACKEND = "github"

_FACTORIES = {
    "github": github_backend.GitHubBackend,
}


def backend_names() -> tuple[str, ...]:
    """Return the registered backend names, sorted."""
    return tuple(sorted(_FACTORIES))


def create_backend(
    name: str, *, cwd: str | pathlib.Path | None = None
) -> backend.VcsBackend:
    """Build the named backend, or raise ``VcsError`` for an unknown name."""
    factory = _FACTORIES.get(name)
    if factory is None:
        raise backend.VcsError(
            f"unknown VCS backend {name!r}; available: {', '.join(backend_names())}"
        )
    return factory(cwd=cwd)

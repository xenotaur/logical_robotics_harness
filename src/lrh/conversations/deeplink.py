"""Session deep links: map LRH session pointers to vendor-app URLs.

An execution record names the agent session that did its work as a
``scheme:identifier`` pointer such as ``claude-app:<host-uuid-stem>``. This
module turns such a pointer into a link that opens the session in the vendor's
desktop app, or ``None`` when no link is known. It is pure: it reads only the
pointer string and the packaged route definition ``session_links.json``, never
the session index, the filesystem, or the network.

``session_links.json`` is the single route definition. The LRH Console shell
allowlist (Rust) is built from the same file, so the builder here and the
allowlist there cannot drift. The Claude ``epitaxy`` route is undocumented by
Anthropic and may change; treat every link as best-effort.

Claude host ids and child ids are both bare UUIDs and only the session index
tells them apart, so this module checks the *shape* of an id, not which kind it
is. The invariant lives on the producer side: only confirmed host ids become
``claude-app:`` pointers.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import re
from importlib import resources
from typing import Any

DEFINITION_RESOURCE = "session_links.json"

_UUID_PATTERN = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_ID_SHAPES = {"uuid": _UUID_PATTERN}
_PLACEHOLDER = re.compile(r"(\{id_prefix\}|\{id\})")


class SessionLinkDefinitionError(ValueError):
    """Raised when the packaged route definition is missing or malformed."""


@dataclasses.dataclass(frozen=True)
class VendorRoute:
    """One vendor's pointer prefix and link shape, from the definition."""

    name: str
    pointer_prefix: str
    scheme: str
    host: str
    path_template: str
    id_prefix: str
    id_pattern: str
    status: str

    def link(self, identifier: str) -> str:
        """Build the link for an id that has already been shape-checked."""

        path = self.path_template.replace("{id_prefix}", self.id_prefix).replace(
            "{id}", identifier
        )
        return f"{self.scheme}://{self.host}{path}"

    def link_pattern(self) -> re.Pattern[str]:
        """Compile a pattern matching exactly this vendor's links."""

        path = "".join(
            (
                self.id_pattern
                if piece == "{id}"
                else (
                    re.escape(self.id_prefix)
                    if piece == "{id_prefix}"
                    else re.escape(piece)
                )
            )
            for piece in _PLACEHOLDER.split(self.path_template)
        )
        return re.compile(f"{re.escape(self.scheme)}://{re.escape(self.host)}{path}")


@functools.lru_cache(maxsize=1)
def load_definition() -> dict[str, Any]:
    """Return the parsed ``session_links.json`` definition."""

    try:
        text = (
            resources.files("lrh.conversations")
            .joinpath(DEFINITION_RESOURCE)
            .read_text(encoding="utf-8")
        )
        definition = json.loads(text)
    except (OSError, ValueError) as error:
        raise SessionLinkDefinitionError(
            f"cannot read {DEFINITION_RESOURCE}: {error}"
        ) from error
    if not isinstance(definition, dict) or not isinstance(
        definition.get("vendors"), list
    ):
        raise SessionLinkDefinitionError(
            f"{DEFINITION_RESOURCE} must be an object with a 'vendors' list"
        )
    return definition


@functools.lru_cache(maxsize=1)
def load_routes() -> tuple[VendorRoute, ...]:
    """Return the supported vendor routes, validated."""

    routes = []
    for entry in load_definition()["vendors"]:
        try:
            route = VendorRoute(
                name=entry["name"],
                pointer_prefix=entry["pointer_prefix"],
                scheme=entry["scheme"],
                host=entry["host"],
                path_template=entry["path_template"],
                id_prefix=entry["id_prefix"],
                id_pattern=_ID_SHAPES[entry["id_shape"]],
                status=entry["status"],
            )
        except (KeyError, TypeError) as error:
            raise SessionLinkDefinitionError(
                f"{DEFINITION_RESOURCE}: malformed vendor entry {entry!r}"
            ) from error
        if (
            not route.pointer_prefix.endswith(":")
            or route.scheme != route.scheme.lower()
            or "{id}" not in route.path_template
            or not route.path_template.startswith("/")
        ):
            raise SessionLinkDefinitionError(
                f"{DEFINITION_RESOURCE}: invalid route for {route.name!r}"
            )
        routes.append(route)
    return tuple(routes)


def link_for(pointer: str) -> str | None:
    """Return the deep link for a session pointer, or ``None``.

    ``None`` means no link is known: the pointer is empty, ``pending``,
    ``none``, malformed, or belongs to a vendor with no known route. The
    result is never a guess.
    """

    if not isinstance(pointer, str):
        return None
    for route in load_routes():
        if not pointer.startswith(route.pointer_prefix):
            continue
        identifier = pointer[len(route.pointer_prefix) :]
        if route.id_prefix and identifier.startswith(route.id_prefix):
            identifier = identifier[len(route.id_prefix) :]
        if re.fullmatch(route.id_pattern, identifier) is None:
            return None
        return route.link(identifier)
    return None


def is_session_link(url: str) -> bool:
    """Return whether ``url`` is exactly one of the supported deep links.

    This is the Python mirror of the Console shell allowlist: exact scheme,
    host and path shape, with no credentials, port, query, fragment, extra
    path segments or surrounding whitespace.
    """

    if not isinstance(url, str):
        return False
    return any(
        route.link_pattern().fullmatch(url) is not None for route in load_routes()
    )

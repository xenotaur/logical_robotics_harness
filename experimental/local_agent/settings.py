"""Versioned defaults for the local-agent prototype.

These values were first recorded in the pre-registered stage-0 pilot
(``experiments/01_local_agent_briefing/``), which ``PROP-LOCAL-AGENT-DOGFOOD``
has since superseded with the toy ladder. They are ordinary defaults now and
can change with the prototype.
"""

from __future__ import annotations

import dataclasses

PROTOTYPE_VERSION = "0.1.0"
RECORD_SCHEMA_VERSION = "1"
POLICY_VERSION = "stage0-v1"
PROMPT_VERSION = "briefing_v1"

STORE_ENV_VAR = "LRH_LOCAL_AGENT_STORE"
DEFAULT_STORE_RELATIVE = (".local", "share", "lrh", "local-agent")

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:12b"
# sha256 of the local Ollama manifest, as reported by /api/tags "digest".
DEFAULT_MODEL_MANIFEST_DIGEST = (
    "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"
)
# Model weight layer inside that manifest (Q4_K_M), recorded for provenance.
DEFAULT_MODEL_LAYER_DIGEST = (
    "sha256:1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606"
)

# Paths (relative to the project root) never copied into a context packet.
EXCLUDED_PROJECT_PREFIXES = (
    "project/sessions/",
    "project/executions/",
    "project/memory/",
)

# Credential-like file names (matched case-insensitively against the basename),
# per PROP-LOCAL-AGENT-DOGFOOD Decision 3. A best-effort guard, not a guarantee.
CREDENTIAL_NAME_PATTERNS = (
    ".env*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "*credential*",
    "*secret*",
    ".netrc",
    ".npmrc",
    ".pypirc",
)

# Directory names that mark everything beneath them as credential-like.
CREDENTIAL_DIR_PATTERNS = ("*secret*", "*credential*")


@dataclasses.dataclass(frozen=True)
class Budgets:
    """Immutable per-run resource limits."""

    max_packet_bytes: int = 80_000
    max_source_bytes: int = 16_000
    max_estimated_input_tokens: int = 24_000
    num_ctx: int = 32_768
    max_output_tokens: int = 2_048
    wall_time_seconds: float = 300.0
    temperature: float = 0.2
    seed: int = 7

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def estimate_tokens(text: str) -> int:
    """Conservative token estimate (about four characters per token)."""
    return (len(text) + 3) // 4

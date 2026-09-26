"""Versioned defaults for the stage-0 briefing prototype.

The values here mirror the pre-registration in
``experiments/01_local_agent_briefing/README.md``. Change them only with a
matching pre-registration update made before live runs.
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

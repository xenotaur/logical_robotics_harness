"""Single-call stage-0 runner with explicit, recorded outcomes.

Every attempt ends in exactly one outcome and stays in the store, including
failures and cancellations, so no stopped attempt leaves the evaluation
denominator. ``completed`` means inference finished with schema-valid output;
it does not mean the briefing is correct or accepted.
"""

from __future__ import annotations

from local_agent import briefing, context, model, recorder, settings

OUTCOME_COMPLETED = "completed"
OUTCOME_MISSING_PREREQUISITE = "missing_prerequisite"
OUTCOME_BUDGET_EXHAUSTED = "budget_exhausted"
OUTCOME_INVALID_OUTPUT = "invalid_model_output"
OUTCOME_BACKEND_ERROR = "backend_error"
OUTCOME_TIMEOUT = "timeout"
OUTCOME_CANCELLED = "cancelled"

OUTCOMES = (
    OUTCOME_COMPLETED,
    OUTCOME_MISSING_PREREQUISITE,
    OUTCOME_BUDGET_EXHAUSTED,
    OUTCOME_INVALID_OUTPUT,
    OUTCOME_BACKEND_ERROR,
    OUTCOME_TIMEOUT,
    OUTCOME_CANCELLED,
)

_KIND_TO_OUTCOME = {
    model.KIND_MISSING_PREREQUISITE: OUTCOME_MISSING_PREREQUISITE,
    model.KIND_BACKEND_ERROR: OUTCOME_BACKEND_ERROR,
    model.KIND_TIMEOUT: OUTCOME_TIMEOUT,
}


class ApprovalError(ValueError):
    """Raised when the approved hash does not match the stored packet."""


def run_briefing(
    *,
    store: recorder.Store,
    packet_sha256: str,
    approved_sha256: str,
    adapter: model.ModelAdapter,
    budgets: settings.Budgets,
    task_id: str | None = None,
    prompt_version: str = settings.PROMPT_VERSION,
) -> str:
    """Run one briefing attempt and return its run id.

    Raises:
        ApprovalError: if ``approved_sha256`` does not match the packet, or the
            stored packet's content no longer hashes to it. No run record is
            created, because nothing valid was approved.
    """
    if approved_sha256 != packet_sha256:
        raise ApprovalError(
            "approval hash does not match the packet; inspect the packet and "
            "approve its exact sha256"
        )
    manifest, packet_text = store.load_packet(packet_sha256)
    if context.packet_sha256(manifest, packet_text) != packet_sha256:
        raise ApprovalError(
            "stored packet content no longer matches its sha256; rebuild and "
            "re-approve it"
        )
    prompt = briefing.render_prompt(packet_text, prompt_version)
    run_id = store.start_run(
        {
            "record_schema_version": settings.RECORD_SCHEMA_VERSION,
            "prototype_version": settings.PROTOTYPE_VERSION,
            "policy_version": settings.POLICY_VERSION,
            "prompt_version": prompt_version,
            "prompt_template_sha256": briefing.prompt_template_sha256(prompt_version),
            "packet_sha256": packet_sha256,
            "task_id": task_id,
            "work_item_id": manifest.get("work_item_id"),
            "source_commit": manifest.get("source_commit"),
            "lrh_commit": manifest.get("lrh_commit"),
            "model": adapter.describe(),
            "budgets": budgets.as_dict(),
            "outcome": None,
        }
    )
    store.append_event(run_id, "attempt_started")

    def finish(outcome: str, detail: str, **extra: object) -> str:
        store.append_event(run_id, "outcome", outcome=outcome, detail=detail)
        store.update_run(run_id, outcome=outcome, outcome_detail=detail, **extra)
        return run_id

    try:
        try:
            preflight = adapter.preflight()
        except model.BackendError as error:
            return finish(_KIND_TO_OUTCOME[error.kind], f"preflight: {error}")
        store.append_event(run_id, "preflight_passed", preflight=preflight)
        store.update_run(run_id, preflight=preflight, model=adapter.describe())

        estimated = settings.estimate_tokens(prompt)
        if estimated > budgets.max_estimated_input_tokens:
            return finish(
                OUTCOME_BUDGET_EXHAUSTED,
                f"estimated input {estimated} tokens exceeds "
                f"{budgets.max_estimated_input_tokens}",
                estimated_input_tokens=estimated,
            )
        store.append_event(run_id, "model_request", estimated_input_tokens=estimated)

        try:
            response = adapter.generate(
                model.ModelRequest(
                    prompt=prompt,
                    output_schema=briefing.OUTPUT_SCHEMA,
                    budgets=budgets,
                )
            )
        except model.BackendError as error:
            return finish(_KIND_TO_OUTCOME[error.kind], f"generate: {error}")

        usage = {
            "estimated_input_tokens": estimated,
            "prompt_tokens": response.prompt_tokens,
            "output_tokens": response.output_tokens,
            "done_reason": response.done_reason,
            "backend_timings": response.backend_timings,
        }
        store.write_json(run_id, "output.json", {"raw_text": response.text})
        store.append_event(run_id, "model_response", **usage)

        if response.done_reason == "length":
            return finish(
                OUTCOME_BUDGET_EXHAUSTED, "output hit the token limit", usage=usage
            )
        if (
            response.output_tokens is not None
            and response.output_tokens > budgets.max_output_tokens
        ):
            return finish(
                OUTCOME_BUDGET_EXHAUSTED,
                f"output used {response.output_tokens} tokens, over "
                f"{budgets.max_output_tokens}",
                usage=usage,
            )
        try:
            parsed = briefing.parse_briefing(response.text)
        except briefing.InvalidBriefingError as error:
            return finish(OUTCOME_INVALID_OUTPUT, str(error), usage=usage)

        sources = manifest.get("sources", [])
        assert isinstance(sources, list)
        citations = briefing.check_citations(parsed, sources)
        store.write_json(
            run_id, "output.json", {"raw_text": response.text, "briefing": parsed}
        )
        return finish(
            OUTCOME_COMPLETED,
            "inference finished with schema-valid output (not human-accepted)",
            usage=usage,
            citations=citations,
        )
    except KeyboardInterrupt:
        finish(OUTCOME_CANCELLED, "interrupted by user")
        raise
    except Exception as error:
        # Record unexpected failures instead of losing the attempt, then surface.
        finish(OUTCOME_BACKEND_ERROR, f"unexpected {type(error).__name__}: {error}")
        raise

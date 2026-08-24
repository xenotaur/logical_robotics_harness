"""``confirm_fixes_batch`` per-gate autopilot predicate for `/lrh-confirm-fixes`.

Decides whether a confirm-fixes batch is routine enough to skip the Step 4
live confirm ask (``chain-defaults.yaml``'s ``confirm_fixes_batch:
auto_unless_unusual``) or unusual enough to still require it. The predicate
is deliberately narrow and gate-owned, per `PROP-LRH-CHAIN-DEFAULTS`
Decision 2 -- it is not a generic, reusable rule engine, and it does not
decide anything about the merge gate, the chain-initiation gate, or
`/lrh-closeout`'s plan-confirm gate, all three of which stay categorically
excluded from any autopilot tier.

Grounded in a survey of 36 real `/lrh-confirm-fixes` rounds from this
repository's own execution records (``WI-LRH-CHAIN-DEFAULTS-INCREMENT-2``'s
execution record cites the specific files). See that record for the full
evidence base; in summary:

- Severity badges (P0/P1) did not predict an unusual round -- they appeared
  throughout the routine population too.
- Bot-vs-human reviewer identity was not a distinguishing signal in the
  sampled data (every reviewer observed was a bot).
- What did predict "unusual": any non-Clear-satisfied thread bucket, CI
  already failing, or a prior round on the same PR that already surfaced a
  non-Clear-satisfied finding (a PR mid-escalation deserves a human look
  even on a round that looks clean in isolation).
"""

from __future__ import annotations

import dataclasses

#: Thread classification buckets that never make a batch routine, per
#: `/lrh-confirm-fixes` Step 3's own taxonomy. Any occurrence forces a live
#: ask regardless of everything else.
_UNROUTINE_BUCKETS = frozenset(
    {
        "unaddressed",
        "partial",
        "ambiguous",
        "problematic_resolution",
        "problematic_comment",
    }
)

_ROUTINE_BUCKET = "clear_satisfied"


def normalize_bucket_label(label: str) -> str:
    """Normalize a Step 3 taxonomy label to its canonical machine token.

    `/lrh-confirm-fixes` Step 3's own table displays buckets as
    ``Clear-satisfied``, ``Problematic resolution``, etc. -- the
    human-facing taxonomy, not the machine token this module expects
    (``clear_satisfied``, ``problematic_resolution``). Without
    normalization, a caller passing the display label verbatim (a real
    risk found in this module's own review round -- ``--bucket
    Clear-satisfied`` silently exits 1 as "unrecognized," falling back to
    the live gate for what may be a genuinely routine batch) would defeat
    the autopilot every time. Case-insensitive; treats ``-`` and ` ` as
    equivalent to ``_``.
    """
    return label.strip().lower().replace("-", "_").replace(" ", "_")


@dataclasses.dataclass(frozen=True)
class BatchRoutineResult:
    """Outcome of the routine-batch predicate, with a human-readable reason."""

    routine: bool
    reason: str


def is_routine_batch(
    bucket_labels: tuple[str, ...],
    *,
    ci_ok: bool,
    had_prior_exception: bool,
) -> BatchRoutineResult:
    """Decide whether a confirm-fixes batch is routine enough to auto-proceed.

    Args:
        bucket_labels: the Step 3 taxonomy bucket for every thread in the
            authoritative (``isResolved == false``) unresolved-thread list --
            never the narrower ``lrh request review_response`` filter, which
            real evidence (PRs #549, #577, #598) showed can undercount by
            excluding outdated-but-unresolved threads. An empty tuple is the
            "nothing to resolve" case and is itself routine, provided the
            other two conditions hold. Accepts either the machine token
            (``clear_satisfied``) or the Step 3 table's display label
            (``Clear-satisfied``) -- normalized internally via
            :func:`normalize_bucket_label` -- so a caller need not worry
            about which form it was given.
        ci_ok: whether the Step 2.3 provisional CI read shows no failing
            check. A red CI is treated as unusual even if every thread is
            Clear-satisfied -- presenting an auto-approved batch summary
            alongside failing CI would misrepresent the run's actual state.
        had_prior_exception: whether any earlier `/lrh-confirm-fixes` round
            on this same PR already surfaced a non-Clear-satisfied finding.
            Real evidence (PRs #518, #535) showed multi-round escalations
            recur on the same PR; a clean-looking round following an
            escalated one still gets a live ask, since that is exactly the
            situation a human should stay in the loop for.

    Returns:
        A :class:`BatchRoutineResult` with the decision and why.
    """
    if had_prior_exception:
        return BatchRoutineResult(
            routine=False,
            reason=(
                "an earlier confirm-fixes round on this PR already surfaced a "
                "non-Clear-satisfied finding -- a mid-escalation PR gets a live "
                "ask even on a round that looks clean in isolation"
            ),
        )
    if not ci_ok:
        return BatchRoutineResult(
            routine=False,
            reason="provisional CI shows a failing check",
        )
    bucket_labels = tuple(normalize_bucket_label(label) for label in bucket_labels)
    unroutine_hits = sorted(
        {label for label in bucket_labels if label in _UNROUTINE_BUCKETS}
    )
    if unroutine_hits:
        return BatchRoutineResult(
            routine=False,
            reason=f"batch contains non-Clear-satisfied bucket(s): {', '.join(unroutine_hits)}",
        )
    unknown = sorted(
        {
            label
            for label in bucket_labels
            if label != _ROUTINE_BUCKET and label not in _UNROUTINE_BUCKETS
        }
    )
    if unknown:
        return BatchRoutineResult(
            routine=False,
            reason=f"unrecognized bucket label(s), failing safe: {', '.join(unknown)}",
        )
    if not bucket_labels:
        return BatchRoutineResult(
            routine=True,
            reason="no unresolved threads (authoritative list empty)",
        )
    return BatchRoutineResult(
        routine=True,
        reason=f"all {len(bucket_labels)} thread(s) are Clear-satisfied",
    )

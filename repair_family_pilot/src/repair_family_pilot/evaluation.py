"""Later-evaluation status. This preview build does not assign it."""

from __future__ import annotations

from typing import Optional, Sequence


def unconditional_exact_match(predicted: Sequence[Optional[str]], reference: Sequence[str]) -> float:
    """Abstention, stored as None, counts as incorrect. Denominator is every case."""
    if len(predicted) != len(reference):
        raise ValueError("predicted and reference lengths differ")
    if not reference:
        return 0.0
    hits = sum(item is not None and item == truth for item, truth in zip(predicted, reference))
    return hits / len(reference)


def later_evaluation_status(
    *,
    collection_complete: bool,
    has_joint: bool,
    has_alternative: bool,
    primary_rate: float,
    additive_rate: float,
    nearest_rate: float,
    recovered_joint: bool,
    recovered_alternative: bool,
    blocker: str = "",
) -> dict:
    """Status for a finished later evaluation of zero-probe donor synthesis.

    Assisted results are not an input. Supported means exploratory pilot support.
    """
    if not collection_complete:
        return {"status": None, "blocker": blocker or "incomplete", "claim": "exploratory"}
    if not has_joint or not has_alternative:
        return {"status": "partial_scientific_scope", "blocker": None, "claim": "exploratory"}
    beats_both = primary_rate > additive_rate and primary_rate > nearest_rate
    recovers_both_types = recovered_joint and recovered_alternative
    if beats_both and recovers_both_types:
        return {"status": "pilot_complete_supported", "blocker": None, "claim": "exploratory pilot support"}
    return {"status": "pilot_complete_negative", "blocker": None, "claim": "exploratory"}


def certificate_status(measured: dict) -> str:
    """Finite-protocol certificate from cells that were actually measured.

    A missing cell is None. Joint certification needs measured failure of empty,
    A, and B, plus measured success of AB. Alternative certification needs
    measured failure of empty and measured success of A and of B.
    """
    needed_for_known = ("empty", "A", "B", "AB")
    if any(measured.get(name) is None for name in needed_for_known):
        if any(measured.get(name) is not None for name in needed_for_known):
            # Alternative certificates do not need AB once A and B both succeed
            # and empty fails.
            if measured.get("empty") is False and measured.get("A") is True and measured.get("B") is True:
                return "protocol_verified"
            return "partially_verified"
        return "predicted"
    if measured["empty"] is False and measured["A"] is False and measured["B"] is False and measured["AB"] is True:
        return "protocol_verified"
    if measured["empty"] is False and measured["A"] is True and measured["B"] is True:
        return "protocol_verified"
    if all(measured[name] is False for name in needed_for_known):
        return "protocol_verified"
    if measured["empty"] is True:
        return "protocol_verified"
    return "protocol_verified"

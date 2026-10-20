"""Inclusion-minimal repair families on {empty, A, B, AB}."""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Sequence


CONFIGS = ("empty", "A", "B", "AB")
THETA = Fraction(4, 5)


def family_from_bits(empty: int, a: int, b: int, ab: int) -> dict:
    """Map one binary four-cell table to the coding-plan family.

    0110 is the non-monotonic case: A and B each succeed and AB fails.
    """
    if int(empty) == 1:
        return {"kind": "baseline_adequate", "sets": None}
    candidates = []
    if int(a) == 1:
        candidates.append(frozenset({"A"}))
    if int(b) == 1:
        candidates.append(frozenset({"B"}))
    if int(ab) == 1:
        candidates.append(frozenset({"A", "B"}))
    minimal = []
    for item in candidates:
        if any(other < item for other in candidates):
            continue
        minimal.append(tuple(sorted(item)))
    return {"kind": "family", "sets": tuple(sorted(minimal))}


def exceeds_theta(successes: int, repeats: int, theta: Fraction = THETA) -> int:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    return int(Fraction(int(successes), int(repeats)) >= theta)


def family_from_counts(counts: dict, repeats: int) -> dict:
    bits = tuple(exceeds_theta(int(counts[name]), repeats) for name in CONFIGS)
    return family_from_bits(*bits)


def family_key(family: dict) -> str:
    if family["kind"] == "baseline_adequate":
        return "baseline_adequate"
    if not family["sets"]:
        return "none"
    return "|".join("".join(item) for item in family["sets"])


def all_binary_tables() -> Iterable[tuple]:
    for empty in (0, 1):
        for a in (0, 1):
            for b in (0, 1):
                for ab in (0, 1):
                    yield (empty, a, b, ab)


def expected_key(bits: Sequence[int]) -> str:
    return family_key(family_from_bits(*bits))

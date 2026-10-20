"""Configuration probe order for the assisted variant.

The primary prediction is zero-probe. A probe executes one whole configuration
after that prediction has been hashed.
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from repair_family_pilot.families import CONFIGS, family_key, family_from_bits

ORDER = ("empty", "A", "B", "AB")


def _assignments(intervals: dict, theta: float) -> list:
    feasible = []
    slots = []
    for name in CONFIGS:
        lower, upper = intervals[name]
        choices = []
        if lower < theta:
            choices.append(0)
        if upper >= theta:
            choices.append(1)
        if not choices:
            choices = [0, 1]
        slots.append(choices)
    for empty in slots[0]:
        for a in slots[1]:
            for b in slots[2]:
                for ab in slots[3]:
                    feasible.append((empty, a, b, ab))
    return feasible


def choose_probe(intervals: dict, unresolved: Sequence[str], costs: dict | None = None, theta: float = 0.8) -> str | None:
    pending = [name for name in ORDER if name in unresolved]
    if not pending:
        return None
    assignments = _assignments(intervals, theta)
    scores = {}
    for name in pending:
        index = CONFIGS.index(name)
        score = 0
        for left, right in combinations(assignments, 2):
            if left[index] == right[index]:
                continue
            if family_key(family_from_bits(*left)) != family_key(family_from_bits(*right)):
                score += 1
        scores[name] = score
    cost_map = costs or {name: 0 for name in ORDER}

    def sort_key(name: str) -> tuple:
        return (-scores[name], cost_map.get(name, 0), ORDER.index(name))

    return sorted(pending, key=sort_key)[0]

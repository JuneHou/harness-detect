"""Group assignment before any repaired outcome is known."""

from __future__ import annotations

import random
from typing import Sequence


def collapse_related(items: Sequence[dict]) -> list:
    """One split unit per group_id. Related variants share that id."""
    seen = []
    for item in items:
        group_id = item["group_id"]
        if group_id not in seen:
            seen.append(group_id)
    return seen


def assign_split(group_ids: Sequence[str], seed: int = 20261020) -> dict:
    labels = list(group_ids)
    random.Random(seed).shuffle(labels)
    count = len(labels)
    donor_count = count // 2
    calibration_count = (count - donor_count) // 2
    assignment = {}
    for index, group_id in enumerate(labels):
        if index < donor_count:
            split = "donor"
        elif index < donor_count + calibration_count:
            split = "calibration"
        else:
            split = "test"
        assignment[group_id] = split
    return {
        "assignment": assignment,
        "group_count": count,
        "donor": donor_count,
        "calibration": calibration_count,
        "test": count - donor_count - calibration_count,
    }

"""Calibration intervals from simultaneous four-cell residuals."""

from __future__ import annotations

import math
from typing import Sequence


def group_residual(rows: Sequence[dict]) -> float:
    values = []
    for row in rows:
        measured = row["measured"]
        predicted = row["predicted"]
        values.append(max(abs(float(measured[name]) - float(predicted[name])) for name in measured))
    return max(values) if values else 0.0


def residual_quantile(group_residuals: Sequence[float], alpha: float = 0.10) -> dict:
    ordered = sorted(float(value) for value in group_residuals)
    count = len(ordered)
    rank = math.ceil((count + 1) * (1.0 - alpha))
    if rank > count or count == 0:
        return {"quantile": None, "informative": False}
    return {"quantile": ordered[rank - 1], "informative": True, "rank": rank}


def cell_interval(predicted: float, quantile: float | None) -> tuple:
    if quantile is None:
        return (0.0, 1.0)
    lower = max(0.0, predicted - quantile)
    upper = min(1.0, predicted + quantile)
    return (lower, upper)

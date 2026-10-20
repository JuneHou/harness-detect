"""Comparators that use the same donor tables and pre-repair features."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from repair_family_pilot.families import family_from_bits, family_key


def uniform_mean(donor_rates: Sequence[Sequence[float]]) -> list:
    table = np.asarray(donor_rates, dtype=float)
    return table.mean(axis=0).tolist()


def nearest_donor(target: Sequence[float], donor_features: Sequence[Sequence[float]], donor_rates: Sequence[Sequence[float]]) -> dict:
    features = np.asarray(donor_features, dtype=float)
    point = np.asarray(target, dtype=float)
    distances = np.linalg.norm(features - point, axis=1)
    index = int(np.argmin(distances))
    return {"donor_index": index, "distance": float(distances[index]), "rates": list(donor_rates[index])}


def additive_ab(empty: float, a: float, b: float) -> float:
    return float(min(1.0, max(0.0, a + b - empty)))


def ridge_predict(donor_features: np.ndarray, donor_rates: np.ndarray, target: np.ndarray, lam: float = 1.0) -> dict:
    """Multi-output ridge fit on donor rows only."""
    features = np.asarray(donor_features, dtype=float)
    rates = np.asarray(donor_rates, dtype=float)
    if features.shape[0] < 2:
        return {"fallback_reason": "insufficient_donors", "rates": None, "family_status": "abstain", "predicted_family": None}
    design = np.concatenate([np.ones((features.shape[0], 1)), features], axis=1)
    gram = design.T @ design
    penalty = lam * np.eye(gram.shape[0])
    penalty[0, 0] = 0.0
    coefficient = np.linalg.solve(gram + penalty, design.T @ rates)
    point = np.concatenate([[1.0], np.asarray(target, dtype=float)])
    predicted = point @ coefficient
    predicted = np.clip(predicted, 0.0, 1.0)
    bits = tuple(int(value >= 0.8) for value in predicted.tolist())
    family = family_from_bits(*bits)
    return {"fallback_reason": None, "rates": predicted.tolist(), "family_status": "predicted", "predicted_family": family, "predicted_family_key": family_key(family)}

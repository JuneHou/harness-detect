"""Simplex donor synthesis of a whole four-cell response table."""

from __future__ import annotations

import math
from typing import Optional, Sequence

import numpy as np
from scipy.optimize import minimize

from repair_family_pilot.families import CONFIGS, family_from_bits, family_key

SUM_TOLERANCE = 1e-6
NONNEG_TOLERANCE = 1e-8
LAMBDA_GRID = (0.0, 0.01, 0.1, 1.0, 10.0)


def _empty_prediction(reason: str, weights: Optional[list] = None, message: str = "", residual: Optional[float] = None) -> dict:
    return {
        "weights": weights,
        "diagnostic_only": True,
        "fallback_reason": reason,
        "family_status": "abstain",
        "predicted_family": None,
        "predicted_rates": None,
        "solver_message": message,
        "constraint_residual": residual,
        "probability_supported_family": "unresolved",
    }


def assess_weights(success: bool, weights: np.ndarray, message: str) -> dict:
    vector = np.asarray(weights, dtype=float).reshape(-1)
    residual = float(vector.sum() - 1.0) if vector.size else None
    finite = bool(vector.size) and bool(np.all(np.isfinite(vector)))
    nonnegative = finite and bool(np.all(vector >= -NONNEG_TOLERANCE))
    sums = finite and residual is not None and abs(residual) <= SUM_TOLERANCE
    if not (success and finite and nonnegative and sums):
        uniform = None
        if vector.size:
            uniform = (np.ones(vector.size) / vector.size).tolist()
        return _empty_prediction("solver_failure", uniform, str(message), residual)
    accepted = np.clip(vector, 0.0, None)
    total = float(accepted.sum())
    if abs(total - 1.0) > SUM_TOLERANCE:
        return _empty_prediction("solver_failure", accepted.tolist(), str(message), residual)
    return {
        "weights": (accepted / total).tolist(),
        "diagnostic_only": False,
        "fallback_reason": None,
        "family_status": "predicted",
        "solver_message": str(message),
        "constraint_residual": float(accepted.sum() - 1.0),
    }


def solve_weights(donor_features: np.ndarray, target: np.ndarray, lam: float) -> dict:
    matrix = np.asarray(donor_features, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        return _empty_prediction("no_eligible_donors")
    target = np.asarray(target, dtype=float).reshape(-1)
    count = matrix.shape[0]

    def objective(weights: np.ndarray) -> float:
        residual = target - matrix.T @ weights
        return float(residual @ residual + lam * (weights @ weights))

    result = minimize(
        objective,
        np.ones(count) / count,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * count,
        constraints={"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0},
        tol=1e-12,
    )
    assessed = assess_weights(bool(result.success), np.asarray(result.x, dtype=float), str(result.message))
    return assessed


def synthesize_rates(weights: Sequence[float], donor_rates: Sequence[Sequence[float]]) -> list:
    """Apply one weight vector to every configuration, including AB."""
    vector = np.asarray(weights, dtype=float)
    table = np.asarray(donor_rates, dtype=float)
    if table.ndim != 2 or table.shape[1] != 4:
        raise ValueError("donor rate tables must have four columns")
    if vector.shape != (table.shape[0],):
        raise ValueError("weights and donor rows differ in length")
    return (vector @ table).tolist()


def family_from_predicted_rates(rates: Sequence[float], theta: float = 0.8) -> dict:
    bits = tuple(int(rate >= theta) for rate in rates)
    family = family_from_bits(*bits)
    return family


def predict_table(donor_features: np.ndarray, target: np.ndarray, donor_rates: Sequence[Sequence[float]], lam: float) -> dict:
    solved = solve_weights(donor_features, target, lam)
    if solved["family_status"] == "abstain":
        solved["predicted_rates"] = None
        solved["predicted_family"] = None
        solved["probability_supported_family"] = "unresolved"
        return solved
    rates = synthesize_rates(solved["weights"], donor_rates)
    family = family_from_predicted_rates(rates)
    solved["predicted_rates"] = rates
    solved["predicted_family"] = family
    solved["predicted_family_key"] = family_key(family)
    solved["probability_supported_family"] = "unresolved"
    return solved


def select_lambda(donor_features: np.ndarray, donor_rates: np.ndarray, groups: Sequence[str], grid: Sequence[float] = LAMBDA_GRID) -> dict:
    """Leave-one-group-out absolute error on donor rows only."""
    labels = list(groups)
    unique = list(dict.fromkeys(labels))
    if len(unique) < 2:
        return {"lambda": None, "fallback_reason": "insufficient_groups_for_lambda"}
    best = None
    best_score = None
    for lam in grid:
        errors = []
        for held in unique:
            train = [index for index, label in enumerate(labels) if label != held]
            test = [index for index, label in enumerate(labels) if label == held]
            for index in test:
                solved = solve_weights(donor_features[train], donor_features[index], lam)
                if solved["family_status"] == "abstain" or solved["weights"] is None:
                    errors.append(1.0)
                    continue
                predicted = synthesize_rates(solved["weights"], donor_rates[train])
                errors.append(float(np.mean(np.abs(np.asarray(predicted) - donor_rates[index]))))
        score = float(np.mean(errors))
        if best_score is None or score < best_score:
            best_score = score
            best = lam
    return {"lambda": best, "mean_absolute_error": best_score, "fallback_reason": None}


def false_joint_example() -> dict:
    """Averaging an A-only table and a B-only table predicts a joint family at theta 0.8."""
    rates = synthesize_rates([0.5, 0.5], [[0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0]])
    family = family_from_predicted_rates(rates)
    return {
        "rates": rates,
        "family_key": family_key(family),
        "protocol_verified": False,
        "note": "simplex weighting does not preserve repair-family structure",
    }


def logo_residual_threshold(residuals: Sequence[float]) -> float:
    ordered = sorted(float(value) for value in residuals)
    count = len(ordered)
    if count == 0:
        return 0.0
    index = min(count - 1, math.ceil(0.95 * count) - 1)
    return ordered[index]

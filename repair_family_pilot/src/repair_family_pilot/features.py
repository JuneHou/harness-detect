"""Seven-feature pre-repair vector taken from structured diagnostic events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

FEATURE_NAMES = (
    "task_char_len",
    "task_turn_count",
    "diagnostic_model_calls",
    "diagnostic_tool_calls",
    "diagnostic_parser_error_count",
    "diagnostic_token_estimate",
    "diagnostic_history_messages",
)

PARSER_MARKERS = ("parsing error", "OUTPUT_PARSING_FAILURE")


def allowlist_document() -> dict:
    return {
        "feature_names": list(FEATURE_NAMES),
        "evidence": "structured diagnostic events, not repaired outputs",
        "scaling": "donor mean and standard deviation only",
    }


def write_allowlist(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(allowlist_document(), indent=2) + "\n", encoding="utf-8")


def _payload_text(event: dict) -> str:
    payload = event.get("payload", "")
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, sort_keys=True)


def extract_features(task_payload: str, turns: Sequence[str], events: Iterable[dict] | None) -> dict:
    """Return the numeric vector and missingness flags.

    A missing event log stores zeros and a missingness flag of 1 for every
    diagnostic feature. Task fields are still taken from the task itself.
    """
    values = {
        "task_char_len": len(task_payload or ""),
        "task_turn_count": len(list(turns)),
    }
    missing = {name: 0 for name in FEATURE_NAMES}
    if events is None:
        for name in FEATURE_NAMES:
            if name not in values:
                values[name] = 0
                missing[name] = 1
        return {"values": [values[name] for name in FEATURE_NAMES], "missingness": [missing[name] for name in FEATURE_NAMES], "names": list(FEATURE_NAMES)}

    event_list = list(events)
    model_requests = [event for event in event_list if event.get("kind") == "model_request"]
    model_responses = [event for event in event_list if event.get("kind") == "model_response"]
    tool_calls = [event for event in event_list if event.get("kind") == "tool_call"]
    parser_hits = 0
    for event in event_list:
        if event.get("kind") not in {"termination", "model_response"}:
            continue
        text = _payload_text(event)
        if any(marker in text for marker in PARSER_MARKERS):
            parser_hits += 1
    snapshots = [event for event in event_list if event.get("kind") == "memory_snapshot"]
    history = 0
    if snapshots:
        payload = snapshots[-1].get("payload")
        if isinstance(payload, list):
            history = len(payload)
        elif isinstance(payload, dict) and isinstance(payload.get("messages"), list):
            history = len(payload["messages"])
    token_chars = sum(len(_payload_text(event)) for event in model_requests + model_responses)
    values.update(
        {
            "diagnostic_model_calls": len(model_requests),
            "diagnostic_tool_calls": len(tool_calls),
            "diagnostic_parser_error_count": parser_hits,
            "diagnostic_token_estimate": token_chars // 4,
            "diagnostic_history_messages": history,
        }
    )
    return {
        "values": [values[name] for name in FEATURE_NAMES],
        "missingness": [missing[name] for name in FEATURE_NAMES],
        "names": list(FEATURE_NAMES),
    }


def fit_scaler(donor_rows: Sequence[Sequence[float]]) -> dict:
    """Donor-only location and scale. A zero standard deviation becomes 1."""
    import numpy as np

    matrix = np.asarray(donor_rows, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_NAMES):
        raise ValueError("donor feature matrix has the wrong shape")
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std = np.where(std == 0, 1.0, std)
    return {"mean": mean.tolist(), "std": std.tolist()}


def apply_scaler(row: Sequence[float], scaler: dict) -> list:
    import numpy as np

    mean = np.asarray(scaler["mean"], dtype=float)
    std = np.asarray(scaler["std"], dtype=float)
    return ((np.asarray(row, dtype=float) - mean) / std).tolist()

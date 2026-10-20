"""Scheduling, configuration order, and resumable cache keys."""

from __future__ import annotations

from repair_family_pilot.records import cache_key

CONFIGS = ("empty", "A", "B", "AB")
PHASES = ("development", "diagnostic", "reference", "online_probe", "confirmation", "unit_test")


def configuration_order(repeat_index: int) -> tuple:
    shift = repeat_index % 4
    return CONFIGS[shift:] + CONFIGS[:shift]


def run_cache_key(**parts: str) -> str:
    ordered = [f"{name}={parts[name]}" for name in sorted(parts)]
    return cache_key(ordered)


def confirmation_ids(count: int = 10) -> list:
    return [f"confirmation-{index}" for index in range(count)]


def accepts_cached_row(requested_phase: str, requested_repeat: str, stored: dict) -> bool:
    if stored.get("phase") != requested_phase or stored.get("repeat_id") != requested_repeat:
        return False
    if requested_phase == "confirmation" and stored.get("phase") in {"reference", "online_probe"}:
        return False
    return True

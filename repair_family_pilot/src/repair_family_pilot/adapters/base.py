"""Adapter protocol for one conversation under one repair set."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class RunRequest:
    task_payload: str
    turns: Sequence[str]
    initial_state: dict
    repair_set: str
    repeat_id: str
    phase: str


@dataclass
class RunResult:
    status: str
    results: list = field(default_factory=list)
    events: list = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

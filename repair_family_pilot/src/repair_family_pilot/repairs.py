"""Patch text for a documented repair. Application follows the written definition."""

from __future__ import annotations

import ast
from pathlib import Path


def parse_status(source: str) -> str:
    try:
        ast.parse(source)
    except SyntaxError:
        return "parse_error"
    return "parse_ok"


def compile_status(source: str, filename: str = "<repair>") -> str:
    if parse_status(source) == "parse_error":
        return "parse_error"
    try:
        compile(source, filename, "exec")
    except SyntaxError:
        return "compile_error"
    return "compile_ok"


SHARED_MODEL_OLD = """llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0,
    openai_api_key=api_key
)"""

SHARED_MODEL_NEW = """llm = ChatOpenAI(
    model="gpt-6-luna",
    temperature=0,
    openai_api_key=api_key,
    reasoning_effort="none",
)"""

FROZEN_MODEL = {
    "model": "gpt-6-luna",
    "reasoning_effort": "none",
    "temperature": 0,
    "applied_to": ["agent", "llm-math"],
    "configurations": ["empty", "A", "B", "AB"],
}


def apply_shared_model(source: str) -> str:
    """Set the experiment model on the shared llm object. Repairs A and B are not changed."""
    return apply_exact_replacement(source, SHARED_MODEL_OLD, SHARED_MODEL_NEW)


def apply_exact_replacement(source: str, old: str, new: str) -> str:
    if old not in source:
        raise ValueError("repair scope is not present in the baseline source")
    if source.count(old) != 1:
        raise ValueError("repair scope is not unique")
    return source.replace(old, new, 1)


def write_harness(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")

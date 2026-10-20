"""Zero-probe files are hashed before any assisted probe file is written."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def write_zero_probe(directory: Path, payload: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "zero_probe.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (directory / "zero_probe.sha256").write_text(digest + "\n", encoding="utf-8")
    return path


def write_assisted(directory: Path, budget: int, payload: dict) -> Path:
    digest_path = directory / "zero_probe.sha256"
    zero_path = directory / "zero_probe.json"
    if not digest_path.exists() or not zero_path.exists():
        raise RuntimeError("zero-probe hash is missing")
    recorded = digest_path.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(zero_path.read_bytes()).hexdigest()
    if recorded != actual:
        raise RuntimeError("zero-probe file changed before the assisted result was stored")
    path = directory / f"assisted_budget_{budget}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if hashlib.sha256(zero_path.read_bytes()).hexdigest() != recorded:
        raise RuntimeError("assisted write overwrote the zero-probe file")
    return path

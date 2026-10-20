"""JSONL, Parquet, and SQLite records."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

import pyarrow as pa
import pyarrow.parquet as pq


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_parquet(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        table = pa.table({"empty": pa.array([], type=pa.string())})
    else:
        columns = sorted({key for row in rows for key in row})
        data = {column: [row.get(column) for row in rows] for column in columns}
        table = pa.table(data)
    pq.write_table(table, path)


def cache_key(parts: Iterable[str]) -> str:
    blob = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS runs (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
    )
    return connection


def cache_get(connection: sqlite3.Connection, key: str) -> dict | None:
    row = connection.execute("SELECT payload FROM runs WHERE cache_key = ?", (key,)).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def cache_put(connection: sqlite3.Connection, key: str, payload: dict) -> None:
    connection.execute(
        "INSERT OR REPLACE INTO runs (cache_key, payload) VALUES (?, ?)",
        (key, json.dumps(payload, sort_keys=True)),
    )
    connection.commit()

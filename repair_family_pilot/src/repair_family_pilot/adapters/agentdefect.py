"""Run one whole conversation in one subprocess."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from repair_family_pilot.adapters.base import RunResult
from repair_family_pilot.repairs import apply_exact_replacement, apply_shared_model, compile_status, parse_status, write_harness

DRIVER = textwrap.dedent(
    '''
    import json, os, sys
    sys.path.insert(0, os.environ["HARNESS_DIR"])
    sys.path.insert(0, os.environ["HOOK_DIR"])
    import trace_hooks
    trace_hooks.install(os.environ["EVENT_LOG"])
    try:
        import harness_under_test as harness
    except Exception as exc:
        trace_hooks.termination("import_error", repr(exc))
        print(json.dumps({"status": "import_error", "error": repr(exc), "results": []}))
        raise SystemExit(0)
    if hasattr(harness, "run_agent"):
        entry = "run_agent"
    elif hasattr(harness, "app"):
        entry = "flask"
    else:
        trace_hooks.termination("construct_error", "no entry point")
        print(json.dumps({"status": "construct_error", "error": "no entry point", "results": []}))
        raise SystemExit(0)
    turns = json.loads(os.environ["TURNS_JSON"])
    initial = json.loads(os.environ.get("INITIAL_MEMORY_JSON") or "[]")
    if initial and hasattr(harness, "memory"):
        for item in initial:
            if item["role"] == "human":
                harness.memory.chat_memory.add_user_message(item["content"])
            else:
                harness.memory.chat_memory.add_ai_message(item["content"])
        trace_hooks.snapshot(harness)
    results = []
    try:
        for turn in turns:
            if entry == "run_agent":
                results.append(harness.run_agent(turn))
            else:
                client = harness.app.test_client()
                response = client.post("/ask_gpt", data={"text": turn})
                results.append(response.get_data(as_text=True))
            trace_hooks.snapshot(harness)
        trace_hooks.termination("finished", "")
        print(json.dumps({"status": "finished", "results": [str(item) for item in results]}))
    except Exception as exc:
        trace_hooks.termination("execute_error", repr(exc))
        print(json.dumps({"status": "execute_error", "error": repr(exc), "results": [str(item) for item in results]}))
    '''
).lstrip()


def prepare_source(baseline: str, repairs: list, repair_set: str) -> tuple[str, str]:
    """Apply the shared model, then the documented repairs for empty, A, B, or AB."""
    source = apply_shared_model(baseline)
    selected = []
    if repair_set in {"A", "AB"}:
        selected.append(next(item for item in repairs if item["repair_id"] == "A"))
    if repair_set in {"B", "AB"}:
        selected.append(next(item for item in repairs if item["repair_id"] == "B"))
    for item in selected:
        source = apply_exact_replacement(source, item["old"], item["new"])
    status = parse_status(source)
    if status == "parse_error":
        return source, "parse_error"
    status = compile_status(source)
    if status == "compile_error":
        return source, "compile_error"
    return source, "ready"


def _read_events(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def run_conversation(work_dir: Path, source: str, turns: list, timeout: int = 180, python_executable: str | None = None, initial_memory: list | None = None) -> RunResult:
    """Create one process, run every turn inside it, then save evidence and reset."""
    work_dir.mkdir(parents=True, exist_ok=True)
    write_harness(work_dir / "harness_under_test.py", source)
    (work_dir / "driver.py").write_text(DRIVER, encoding="utf-8")
    event_log = work_dir / "events.jsonl"
    hook_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.update(
        {
            "HARNESS_DIR": str(work_dir),
            "HOOK_DIR": str(hook_dir),
            "EVENT_LOG": str(event_log),
            "TURNS_JSON": json.dumps(turns),
            "INITIAL_MEMORY_JSON": json.dumps(initial_memory or []),
            "PYTHONPATH": str(hook_dir) + os.pathsep + str(work_dir) + os.pathsep + env.get("PYTHONPATH", ""),
        }
    )
    try:
        completed = subprocess.run(
            [python_executable or sys.executable, str(work_dir / "driver.py")],
            cwd=str(work_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return RunResult(status="infrastructure_error", stdout=exc.stdout or "", stderr=exc.stderr or "")
    stdout = completed.stdout
    stderr = completed.stderr
    payload = {}
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            payload = json.loads(line)
            break
    status = payload.get("status", "execute_error")
    result = RunResult(
        status=status,
        results=payload.get("results", []),
        events=_read_events(event_log),
        stdout=stdout,
        stderr=stderr,
        returncode=completed.returncode,
    )
    # Reset the work directory after the evidence has been copied into the result.
    for child in work_dir.iterdir():
        if child.is_file():
            child.unlink()
    return result

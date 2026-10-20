"""Runtime construction screen. Environment failures do not consume a slot."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from repair_family_pilot.adapters.agentdefect import prepare_source, run_conversation
from repair_family_pilot.environment import check_model, ensure_case_env
from repair_family_pilot.oracle import check_result, inspect_source
from repair_family_pilot.runner import configuration_order

EXECUTED = {"finished", "task_failure", "success"}
NOT_READY = {"import_error", "construct_error", "execute_error", "parse_error", "compile_error", "infrastructure_error"}
FROZEN_MODEL_NAME = "gpt-6-luna"
FROZEN_REASONING = "none"


def _harness_contract_error(result) -> str:
    """A repair can raise before any model call because its own memory contract is unmet."""
    text = result.stdout or ""
    if "chat_history should be a list of base messages" in text:
        return text
    return ""


def technical_report(result, turns: list, checks: list) -> dict:
    """Technical gate for one conversation. A wrong answer is recorded and does not fail this gate."""
    problems = []
    harness_error = _harness_contract_error(result)
    if harness_error:
        return {
            "technical_ok": True,
            "problems": [],
            "correct": False,
            "model_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "memory_snapshots": [],
            "status": "task_failure",
            "error": "chat_history should be a list of base messages, got str",
        }
    if result.status in NOT_READY:
        problems.append(result.status)
    parsed = bool(result.results) and all(isinstance(item, str) and item.strip() for item in result.results)
    if not parsed:
        problems.append("output_not_parsed")
    requests = [event for event in result.events if event.get("kind") == "model_request"]
    responses = [event for event in result.events if event.get("kind") == "model_response"]
    if not requests or not responses:
        problems.append("no_model_trace")
    models = {event.get("payload", {}).get("model") for event in requests}
    efforts = {event.get("payload", {}).get("reasoning_effort") for event in requests}
    if requests and models != {FROZEN_MODEL_NAME}:
        problems.append("model_mismatch")
    if requests and efforts != {FROZEN_REASONING}:
        problems.append("reasoning_effort_mismatch")
    snapshots = [event for event in result.events if event.get("kind") == "memory_snapshot"]
    if len(snapshots) < len(turns):
        problems.append("missing_memory_snapshot")
    usage_rows = [event.get("payload", {}).get("usage") for event in responses]
    input_tokens = sum(int(row.get("input_tokens") or 0) for row in usage_rows if isinstance(row, dict))
    output_tokens = sum(int(row.get("output_tokens") or 0) for row in usage_rows if isinstance(row, dict))
    if responses and input_tokens == 0 and output_tokens == 0:
        problems.append("token_usage_missing")
    error = ""
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{") and "error" in line:
            try:
                error = json.loads(line).get("error", "")
            except json.JSONDecodeError:
                error = line
    correct = check_result(result.results[-1] if result.results else "", checks)
    return {
        "technical_ok": not problems,
        "problems": problems,
        "correct": correct,
        "model_calls": len(requests),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "memory_snapshots": [event.get("payload") for event in snapshots],
        "status": result.status,
        "error": error,
    }


def _rows(root: Path) -> dict:
    path = root / "artifacts" / "audit" / "case_audit.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["case_id"]: row for row in csv.DictReader(handle)}


def _turns_from_test(source: str) -> list:
    """Prompts passed to run_agent, in source order. Print labels are not turns."""
    import ast
    tree = ast.parse(source)
    assigned = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                assigned[node.targets[0].id] = node.value.value
    turns = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name != "run_agent" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            turns.append(arg.value)
        elif isinstance(arg, ast.Name) and arg.id in assigned:
            turns.append(assigned[arg.id])
    return turns


def construction_screen(root: Path, queue: list, repeats: int, caps: dict) -> int:
    """Walk the full queue. Stop after two cases have started all four configurations.

    Stop before another episode when the episode count or the recorded model-call
    count has reached the resolved cap.
    """
    max_episodes = int(caps["max_episodes"])
    max_calls = int(caps["max_model_calls"])
    rows = _rows(root)
    completed = 0
    episodes = 0
    model_calls = 0
    notes = []
    for case_id in queue:
        if completed >= 2:
            break
        row = rows[case_id]
        minimal = root / "artifacts" / "environments" / "cases" / case_id / "requirements.min.txt"
        if minimal.exists():
            requirements = minimal.read_text(encoding="utf-8")
        else:
            requirements = _requirements_only(row["dependency_runtime"])
        env = ensure_case_env(root, case_id, requirements)
        if env["status"] != "ok":
            notes.append({"case_id": case_id, "status": "environment_blocked", "finding": env["finding"]})
            continue
        repairs = json.loads(row["proposed_candidates"])
        # Baseline source is recovered by reversing nothing: read the diff's from-file via the zip in audit.
        baseline = _baseline_source(root, case_id)
        from repair_family_pilot.repairs import apply_shared_model

        configured = apply_shared_model(baseline)
        model = check_model(configured)
        if model["status"] != "ok":
            notes.append({"case_id": case_id, "status": "environment_blocked", "finding": model["finding"], "model_id": model.get("model_id", "")})
            continue
        test_source = _zip_text(case_id, "test.py")
        turns = _turns_from_test(test_source)
        checks = inspect_source(test_source, _zip_text(case_id, "readme.md"))["content_checks"]
        _, smoke_results, episodes, model_calls, smoke_ready = _run_block(
            root, case_id, baseline, repairs, turns, checks, env.get("python"),
            repeats=1, phase="smoke", episodes=episodes, model_calls=model_calls,
            max_episodes=max_episodes, max_calls=max_calls, notes=notes,
        )
        smoke_report = {}
        for name in ("empty", "A", "B", "AB"):
            if not smoke_results[name]:
                smoke_report[name] = {"technical_ok": False, "problems": ["not_run"], "correct": None}
            else:
                smoke_report[name] = technical_report(smoke_results[name][-1], turns, checks)
        smoke_path = root / "artifacts" / "audit" / f"smoke_{case_id}.json"
        smoke_path.write_text(json.dumps(smoke_report, indent=2) + "\n", encoding="utf-8")
        if not smoke_ready or not all(item["technical_ok"] for item in smoke_report.values()):
            notes.append({
                "case_id": case_id,
                "status": "technical_failed",
                "smoke": {
                    name: item["problems"] + ([item["error"]] if item.get("error") else [])
                    for name, item in smoke_report.items()
                },
            })
            continue
        outcomes, _, episodes, model_calls, ready = _run_block(
            root, case_id, baseline, repairs, turns, checks, env.get("python"),
            repeats=repeats, phase="repeat", episodes=episodes, model_calls=model_calls,
            max_episodes=max_episodes, max_calls=max_calls, notes=notes,
        )
        if not ready:
            notes.append({"case_id": case_id, "status": "not_ready", "outcomes": outcomes})
            completed += 1
            continue
        _write_preview(root, row, repairs, outcomes, turns, checks, smoke_report)
        notes.append({"case_id": case_id, "status": "preview_written", "outcomes": outcomes})
        completed += 1
    (root / "artifacts" / "audit" / "screen_notes.json").write_text(json.dumps(notes, indent=2) + "\n", encoding="utf-8")
    return sum(1 for note in notes if note["status"] == "preview_written")


def _run_block(root, case_id, baseline, repairs, turns, checks, python_executable, repeats, phase, episodes, model_calls, max_episodes, max_calls, notes):
    outcomes = {name: [] for name in ("empty", "A", "B", "AB")}
    results = {name: [] for name in ("empty", "A", "B", "AB")}
    ready = True
    for repeat_index in range(repeats):
        stopped = False
        for repair_set in configuration_order(repeat_index):
            if episodes >= max_episodes or model_calls >= max_calls:
                notes.append({"case_id": case_id, "status": "cap_reached", "episodes": episodes, "model_calls": model_calls, "phase": phase})
                outcomes[repair_set].append("cap_reached")
                ready = False
                stopped = True
                break
            source, prep = prepare_source(baseline, repairs, repair_set)
            if prep != "ready":
                outcomes[repair_set].append(prep)
                ready = False
                continue
            result = run_conversation(
                root / "artifacts" / "traces" / "work" / f"{case_id}-{phase}-{repair_set}-{repeat_index}",
                source,
                turns,
                python_executable=python_executable,
            )
            episodes += 1
            model_calls += sum(1 for event in result.events if event.get("kind") == "model_request")
            results[repair_set].append(result)
            if _harness_contract_error(result):
                outcomes[repair_set].append("task_failure")
                continue
            if result.status in NOT_READY:
                outcomes[repair_set].append(result.status)
                ready = False
                continue
            passed = check_result(result.results[-1] if result.results else "", checks)
            if passed is False:
                outcomes[repair_set].append("task_failure")
            else:
                outcomes[repair_set].append("success" if passed else "finished")
        if stopped:
            break
    return outcomes, results, episodes, model_calls, ready


def _requirements_only(dependency_runtime: str) -> str:
    lines = []
    for line in dependency_runtime.splitlines():
        if line.strip().lower().startswith("how to run"):
            break
        lines.append(line)
    return "\n".join(lines).strip() + ("\n" if lines else "")


def _zip_text(case_id: str, filename: str) -> str:
    import zipfile
    from repair_family_pilot.audit import ARCHIVE
    with zipfile.ZipFile(ARCHIVE) as archive:
        key = f"AgentDefect/{case_id}/{filename}"
        if key not in archive.namelist():
            return ""
        return archive.read(key).decode("utf-8", errors="replace")


def _baseline_source(root: Path, case_id: str) -> str:
    del root
    return _zip_text(case_id, "run_buggy.py")


def _write_preview(root: Path, row: dict, repairs: list, outcomes: dict, turns: list, checks: list, smoke_report: dict) -> None:
    claim = (
        "The candidate configurations execute; their preliminary outcomes are recorded; "
        "the proposed task grid and correctness checks are ready for review. "
        "Scientific qualification remains pending."
    )
    lines = [
        f"# Task grid preview for {row['case_id']}",
        "",
        claim,
        "",
        "## Repairs",
    ]
    for item in repairs:
        lines.append(f"### {item['repair_id']}: {item['mechanism']}")
        lines.append(item["scope"])
        lines.append(item["why_independent"])
        lines.append("")
        lines.append("```")
        lines.append(item["old"])
        lines.append("```")
        lines.append("becomes")
        lines.append("```")
        lines.append(item["new"])
        lines.append("```")
        lines.append("")
    lines.append("## Why these dimensions bear on the repairs")
    for item in repairs:
        lines.append(f"- {item['repair_id']} ({item['mechanism']}): {item['why_independent']}")
    lines.append("This preview shows one published conversation. It does not draw the first 60 cells of a loop.")
    lines.append("")
    lines.append("## Concrete task")
    lines.append("Turns: " + " | ".join(turns))
    lines.append("Correctness checks were taken from the published test before this screen. They do not mention whether A or B is enabled.")
    for check in checks:
        lines.append(f"- {check['kind']} {check['expected']}")
    lines.append("")
    lines.append("## Frozen model")
    lines.append("gpt-6-luna with reasoning_effort none, temperature 0.")
    lines.append("The same ChatOpenAI object is passed to the agent and to llm-math.")
    lines.append("This setting is outside repairs A and B and is the same for empty, A, B, and AB.")
    lines.append("")
    lines.append("## Smoke technical check")
    for name, item in smoke_report.items():
        lines.append(f"- {name}: technical_ok={item['technical_ok']} correct={item['correct']} calls={item.get('model_calls')} input_tokens={item.get('input_tokens')} output_tokens={item.get('output_tokens')}")
    lines.append("A wrong answer does not by itself decide the repair family. Joint and alternative families are not assumed.")
    lines.append("")
    lines.append("## Three-repeat outcomes")
    lines.append(json.dumps(outcomes, indent=2))
    lines.append("")
    lines.append("probability_supported_family: unresolved")
    preview = root / "artifacts" / "audit" / "task_grid_preview.md"
    preview.write_text("\n".join(lines) + "\n", encoding="utf-8")
    import hashlib
    digest = hashlib.sha256(preview.read_bytes()).hexdigest()
    preview.with_suffix(".sha256").write_text(digest + "\n", encoding="utf-8")
    manifest = {
        "selected_case": row["case_id"],
        "repairs": repairs,
        "preliminary_outcomes": outcomes,
        "probability_supported_family": "unresolved",
        "scientific_qualification": "pending",
        "claim": claim,
        "model_config": {
            "model": "gpt-6-luna",
            "reasoning_effort": "none",
            "temperature": 0,
            "applied_to": ["agent", "llm-math"],
            "configurations": ["empty", "A", "B", "AB"],
            "frozen_before_donor_collection": True,
        },
        "smoke": {name: {"technical_ok": item["technical_ok"], "correct": item["correct"], "problems": item["problems"]} for name, item in smoke_report.items()},
    }
    path = root / "artifacts" / "manifests" / "provisional_candidate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

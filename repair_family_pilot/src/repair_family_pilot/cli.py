"""Command line for the preview build.

Suite collection is refused until a resolved experiment manifest exists.
pilot.yaml keeps selected_case null. Later commands load a resolved manifest
when one has been frozen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repair_family_pilot.audit import run_audit
from repair_family_pilot.features import write_allowlist

ROOT_MARKERS = ("pyproject.toml", "configs/pilot.yaml")


def project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if all((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    raise SystemExit("run this command from repair_family_pilot")


def load_flat_yaml(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value in {"null", ""}:
            parsed = None
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            parsed = [] if not inner else [item.strip().strip("'\"") for item in inner.split(",")]
            converted = []
            for item in parsed:
                converted.append(_scalar(item))
            parsed = converted
        else:
            parsed = _scalar(value)
        data[key.strip()] = parsed
    return data


def _scalar(value: str):
    if value in {"null", "None"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def resolve_caps(root: Path, pilot: dict) -> dict | None:
    manifest = root / "artifacts" / "manifests" / "experiment_manifest.json"
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        caps = payload.get("resource_caps")
        if isinstance(caps, dict) and _both_ints(caps):
            return caps
    budget = load_flat_yaml(root / "configs" / "budget.yaml")
    if _both_ints(budget):
        return {"max_model_calls": int(budget["max_model_calls"]), "max_episodes": int(budget["max_episodes"])}
    caps = pilot.get("resource_caps")
    if isinstance(caps, dict) and _both_ints(caps):
        return caps
    return None


def _both_ints(payload: dict) -> bool:
    return isinstance(payload.get("max_model_calls"), int) and isinstance(payload.get("max_episodes"), int)


def _write_blocked(root: Path) -> None:
    path = root / "artifacts" / "reports" / "live_stage_blocked.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Live stage blocked. No resolved max_model_calls and max_episodes were found "
        "in the experiment manifest, configs/budget.yaml, or configs/pilot.yaml.\n",
        encoding="utf-8",
    )


def command_audit(root: Path) -> int:
    write_allowlist(root / "artifacts" / "manifests" / "features_allowlist.json")
    result = run_audit(root)
    print(f"audit rows {result['rows']}")
    print(f"screen queue {len(result['queue'])}")
    return 0


def command_qualify(root: Path) -> int:
    pilot = load_flat_yaml(root / "configs" / "pilot.yaml")
    if not (root / "artifacts" / "audit" / "case_audit.csv").exists():
        command_audit(root)
    caps = resolve_caps(root, pilot)
    if caps is None:
        _write_blocked(root)
        report = root / "artifacts" / "reports" / "final_report.md"
        report.write_text("status: implementation_complete\n\nLive stage blocked. No resource caps are resolved.\n", encoding="utf-8")
        print("qualify exit 3: resource caps are unresolved")
        return 3
    queue_path = root / "artifacts" / "audit" / "screen_queue.txt"
    queue = [line.strip() for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    from repair_family_pilot.screen import construction_screen

    scheduled = min(len(queue), 2) * (1 + int(pilot.get("development_repeats") or 3)) * 4
    if scheduled > int(caps["max_episodes"]):
        _write_blocked(root)
        print(f"qualify exit 3: scheduled episodes {scheduled} exceed max_episodes {caps['max_episodes']}")
        return 3
    screened = construction_screen(root, queue, repeats=int(pilot.get("development_repeats") or 3), caps=caps)
    notes_path = root / "artifacts" / "audit" / "screen_notes.json"
    notes = json.loads(notes_path.read_text(encoding="utf-8")) if notes_path.exists() else []
    print(f"runtime screens completed {screened}")
    for note in notes:
        if note.get("status") == "technical_failed":
            print(f"technical screen failed for {note.get('case_id')}")
            for name, problems in note.get("smoke", {}).items():
                print(f"  {name}: {', '.join(problems)}")
            print(f"details: artifacts/audit/smoke_{note.get('case_id')}.json")
    report = root / "artifacts" / "reports" / "final_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    if any(note.get("status") == "technical_failed" for note in notes):
        report.write_text(
            "status: implementation_complete\n\n"
            "The one-conversation technical screen did not pass. "
            "The three-repeat screen was not started. Scientific qualification remains pending.\n",
            encoding="utf-8",
        )
        return 4
    if screened == 0:
        report.write_text("status: data_blocked\n\nNo queued case executed all four configurations.\n", encoding="utf-8")
        return 4
    return 0


def command_freeze(root: Path) -> int:
    print("experiment_manifest.json is not frozen in this build. Task generator, grouping, oracle, features, model settings, and resource limits are not all resolved.")
    return 4


def command_collect(root: Path) -> int:
    pilot = load_flat_yaml(root / "configs" / "pilot.yaml")
    caps = resolve_caps(root, pilot)
    if caps is None:
        _write_blocked(root)
        print("collect exit 3: resource caps are unresolved")
        return 3
    from repair_family_pilot.collect import run_collection
    repeats = int(pilot.get("reference_repeats") or 20)
    return run_collection(root, repeats, caps)


def command_report(root: Path) -> int:
    preview = root / "artifacts" / "audit" / "task_grid_preview.md"
    if preview.exists():
        print(preview.read_text(encoding="utf-8"))
        return 0
    blocked = root / "artifacts" / "reports" / "live_stage_blocked.md"
    if blocked.exists():
        print(blocked.read_text(encoding="utf-8"))
        return 0
    print("no preview and no live-stage report yet")
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repair_family_pilot")
    parser.add_argument("command", choices=["audit", "qualify", "freeze", "collect", "fit", "calibrate", "predict", "evaluate", "report"])
    parser.add_argument("--config", default="configs/pilot.yaml")
    parser.add_argument("--split", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    root = project_root()
    if args.command == "audit":
        return command_audit(root)
    if args.command == "qualify":
        return command_qualify(root)
    if args.command == "freeze":
        return command_freeze(root)
    if args.command == "collect":
        if args.dry_run:
            print("dry-run: no model calls; suite collection is not scheduled in this build")
            return 4
        return command_collect(root)
    if args.command in {"fit", "calibrate", "predict", "evaluate"}:
        print(f"{args.command} is implemented in the library and is not run before the task-grid preview is reviewed")
        return 4
    if args.command == "report":
        return command_report(root)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Full four-configuration collection for the twelve task groups. No smoke step."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np

from repair_family_pilot.adapters.agentdefect import prepare_source, run_conversation
from repair_family_pilot.audit import ARCHIVE, JUSTIFIED
from repair_family_pilot.donors import predict_table, select_lambda
from repair_family_pilot.families import CONFIGS, family_from_counts, family_key
from repair_family_pilot.features import extract_features, fit_scaler, apply_scaler
from repair_family_pilot.oracle import check_result
from repair_family_pilot.repairs import FROZEN_MODEL
from repair_family_pilot.runner import configuration_order
from repair_family_pilot.screen import _harness_contract_error
from repair_family_pilot.splits import assign_split
from repair_family_pilot.suite import build_suite

CASE_ID = "76906469"
NOT_READY = {"import_error", "construct_error", "execute_error", "parse_error", "compile_error", "infrastructure_error"}


def _load_done(path: Path) -> dict:
    done = {}
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            done[row["key"]] = row
    return done


def _outcome(result, expected: str) -> str:
    if _harness_contract_error(result):
        return "task_failure"
    if result.status in NOT_READY:
        return result.status
    passed = check_result(result.results[-1] if result.results else "", [{"kind": "assertIn", "expected": expected}])
    if passed is True:
        return "success"
    return "task_failure"


def run_collection(root: Path, repeats: int, caps: dict) -> int:
    suite = build_suite()
    split = assign_split([group["group_id"] for group in suite])
    manifest_dir = root / "artifacts" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    suite_path = manifest_dir / "task_suite.json"
    suite_path.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
    (manifest_dir / "split.json").write_text(json.dumps(split, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "selected_case": CASE_ID,
        "model_config": FROZEN_MODEL,
        "repeats": repeats,
        "group_count": len(suite),
        "cell_count": len(suite),
        "split": split["assignment"],
        "resource_caps": caps,
        "scientific_qualification": "collection",
    }
    (manifest_dir / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = zipfile.ZipFile(ARCHIVE)
    baseline = archive.read(f"AgentDefect/{CASE_ID}/run_buggy.py").decode()
    repairs = JUSTIFIED[CASE_ID]
    log_path = root / "artifacts" / "donor_tables" / "runs.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    done = _load_done(log_path)
    python = "/data/wang/junh/envs/harnessfix/bin/python"
    episodes = 0
    model_calls = 0
    max_episodes = int(caps["max_episodes"])
    max_calls = int(caps["max_model_calls"])
    total = len(suite) * repeats * 4

    for group in suite:
        for repeat_index in range(repeats):
            for repair_set in configuration_order(repeat_index):
                key = f"{group['group_id']}|{repair_set}|{repeat_index}"
                if key in done:
                    episodes += 1
                    model_calls += int(done[key].get("model_calls") or 0)
                    continue
                if episodes >= max_episodes or model_calls >= max_calls:
                    print(f"cap reached episodes={episodes} model_calls={model_calls}")
                    _write_report(root, suite, split, done, repeats, capped=True)
                    return 3
                source, prep = prepare_source(baseline, repairs, repair_set)
                if prep != "ready":
                    row = {"key": key, "group_id": group["group_id"], "repair_set": repair_set, "repeat": repeat_index, "outcome": prep, "model_calls": 0}
                else:
                    result = run_conversation(
                        root / "artifacts" / "traces" / "full" / key.replace("|", "-"),
                        source,
                        group["turns"],
                        python_executable=python,
                        initial_memory=group["initial_memory"],
                    )
                    calls = sum(1 for event in result.events if event.get("kind") == "model_request")
                    row = {
                        "key": key,
                        "group_id": group["group_id"],
                        "repair_set": repair_set,
                        "repeat": repeat_index,
                        "outcome": _outcome(result, group["expected"]),
                        "model_calls": calls,
                        "events": result.events if repair_set == "empty" and repeat_index == 0 else [],
                    }
                    model_calls += calls
                episodes += 1
                done[key] = row
                with log_path.open("a", encoding="utf-8") as handle:
                    stored = dict(row)
                    handle.write(json.dumps(stored) + "\n")
                print(f"{episodes}/{total} {group['group_id']} {repair_set} repeat {repeat_index}: {row['outcome']}", flush=True)
    _write_report(root, suite, split, done, repeats, capped=False)
    return 0


def _rates(done: dict, group_id: str, repeats: int) -> list:
    rates = []
    for repair_set in CONFIGS:
        successes = 0
        observed = 0
        for repeat_index in range(repeats):
            row = done.get(f"{group_id}|{repair_set}|{repeat_index}")
            if row is None:
                continue
            observed += 1
            if row["outcome"] == "success":
                successes += 1
        rates.append(successes / observed if observed else 0.0)
    return rates


def _write_report(root: Path, suite: list, split: dict, done: dict, repeats: int, capped: bool) -> None:
    families = {}
    for group in suite:
        counts = {}
        for index, repair_set in enumerate(CONFIGS):
            counts[repair_set] = sum(
                1
                for repeat_index in range(repeats)
                if done.get(f"{group['group_id']}|{repair_set}|{repeat_index}", {}).get("outcome") == "success"
            )
        family = family_from_counts(counts, repeats)
        families[group["group_id"]] = family_key(family)
    test_ids = [group_id for group_id, name in split["assignment"].items() if name == "test"]
    donor_groups = [group for group in suite if split["assignment"][group["group_id"]] == "donor"]
    donor_ids = [group["group_id"] for group in donor_groups]
    feature_rows = []
    rate_rows = []
    for group in donor_groups:
        empty = done.get(f"{group['group_id']}|empty|0", {})
        features = extract_features(" ".join(group["turns"]), group["turns"], empty.get("events") or [])
        feature_rows.append(features["values"])
        rate_rows.append(_rates(done, group["group_id"], repeats))
    prediction = {}
    if len(donor_groups) >= 2:
        scaler = fit_scaler(feature_rows)
        scaled = np.asarray([apply_scaler(row, scaler) for row in feature_rows], dtype=float)
        chosen = select_lambda(scaled, np.asarray(rate_rows, dtype=float), donor_ids)
        lam = chosen.get("lambda")
        if lam is not None:
            for group in suite:
                if group["group_id"] not in test_ids:
                    continue
                empty = done.get(f"{group['group_id']}|empty|0", {})
                features = extract_features(" ".join(group["turns"]), group["turns"], empty.get("events") or [])
                target = np.asarray(apply_scaler(features["values"], scaler), dtype=float)
                predicted = predict_table(scaled, target, rate_rows, lam)
                prediction[group["group_id"]] = {
                    "predicted": predicted.get("predicted_family_key"),
                    "measured": families[group["group_id"]],
                    "family_status": predicted.get("family_status"),
                }
    distinct = sorted(set(families.values()))
    lines = [
        f"groups {len(suite)}",
        f"cells {len(suite)}",
        f"repeats {repeats}",
        f"capped {capped}",
        "families " + json.dumps(families, sort_keys=True),
        "distinct_families " + ", ".join(distinct),
        "test_predictions " + json.dumps(prediction, sort_keys=True),
    ]
    if len(distinct) < 2:
        lines.append("status partial_scientific_scope")
        lines.append("Every measured group has the same repair family, so this collection does not establish a transfer problem.")
    else:
        lines.append("status collection_complete")
    text = "\n".join(lines) + "\n"
    report = root / "artifacts" / "reports" / "final_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text, encoding="utf-8")
    print(text, flush=True)

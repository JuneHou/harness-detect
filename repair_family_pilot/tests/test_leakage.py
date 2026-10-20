import json
from pathlib import Path

from repair_family_pilot.predictions import write_assisted, write_zero_probe


def _predict(donor_rates, features):
    return {"rates": [sum(column) / len(donor_rates) for column in zip(*donor_rates)], "features": features}


def test_sealed_reference_file_does_not_change_zero_probe(tmp_path: Path):
    reference = tmp_path / "artifacts" / "reference_private" / "outcomes.json"
    reference.parent.mkdir(parents=True)
    reference.write_text(json.dumps({"hidden": 0}), encoding="utf-8")
    donors = [[0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0]]
    first = _predict(donors, [1, 2, 3])
    reference.write_text(json.dumps({"hidden": 1}), encoding="utf-8")
    second = _predict(donors, [1, 2, 3])
    assert first == second
    assert "reference_private" not in _predict.__code__.co_varnames


def test_zero_probe_is_hashed_before_assisted_result(tmp_path: Path):
    directory = tmp_path / "predictions"
    write_zero_probe(directory, {"family": "AB"})
    digest = (directory / "zero_probe.sha256").read_text(encoding="utf-8").strip()
    write_assisted(directory, 1, {"queried": "A"})
    assert (directory / "assisted_budget_1.json").exists()
    assert (directory / "zero_probe.sha256").read_text(encoding="utf-8").strip() == digest

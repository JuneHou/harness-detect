import json
from pathlib import Path

from repair_family_pilot.adapters.agentdefect import run_conversation
from repair_family_pilot.records import cache_get, cache_put, connect
from repair_family_pilot.runner import accepts_cached_row, confirmation_ids, configuration_order, run_cache_key


def test_configuration_order_rotates_and_confirmation_ids_are_fresh():
    assert configuration_order(0) == ("empty", "A", "B", "AB")
    assert configuration_order(1) == ("A", "B", "AB", "empty")
    ids = confirmation_ids()
    assert ids[0] == "confirmation-0"
    assert "reference-0" not in ids
    assert accepts_cached_row("confirmation", "confirmation-0", {"phase": "reference", "repeat_id": "confirmation-0"}) is False


def test_cache_key_includes_phase_and_repeat(tmp_path: Path):
    left = run_cache_key(phase="reference", repeat_id="0", repair="A", task="t")
    right = run_cache_key(phase="confirmation", repeat_id="confirmation-0", repair="A", task="t")
    assert left != right
    connection = connect(tmp_path / "cache.sqlite")
    cache_put(connection, left, {"phase": "reference", "repeat_id": "0"})
    assert cache_get(connection, right) is None


def test_one_process_keeps_memory_across_turns(tmp_path: Path):
    source = (
        "messages = []\n"
        "def run_agent(text):\n"
        "    messages.append(text)\n"
        "    return '|'.join(messages)\n"
    )
    result = run_conversation(tmp_path / "work", source, ["first", "second"])
    assert result.status == "finished"
    assert result.results == ["first", "first|second"]
    snapshots = [event for event in result.events if event["kind"] == "memory_snapshot"]
    assert [event["payload"]["messages"]["contents"] for event in snapshots] == [["first"], ["first", "second"]]
    assert json.dumps(result.events)

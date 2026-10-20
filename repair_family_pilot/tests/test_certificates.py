import json
import zipfile

from repair_family_pilot.adapters.agentdefect import prepare_source
from repair_family_pilot.audit import JUSTIFIED
from repair_family_pilot.evaluation import certificate_status, later_evaluation_status, unconditional_exact_match
from repair_family_pilot.repairs import FROZEN_MODEL
from repair_family_pilot.screen import technical_report
from repair_family_pilot.adapters.base import RunResult
from repair_family_pilot.probing import choose_probe


def test_joint_certificate_needs_three_failures_and_ab_success():
    assert certificate_status({"empty": False, "A": False, "B": False, "AB": True}) == "protocol_verified"


def test_alternative_certificate_does_not_need_ab():
    assert certificate_status({"empty": False, "A": True, "B": True, "AB": None}) == "protocol_verified"


def test_partial_measurement_is_not_a_complete_certificate():
    assert certificate_status({"empty": False, "A": None, "B": None, "AB": None}) == "partially_verified"


def test_no_measurement_is_predicted_only():
    assert certificate_status({"empty": None, "A": None, "B": None, "AB": None}) == "predicted"


def test_task_failure_is_a_recorded_outcome_not_a_missing_cell():
    assert certificate_status({"empty": False, "A": False, "B": False, "AB": False}) == "protocol_verified"


def test_later_status_requires_recovery_of_both_family_types():
    blocked = later_evaluation_status(
        collection_complete=False, has_joint=True, has_alternative=True,
        primary_rate=1, additive_rate=0, nearest_rate=0,
        recovered_joint=True, recovered_alternative=True,
    )
    assert blocked["status"] is None
    partial = later_evaluation_status(
        collection_complete=True, has_joint=True, has_alternative=False,
        primary_rate=1, additive_rate=0, nearest_rate=0,
        recovered_joint=True, recovered_alternative=False,
    )
    assert partial["status"] == "partial_scientific_scope"
    negative = later_evaluation_status(
        collection_complete=True, has_joint=True, has_alternative=True,
        primary_rate=0.9, additive_rate=0.1, nearest_rate=0.1,
        recovered_joint=True, recovered_alternative=False,
    )
    assert negative["status"] == "pilot_complete_negative"
    supported = later_evaluation_status(
        collection_complete=True, has_joint=True, has_alternative=True,
        primary_rate=0.9, additive_rate=0.1, nearest_rate=0.1,
        recovered_joint=True, recovered_alternative=True,
    )
    assert supported["status"] == "pilot_complete_supported"
    assert unconditional_exact_match([None, "AB"], ["AB", "AB"]) == 0.5


def test_shared_model_is_outside_repairs_and_on_every_configuration():
    archive = zipfile.ZipFile("/data/wang/junh/githubs/SelfHeal/AgentDefect.zip")
    baseline = archive.read("AgentDefect/76906469/run_buggy.py").decode()
    repairs = JUSTIFIED["76906469"]
    seen = {}
    for name in ("empty", "A", "B", "AB"):
        source, status = prepare_source(baseline, repairs, name)
        assert status == "ready"
        assert 'model="gpt-6-luna"' in source
        assert 'reasoning_effort="none"' in source
        assert 'model_name="gpt-4"' not in source
        seen[name] = source
    assert 'return_messages=True' in seen["A"]
    assert 'return_messages=True' not in seen["B"]
    assert "CHAT_CONVERSATIONAL_REACT_DESCRIPTION" in seen["B"]
    assert "CHAT_ZERO_SHOT_REACT_DESCRIPTION" in seen["A"]
    assert "CHAT_CONVERSATIONAL_REACT_DESCRIPTION" in seen["AB"]
    assert 'return_messages=True' in seen["AB"]
    assert FROZEN_MODEL["model"] == "gpt-6-luna"
    assert "gpt-6-luna" not in repairs[0]["new"]
    assert "gpt-6-luna" not in repairs[1]["new"]


def test_technical_gate_records_a_wrong_answer_without_failing():
    result = RunResult(
        status="finished",
        results=["Paris", "I do not know"],
        events=[
            {"kind": "model_request", "payload": {"model": "gpt-6-luna", "reasoning_effort": "none"}},
            {"kind": "model_response", "payload": {"usage": {"input_tokens": 10, "output_tokens": 2}, "text": "Paris"}},
            {"kind": "memory_snapshot", "payload": {"memory": {"contents": ["q1"], "roles": ["human"]}}},
            {"kind": "model_request", "payload": {"model": "gpt-6-luna", "reasoning_effort": "none"}},
            {"kind": "model_response", "payload": {"usage": {"input_tokens": 12, "output_tokens": 3}, "text": "no"}},
            {"kind": "memory_snapshot", "payload": {"memory": {"contents": ["q1", "a1"], "roles": ["human", "ai"]}}},
        ],
    )
    report = technical_report(result, ["q1", "q2"], [{"kind": "assertIn", "expected": "france"}])
    assert report["technical_ok"] is True
    assert report["correct"] is False
    assert report["input_tokens"] == 22


def test_memory_contract_error_is_a_recorded_failure():
    result = RunResult(
        status="execute_error",
        results=[],
        events=[],
        stdout='{"error": "variable chat_history should be a list of base messages, got str"}',
    )
    report = technical_report(result, ["q1", "q2"], [{"kind": "assertIn", "expected": "france"}])
    assert report["technical_ok"] is True
    assert report["status"] == "task_failure"
    assert report["correct"] is False


def test_published_test_turns_are_the_run_agent_prompts():
    from repair_family_pilot.screen import _turns_from_test
    source = '''
def test_memory_contains_country(self):
    first_prompt = "what is the capital of France?"
    second_prompt = "what is the last question I asked?"
    run_agent(first_prompt)
    response = run_agent(second_prompt)
    print("Second response:", response)
'''
    assert _turns_from_test(source) == [
        "what is the capital of France?",
        "what is the last question I asked?",
    ]


def test_probe_tie_breaks_in_declared_order():
    intervals = {name: (0.0, 1.0) for name in ("empty", "A", "B", "AB")}
    assert choose_probe(intervals, ["AB", "empty", "B", "A"], costs={"empty": 1, "A": 1, "B": 1, "AB": 1}) == "empty"

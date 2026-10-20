import numpy as np

from repair_family_pilot.donors import assess_weights, false_joint_example, predict_table, solve_weights


def test_one_weight_vector_is_used_for_every_cell():
    features = np.asarray([[0.0, 0.0], [1.0, 1.0]])
    rates = [[0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0]]
    solved = solve_weights(features, np.asarray([0.5, 0.5]), 0.0)
    assert solved["family_status"] != "abstain"
    from repair_family_pilot.donors import synthesize_rates
    predicted = synthesize_rates(solved["weights"], rates)
    assert len(predicted) == 4
    assert abs(sum(solved["weights"]) - 1.0) <= 1e-6
    assert min(solved["weights"]) >= -1e-8


def test_solver_failure_abstains_and_does_not_emit_an_empty_family():
    assessed = assess_weights(False, np.asarray([0.2, 0.2]), "failed")
    assert assessed["fallback_reason"] == "solver_failure"
    assert assessed["family_status"] == "abstain"
    assert assessed["predicted_family"] is None
    assert assessed["weights"] == [0.5, 0.5]


def test_sum_constraint_failure_abstains():
    assessed = assess_weights(True, np.asarray([0.2, 0.2]), "sum is short")
    assert assessed["family_status"] == "abstain"
    assert assessed["predicted_family"] is None


def test_no_eligible_donors_stores_no_weights():
    solved = solve_weights(np.zeros((0, 2)), np.asarray([0.0, 0.0]), 0.0)
    assert solved["fallback_reason"] == "no_eligible_donors"
    assert solved["weights"] is None
    assert solved["predicted_family"] is None


def test_false_joint_average_is_not_protocol_verified():
    example = false_joint_example()
    assert example["family_key"] == "AB"
    assert example["protocol_verified"] is False
    assert example["rates"][1] == 0.5
    assert example["rates"][3] == 1.0


def test_predict_table_marks_probability_support_unresolved():
    features = np.asarray([[0.0], [0.0]])
    result = predict_table(features, np.asarray([0.0]), [[0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0]], 0.0)
    assert result["probability_supported_family"] == "unresolved"

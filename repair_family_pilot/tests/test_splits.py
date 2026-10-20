from repair_family_pilot.splits import assign_split, collapse_related
from repair_family_pilot.suite import build_suite


def test_related_variants_share_a_group_and_outcomes_are_not_an_input():
    items = [
        {"group_id": "g1", "variant": "a"},
        {"group_id": "g1", "variant": "paraphrase"},
        {"group_id": "g2", "variant": "a"},
        {"group_id": "g3", "variant": "a"},
        {"group_id": "g4", "variant": "a"},
    ]
    groups = collapse_related(items)
    assert groups == ["g1", "g2", "g3", "g4"]
    assignment = assign_split(groups, seed=20261020)
    assert assignment["group_count"] == 4
    assert set(assignment["assignment"]) == set(groups)
    assert "outcome" not in assign_split.__code__.co_varnames


def test_suite_covers_the_three_dimensions_once():
    suite = build_suite()
    assert len(suite) == 12
    assert len({group["group_id"] for group in suite}) == 12
    assert {(group["needed"], group["origin"], group["gap"]) for group in suite} == {
        (needed, origin, gap)
        for needed in ("prior_question", "stated_capital")
        for origin in ("user", "assistant")
        for gap in (0, 2, 5)
    }
    for group in suite:
        assert "A" not in group["expected"]
        assert "B" not in group["expected"]
    split = assign_split([group["group_id"] for group in suite])
    assert split["donor"] == 6
    assert split["calibration"] == 3
    assert split["test"] == 3

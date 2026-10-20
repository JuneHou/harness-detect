from repair_family_pilot.families import all_binary_tables, exceeds_theta, family_from_bits, family_key

EXPECTED = {
    (0, 0, 0, 0): "none",
    (0, 0, 0, 1): "AB",
    (0, 0, 1, 0): "B",
    (0, 0, 1, 1): "B",
    (0, 1, 0, 0): "A",
    (0, 1, 0, 1): "A",
    (0, 1, 1, 0): "A|B",
    (0, 1, 1, 1): "A|B",
}


def test_all_sixteen_binary_tables():
    seen = list(all_binary_tables())
    assert len(seen) == 16
    for bits in seen:
        key = family_key(family_from_bits(*bits))
        if bits[0] == 1:
            assert key == "baseline_adequate"
        else:
            assert key == EXPECTED[bits]


def test_threshold_uses_fractions():
    assert exceeds_theta(2, 3) == 0
    assert exceeds_theta(3, 3) == 1
    assert exceeds_theta(4, 5) == 1

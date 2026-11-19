from src.scoring import compute_stress, stress_level


def test_high_stress_scenario():
    # No rain, hot, deep groundwater, low reservoir
    score = compute_stress(0, 20, 38, 14, 20)
    assert score >= 70
    assert stress_level(score) == "Critical"


def test_low_stress_scenario():
    # Good rain, mild, shallow groundwater, full reservoir
    score = compute_stress(40, 20, 28, 4, 90)
    assert stress_level(score) == "Low"
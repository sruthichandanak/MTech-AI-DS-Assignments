"""Basic tests for the AQI reflex agent. Run: python -m pytest  (or python tests/test_aqi.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aqi_agent import sub_index, calculate_aqi, classify


def test_sub_index_boundaries():
    assert sub_index("pm25", 0) == 0
    assert sub_index("pm25", 30) == 50
    assert sub_index("pm10", 100) == 100


def test_classify_bands():
    assert classify(45) == "low"
    assert classify(150) == "moderate"
    assert classify(320) == "high"


def test_final_aqi_is_max_subindex():
    readings = {"pm25": 85, "pm10": 140, "no2": 55}
    r = calculate_aqi(readings)
    assert r["valid"] is True
    assert r["aqi"] == max(r["sub_indices"].values())
    assert r["dominant_pollutant"] == "pm25"


def test_validity_rule_requires_pm_and_three_pollutants():
    assert calculate_aqi({"no2": 55, "so2": 20, "co": 1.4})["valid"] is False  # no PM
    assert calculate_aqi({"pm25": 85})["valid"] is False                       # < 3

def test_decimal_concentrations_do_not_fall_through():
    assert sub_index("pm25", 30.5) < 100
    assert sub_index("no2", 40.2) < 100
    assert calculate_aqi({"pm25": 30.5, "pm10": 45.2, "no2": 22.1})["aqi"] < 100
    
if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"PASS {name}")
    print("All tests passed.")

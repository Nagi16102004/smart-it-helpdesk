import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.priority import calculate_priority


def test_high_high_gives_p1():
    assert calculate_priority("High", "High") == "P1"


def test_low_low_gives_p4():
    assert calculate_priority("Low", "Low") == "P4"


def test_high_medium_gives_p2():
    assert calculate_priority("High", "Medium") == "P2"


def test_medium_high_gives_p2():
    assert calculate_priority("Medium", "High") == "P2"


def test_medium_medium_gives_p3():
    assert calculate_priority("Medium", "Medium") == "P3"


def test_unknown_combination_defaults_to_p4():
    assert calculate_priority("Unknown", "Unknown") == "P4"
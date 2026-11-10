
import pytest
from decimal import Decimal


def calculate_total(items):
    total = 0

    for item in items:
        if "qty" not in item or "rate" not in item:
            raise ValueError("Each item needs qty and rate")

        qty = item["qty"]
        rate = item["rate"]

        if type(qty) is not int or qty <= 0:
            raise ValueError("Invalid quantity")

        if not isinstance(rate, (int, float, Decimal)) or isinstance(rate, bool):
            raise ValueError("Invalid rate")

        if rate < 0:
            raise ValueError("Rate cannot be negative")

        total += qty * rate

    return total


def test_expected_total():
    assert calculate_total([
        {"qty": 2, "rate": 100},
        {"qty": 3, "rate": 50}
    ]) == 350


def test_empty_items():
    assert calculate_total([]) == 0


def test_missing_rate():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 2}])


def test_invalid_quantity():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 0, "rate": 20}])


def test_negative_rate():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 2, "rate": -20}])


def test_invalid_rate():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 2, "rate": "invalid"}])


def test_boolean_quantity():
    with pytest.raises(ValueError):
        calculate_total([{"qty": True, "rate": 20}])

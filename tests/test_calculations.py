"""Tests for Calculation and format_decimal."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.calculation import Calculation, format_decimal
from app.exceptions import OperationError, ValidationError

D = Decimal


@pytest.mark.parametrize("operation, a, b, expected", [
    ("add", "2", "3", "5"),
    ("+", "2", "3", "5"),
    ("subtract", "10", "4", "6"),
    ("multiply", "3", "4", "12"),
    ("divide", "9", "3", "3"),
    ("power", "3", "2", "9"),
    ("root", "16", "2", "4"),
])
def test_result_computed_when_not_given(operation, a, b, expected):
    calc = Calculation(operation, D(a), D(b))
    assert calc.result == D(expected)


def test_operation_name_is_canonical():
    assert Calculation("*", D(2), D(3)).operation == "multiply"


def test_given_result_is_kept():
    assert Calculation("add", D(1), D(1), result=D(99)).result == D(99)


@pytest.mark.parametrize("operation, a, b, error", [
    ("divide", "1", "0", ValidationError),
    ("unknown", "1", "2", ValidationError),
    ("power", "-8", "0.5", OperationError),
])
def test_invalid_calculations_raise(operation, a, b, error):
    with pytest.raises(error):
        Calculation(operation, D(a), D(b))


def test_to_dict_from_dict_round_trip():
    original = Calculation("divide", D(1), D(4), timestamp=datetime(2026, 1, 2, 3, 4, 5))
    data = original.to_dict()
    assert data == {
        "operation": "divide", "operand1": "1", "operand2": "4",
        "result": "0.25", "timestamp": "2026-01-02T03:04:05",
    }
    assert Calculation.from_dict(data) == original


@pytest.mark.parametrize("data", [
    {},
    {"operation": "add", "operand1": "x", "operand2": "1", "result": "1", "timestamp": "2026-01-01"},
    {"operation": "add", "operand1": "1", "operand2": "1", "result": "2", "timestamp": "not-a-date"},
    {"operation": "nope", "operand1": "1", "operand2": "1", "result": "2", "timestamp": "2026-01-01"},
    {"operation": "add", "operand1": None, "operand2": "1", "result": "2", "timestamp": "2026-01-01"},
])
def test_from_dict_rejects_bad_data(data):
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)


def test_str_and_format():
    calc = Calculation("divide", D(1), D(3))
    assert calc.format(3) == "divide(1, 3) = 0.333"
    assert str(calc) == "divide(1, 3) = 0.3333333333"


@pytest.mark.parametrize("value, precision, expected", [
    (D("2.50000"), 4, "2.5"),
    (D("1E+3"), 2, "1000"),
    (D("0.123456"), 3, "0.123"),
    (D("-0.0000001"), 2, "0"),
    (D("-0"), 2, "0"),
    (D("1E+40"), 10, "10000000000000000000000000000000000000000"),  # too large to quantize
])
def test_format_decimal(value, precision, expected):
    assert format_decimal(value, precision) == expected

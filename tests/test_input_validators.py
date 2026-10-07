"""Tests for InputValidator."""

from decimal import Decimal

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError
from app.input_validators import InputValidator


@pytest.fixture
def cfg():
    return CalculatorConfig(max_input_value=1000)


@pytest.mark.parametrize("value, expected", [
    ("5", Decimal("5")),
    ("  -3.25 ", Decimal("-3.25")),
    ("1e2", Decimal("100")),
    (7, Decimal("7")),
    (2.5, Decimal("2.5")),
    (Decimal("1000"), Decimal("1000")),
    ("-1000", Decimal("-1000")),
])
def test_valid_numbers(cfg, value, expected):
    assert InputValidator.validate_number(value, cfg) == expected


@pytest.mark.parametrize("value, message", [
    ("", "cannot be empty"),
    ("   ", "cannot be empty"),
    ("abc", "Invalid number format"),
    ("1,000", "Invalid number format"),
    (None, "Invalid number format"),
    ("nan", "finite"),
    ("inf", "finite"),
    ("1000.01", "exceeds maximum"),
    (-5000, "exceeds maximum"),
])
def test_invalid_numbers(cfg, value, message):
    with pytest.raises(ValidationError, match=message):
        InputValidator.validate_number(value, cfg)

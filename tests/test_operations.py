"""Tests for the operation strategies and the OperationFactory."""

from decimal import Decimal

import pytest

from app.exceptions import OperationError, ValidationError
from app.operations import (
    Addition, Division, Multiplication, Operation, OperationFactory, Power, Root, Subtraction,
)

D = Decimal


@pytest.mark.parametrize("operation, a, b, expected", [
    (Addition(), D("2"), D("3"), D("5")),
    (Addition(), D("-1.5"), D("1.5"), D("0")),
    (Subtraction(), D("5"), D("3"), D("2")),
    (Subtraction(), D("3"), D("5"), D("-2")),
    (Multiplication(), D("4"), D("2.5"), D("10")),
    (Multiplication(), D("-3"), D("3"), D("-9")),
    (Division(), D("10"), D("4"), D("2.5")),
    (Division(), D("-9"), D("3"), D("-3")),
    (Power(), D("2"), D("10"), D("1024")),
    (Power(), D("2"), D("-1"), D("0.5")),
    (Power(), D("0"), D("0"), D("1")),
    (Root(), D("27"), D("3"), D("3")),
    (Root(), D("16"), D("2"), D("4")),
    (Root(), D("-8"), D("3"), D("-2")),
    (Root(), D("0.25"), D("0.5"), D("0.0625")),
])
def test_operations_compute(operation, a, b, expected):
    assert operation.execute(a, b).quantize(D("1e-10")) == expected.quantize(D("1e-10"))


@pytest.mark.parametrize("operation, a, b, message", [
    (Division(), D("1"), D("0"), "Division by zero"),
    (Power(), D("0"), D("-2"), "negative power"),
    (Root(), D("9"), D("0"), "Zero root"),
    (Root(), D("-16"), D("2"), "negative number"),
    (Root(), D("-8"), D("1.5"), "negative number"),
])
def test_operations_reject_invalid_operands(operation, a, b, message):
    with pytest.raises(ValidationError, match=message):
        operation.execute(a, b)


def test_arithmetic_failure_becomes_operation_error():
    # A negative base with a fractional exponent is invalid in Decimal arithmetic.
    with pytest.raises(OperationError, match="power failed"):
        Power().execute(D("-8"), D("0.5"))


def test_operation_str_is_class_name():
    assert str(Addition()) == "Addition"


@pytest.mark.parametrize("name, expected_class", [
    ("add", Addition), ("+", Addition), ("  ADD ", Addition),
    ("subtract", Subtraction), ("-", Subtraction),
    ("multiply", Multiplication), ("*", Multiplication), ("x", Multiplication),
    ("divide", Division), ("/", Division),
    ("power", Power), ("^", Power), ("**", Power), ("pow", Power),
    ("root", Root), ("sqrt", Root),
])
def test_factory_creates_operations(name, expected_class):
    assert isinstance(OperationFactory.create_operation(name), expected_class)


@pytest.mark.parametrize("name", ["modulo", "", "%", "sum"])
def test_factory_rejects_unknown(name):
    assert not OperationFactory.is_supported(name)
    with pytest.raises(ValidationError, match="Unknown operation"):
        OperationFactory.create_operation(name)


def test_available_operations():
    assert OperationFactory.available_operations() == [
        "add", "divide", "multiply", "power", "root", "subtract",
    ]


def test_register_custom_operation(monkeypatch):
    monkeypatch.setattr(OperationFactory, "_operations", dict(OperationFactory._operations))

    class Modulus(Operation):
        name = "modulus"

        def _compute(self, a, b):
            return a % b

    OperationFactory.register_operation("Modulus", Modulus)
    assert OperationFactory.create_operation("modulus").execute(D(10), D(3)) == D(1)


@pytest.mark.parametrize("bad", [str, object(), "not a class"])
def test_register_rejects_non_operations(bad):
    with pytest.raises(TypeError):
        OperationFactory.register_operation("bad", bad)

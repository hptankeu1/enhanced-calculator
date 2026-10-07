"""Tests for the custom exception hierarchy."""

import pytest

from app.exceptions import CalculatorError, ConfigurationError, OperationError, ValidationError


@pytest.mark.parametrize("exc_class", [ValidationError, OperationError, ConfigurationError])
def test_subclasses_of_calculator_error(exc_class):
    assert issubclass(exc_class, CalculatorError)
    assert issubclass(exc_class, Exception)


@pytest.mark.parametrize("exc_class, message", [
    (CalculatorError, "base"),
    (ValidationError, "bad input"),
    (OperationError, "failed op"),
    (ConfigurationError, "bad config"),
])
def test_raise_and_catch_as_base(exc_class, message):
    with pytest.raises(CalculatorError, match=message) as info:
        raise exc_class(message)
    assert type(info.value) is exc_class
    assert str(info.value) == message

"""Validation of raw user input."""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError


class InputValidator:
    """Turns raw input into a safe :class:`~decimal.Decimal`.

    Mixes both error-handling styles on purpose:

    * **LBYL** — check for empty strings, non-finite values and range limits
      before using the value.
    * **EAFP** — just try ``Decimal(value)`` and translate the failure.
    """

    @staticmethod
    def validate_number(value: Any, config: CalculatorConfig) -> Decimal:
        """Return ``value`` as a Decimal or raise :class:`ValidationError`."""
        # LBYL: inspect strings before converting them.
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValidationError("Input cannot be empty")

        # EAFP: attempt the conversion and handle failure.
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValidationError(f"Invalid number format: {value!r}") from exc

        # LBYL: range checks on the converted value.
        if not number.is_finite():
            raise ValidationError("Input must be a finite number")
        if abs(number) > config.max_input_value:
            raise ValidationError(f"Value exceeds maximum allowed: {config.max_input_value}")
        return number

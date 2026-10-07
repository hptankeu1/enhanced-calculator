"""Arithmetic operations (Strategy pattern) and their factory (Factory pattern).

Each operation is an interchangeable *strategy* sharing the same interface:
``execute(a, b) -> Decimal``. The calculator holds one strategy at a time and
can swap it at runtime. :class:`OperationFactory` turns user input such as
``"add"`` or ``"+"`` into the right strategy object.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Type

from app.exceptions import OperationError, ValidationError


class Operation(ABC):
    """Abstract strategy for a binary arithmetic operation.

    ``execute`` is a template method: it validates operands (LBYL), then runs the
    concrete computation and converts any low-level arithmetic failure into an
    :class:`OperationError` (EAFP). Subclasses only implement ``_compute`` and,
    when needed, ``validate_operands``.
    """

    name: str = ""
    symbol: str = ""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """Validate the operands and return the result of the operation."""
        self.validate_operands(a, b)
        try:
            return self._compute(a, b)
        except ArithmeticError as exc:
            raise OperationError(f"{self.name} failed: {exc}") from exc

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """Hook for operation-specific checks. The default accepts every operand."""

    @abstractmethod
    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        """Perform the actual computation."""
        pass  # pragma: no cover

    def __str__(self) -> str:
        return self.__class__.__name__


class Addition(Operation):
    """a + b"""

    name, symbol = "add", "+"

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        return a + b


class Subtraction(Operation):
    """a - b"""

    name, symbol = "subtract", "-"

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        return a - b


class Multiplication(Operation):
    """a * b"""

    name, symbol = "multiply", "*"

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        return a * b


class Division(Operation):
    """a / b — rejects a zero divisor before dividing (LBYL)."""

    name, symbol = "divide", "/"

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        if b == 0:
            raise ValidationError("Division by zero is not allowed")

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        return a / b


class Power(Operation):
    """a raised to the power b."""

    name, symbol = "power", "^"

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        if a == 0 and b < 0:
            raise ValidationError("Zero cannot be raised to a negative power")

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        if b == 0:
            return Decimal(1)  # x**0 == 1, including the 0**0 convention Decimal rejects
        return a ** b


class Root(Operation):
    """The b-th root of a (e.g. ``root 27 3`` = 3).

    Odd integer roots of negative numbers are supported (``root -8 3`` = -2);
    even or fractional roots of negative numbers are rejected.
    """

    name, symbol = "root", "√"

    @staticmethod
    def _is_odd_integer(value: Decimal) -> bool:
        return value == value.to_integral_value() and value % 2 != 0

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        if b == 0:
            raise ValidationError("Zero root is undefined")
        if a < 0 and not self._is_odd_integer(b):
            raise ValidationError("Cannot take an even or fractional root of a negative number")

    def _compute(self, a: Decimal, b: Decimal) -> Decimal:
        magnitude = abs(a) ** (Decimal(1) / b)
        return -magnitude if a < 0 else magnitude


class OperationFactory:
    """Creates operation strategies from names or symbols (Factory pattern)."""

    _operations: Dict[str, Type[Operation]] = {
        cls.name: cls for cls in (Addition, Subtraction, Multiplication, Division, Power, Root)
    }
    _aliases: Dict[str, str] = {
        "+": "add", "-": "subtract", "*": "multiply", "x": "multiply",
        "/": "divide", "^": "power", "**": "power", "pow": "power", "sqrt": "root",
    }

    @classmethod
    def _resolve(cls, name: str) -> str:
        key = name.strip().lower()
        return cls._aliases.get(key, key)

    @classmethod
    def is_supported(cls, name: str) -> bool:
        """Return True if ``name`` (or its alias) maps to a registered operation."""
        return cls._resolve(name) in cls._operations

    @classmethod
    def register_operation(cls, name: str, operation_class: Type[Operation]) -> None:
        """Register a new operation class so it can be created by name."""
        if not (isinstance(operation_class, type) and issubclass(operation_class, Operation)):
            raise TypeError("operation_class must be a subclass of Operation")
        cls._operations[name.strip().lower()] = operation_class

    @classmethod
    def create_operation(cls, name: str) -> Operation:
        """Return a new strategy instance for ``name`` or raise :class:`ValidationError`."""
        operation_class = cls._operations.get(cls._resolve(name))
        if operation_class is None:
            raise ValidationError(f"Unknown operation: {name!r}")
        return operation_class()

    @classmethod
    def available_operations(cls) -> List[str]:
        """Return the canonical names of all registered operations."""
        return sorted(cls._operations)

"""The :class:`Calculation` record and result-formatting helpers."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from app.exceptions import OperationError, ValidationError
from app.operations import OperationFactory


def format_decimal(value: Decimal, precision: int) -> str:
    """Round ``value`` to ``precision`` places and render it without trailing zeros or exponents."""
    try:
        value = value.quantize(Decimal(1).scaleb(-precision))
    except InvalidOperation:
        # Too many digits to quantize within the decimal context: keep full value.
        pass
    if value == 0:
        value = Decimal(0)  # avoid printing "-0"
    return format(value.normalize(), "f")


@dataclass
class Calculation:
    """One completed calculation.

    If ``result`` is not supplied it is computed on creation via the
    :class:`OperationFactory`. The operation name is always stored in its
    canonical form (``"+"`` becomes ``"add"``).
    """

    operation: str
    operand1: Decimal
    operand2: Decimal
    result: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        strategy = OperationFactory.create_operation(self.operation)
        self.operation = strategy.name
        if self.result is None:
            self.result = strategy.execute(self.operand1, self.operand2)

    def to_dict(self) -> Dict[str, str]:
        """Serialize to a flat dict of strings (one CSV row)."""
        return {
            "operation": self.operation,
            "operand1": str(self.operand1),
            "operand2": str(self.operand2),
            "result": str(self.result),
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Calculation":
        """Rebuild a calculation from :meth:`to_dict` output (EAFP)."""
        try:
            return Calculation(
                operation=data["operation"],
                operand1=Decimal(data["operand1"]),
                operand2=Decimal(data["operand2"]),
                result=Decimal(data["result"]),
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        except (KeyError, TypeError, ValueError, ArithmeticError, ValidationError) as exc:
            raise OperationError(f"Invalid calculation data: {exc}") from exc

    def format(self, precision: int = 10) -> str:
        """Human-readable form with the result rounded to ``precision`` places."""
        return (
            f"{self.operation}({format_decimal(self.operand1, precision)}, "
            f"{format_decimal(self.operand2, precision)}) = {format_decimal(self.result, precision)}"
        )

    def __str__(self) -> str:
        return self.format()

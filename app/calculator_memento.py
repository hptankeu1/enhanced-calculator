"""Memento pattern: snapshots of calculator history used for undo/redo."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from app.calculation import Calculation


@dataclass
class CalculatorMemento:
    """An immutable-by-convention snapshot of the calculator's history.

    The list is copied on creation so later changes to the calculator's
    history never alter a saved snapshot.
    """

    history: List[Calculation]
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.history = list(self.history)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the snapshot to plain Python types."""
        return {
            "history": [calc.to_dict() for calc in self.history],
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CalculatorMemento":
        """Rebuild a snapshot from :meth:`to_dict` output."""
        return CalculatorMemento(
            history=[Calculation.from_dict(item) for item in data["history"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

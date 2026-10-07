"""Observer pattern: observers notified after every new calculation."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.calculation import Calculation


class HistoryObserver(ABC):
    """Interface for objects that react to new calculations."""

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        """Handle a newly completed calculation."""
        pass  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """Writes every calculation to the application log."""

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        logging.info(
            "Calculation performed: %s (%s, %s) = %s",
            calculation.operation, calculation.operand1, calculation.operand2, calculation.result,
        )


class AutoSaveObserver(HistoryObserver):
    """Persists the history to CSV after each calculation when auto-save is enabled."""

    def __init__(self, calculator: Any):
        if not hasattr(calculator, "config") or not hasattr(calculator, "save_history"):
            raise TypeError("Calculator must have 'config' and 'save_history' attributes")
        self.calculator = calculator

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        if self.calculator.config.auto_save:
            self.calculator.save_history()
            logging.info("History auto-saved")

"""The :class:`Calculator` facade.

``Calculator`` is the single entry point the REPL talks to. Behind a few simple
methods (``calculate``, ``undo``, ``redo``, ``save_history``...) it coordinates
the configuration, input validation, operation strategies, observers,
memento-based undo/redo, logging and pandas-backed persistence.
"""

import logging
from decimal import Decimal
from typing import Any, List, Optional

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.operations import Operation, OperationFactory

HISTORY_COLUMNS = ["operation", "operand1", "operand2", "result", "timestamp"]


class Calculator:
    """Facade over the calculator's subsystems."""

    def __init__(self, config: Optional[CalculatorConfig] = None):
        self.config = config or CalculatorConfig()
        self.config.validate()
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self.config.history_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

        self.history: List[Calculation] = []
        self.operation_strategy: Optional[Operation] = None
        self.observers: List[HistoryObserver] = []
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []

        try:
            self.load_history()
        except OperationError as exc:
            logging.warning("Could not load existing history: %s", exc)
        logging.info("Calculator initialized with %r", self.config)

    # ----- setup ---------------------------------------------------------
    def _setup_logging(self) -> None:
        logging.basicConfig(
            filename=str(self.config.log_file),
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding=self.config.default_encoding,
            force=True,
        )

    # ----- observer management ------------------------------------------
    def add_observer(self, observer: HistoryObserver) -> None:
        """Subscribe an observer to calculation events."""
        self.observers.append(observer)

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Unsubscribe an observer (no error if it was not subscribed)."""
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self, calculation: Calculation) -> None:
        """Send ``calculation`` to every observer."""
        for observer in self.observers:
            observer.update(calculation)

    # ----- strategy & calculation ---------------------------------------
    def set_operation(self, operation: Operation) -> None:
        """Choose the strategy used by :meth:`perform_operation`."""
        self.operation_strategy = operation
        logging.info("Operation set to %s", operation)

    def perform_operation(self, a: Any, b: Any) -> Decimal:
        """Validate inputs, run the current strategy and record the calculation."""
        if self.operation_strategy is None:
            raise OperationError("No operation set")
        x = InputValidator.validate_number(a, self.config)
        y = InputValidator.validate_number(b, self.config)
        result = self.operation_strategy.execute(x, y)

        self._save_state()
        calculation = Calculation(self.operation_strategy.name, x, y, result)
        self.history.append(calculation)
        self._trim_history()
        self.notify_observers(calculation)
        return result

    def calculate(self, operation_name: str, a: Any, b: Any) -> Decimal:
        """One-call convenience: pick the operation by name and run it."""
        self.set_operation(OperationFactory.create_operation(operation_name))
        return self.perform_operation(a, b)

    def _trim_history(self) -> None:
        overflow = len(self.history) - self.config.max_history_size
        if overflow > 0:
            del self.history[:overflow]

    # ----- memento: undo / redo -----------------------------------------
    def _save_state(self) -> None:
        """Snapshot the current history before a change and invalidate redo."""
        self.undo_stack.append(CalculatorMemento(self.history))
        self.redo_stack.clear()

    def _restore(self, source: List[CalculatorMemento], target: List[CalculatorMemento]) -> bool:
        """Shared undo/redo logic (DRY): move the current state onto ``target``, restore from ``source``."""
        if not source:
            return False
        memento = source.pop()
        target.append(CalculatorMemento(self.history))
        self.history = list(memento.history)
        return True

    def undo(self) -> bool:
        """Revert the last change. Returns False when there is nothing to undo."""
        return self._restore(self.undo_stack, self.redo_stack)

    def redo(self) -> bool:
        """Re-apply the last undone change. Returns False when there is nothing to redo."""
        return self._restore(self.redo_stack, self.undo_stack)

    # ----- history -------------------------------------------------------
    def clear_history(self) -> None:
        """Remove all calculations (undoable)."""
        self._save_state()
        self.history.clear()
        logging.info("History cleared")

    def show_history(self) -> List[str]:
        """Return each calculation as a formatted string, oldest first."""
        return [calc.format(self.config.precision) for calc in self.history]

    def get_history_dataframe(self) -> pd.DataFrame:
        """Return the history as a pandas DataFrame."""
        return pd.DataFrame([calc.to_dict() for calc in self.history], columns=HISTORY_COLUMNS)

    def save_history(self) -> None:
        """Write the history to the configured CSV file."""
        try:
            self.get_history_dataframe().to_csv(
                self.config.history_file, index=False, encoding=self.config.default_encoding
            )
        except OSError as exc:
            raise OperationError(f"Failed to save history: {exc}") from exc
        logging.info("History saved to %s (%d records)", self.config.history_file, len(self.history))

    def load_history(self) -> None:
        """Replace the in-memory history with the contents of the CSV file, if it exists."""
        path = self.config.history_file
        if not path.exists():
            logging.info("No history file at %s; starting fresh", path)
            return
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=self.config.default_encoding)
        except (OSError, UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
            raise OperationError(f"Failed to load history: {exc}") from exc
        loaded = [Calculation.from_dict(row) for row in df.to_dict("records")]
        self.history = loaded[-self.config.max_history_size:]
        logging.info("Loaded %d calculations from %s", len(self.history), path)

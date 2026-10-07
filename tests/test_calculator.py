"""Tests for the Calculator facade: strategy, observers, undo/redo, pandas persistence."""

from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from app.calculator import HISTORY_COLUMNS, Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError, OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver
from app.operations import Addition, Division


def test_init_creates_directories(calculator, config):
    assert config.log_dir.is_dir()
    assert config.history_dir.is_dir()
    assert calculator.history == []


def test_init_with_default_config(tmp_path):
    calc = Calculator()
    assert calc.config.base_dir == tmp_path.resolve()


def test_init_rejects_invalid_config(tmp_path):
    with pytest.raises(ConfigurationError):
        Calculator(CalculatorConfig(base_dir=tmp_path, precision=0))


def test_init_logs_warning_on_corrupt_history(config):
    config.history_dir.mkdir(parents=True)
    config.history_file.write_text("operation,operand1\nadd,notanumber\n")
    calc = Calculator(config)
    assert calc.history == []
    assert "Could not load existing history" in config.log_file.read_text()


@pytest.mark.parametrize("operation, a, b, expected", [
    ("add", "2", "3", Decimal("5")),
    ("subtract", 10, 4, Decimal("6")),
    ("multiply", "2.5", "4", Decimal("10")),
    ("divide", "7", "2", Decimal("3.5")),
    ("power", "2", "8", Decimal("256")),
    ("root", "81", "4", Decimal("3")),
])
def test_calculate(calculator, operation, a, b, expected):
    assert calculator.calculate(operation, a, b).quantize(Decimal("1e-10")) == expected
    assert len(calculator.history) == 1


@pytest.mark.parametrize("operation, a, b, error", [
    ("divide", "1", "0", ValidationError),
    ("add", "abc", "1", ValidationError),
    ("add", "1", "", ValidationError),
    ("add", "1e11", "1", ValidationError),  # above max_input_value of the fixture config
    ("modulo", "1", "2", ValidationError),
    ("power", "-8", "0.5", OperationError),
])
def test_calculate_errors_leave_history_untouched(calculator, operation, a, b, error):
    with pytest.raises(error):
        calculator.calculate(operation, a, b)
    assert calculator.history == []
    assert calculator.undo_stack == []


def test_perform_operation_without_strategy(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(1, 2)


def test_strategy_can_be_swapped(calculator):
    calculator.set_operation(Addition())
    assert calculator.perform_operation(6, 3) == 9
    calculator.set_operation(Division())
    assert calculator.perform_operation(6, 3) == 2


def test_history_is_trimmed_to_max_size(calculator):
    for i in range(7):
        calculator.calculate("add", i, 0)
    assert len(calculator.history) == 5
    assert calculator.history[0].operand1 == 2


# ----- observers -------------------------------------------------------------
def test_observers_are_notified(calculator):
    observer = Mock()
    calculator.add_observer(observer)
    calculator.calculate("add", 1, 1)
    observer.update.assert_called_once_with(calculator.history[-1])


def test_remove_observer(calculator):
    observer = Mock()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    calculator.remove_observer(observer)  # removing twice is harmless
    calculator.calculate("add", 1, 1)
    observer.update.assert_not_called()


def test_auto_save_and_logging_observers_integration(calculator, config):
    calculator.add_observer(LoggingObserver())
    calculator.add_observer(AutoSaveObserver(calculator))
    calculator.calculate("multiply", 3, 3)
    df = pd.read_csv(config.history_file)
    assert df.iloc[0]["operation"] == "multiply"
    assert "Calculation performed: multiply" in config.log_file.read_text()


# ----- undo / redo -----------------------------------------------------------
def test_undo_redo_cycle(calculator):
    calculator.calculate("add", 1, 1)
    calculator.calculate("add", 2, 2)
    assert calculator.undo() is True
    assert [c.result for c in calculator.history] == [2]
    assert calculator.undo() is True
    assert calculator.history == []
    assert calculator.undo() is False
    assert calculator.redo() is True
    assert calculator.redo() is True
    assert [c.result for c in calculator.history] == [2, 4]
    assert calculator.redo() is False


def test_new_calculation_clears_redo(calculator):
    calculator.calculate("add", 1, 1)
    calculator.undo()
    calculator.calculate("add", 5, 5)
    assert calculator.redo() is False


def test_clear_history_is_undoable(calculator):
    calculator.calculate("add", 1, 1)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo() is True
    assert len(calculator.history) == 1


# ----- display & pandas ------------------------------------------------------
def test_show_history_uses_precision(calculator):
    calculator.calculate("divide", 1, 3)
    assert calculator.show_history() == ["divide(1, 3) = 0.3333"]


def test_dataframe_columns(calculator):
    assert list(calculator.get_history_dataframe().columns) == HISTORY_COLUMNS
    calculator.calculate("add", 1, 2)
    df = calculator.get_history_dataframe()
    assert len(df) == 1 and df.loc[0, "result"] == "3"


def test_save_and_load_round_trip(calculator, config):
    calculator.calculate("add", "1.5", "2")
    calculator.calculate("power", 2, 3)
    calculator.save_history()

    fresh = Calculator(config)  # loads history on start
    assert [c.to_dict() for c in fresh.history] == [c.to_dict() for c in calculator.history]


def test_save_empty_history_then_load(calculator, config):
    calculator.save_history()
    assert pd.read_csv(config.history_file).empty
    calculator.load_history()
    assert calculator.history == []


def test_load_respects_max_history_size(calculator, config):
    rows = [{"operation": "add", "operand1": str(i), "operand2": "0", "result": str(i),
             "timestamp": "2026-01-01T00:00:00"} for i in range(8)]
    pd.DataFrame(rows).to_csv(config.history_file, index=False)
    calculator.load_history()
    assert [c.operand1 for c in calculator.history] == [Decimal(i) for i in range(3, 8)]


def test_load_missing_file_is_noop(calculator):
    calculator.calculate("add", 1, 1)
    calculator.load_history()
    assert len(calculator.history) == 1


@pytest.mark.parametrize("content", [
    "",                                                   # EmptyDataError
    'a,b\n"unterminated,1\n',                             # ParserError
    "operation,operand1,operand2,result,timestamp\nadd,1,1,x,2026-01-01\n",  # bad row
])
def test_load_corrupt_file_raises(calculator, config, content):
    config.history_file.write_text(content)
    with pytest.raises(OperationError):
        calculator.load_history()


def test_load_wrong_encoding_raises(tmp_path):
    calc = Calculator(CalculatorConfig(base_dir=tmp_path, default_encoding="ascii"))
    calc.config.history_file.write_bytes("operation\n\xe9\n".encode("latin-1"))
    with pytest.raises(OperationError, match="Failed to load"):
        calc.load_history()


def test_save_failure_raises_operation_error(calculator, config):
    config.history_file.mkdir()  # a directory where the file should be
    with pytest.raises(OperationError, match="Failed to save"):
        calculator.save_history()

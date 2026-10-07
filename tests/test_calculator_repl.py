"""Tests for the REPL, driven by scripted input."""

from unittest.mock import patch

import pytest

from app import calculator_repl as repl_module
from app.calculator_repl import calculator_repl
from app.exceptions import ConfigurationError, OperationError


def run_repl(inputs, capsys):
    """Feed ``inputs`` to the REPL one line at a time and return everything it printed."""
    with patch("builtins.input", side_effect=list(inputs)):
        calculator_repl()
    return capsys.readouterr().out


def test_exit_saves_and_says_goodbye(capsys, tmp_path):
    out = run_repl(["exit"], capsys)
    assert "Calculator started" in out
    assert "History saved successfully." in out
    assert "Goodbye!" in out
    assert (tmp_path / "history" / "calculator_history.csv").exists()


@pytest.mark.parametrize("inputs, expected", [
    (["add 2 3"], "Result: 5"),
    (["+ 2 3"], "Result: 5"),
    (["subtract 10 4"], "Result: 6"),
    (["multiply", "3", "4"], "Result: 12"),
    (["divide 1 3"], "Result: 0.3333333333"),
    (["POWER 2 10"], "Result: 1024"),
    (["root 27 3"], "Result: 3"),
    (["^", "2", "0.5"], "Result: 1.4142135624"),
])
def test_operations(capsys, inputs, expected):
    assert expected in run_repl([*inputs, "exit"], capsys)


@pytest.mark.parametrize("inputs, expected", [
    (["divide 1 0"], "Error: Division by zero is not allowed"),
    (["add 1"], "Error: 'add' needs exactly two numbers"),
    (["add 1 2 3"], "Error: 'add' needs exactly two numbers"),
    (["add a b"], "Error: Invalid number format"),
    (["power -8 0.5"], "Error: power failed"),
    (["foo"], "Unknown command: 'foo'"),
])
def test_errors_are_reported_and_loop_continues(capsys, inputs, expected):
    out = run_repl([*inputs, "exit"], capsys)
    assert expected in out
    assert "Goodbye!" in out


@pytest.mark.parametrize("inputs", [
    ["add", "cancel"],
    ["add", "5", "CANCEL"],
])
def test_cancel_operation(capsys, inputs):
    out = run_repl([*inputs, "exit"], capsys)
    assert "Operation cancelled" in out
    assert "Result:" not in out


def test_help(capsys):
    out = run_repl(["help", "exit"], capsys)
    assert "Available commands" in out and "undo" in out


def test_blank_line_is_ignored(capsys):
    out = run_repl(["", "   ", "exit"], capsys)
    assert "Unknown command" not in out


def test_history_empty_and_filled(capsys):
    out = run_repl(["history", "add 1 2", "history", "exit"], capsys)
    assert "No calculations in history" in out
    assert "1. add(1, 2) = 3" in out


def test_clear_undo_redo(capsys):
    out = run_repl(
        ["undo", "redo", "add 1 1", "clear", "history", "undo", "history", "redo", "exit"], capsys
    )
    assert "Nothing to undo" in out
    assert "Nothing to redo" in out
    assert "History cleared" in out
    assert "Operation undone" in out
    assert "Operation redone" in out
    assert out.count("1. add(1, 1) = 2") == 1


def test_save_and_load(capsys):
    out = run_repl(["add 4 4", "save", "clear", "load", "history", "exit"], capsys)
    assert "History saved successfully" in out
    assert "History loaded successfully" in out
    assert "1. add(4, 4) = 8" in out


def test_history_persists_between_sessions(capsys):
    run_repl(["multiply 6 7", "exit"], capsys)
    out = run_repl(["history", "exit"], capsys)
    assert "multiply(6, 7) = 42" in out


def test_keyboard_interrupt_is_handled(capsys):
    out = run_repl([KeyboardInterrupt, "exit"], capsys)
    assert "Operation cancelled" in out
    assert "Goodbye!" in out


def test_eof_exits(capsys):
    out = run_repl([EOFError], capsys)
    assert "Input terminated. Exiting..." in out


def test_unexpected_error_is_reported(capsys):
    with patch.object(repl_module, "_show_help", side_effect=RuntimeError("boom")), \
         patch.dict(repl_module.COMMANDS, {"help": repl_module._show_help}):
        out = run_repl(["help", "exit"], capsys)
    assert "Unexpected error: boom" in out


def test_exit_reports_save_failure(capsys):
    with patch("app.calculator.Calculator.save_history", side_effect=OperationError("disk full")):
        out = run_repl(["exit"], capsys)
    assert "Warning: Could not save history: disk full" in out
    assert "Goodbye!" in out


def test_fatal_error_on_startup(capsys):
    with patch.object(repl_module, "Calculator", side_effect=ConfigurationError("bad config")):
        with pytest.raises(ConfigurationError):
            calculator_repl()
    assert "Fatal error: bad config" in capsys.readouterr().out

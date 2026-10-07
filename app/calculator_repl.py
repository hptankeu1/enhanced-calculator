"""Command-line Read-Eval-Print Loop for the calculator."""

import logging
from typing import Callable, Dict, List, Optional

from app.calculation import format_decimal
from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver
from app.operations import OperationFactory

HELP_TEXT = """
Available commands:
  add, subtract, multiply, divide, power, root
      Run an operation. Type it alone to be prompted for two numbers,
      or inline, e.g. 'add 2 3' or '^ 2 10'. Symbols + - * / ^ also work.
  history  Show calculation history
  clear    Clear calculation history (can be undone)
  undo     Undo the last change
  redo     Redo the last undone change
  save     Save history to CSV
  load     Load history from CSV
  help     Show this help
  exit     Save history and quit
""".strip()


# ----- command handlers ------------------------------------------------------
def _show_help(calc: Calculator) -> None:
    print(HELP_TEXT)


def _show_history(calc: Calculator) -> None:
    entries = calc.show_history()
    if not entries:
        print("No calculations in history")
        return
    print("\nCalculation History:")
    for index, entry in enumerate(entries, start=1):
        print(f"{index}. {entry}")


def _clear(calc: Calculator) -> None:
    calc.clear_history()
    print("History cleared")


def _undo(calc: Calculator) -> None:
    print("Operation undone" if calc.undo() else "Nothing to undo")


def _redo(calc: Calculator) -> None:
    print("Operation redone" if calc.redo() else "Nothing to redo")


def _save(calc: Calculator) -> None:
    calc.save_history()
    print("History saved successfully")


def _load(calc: Calculator) -> None:
    calc.load_history()
    print("History loaded successfully")


COMMANDS: Dict[str, Callable[[Calculator], None]] = {
    "help": _show_help,
    "history": _show_history,
    "clear": _clear,
    "undo": _undo,
    "redo": _redo,
    "save": _save,
    "load": _load,
}


# ----- operation handling ----------------------------------------------------
def _prompt_number(label: str) -> Optional[str]:
    """Ask for a number; return None if the user types 'cancel'."""
    value = input(f"{label}: ").strip()
    return None if value.lower() == "cancel" else value


def _handle_operation(calc: Calculator, operation: str, args: List[str]) -> None:
    """Run ``operation`` with inline ``args`` or prompt for the two operands."""
    if args:
        if len(args) != 2:
            raise ValidationError(f"'{operation}' needs exactly two numbers, e.g. '{operation} 2 3'")
        a, b = args
    else:
        print("\nEnter numbers (or 'cancel' to abort):")
        a = _prompt_number("First number")
        b = None if a is None else _prompt_number("Second number")
        if b is None:
            print("Operation cancelled")
            return
    result = calc.calculate(operation, a, b)
    print(f"\nResult: {format_decimal(result, calc.config.precision)}")


def _exit(calc: Calculator) -> None:
    try:
        calc.save_history()
        print("History saved successfully.")
    except OperationError as exc:
        print(f"Warning: Could not save history: {exc}")
    print("Goodbye!")


# ----- main loop -------------------------------------------------------------
def calculator_repl() -> None:
    """Start the interactive calculator."""
    try:
        calc = Calculator()
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))
    except Exception as exc:
        print(f"Fatal error: {exc}")
        logging.error("Fatal error in calculator REPL: %s", exc)
        raise

    print("Calculator started. Type 'help' for commands.")
    while True:
        try:
            parts = input("\nEnter command: ").strip().split()
            if not parts:
                continue
            command, args = parts[0].lower(), parts[1:]

            if command == "exit":
                _exit(calc)
                break
            if command in COMMANDS:
                COMMANDS[command](calc)
            elif OperationFactory.is_supported(command):
                _handle_operation(calc, command, args)
            else:
                print(f"Unknown command: '{command}'. Type 'help' for available commands.")
        except KeyboardInterrupt:
            print("\nOperation cancelled")
        except EOFError:
            print("\nInput terminated. Exiting...")
            break
        except (ValidationError, OperationError) as exc:
            print(f"Error: {exc}")
        except Exception as exc:
            print(f"Unexpected error: {exc}")
            logging.exception("Unexpected error in REPL")

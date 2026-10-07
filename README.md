# Enhanced Calculator (Python CLI)

![Tests](https://github.com/hptankeu1/enhanced-calculator/actions/workflows/python-app.yml/badge.svg)

An interactive command-line calculator built around five design patterns (Factory, Strategy, Observer, Memento, Facade), with pandas-backed history, `.env` configuration, undo/redo, and a test suite at **100% line and branch coverage** enforced by GitHub Actions.

## Features

- **REPL** — type commands continuously until `exit`
- **Operations** — `add`, `subtract`, `multiply`, `divide`, `power`, `root` (symbols `+ - * / ^` also work)
- **Inline or prompted input** — `add 2 3`, or type `add` and answer the prompts (`cancel` aborts)
- **Undo / redo** — including undoing `clear`
- **History** — kept in a pandas DataFrame, auto-saved to CSV after each calculation and reloaded on start
- **Exact arithmetic** — uses `Decimal`, so `0.1 + 0.2 = 0.3`
- **Logging** — every calculation is written to `logs/calculator.log`

## Project structure

```
.
├── app/
│   ├── calculation.py         # Calculation record + result formatting
│   ├── calculator.py          # Calculator facade
│   ├── calculator_config.py   # .env / environment configuration + validation
│   ├── calculator_memento.py  # Memento for undo/redo
│   ├── calculator_repl.py     # REPL loop and command handlers
│   ├── exceptions.py          # CalculatorError hierarchy
│   ├── history.py             # Observers (logging, auto-save)
│   ├── input_validators.py    # Input validation (LBYL + EAFP)
│   └── operations.py          # Operation strategies + OperationFactory
├── tests/                     # pytest suite (one file per module)
├── .github/workflows/python-app.yml
├── .coveragerc                # branch coverage, fail_under = 100
├── .env.example
├── main.py                    # entry point
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/hptankeu1/enhanced-calculator.git
cd enhanced-calculator

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # optional — defaults work without it
```

## Usage

```bash
python main.py
```

```
Calculator started. Type 'help' for commands.

Enter command: add 2 3
Result: 5

Enter command: root -8 3
Result: -2

Enter command: divide 1 0
Error: Division by zero is not allowed

Enter command: history
Calculation History:
1. add(2, 3) = 5
2. root(-8, 3) = -2

Enter command: undo
Operation undone

Enter command: exit
History saved successfully.
Goodbye!
```

### Commands

| Command | Description |
|---|---|
| `add`, `subtract`, `multiply`, `divide`, `power`, `root` | Run an operation (`root a n` = n-th root of a) |
| `history` | Show past calculations |
| `clear` | Clear history (undoable) |
| `undo` / `redo` | Step backward / forward through changes |
| `save` / `load` | Write history to / read history from CSV |
| `help` | Show the command list |
| `exit` | Save history and quit |

## Configuration

Set these in `.env` or the environment. All are optional.

| Variable | Default | Meaning |
|---|---|---|
| `CALCULATOR_BASE_DIR` | project root | Base folder for `logs/` and `history/` |
| `CALCULATOR_LOG_DIR` | `<base>/logs` | Log folder |
| `CALCULATOR_HISTORY_DIR` | `<base>/history` | History CSV folder |
| `CALCULATOR_MAX_HISTORY_SIZE` | `1000` | Max calculations kept |
| `CALCULATOR_AUTO_SAVE` | `true` | Save history after each calculation |
| `CALCULATOR_PRECISION` | `10` | Decimal places shown |
| `CALCULATOR_MAX_INPUT_VALUE` | `1e999` | Largest accepted absolute input |
| `CALCULATOR_DEFAULT_ENCODING` | `utf-8` | Encoding of the history CSV |

Invalid values (e.g. `CALCULATOR_PRECISION=abc` or `CALCULATOR_AUTO_SAVE=maybe`) raise a clear `ConfigurationError` at startup.

## Design patterns

| Pattern | Where | How |
|---|---|---|
| **Strategy** | `operations.py` | Each operation subclasses `Operation` and implements `_compute`; the calculator swaps strategies with `set_operation`. |
| **Factory** | `OperationFactory` | Maps names and symbols (`"add"`, `"+"`) to strategy classes; new operations can be added with `register_operation`. |
| **Observer** | `history.py` | `LoggingObserver` and `AutoSaveObserver` are notified after every calculation. |
| **Memento** | `calculator_memento.py` | A snapshot of the history is saved before every change; undo/redo move snapshots between two stacks. |
| **Facade** | `calculator.py` | `Calculator` hides validation, strategies, observers, mementos, logging and pandas I/O behind simple methods like `calculate()` and `undo()`. |

## Error handling: LBYL and EAFP

- **LBYL (Look Before You Leap)** — `Division` checks for a zero divisor before dividing; `InputValidator` checks for empty strings and range limits; `load_history` checks the file exists before reading.
- **EAFP (Easier to Ask Forgiveness than Permission)** — `InputValidator` simply tries `Decimal(value)` and converts the failure into a `ValidationError`; `Operation.execute` turns any `ArithmeticError` into an `OperationError`; config parsing tries `int(...)` and reports a `ConfigurationError`.

All intentional errors inherit from `CalculatorError`, so the REPL reports them and keeps running.

## Testing

```bash
pytest --cov=app --cov-report=term-missing
coverage report --fail-under=100
```

The suite uses parameterized tests throughout and covers both success and failure paths. `.coveragerc` turns on **branch coverage** and fails below 100%. The only exclusions are the bodies of two abstract methods, marked `# pragma: no cover` because they can never run.

## Continuous integration

`.github/workflows/python-app.yml` runs on every push and pull request to `main`: it installs dependencies, runs the tests with coverage, and fails the build if coverage drops below 100%.

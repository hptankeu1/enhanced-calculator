"""Configuration management for the calculator.

Settings are read from environment variables (optionally loaded from a
``.env`` file through ``python-dotenv``). Explicit constructor arguments take
precedence over environment variables, which take precedence over defaults.

Supported variables:

* ``CALCULATOR_BASE_DIR``          - root directory for logs and history
* ``CALCULATOR_LOG_DIR``           - directory for log files
* ``CALCULATOR_HISTORY_DIR``       - directory for the history CSV
* ``CALCULATOR_MAX_HISTORY_SIZE``  - max number of calculations kept (int > 0)
* ``CALCULATOR_AUTO_SAVE``         - auto-save history after each calculation (bool)
* ``CALCULATOR_PRECISION``         - decimal places shown in results (int > 0)
* ``CALCULATOR_MAX_INPUT_VALUE``   - largest accepted absolute input (number > 0)
* ``CALCULATOR_DEFAULT_ENCODING``  - encoding for the history file
"""

import codecs
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

load_dotenv()

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}


def get_project_root() -> Path:
    """Return the project's root directory (the folder that contains ``app/``)."""
    return Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable (EAFP: try the conversion, translate the error)."""
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from exc


def _env_decimal(name: str, default: str) -> Decimal:
    """Read a decimal environment variable (EAFP)."""
    raw = os.getenv(name, default)
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable (LBYL: check against known spellings)."""
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ConfigurationError(f"{name} must be a boolean (true/false), got {raw!r}")


class CalculatorConfig:
    """Holds and validates all calculator settings."""

    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        max_history_size: Optional[int] = None,
        auto_save: Optional[bool] = None,
        precision: Optional[int] = None,
        max_input_value: Optional[Union[int, Decimal]] = None,
        default_encoding: Optional[str] = None,
    ):
        self.base_dir = Path(base_dir or os.getenv("CALCULATOR_BASE_DIR", get_project_root())).resolve()
        self.max_history_size = (
            max_history_size if max_history_size is not None
            else _env_int("CALCULATOR_MAX_HISTORY_SIZE", 1000)
        )
        self.auto_save = auto_save if auto_save is not None else _env_bool("CALCULATOR_AUTO_SAVE", True)
        self.precision = precision if precision is not None else _env_int("CALCULATOR_PRECISION", 10)
        self.max_input_value = (
            Decimal(max_input_value) if max_input_value is not None
            else _env_decimal("CALCULATOR_MAX_INPUT_VALUE", "1e999")
        )
        self.default_encoding = default_encoding or os.getenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")

    # ----- derived paths -------------------------------------------------
    @property
    def log_dir(self) -> Path:
        """Directory where log files are written."""
        return Path(os.getenv("CALCULATOR_LOG_DIR", self.base_dir / "logs")).resolve()

    @property
    def log_file(self) -> Path:
        """Full path of the log file."""
        return self.log_dir / "calculator.log"

    @property
    def history_dir(self) -> Path:
        """Directory where the history CSV is stored."""
        return Path(os.getenv("CALCULATOR_HISTORY_DIR", self.base_dir / "history")).resolve()

    @property
    def history_file(self) -> Path:
        """Full path of the history CSV file."""
        return self.history_dir / "calculator_history.csv"

    # ----- validation ----------------------------------------------------
    def validate(self) -> None:
        """Validate settings, raising :class:`ConfigurationError` on the first problem found."""
        if self.max_history_size <= 0:
            raise ConfigurationError("max_history_size must be a positive integer")
        if self.precision <= 0:
            raise ConfigurationError("precision must be a positive integer")
        if self.max_input_value <= 0:
            raise ConfigurationError("max_input_value must be positive")
        try:
            codecs.lookup(self.default_encoding)
        except LookupError as exc:
            raise ConfigurationError(f"Unknown encoding: {self.default_encoding!r}") from exc

    def __repr__(self) -> str:
        return (
            f"CalculatorConfig(base_dir={str(self.base_dir)!r}, max_history_size={self.max_history_size}, "
            f"auto_save={self.auto_save}, precision={self.precision}, "
            f"max_input_value={self.max_input_value}, default_encoding={self.default_encoding!r})"
        )

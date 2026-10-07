"""Custom exception hierarchy for the calculator application.

Every error raised on purpose by the application derives from
:class:`CalculatorError`, so callers (such as the REPL) can catch one base
class while still being able to distinguish specific failure modes.
"""


class CalculatorError(Exception):
    """Base class for all calculator-specific errors."""


class ValidationError(CalculatorError):
    """Raised when user input or operands fail validation (e.g. division by zero)."""


class OperationError(CalculatorError):
    """Raised when an operation, history action or persistence step fails."""


class ConfigurationError(CalculatorError):
    """Raised when the application configuration is missing or invalid."""

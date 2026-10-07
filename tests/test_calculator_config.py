"""Tests for CalculatorConfig and its environment helpers."""

from decimal import Decimal

import pytest

from app.calculator_config import CalculatorConfig, get_project_root
from app.exceptions import ConfigurationError


def test_project_root_contains_app_package():
    assert (get_project_root() / "app" / "calculator_config.py").exists()


def test_defaults(tmp_path):
    config = CalculatorConfig()
    assert config.base_dir == tmp_path.resolve()  # from CALCULATOR_BASE_DIR set by conftest
    assert config.max_history_size == 1000
    assert config.auto_save is True
    assert config.precision == 10
    assert config.max_input_value == Decimal("1e999")
    assert config.default_encoding == "utf-8"
    config.validate()


def test_falls_back_to_project_root(monkeypatch):
    monkeypatch.delenv("CALCULATOR_BASE_DIR")
    assert CalculatorConfig().base_dir == get_project_root()


def test_explicit_arguments_override_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CALCULATOR_PRECISION", "3")
    config = CalculatorConfig(base_dir=tmp_path / "x", max_history_size=7, auto_save=False,
                              precision=2, max_input_value=50, default_encoding="latin-1")
    assert (config.max_history_size, config.auto_save, config.precision) == (7, False, 2)
    assert config.max_input_value == Decimal(50)
    assert config.default_encoding == "latin-1"
    assert config.base_dir == (tmp_path / "x").resolve()


def test_env_values_are_read(monkeypatch):
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY_SIZE", "42")
    monkeypatch.setenv("CALCULATOR_PRECISION", "6")
    monkeypatch.setenv("CALCULATOR_MAX_INPUT_VALUE", "1000")
    monkeypatch.setenv("CALCULATOR_DEFAULT_ENCODING", "ascii")
    config = CalculatorConfig()
    assert (config.max_history_size, config.precision) == (42, 6)
    assert config.max_input_value == Decimal(1000)
    assert config.default_encoding == "ascii"


@pytest.mark.parametrize("raw, expected", [
    ("true", True), ("TRUE", True), ("1", True), ("yes", True), (" on ", True),
    ("false", False), ("0", False), ("No", False), ("off", False),
])
def test_auto_save_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", raw)
    assert CalculatorConfig().auto_save is expected


@pytest.mark.parametrize("name, raw", [
    ("CALCULATOR_AUTO_SAVE", "maybe"),
    ("CALCULATOR_MAX_HISTORY_SIZE", "lots"),
    ("CALCULATOR_PRECISION", "1.5"),
    ("CALCULATOR_MAX_INPUT_VALUE", "big"),
])
def test_bad_env_values_raise(monkeypatch, name, raw):
    monkeypatch.setenv(name, raw)
    with pytest.raises(ConfigurationError, match=name):
        CalculatorConfig()


def test_derived_paths(tmp_path):
    config = CalculatorConfig(base_dir=tmp_path)
    assert config.log_dir == tmp_path.resolve() / "logs"
    assert config.log_file == tmp_path.resolve() / "logs" / "calculator.log"
    assert config.history_dir == tmp_path.resolve() / "history"
    assert config.history_file == tmp_path.resolve() / "history" / "calculator_history.csv"


def test_path_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "L"))
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "H"))
    config = CalculatorConfig()
    assert config.log_dir == (tmp_path / "L").resolve()
    assert config.history_dir == (tmp_path / "H").resolve()


@pytest.mark.parametrize("kwargs, message", [
    ({"max_history_size": 0}, "max_history_size"),
    ({"max_history_size": -3}, "max_history_size"),
    ({"precision": 0}, "precision"),
    ({"max_input_value": 0}, "max_input_value"),
    ({"max_input_value": -1}, "max_input_value"),
    ({"default_encoding": "not-a-codec"}, "Unknown encoding"),
])
def test_validate_rejects_bad_settings(kwargs, message):
    with pytest.raises(ConfigurationError, match=message):
        CalculatorConfig(**kwargs).validate()


def test_repr_mentions_settings(tmp_path):
    text = repr(CalculatorConfig(base_dir=tmp_path, precision=3))
    assert text.startswith("CalculatorConfig(") and "precision=3" in text

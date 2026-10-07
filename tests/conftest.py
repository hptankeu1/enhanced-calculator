"""Shared pytest fixtures."""

import os
from decimal import Decimal

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Strip CALCULATOR_* variables (e.g. from a local .env) and point the base dir at tmp_path."""
    for key in list(os.environ):
        if key.startswith("CALCULATOR_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("CALCULATOR_BASE_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def config(tmp_path):
    """A config writing logs/history under tmp_path."""
    return CalculatorConfig(base_dir=tmp_path, max_history_size=5, auto_save=True, precision=4,
                            max_input_value=Decimal("1e10"))


@pytest.fixture
def calculator(config):
    """A fresh Calculator using the temporary config."""
    return Calculator(config)

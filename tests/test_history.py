"""Tests for the observers."""

import logging
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.calculation import Calculation
from app.history import AutoSaveObserver, HistoryObserver, LoggingObserver


@pytest.fixture
def calc_record():
    return Calculation("add", Decimal(2), Decimal(3))


def test_history_observer_is_abstract():
    with pytest.raises(TypeError):
        HistoryObserver()


def test_logging_observer_logs(calc_record, caplog):
    with caplog.at_level(logging.INFO):
        LoggingObserver().update(calc_record)
    assert "Calculation performed: add (2, 3) = 5" in caplog.text


@pytest.mark.parametrize("observer_factory", [
    lambda: LoggingObserver(),
    lambda: AutoSaveObserver(Mock(config=Mock(), save_history=Mock())),
])
def test_observers_reject_none(observer_factory):
    with pytest.raises(AttributeError, match="cannot be None"):
        observer_factory().update(None)


@pytest.mark.parametrize("auto_save, expected_calls", [(True, 1), (False, 0)])
def test_auto_save_observer(calc_record, auto_save, expected_calls):
    calculator = Mock()
    calculator.config.auto_save = auto_save
    AutoSaveObserver(calculator).update(calc_record)
    assert calculator.save_history.call_count == expected_calls


@pytest.mark.parametrize("bad_calculator", [object(), Mock(spec=["config"]), Mock(spec=["save_history"])])
def test_auto_save_observer_requires_calculator_interface(bad_calculator):
    with pytest.raises(TypeError, match="config"):
        AutoSaveObserver(bad_calculator)

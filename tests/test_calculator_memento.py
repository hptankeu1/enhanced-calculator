"""Tests for CalculatorMemento."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


def make_history(n):
    return [Calculation("add", Decimal(i), Decimal(1)) for i in range(n)]


@pytest.mark.parametrize("size", [0, 1, 3])
def test_snapshot_is_a_copy(size):
    history = make_history(size)
    memento = CalculatorMemento(history)
    history.append(Calculation("add", Decimal(9), Decimal(9)))
    assert len(memento.history) == size


@pytest.mark.parametrize("size", [0, 2])
def test_round_trip(size):
    memento = CalculatorMemento(make_history(size), timestamp=datetime(2026, 5, 1, 12, 0))
    data = memento.to_dict()
    assert data["timestamp"] == "2026-05-01T12:00:00"
    assert len(data["history"]) == size
    restored = CalculatorMemento.from_dict(data)
    assert restored.history == memento.history
    assert restored.timestamp == memento.timestamp


def test_default_timestamp_is_now():
    before = datetime.now()
    memento = CalculatorMemento([])
    assert before <= memento.timestamp <= datetime.now()

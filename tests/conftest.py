"""Fixtures compartidas por la suite de tests."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from main import app
from tasks import clock
from tasks import repository as tasks_repository
from users import repository

# Día fijo para todos los tests: ningún resultado depende de cuándo se corre la suite.
TODAY = date(2026, 10, 18)


@pytest.fixture(autouse=True)
def _reset_data():
    """Cada test arranca con los datos semilla y no contamina a los demás."""
    repository.reset()
    tasks_repository.reset()
    yield
    repository.reset()
    tasks_repository.reset()


@pytest.fixture(autouse=True)
def _fixed_today(monkeypatch: pytest.MonkeyPatch) -> date:
    """Fija `clock.today()` en TODAY (mock del reloj)."""
    monkeypatch.setattr(clock, "today", lambda: TODAY)
    return TODAY


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

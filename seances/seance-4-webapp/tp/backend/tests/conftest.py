from collections.abc import Iterator
from dataclasses import dataclass, fields
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import items, reservations


@dataclass
class Storage:
    """Reference the real dictionaries; never substitute a mock database."""

    items: dict[int, dict[str, Any]]
    reservations: dict[int, dict[str, Any]]

    def reset_all(self) -> None:
        for field in fields(self):
            getattr(self, field.name).clear()


@pytest.fixture
def storage() -> Iterator[Storage]:
    state = Storage(items=items.FAKE_DB, reservations=reservations.FAKE_DB)
    state.reset_all()
    yield state
    state.reset_all()


@pytest.fixture
def client(storage: Storage) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def item_velo(client: TestClient) -> dict[str, Any]:
    response = client.post('/items', json={
        'titre': 'Vélo de ville', 'description': 'Trois vitesses', 'tarif_jour': 8.5,
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def reservation_active(client: TestClient, item_velo: dict[str, Any]) -> dict[str, Any]:
    response = client.post('/reservations', json={
        'item_id': item_velo['id'], 'date_debut': '2026-09-01', 'date_fin': '2026-09-05',
    })
    assert response.status_code == 201
    return response.json()

"""Tests de la aplicación (endpoints que no pertenecen a un recurso)."""
from fastapi.testclient import TestClient


def test_health_devuelve_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_el_router_de_tasks_esta_montado_en_openapi(client: TestClient) -> None:
    """Integración: las rutas nuevas aparecen en la documentación generada (/docs)."""
    paths = client.get("/openapi.json").json()["paths"]

    assert {"/tasks", "/tasks/{task_id}", "/tasks/{task_id}/status"} <= set(paths)

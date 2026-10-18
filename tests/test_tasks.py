"""Tests de integración HTTP del recurso `tasks` (ver docs/especificacion.md).

Mismo estilo que tests/test_users.py: un caso por test, arrange / act / assert
separados por una línea en blanco. Cada test menciona el criterio CA-xx que cubre.
"""
from fastapi.testclient import TestClient


def _create(client: TestClient, **overrides: object) -> dict:
    """Crea una tarea válida (con los campos que se sobrescriban) y devuelve el cuerpo."""
    payload = {"title": "Revisar respaldos nocturnos", **overrides}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- POST /tasks · camino feliz -------------------------------------------------


def test_create_task_solo_titulo_aplica_defaults(client: TestClient) -> None:
    """CA-01."""
    payload = {"title": "Revisar respaldos nocturnos"}

    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "pending"
    assert body["priority"] == 3
    assert body["description"] is None
    assert body["due_date"] is None
    assert body["assignee_id"] is None
    assert [h["status"] for h in body["status_history"]] == ["pending"]
    assert body["created_at"] == body["updated_at"]


def test_create_task_con_todos_los_campos(client: TestClient) -> None:
    """CA-02: el responsable es un usuario semilla (integración con `users`)."""
    payload = {
        "title": "Rotar credenciales del VPN",
        "description": "Antes del cierre de mes",
        "priority": 5,
        "due_date": "2026-10-31",
        "assignee_id": 2,
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert {k: body[k] for k in payload} == payload


def test_create_task_recorta_espacios_del_titulo(client: TestClient) -> None:
    """CA-03 (normalización): el título se guarda sin espacios alrededor."""
    response = client.post("/tasks", json={"title": "   Revisar logs   "})

    assert response.status_code == 201
    assert response.json()["title"] == "Revisar logs"


def test_create_task_ids_consecutivos(client: TestClient) -> None:
    """CA-01: el servidor asigna ids consecutivos."""
    first = _create(client)

    second = _create(client)

    assert second["id"] == first["id"] + 1


# --- GET /tasks/{task_id} ------------------------------------------------------


def test_get_task_existente_devuelve_200(client: TestClient) -> None:
    """CA-16."""
    created = _create(client, title="Actualizar inventario de equipos")

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_task_inexistente_devuelve_404(client: TestClient) -> None:
    """CA-17."""
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "tarea no encontrado: 999"

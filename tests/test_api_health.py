from __future__ import annotations


def test_liveness_does_not_depend_on_database(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_readiness_uses_api_health(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr("src.api.routes.misc.get_engine", lambda: db_session.get_bind())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_integrity_check_is_explicit(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr("src.api.routes.misc.get_engine", lambda: db_session.get_bind())
    response = client.get("/api/v1/health/integrity")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

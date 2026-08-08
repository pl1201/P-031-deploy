"""Patient-centric workspace API: timeline, notes, overview, and RBAC."""

from __future__ import annotations


def _register_and_login(client, email: str, role: str):
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "matkhau123", "role": role, "full_name": "Test User"},
    )
    user_id = registration.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "matkhau123"})
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_profile(client):
    _, dietitian_headers = _register_and_login(client, "workspace-dietitian@example.com", "dietitian")
    patient_user_id, patient_headers = _register_and_login(client, "workspace-patient@example.com", "patient")
    response = client.post(
        "/api/v1/patients",
        headers=dietitian_headers,
        json={
            "user_id": patient_user_id,
            "age": 58,
            "sex": "male",
            "height_cm": 165,
            "weight_kg": 68,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
            "region": "north",
        },
    )
    assert response.status_code == 201, response.text
    return response.json(), dietitian_headers, patient_headers


def test_create_profile_seeds_weight_observation(client):
    profile, dietitian_headers, _ = _create_profile(client)
    response = client.get(f"/api/v1/patients/{profile['id']}/observations", headers=dietitian_headers)
    assert response.status_code == 200
    assert response.json()[0]["observation_type"] == "weight"
    assert response.json()[0]["value"] == 68


def test_dietitian_adds_observation_and_overview_returns_latest(client):
    profile, dietitian_headers, _ = _create_profile(client)
    response = client.post(
        f"/api/v1/patients/{profile['id']}/observations",
        headers=dietitian_headers,
        json={
            "observation_type": "hba1c",
            "value": 7.2,
            "unit": "%",
            "measured_at": "2026-08-08T09:00:00",
            "source": "lab",
        },
    )
    assert response.status_code == 201, response.text
    overview = client.get(f"/api/v1/patients/{profile['id']}/overview", headers=dietitian_headers)
    assert overview.status_code == 200, overview.text
    assert overview.json()["latest_observations"]["hba1c"]["value"] == 7.2
    assert overview.json()["meal_plans"]["total"] == 0


def test_patient_only_reads_patient_visible_notes(client):
    profile, dietitian_headers, patient_headers = _create_profile(client)
    for visibility, content in [("care_team", "Ghi chú nội bộ"), ("patient_visible", "Theo dõi bữa sáng")]:
        response = client.post(
            f"/api/v1/patients/{profile['id']}/notes",
            headers=dietitian_headers,
            json={"note_type": "follow_up", "content": content, "visibility": visibility},
        )
        assert response.status_code == 201, response.text

    response = client.get(f"/api/v1/patients/{profile['id']}/notes", headers=patient_headers)
    assert response.status_code == 200
    assert [note["content"] for note in response.json()] == ["Theo dõi bữa sáng"]


def test_patient_cannot_create_clinical_note(client):
    profile, _, patient_headers = _create_profile(client)
    response = client.post(
        f"/api/v1/patients/{profile['id']}/notes",
        headers=patient_headers,
        json={"note_type": "follow_up", "content": "Không được phép", "visibility": "patient_visible"},
    )
    assert response.status_code == 403

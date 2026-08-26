import os

from fastapi.testclient import TestClient

from app.main import app


def test_request_without_api_key_is_rejected(client):
    unauthenticated = TestClient(app)
    response = unauthenticated.get("/api/leads")
    assert response.status_code == 401


def test_request_with_wrong_api_key_is_rejected(client):
    wrong_key_client = TestClient(app, headers={"X-API-Key": "not-the-real-key"})
    response = wrong_key_client.get("/api/leads")
    assert response.status_code == 401


def test_request_with_correct_api_key_succeeds(client):
    response = client.get("/api/leads")
    assert response.status_code == 200


def test_health_check_does_not_require_api_key():
    unauthenticated = TestClient(app)
    response = unauthenticated.get("/api/health")
    assert response.status_code == 200

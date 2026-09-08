"""
Tests for the /healthz liveness endpoint added in Stage 6.
"""


def test_healthz_does_not_require_login(client):
    response = client.get("/healthz")

    assert response.status_code == 200


def test_healthz_response_is_minimal_and_not_sensitive(client):
    response = client.get("/healthz")

    assert response.get_json() == {"status": "ok"}

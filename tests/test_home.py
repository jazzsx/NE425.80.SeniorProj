"""
Tests for the homepage, which is now protected by login.
"""


def test_homepage_redirects_to_login_when_not_logged_in(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_homepage_loads_when_logged_in(client):
    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/")

    assert response.status_code == 200
    assert b"Incident Response Playbook Generator" in response.data

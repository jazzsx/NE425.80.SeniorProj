"""
Tests for login and logout.

These tests never contact a real Active Directory server -- that
wouldn't work in CI anyway, since there's no domain controller
reachable from a GitHub Actions runner. Instead, we replace
("mock") the authenticate() function from app/auth/ldap_client.py
with a fake version that we control, so we can test the login route's
own behavior (setting the session, redirecting, showing errors) in
isolation from the real LDAPS connection logic.
"""

from unittest.mock import patch


def test_login_page_loads(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Log In" in response.data


@patch("app.auth.routes.authenticate", return_value=True)
def test_login_with_valid_credentials_logs_in(mock_authenticate, client):
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "correct-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Incident Response Playbook Generator" in response.data

    with client.session_transaction() as session:
        assert session["username"] == "testuser"


@patch("app.auth.routes.authenticate", return_value=False)
def test_login_with_invalid_credentials_shows_error(mock_authenticate, client):
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrong-password"},
    )

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

    with client.session_transaction() as session:
        assert "username" not in session


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/logout")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with client.session_transaction() as session:
        assert "username" not in session

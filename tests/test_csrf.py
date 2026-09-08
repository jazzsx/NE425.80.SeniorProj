"""
Tests for CSRF (Cross-Site Request Forgery) protection, added in
Stage 6.

Unlike the rest of the test suite (which disables WTF_CSRF_ENABLED in
tests/conftest.py so ordinary view-logic tests don't need to fetch a
token first), these tests build their own app instance with CSRF left
at its real, enabled default -- that's the whole point of them.
"""

import re

from app import create_app
from app.extensions import db


def _make_app():
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        db.create_all()
    return app


def _extract_csrf_token(html_bytes):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', html_bytes)
    assert match, "csrf_token hidden field not found in the rendered form"
    return match.group(1).decode()


def test_login_post_without_csrf_token_is_rejected():
    app = _make_app()
    client = app.test_client()

    response = client.post("/login", data={"username": "someone", "password": "whatever"})

    assert response.status_code == 400


def test_login_post_with_valid_csrf_token_is_accepted():
    app = _make_app()
    client = app.test_client()

    get_response = client.get("/login")
    token = _extract_csrf_token(get_response.data)

    response = client.post(
        "/login",
        data={"username": "someone", "password": "wrong-password", "csrf_token": token},
    )

    # Not rejected for CSRF -- it reaches the real login logic and
    # fails authentication normally (there's no real AD server here),
    # rather than failing with a CSRF 400.
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_generate_post_without_csrf_token_is_rejected():
    app = _make_app()
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "ransomware", "organization_profile": "A test organization."},
    )

    assert response.status_code == 400


def test_healthz_does_not_require_a_csrf_token():
    # /healthz is a GET-only route; CSRF protection only ever applies
    # to POST/PUT/PATCH/DELETE, so this should never be affected.
    app = _make_app()
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200

"""
Tests for Stage 6 production hardening: session cookie settings,
debug mode being off, and unhandled errors never leaking internal
details to the client.
"""


def test_session_cookie_settings(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    # SESSION_COOKIE_SECURE isn't asserted to a fixed value here: it's
    # controlled by the SESSION_COOKIE_SECURE environment variable and
    # is meant to stay off for local/dev/test (plain HTTP) and only be
    # turned on in production once Nginx is confirmed serving real
    # HTTPS -- see app/config.py and the README's Stage 6 section.
    assert "SESSION_COOKIE_SECURE" in app.config


def test_debug_mode_is_disabled_by_default(app):
    assert app.debug is False


def test_unhandled_error_does_not_leak_internal_details(app):
    # Register a route that deliberately raises, so we can confirm
    # production-style error handling (TESTING/DEBUG/PROPAGATE_EXCEPTIONS
    # all off, as in real deployment) never exposes a traceback or
    # exception message to the client -- only a generic 500 page.
    @app.route("/__raises-for-test")
    def _raises_for_test():
        raise RuntimeError("some internal detail that must never leak")

    app.config["TESTING"] = False
    app.config["DEBUG"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = False

    client = app.test_client()
    response = client.get("/__raises-for-test")

    assert response.status_code == 500
    assert b"some internal detail" not in response.data
    assert b"Traceback" not in response.data
    assert b"RuntimeError" not in response.data

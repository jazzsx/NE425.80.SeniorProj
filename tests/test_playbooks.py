"""
Tests for the AI playbook generator page.

These tests never call the real Anthropic API. Most of them mock
generate_playbook() (as imported into app/playbooks/routes.py) so the
suite needs no network access and no real API key -- exactly like
CI. One test (test_generate_without_api_key_shows_friendly_message)
deliberately mocks nothing: ANTHROPIC_API_KEY is unset in this test
environment, the same as in CI, so it exercises the real
ClaudeNotConfiguredError path end-to-end without ever attempting a
network call.
"""

from unittest.mock import patch

from app.models import Playbook
from app.playbooks.claude_client import ClaudeGenerationError
from app.playbooks.rendering import render_playbook_html


def _login(client, username="testuser"):
    with client.session_transaction() as session:
        session["username"] = username


def test_generate_page_redirects_when_not_logged_in(client):
    response = client.get("/playbooks/generate")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_generate_page_loads_when_logged_in(client):
    _login(client)

    response = client.get("/playbooks/generate")

    assert response.status_code == 200
    assert b"Generate an Incident Response Playbook" in response.data
    assert b"Ransomware" in response.data
    assert b"Business Email Compromise" in response.data
    assert b"Data Exfiltration" in response.data


def test_generate_rejects_invalid_incident_type(app, client):
    _login(client)

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "not-a-real-type", "organization_profile": "A small clinic."},
    )

    assert response.status_code == 200
    assert b"choose a valid incident type" in response.data

    with app.app_context():
        assert Playbook.query.count() == 0


def test_generate_rejects_empty_organization_profile(app, client):
    _login(client)

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "ransomware", "organization_profile": "   "},
    )

    assert response.status_code == 200
    assert b"describe the organization" in response.data

    with app.app_context():
        assert Playbook.query.count() == 0


def test_generate_rejects_overly_long_organization_profile(app, client):
    _login(client)

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "ransomware", "organization_profile": "x" * 5000},
    )

    assert response.status_code == 200
    assert b"too long" in response.data

    with app.app_context():
        assert Playbook.query.count() == 0


def test_generate_without_api_key_shows_friendly_message(app, client):
    # ANTHROPIC_API_KEY is unset in this test environment (as in CI),
    # so app.playbooks.claude_client.generate_playbook() itself raises
    # ClaudeNotConfiguredError before attempting any network call --
    # nothing is mocked here on purpose.
    _login(client)

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "ransomware", "organization_profile": "A regional hospital network."},
    )

    assert response.status_code == 200
    assert b"ANTHROPIC_API_KEY" in response.data

    with app.app_context():
        assert Playbook.query.count() == 0


@patch("app.playbooks.routes.generate_playbook")
def test_generate_success_renders_and_saves_playbook(mock_generate_playbook, app, client):
    mock_generate_playbook.return_value = (
        "# Ransomware Incident Response Playbook\n\n"
        "## Purpose and Scope\n\n"
        "This playbook covers ransomware incidents.\n\n"
        "- Contain affected hosts\n"
        "- Notify leadership\n"
    )

    _login(client, username="alice")

    response = client.post(
        "/playbooks/generate",
        data={
            "incident_type": "ransomware",
            "organization_profile": "A 200-person manufacturing company running mostly on-prem Windows servers.",
        },
    )

    assert response.status_code == 200
    mock_generate_playbook.assert_called_once_with(
        "ransomware",
        "A 200-person manufacturing company running mostly on-prem Windows servers.",
    )
    assert b"<h1>Ransomware Incident Response Playbook</h1>" in response.data
    assert b"<h2>Purpose and Scope</h2>" in response.data
    assert b"<li>Contain affected hosts</li>" in response.data

    with app.app_context():
        assert Playbook.query.count() == 1
        saved = Playbook.query.one()
        assert saved.created_by_username == "alice"
        assert saved.incident_type == "ransomware"
        assert saved.organization_profile == (
            "A 200-person manufacturing company running mostly on-prem Windows servers."
        )
        assert saved.content == mock_generate_playbook.return_value
        assert saved.created_at is not None


@patch("app.playbooks.routes.generate_playbook")
def test_generate_handles_api_error_gracefully(mock_generate_playbook, app, client):
    mock_generate_playbook.side_effect = ClaudeGenerationError("some internal detail")

    _login(client)

    response = client.post(
        "/playbooks/generate",
        data={"incident_type": "data_exfiltration", "organization_profile": "A small SaaS startup."},
    )

    assert response.status_code == 200
    assert b"Something went wrong generating the playbook" in response.data
    assert b"some internal detail" not in response.data

    with app.app_context():
        assert Playbook.query.count() == 0


def test_rendering_strips_unsafe_html():
    html = render_playbook_html(
        "# Title\n\n<script>alert(1)</script>\n\nSome text.\n\n[bad link](javascript:alert(1))"
    )

    assert "<script" not in html.lower()
    assert "javascript:" not in html.lower()
    assert "<h1>Title</h1>" in html
    assert "Some text." in html

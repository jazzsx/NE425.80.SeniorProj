"""
Tests for "My Playbooks" (the history list) and the single-playbook
detail page, including per-user access control.
"""

from app.extensions import db
from app.models import Playbook


def _login(client, username="testuser"):
    with client.session_transaction() as session:
        session["username"] = username


def _create_playbook(app, username, incident_type="ransomware", profile="A test organization."):
    with app.app_context():
        playbook = Playbook(
            created_by_username=username,
            incident_type=incident_type,
            organization_profile=profile,
            content="# Test Playbook\n\nSome generated content.",
        )
        db.session.add(playbook)
        db.session.commit()
        return playbook.id


def test_history_requires_login(client):
    response = client.get("/playbooks/history")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_history_shows_only_current_users_playbooks(app, client):
    _create_playbook(app, "alice", incident_type="ransomware", profile="Alice's hospital network.")
    _create_playbook(app, "bob", incident_type="data_exfiltration", profile="Bob's law firm.")

    _login(client, username="alice")

    response = client.get("/playbooks/history")

    assert response.status_code == 200
    assert b"Ransomware" in response.data
    assert b"Data Exfiltration" not in response.data


def test_history_shows_empty_state_with_no_saved_playbooks(client):
    _login(client)

    response = client.get("/playbooks/history")

    assert response.status_code == 200
    assert b"haven't generated any playbooks yet" in response.data


def test_detail_requires_login(client):
    response = client.get("/playbooks/history/1")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_detail_shows_own_playbook(app, client):
    playbook_id = _create_playbook(
        app, "alice", incident_type="ransomware", profile="A very distinctive hospital network for Alice."
    )

    _login(client, username="alice")

    response = client.get(f"/playbooks/history/{playbook_id}")

    assert response.status_code == 200
    assert b"Ransomware" in response.data
    assert b"A very distinctive hospital network for Alice." in response.data
    assert b"<h1>Test Playbook</h1>" in response.data


def test_detail_blocks_access_to_another_users_playbook(app, client):
    bobs_playbook_id = _create_playbook(app, "bob", profile="Bob's confidential law firm details.")

    _login(client, username="alice")

    response = client.get(f"/playbooks/history/{bobs_playbook_id}")

    assert response.status_code == 404
    assert b"confidential law firm" not in response.data


def test_detail_nonexistent_id_returns_404(client):
    _login(client, username="alice")

    response = client.get("/playbooks/history/999999")

    assert response.status_code == 404

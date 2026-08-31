"""
Tests for the Playbook database model.

These run against the in-memory SQLite database set up in
tests/conftest.py, not a real PostgreSQL server -- they're testing
that our model and its columns behave correctly, not testing
PostgreSQL itself.
"""

from app.extensions import db
from app.models import Playbook


def test_create_and_read_playbook(app):
    with app.app_context():
        playbook = Playbook(
            created_by_username="jdoe",
            incident_type="ransomware",
            organization_profile="Mid-size healthcare provider, ~500 employees",
            content="# Ransomware Incident Response Playbook\n...",
        )
        db.session.add(playbook)
        db.session.commit()

        saved = db.session.get(Playbook, playbook.id)

        assert saved is not None
        assert saved.created_by_username == "jdoe"
        assert saved.incident_type == "ransomware"
        assert saved.organization_profile.startswith("Mid-size healthcare")
        assert saved.content.startswith("# Ransomware")
        assert saved.created_at is not None
        assert saved.updated_at is not None


def test_updated_at_advances_when_a_playbook_is_edited(app):
    with app.app_context():
        playbook = Playbook(
            created_by_username="jdoe",
            incident_type="business_email_compromise",
            organization_profile="Small law firm",
            content="draft content",
        )
        db.session.add(playbook)
        db.session.commit()

        original_updated_at = playbook.updated_at

        playbook.content = "revised content"
        db.session.commit()

        assert playbook.updated_at >= original_updated_at
        assert playbook.content == "revised content"

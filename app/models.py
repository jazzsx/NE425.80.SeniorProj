"""
Database models.

Right now there's just one: Playbook, a saved incident-response
playbook. The Claude API integration (a later stage) will create
these rows; for now this just defines the table shape.
"""

from datetime import datetime, timezone

from app.extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


class Playbook(db.Model):
    __tablename__ = "playbooks"

    id = db.Column(db.Integer, primary_key=True)

    # The Active Directory username (set at login) of whoever
    # generated this playbook.
    created_by_username = db.Column(db.String(150), nullable=False)

    # e.g. "ransomware", "business_email_compromise", "data_exfiltration".
    incident_type = db.Column(db.String(100), nullable=False)

    # Free-text description of the organization the playbook was
    # generated for (size, industry, systems in use, etc.).
    organization_profile = db.Column(db.Text, nullable=False)

    # The generated playbook itself.
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    def __repr__(self):
        return f"<Playbook id={self.id} incident_type={self.incident_type!r}>"

"""
The playbook generator, history, and detail pages: let a logged-in
user pick an incident type, describe their organization, generate a
draft incident response playbook using the Claude API, and revisit
their own previously generated playbooks.

Every successfully generated playbook is saved to the "playbooks"
table under the logged-in user's AD username. Nothing is saved for a
failed generation or a submission that fails validation.
"""

from flask import Blueprint, render_template, request, session

from app.auth.decorators import login_required
from app.extensions import db
from app.models import Playbook
from app.playbooks.claude_client import (
    ClaudeGenerationError,
    ClaudeNotConfiguredError,
    generate_playbook,
)
from app.playbooks.prompts import INCIDENT_TYPES, MAX_ORGANIZATION_PROFILE_LENGTH
from app.playbooks.rendering import render_playbook_html

playbooks = Blueprint("playbooks", __name__, url_prefix="/playbooks")


@playbooks.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    playbook_html = None
    error = None
    selected_incident_type = ""
    organization_profile = ""

    if request.method == "POST":
        selected_incident_type = request.form.get("incident_type", "")
        organization_profile = request.form.get("organization_profile", "")

        error = _validate(selected_incident_type, organization_profile)

        if not error:
            stripped_profile = organization_profile.strip()
            try:
                playbook_markdown = generate_playbook(selected_incident_type, stripped_profile)
            except ClaudeNotConfiguredError:
                error = (
                    "The AI playbook generator isn't configured yet. "
                    "Ask an administrator to set the ANTHROPIC_API_KEY "
                    "environment variable on the server."
                )
            except ClaudeGenerationError:
                error = "Something went wrong generating the playbook. Please try again in a moment."
            else:
                # Only reached when generation actually succeeded -- a
                # failed generation or a validation error never
                # creates a database row.
                playbook = Playbook(
                    created_by_username=session["username"],
                    incident_type=selected_incident_type,
                    organization_profile=stripped_profile,
                    content=playbook_markdown,
                )
                db.session.add(playbook)
                db.session.commit()

                playbook_html = render_playbook_html(playbook_markdown)

    return render_template(
        "playbooks/generate.html",
        incident_types=INCIDENT_TYPES,
        selected_incident_type=selected_incident_type,
        organization_profile=organization_profile,
        organization_profile_max_length=MAX_ORGANIZATION_PROFILE_LENGTH,
        playbook_html=playbook_html,
        error=error,
        username=session.get("username"),
    )


@playbooks.route("/history")
@login_required
def history():
    """List only the logged-in user's own saved playbooks, newest first."""
    saved_playbooks = (
        Playbook.query.filter_by(created_by_username=session["username"])
        .order_by(Playbook.created_at.desc())
        .all()
    )

    return render_template(
        "playbooks/history.html",
        playbooks=saved_playbooks,
        incident_types=INCIDENT_TYPES,
        username=session.get("username"),
    )


@playbooks.route("/history/<int:playbook_id>")
@login_required
def detail(playbook_id):
    """Show one saved playbook, but only if it belongs to this user.

    Filtering by created_by_username in the same query used to look
    the row up (rather than fetching by ID and checking ownership
    afterward) means a playbook that exists but belongs to someone
    else produces the exact same 404 as an ID that doesn't exist at
    all -- nothing about the response reveals whether another user
    owns that ID.
    """
    playbook = Playbook.query.filter_by(
        id=playbook_id, created_by_username=session["username"]
    ).first_or_404()

    return render_template(
        "playbooks/detail.html",
        playbook=playbook,
        incident_type_label=INCIDENT_TYPES.get(playbook.incident_type, playbook.incident_type),
        playbook_html=render_playbook_html(playbook.content),
        username=session.get("username"),
    )


def _validate(incident_type, organization_profile):
    """Server-side validation of the submitted form.

    Never trust that the browser enforced the <select> options or the
    textarea's maxlength -- a request can be crafted by hand, so every
    rule here is re-checked on the server.
    """
    if incident_type not in INCIDENT_TYPES:
        return "Please choose a valid incident type."

    stripped_profile = organization_profile.strip()

    if not stripped_profile:
        return "Please describe the organization before generating a playbook."

    if len(stripped_profile) > MAX_ORGANIZATION_PROFILE_LENGTH:
        return f"Organization profile is too long (max {MAX_ORGANIZATION_PROFILE_LENGTH} characters)."

    return None

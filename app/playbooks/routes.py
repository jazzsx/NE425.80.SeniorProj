"""
The playbook generator page: lets a logged-in user pick an incident
type, describe their organization, and generate a draft incident
response playbook using the Claude API.

Stage 4 does not save anything to the database yet -- that's Stage 5
(persistence/history). Each generated playbook only exists for the
current page load; refreshing or navigating away loses it.
"""

from flask import Blueprint, render_template, request, session

from app.auth.decorators import login_required
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
            try:
                playbook_markdown = generate_playbook(
                    selected_incident_type, organization_profile.strip()
                )
                playbook_html = render_playbook_html(playbook_markdown)
            except ClaudeNotConfiguredError:
                error = (
                    "The AI playbook generator isn't configured yet. "
                    "Ask an administrator to set the ANTHROPIC_API_KEY "
                    "environment variable on the server."
                )
            except ClaudeGenerationError:
                error = "Something went wrong generating the playbook. Please try again in a moment."

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

"""
Wraps calls to the Anthropic Claude API for generating incident
response playbooks.

This is the only file in the project that talks to Anthropic. Its
job is narrow and safe: send a prompt, get back text. It never
executes anything the model returns -- the response is treated purely
as text to be displayed, never as commands, code, or instructions to
act on.
"""

import logging

import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from app.playbooks.prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Generous enough for a full, detailed playbook without letting a
# single request run unbounded.
MAX_OUTPUT_TOKENS = 4096


class ClaudeNotConfiguredError(Exception):
    """Raised when ANTHROPIC_API_KEY isn't set on this server."""


class ClaudeGenerationError(Exception):
    """Raised when the Claude API call fails or returns something unusable."""


def generate_playbook(incident_type_key, organization_profile):
    """Ask Claude to generate an incident-response playbook.

    Returns the generated playbook as Markdown text. Callers are
    expected to catch ClaudeNotConfiguredError and
    ClaudeGenerationError and show the user a friendly message --
    neither should ever surface as an unhandled 500 error.
    """
    if not ANTHROPIC_API_KEY:
        raise ClaudeNotConfiguredError("ANTHROPIC_API_KEY is not configured on this server.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(incident_type_key, organization_profile),
                }
            ],
        )
    except anthropic.APIError as exc:
        # Log only the exception type, never the exception's full
        # message/args or the request itself -- the API key is never
        # part of either, but request/response bodies could contain
        # the organization profile text, which we don't need to log.
        logger.warning("Anthropic API call failed: %s", exc.__class__.__name__)
        raise ClaudeGenerationError("The AI service is currently unavailable.") from exc
    except Exception as exc:
        # Catches anything unexpected (e.g. a network-level error the
        # SDK doesn't wrap) so a Claude outage can never crash the
        # request -- it always degrades to a friendly error message.
        logger.warning("Unexpected error calling the Anthropic API: %s", exc.__class__.__name__)
        raise ClaudeGenerationError("The AI service is currently unavailable.") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    playbook_text = "".join(text_parts).strip()

    if not playbook_text:
        raise ClaudeGenerationError("The AI service returned an empty response.")

    return playbook_text

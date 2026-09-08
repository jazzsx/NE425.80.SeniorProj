"""
Safely converts the Markdown text Claude returns into HTML for
display.

The model's output is never trusted as safe HTML on its own -- even
though our prompt asks for Markdown, nothing stops a model response
(or a future different model, or a prompt-injection attempt inside
the organization profile) from containing raw HTML like <script>
tags. So the Markdown-to-HTML conversion is always followed by an
allowlist sanitizer (bleach) that strips anything not explicitly
permitted. Only the sanitized result is ever marked safe for Jinja to
render as raw HTML.
"""

import bleach
import markdown

ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "strong", "em", "code", "pre",
    "ul", "ol", "li",
    "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "a",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}


def render_playbook_html(markdown_text):
    """Convert Claude's Markdown playbook into safe, displayable HTML.

    Two steps: render Markdown to HTML, then run that HTML through an
    allowlist sanitizer. bleach.clean() strips any tag/attribute not
    on the allowlist (e.g. <script>, onclick=, javascript: links)
    while keeping the surrounding text, so nothing unexpected in the
    model's output can execute in the browser.
    """
    raw_html = markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])

    return bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

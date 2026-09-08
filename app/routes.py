"""
This file defines the web pages ("routes") that the Flask app can show.

The homepage ("/") is here. Login/logout live separately in
app/auth/routes.py, and the playbook generator/history/detail pages
live in app/playbooks/routes.py.
"""

from flask import Blueprint, render_template, session

from app.auth.decorators import login_required

# A Blueprint is a way of grouping related routes together.
# For now we only have one group, called "main".
main = Blueprint("main", __name__)


@main.route("/")
@login_required
def home():
    """Show the homepage.

    @login_required means this page can only be viewed by someone
    who's already logged in -- anyone else is redirected to /login
    first. When someone visits the site's main address, Flask runs
    this function and displays the templates/index.html page.
    """
    return render_template("index.html", username=session.get("username"))


@main.route("/healthz")
def healthz():
    """A minimal liveness check for systemd/monitoring, not for humans.

    Deliberately does not require login and does not touch the
    database, Active Directory, or the Claude API -- it only confirms
    that the Flask/Gunicorn process itself is up and able to handle a
    request. It must never return anything sensitive (no config
    values, no version/path details, no stack traces), so there's
    nothing here for an unauthenticated caller to learn beyond "the
    process is alive."
    """
    return {"status": "ok"}, 200

"""
This file defines the web pages ("routes") that the Flask app can show.

Right now there is only one page: the homepage ("/"). Login and
logout live separately in app/auth/routes.py. In later stages we'll
add more routes here, such as a page for generating playbooks.
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

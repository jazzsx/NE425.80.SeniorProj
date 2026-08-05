"""
This file defines the web pages ("routes") that the Flask app can show.

Right now there is only one page: the homepage ("/"). In later stages
we will add more routes here, such as a login page and a page for
generating playbooks.
"""

from flask import Blueprint, render_template

# A Blueprint is a way of grouping related routes together.
# For now we only have one group, called "main".
main = Blueprint("main", __name__)


@main.route("/")
def home():
    """Show the homepage.

    When someone visits the site's main address, Flask runs this
    function and displays the templates/index.html page.
    """
    return render_template("index.html")

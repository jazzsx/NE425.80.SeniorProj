"""
Login and logout pages.

These are grouped into their own "auth" blueprint, separate from the
main application's routes, so authentication logic stays in one place
and can be extended later without touching app/routes.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.auth.ldap_client import authenticate

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if authenticate(username, password):
            # Clearing the session first avoids "session fixation":
            # it throws away anything set before the user proved who
            # they are, and starts a clean session for the login.
            session.clear()
            session["username"] = username

            next_page = request.values.get("next") or url_for("main.home")
            return redirect(next_page)

        flash("Invalid username or password.")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

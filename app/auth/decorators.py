"""
A decorator that protects a route from being viewed unless a user is
logged in.
"""

from functools import wraps

from flask import session, redirect, url_for, request


def login_required(view):
    """Redirect to the login page if there's no logged-in user.

    Put @login_required directly above any route function that
    should only be reachable by an authenticated user. It checks for
    a "username" key in the session (set at login) and, if missing,
    sends the visitor to /login -- remembering the page they wanted
    so they land back there after signing in.
    """

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view

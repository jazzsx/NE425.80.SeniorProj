"""
This file turns the "app" folder into a Python package and builds
the Flask application itself.
"""

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import SECRET_KEY, SESSION_COOKIE_SECURE, SQLALCHEMY_DATABASE_URI
from app.extensions import csrf, db


def create_app(config_overrides=None):
    """Build and configure the Flask application.

    This is called an "application factory." Instead of creating the
    app as a plain global variable, we build it inside a function.
    That makes it much easier to add configuration (like database
    settings) in later stages without breaking anything.

    config_overrides lets callers (mainly the test suite) replace
    specific settings -- e.g. pointing SQLALCHEMY_DATABASE_URI at a
    throwaway test database instead of real PostgreSQL. It must be
    applied before db.init_app(app) below, since Flask-SQLAlchemy
    reads the database URI out of app.config at that point.
    """
    app = Flask(__name__)

    # Needed so Flask can securely sign session cookies -- this is
    # what makes @login_required's session check trustworthy.
    app.config["SECRET_KEY"] = SECRET_KEY

    # Where the database lives, and turning off a Flask-SQLAlchemy
    # feature (change tracking for a signals system) that this
    # project doesn't use and that just adds overhead.
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Session cookie hardening. HttpOnly (default in Flask, set
    # explicitly here so it's never accidentally turned off) stops
    # JavaScript from reading the cookie at all. SameSite=Lax stops it
    # being sent on cross-site POST/PUT/etc requests, which -- together
    # with the CSRF protection below -- is the app's defense against
    # cross-site request forgery. Secure is controlled by
    # SESSION_COOKIE_SECURE (see app/config.py): off for local/dev
    # HTTP, meant to be turned on once Nginx is serving real HTTPS.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = SESSION_COOKIE_SECURE

    if config_overrides:
        app.config.update(config_overrides)

    # In production, Nginx sits in front of Gunicorn and terminates
    # TLS, forwarding plain HTTP to Gunicorn on localhost. Without
    # this, Flask/Werkzeug would think every request is plain HTTP
    # (since that's what Gunicorn actually sees), which would break
    # CSRF's same-origin referrer check and any https:// URLs the app
    # generates. ProxyFix makes Flask trust the X-Forwarded-* headers
    # Nginx sets, so request.is_secure reflects what the browser
    # actually used. It's harmless with no proxy in front (e.g. local
    # "python run.py"): those headers simply won't be present.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Connect the SQLAlchemy extension to this app. This does not
    # create any tables yet -- see app/commands.py's "init-db" command
    # for that.
    db.init_app(app)

    # Protects every state-changing (POST/PUT/PATCH/DELETE) request
    # against cross-site request forgery. The login form and the
    # playbook generator form both need a matching {{ csrf_token() }}
    # hidden field for their POSTs to be accepted.
    csrf.init_app(app)

    # Import the models so SQLAlchemy knows about the "playbooks"
    # table before anything tries to create tables or query them.
    from app import models  # noqa: F401

    # Import and register the routes (the web pages) defined in routes.py,
    # the login/logout pages defined in auth/routes.py, and the AI
    # playbook generator page defined in playbooks/routes.py.
    from app.routes import main
    from app.auth.routes import auth
    from app.playbooks.routes import playbooks

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(playbooks)

    from app.commands import register_commands

    register_commands(app)

    return app

"""
This file turns the "app" folder into a Python package and builds
the Flask application itself.

Later project stages will plug new pieces in here (the Claude API
client, etc.) without us having to rewrite the rest of the project.
"""

from flask import Flask

from app.config import SECRET_KEY, SQLALCHEMY_DATABASE_URI
from app.extensions import db


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

    if config_overrides:
        app.config.update(config_overrides)

    # Connect the SQLAlchemy extension to this app. This does not
    # create any tables yet -- see app/commands.py's "init-db" command
    # for that.
    db.init_app(app)

    # Import the models so SQLAlchemy knows about the "playbooks"
    # table before anything tries to create tables or query them.
    from app import models  # noqa: F401

    # Import and register the routes (the web pages) defined in routes.py,
    # plus the login/logout pages defined in auth/routes.py.
    from app.routes import main
    from app.auth.routes import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    from app.commands import register_commands

    register_commands(app)

    return app

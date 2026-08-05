"""
This file turns the "app" folder into a Python package and builds
the Flask application itself.

Later project stages will plug new pieces in here (database setup,
Active Directory login, the Claude API client, etc.) without us having
to rewrite the rest of the project.
"""

from flask import Flask


def create_app():
    """Build and configure the Flask application.

    This is called an "application factory." Instead of creating the
    app as a plain global variable, we build it inside a function.
    That makes it much easier to add configuration (like database
    settings) in later stages without breaking anything.
    """
    app = Flask(__name__)

    # Import and register the routes (the web pages) defined in routes.py.
    from app.routes import main

    app.register_blueprint(main)

    return app

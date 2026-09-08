"""
Shared pytest fixtures for the test suite.

"app" and "client" are available to any test function in this folder
just by naming them as a parameter -- pytest finds them here
automatically.
"""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    # Tests use a throwaway in-memory SQLite database instead of a
    # real PostgreSQL server -- there isn't one available in CI, and
    # the tables/behavior we're testing don't depend on anything
    # PostgreSQL-specific. The database is recreated fresh for every
    # test and thrown away afterward. This has to be passed in to
    # create_app() itself (rather than set on app.config afterward)
    # because Flask-SQLAlchemy reads the database URI when db.init_app()
    # runs, inside create_app().
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            # The rest of this suite posts test form data directly,
            # without fetching a CSRF token first -- that's fine, since
            # these tests are about the app's own view logic, not
            # re-testing Flask-WTF's CSRF protection itself. That gets
            # its own dedicated tests, with CSRF deliberately left on,
            # in tests/test_csrf.py.
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

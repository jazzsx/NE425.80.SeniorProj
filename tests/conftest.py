"""
Shared pytest fixtures for the test suite.

"app" and "client" are available to any test function in this folder
just by naming them as a parameter -- pytest finds them here
automatically.
"""

import pytest

from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(app):
    return app.test_client()

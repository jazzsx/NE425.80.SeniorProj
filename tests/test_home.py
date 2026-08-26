"""
A minimal automated test for the Flask application.

It checks that the homepage ("/") loads successfully, returning an
HTTP 200 status code. This is the smallest useful test we can write:
it proves the app starts up and responds, without checking every
detail of the page content.
"""

from app import create_app


def test_homepage_returns_200():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200

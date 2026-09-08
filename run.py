"""
This is the file you run to start the web application.

Usage:
    python run.py

It builds the Flask app (using the factory function in app/__init__.py)
and starts a local development web server.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True gives helpful error pages while you are developing.
    # This must be turned off before the app ever goes on a real server.
    app.run(host="0.0.0.0", port=5000, debug=True)

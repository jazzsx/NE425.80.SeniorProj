"""
Shared Flask extension instances.

SQLAlchemy lives in its own file, separate from app/__init__.py. If it
were created directly inside create_app(), app/models.py would have
nothing to import "db" from without importing app/__init__.py itself
-- which imports models.py -- causing a circular import. Keeping the
plain SQLAlchemy() instance here lets both files import it safely.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()

# Protects every POST/PUT/PATCH/DELETE request (the login form and the
# playbook generator form, currently) against Cross-Site Request
# Forgery -- a request is rejected unless it carries a valid token
# tied to the user's own session. GET requests are never affected.
csrf = CSRFProtect()

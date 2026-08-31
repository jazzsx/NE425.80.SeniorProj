"""
Shared Flask extension instances.

SQLAlchemy lives in its own file, separate from app/__init__.py. If it
were created directly inside create_app(), app/models.py would have
nothing to import "db" from without importing app/__init__.py itself
-- which imports models.py -- causing a circular import. Keeping the
plain SQLAlchemy() instance here lets both files import it safely.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

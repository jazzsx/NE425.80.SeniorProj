"""
Custom `flask` command-line commands for this project.
"""

import click

from app.extensions import db


@click.command("init-db")
def init_db_command():
    """Create any database tables that don't already exist yet.

    This is safe to run more than once, on a fresh database or an
    existing one: SQLAlchemy's create_all() only creates tables that
    are missing. It never drops or overwrites an existing table, so
    it will not touch any playbooks that are already saved.

    Run it once, after the "ir_playbook_db" database and the
    "ir_playbook_app" role already exist on PostgreSQL:

        flask --app run.py init-db
    """
    db.create_all()
    click.echo("Database tables created (or already existed).")


def register_commands(app):
    app.cli.add_command(init_db_command)

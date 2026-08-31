"""
Configuration values for the application.

Everything here is read from environment variables, with sensible
defaults for this project's Active Directory environment. Nothing in
this file is a secret: it's the address of the domain controller, not
a password. The one exception is SECRET_KEY, which Flask uses to
cryptographically sign session cookies -- see the note below.
"""

import os
import secrets

# --- Active Directory / LDAPS settings ---
# The Windows Server domain we authenticate users against.
AD_DOMAIN = os.environ.get("AD_DOMAIN", "seniorproj25.local")

# The domain controller's hostname. We connect to it directly over
# LDAPS (LDAP + TLS) rather than doing a DNS SRV lookup, since this
# project has a single, known domain controller.
AD_SERVER_HOST = os.environ.get("AD_SERVER_HOST", "dc01.seniorproj25.local")

# 636 is the standard LDAPS port (LDAP over TLS).
AD_LDAPS_PORT = int(os.environ.get("AD_LDAPS_PORT", "636"))

# Ubuntu's system-wide trusted certificate bundle. This is the same
# store the "ca-certificates" package maintains and that most other
# tools on the server (curl, apt, etc.) already trust. Using it means
# we don't need to ship or manage our own copy of the domain
# controller's certificate chain.
CA_CERTS_FILE = os.environ.get("LDAP_CA_CERTS_FILE", "/etc/ssl/certs/ca-certificates.crt")

# --- Flask session settings ---
# Flask signs session cookies with this key so users can't tamper
# with their own session data (e.g. forging a login). It must never
# be committed to source control.
#
# In production, set the SECRET_KEY environment variable yourself
# (for example in a systemd unit's EnvironmentFile, which is not
# tracked by git). If it isn't set -- such as during local testing or
# CI -- we generate a random one for this run only. That's fine for
# tests, but it does mean logins won't survive an app restart until a
# real SECRET_KEY is configured.
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)

# --- PostgreSQL / SQLAlchemy settings ---
# PostgreSQL runs locally on the same Ubuntu server as the Flask app,
# under the database "ir_playbook_db" and the application role
# "ir_playbook_app". None of this is secret except the password,
# which has no default -- it must come from the environment (e.g. a
# systemd EnvironmentFile) and is never written into this codebase.
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ir_playbook_db")
DB_USER = os.environ.get("DB_USER", "ir_playbook_app")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# DATABASE_URL, if set, overrides the individual DB_* variables above
# entirely -- useful for pointing at something other than a local
# PostgreSQL database (for example, a test database).
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

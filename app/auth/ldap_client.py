"""
Checks a username and password against Active Directory over LDAPS.

This uses what's called a "direct bind": instead of keeping a
separate service account with its own stored password, we attempt to
log in to the domain controller AS the person signing in, using
exactly the username and password they typed into the login form. If
Active Directory accepts that login, the credentials are correct. If
it doesn't -- wrong password, unknown user, disabled account, domain
controller unreachable, certificate problem, anything -- we simply
report "not authenticated". No password is ever stored; it only
exists in memory for the moment it takes to attempt the bind.
"""

import ssl

from ldap3 import Connection, Server, Tls, SIMPLE, NONE
from ldap3.core.exceptions import LDAPException

from app.config import AD_DOMAIN, AD_SERVER_HOST, AD_LDAPS_PORT, CA_CERTS_FILE


def authenticate(username, password):
    """Return True if username/password are a valid AD login, else False.

    Every failure mode (bad password, unreachable server, bad
    certificate, etc.) returns False rather than raising or reporting
    a specific reason. That's deliberate: telling a would-be attacker
    *why* a login failed (e.g. "that account doesn't exist" vs. "wrong
    password") makes it easier for them to enumerate valid usernames.
    """
    if not username or not password:
        return False

    # Validate the domain controller's TLS certificate against
    # Ubuntu's system-wide trusted CA store, the same one apt/curl use.
    tls_config = Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=CA_CERTS_FILE)

    server = Server(
        AD_SERVER_HOST,
        port=AD_LDAPS_PORT,
        use_ssl=True,
        tls=tls_config,
        get_info=NONE,
        connect_timeout=5,
    )

    # Active Directory accepts logins in "user@domain" form (a User
    # Principal Name), which avoids needing the more error-prone
    # distinguished-name (DN) format.
    user_principal_name = f"{username}@{AD_DOMAIN}"

    try:
        connection = Connection(
            server,
            user=user_principal_name,
            password=password,
            authentication=SIMPLE,
            receive_timeout=5,
        )
        success = connection.bind()
        connection.unbind()
        return success
    except LDAPException:
        return False

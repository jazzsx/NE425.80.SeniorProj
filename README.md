# Incident Response Playbook Generator

This is the final stage (Stage 6) of a six-stage senior project. The
application itself was finished in Stage 5; this stage is entirely
about running it safely in the real lab environment: Gunicorn +
systemd instead of the Flask development server, Nginx as a reverse
proxy with a path to real HTTPS, CSRF protection, hardened session
cookies, security headers, a non-sensitive health check, and CI
extended to test on the same Python version the Ubuntu server runs.
No application feature changed in this stage.

## What the finished project does

A user logs in with their Active Directory credentials (over LDAPS),
picks an incident type (Ransomware, Business Email Compromise, or
Data Exfiltration), describes their organization, and generates a
NIST SP 800-61 Rev. 3 / CSF 2.0-aligned draft incident-response
playbook using the Claude API. Every generated playbook is saved to
PostgreSQL under that user's username, and a "My Playbooks" page lets
them revisit their own past playbooks — and only their own.

## Architecture (for a demo)

```
                     ┌─────────────────────────────┐
   Lab client        │   Windows Server 2025        │
   browser  ────────▶│   Active Directory / DNS /   │
       │             │   AD CS (Enterprise Root CA) │
       │  HTTPS       └──────────────┬───────────────┘
       │  (Nginx-terminated)         │ LDAPS (636, validated TLS)
       ▼                              │
┌────────────────────────────────────▼──────────────┐
│  Ubuntu Server                                      │
│                                                       │
│   Nginx (443/80) ──▶ Gunicorn (127.0.0.1:8000, only) │
│                          │                            │
│                          ▼                            │
│                    Flask application                  │
│                    (this repository)                  │
│                          │                             │
│              ┌───────────┴───────────┐                 │
│              ▼                       ▼                 │
│        PostgreSQL              Anthropic Claude API     │
│        (localhost)             (outbound HTTPS)         │
└───────────────────────────────────────────────────────┘
```

- **Nginx** is the only thing exposed to the lab network. It
  terminates TLS (once configured — see below) and reverse-proxies
  everything to Gunicorn on `127.0.0.1:8000`.
- **Gunicorn**, managed by **systemd**, runs the Flask application
  (`run:app`) as a dedicated, unprivileged service account, and
  restarts it automatically if it crashes or the server reboots.
- **Flask** authenticates against **Active Directory** over LDAPS
  (validated against the system CA trust store, never with
  certificate validation disabled), stores playbooks in **PostgreSQL**
  as a low-privilege database role, and calls the **Anthropic API**
  outbound over HTTPS to generate playbook content.

## What's in this project

```
.
├── app/
│   ├── __init__.py            # Builds the Flask application (CSRF, cookies, ProxyFix, DB)
│   ├── config.py               # Reads AD/session/database/Anthropic settings from env vars
│   ├── extensions.py            # The shared SQLAlchemy db object and CSRFProtect instance
│   ├── models.py                 # The Playbook database table
│   ├── commands.py                # The "flask init-db" command
│   ├── routes.py                   # The homepage ("/") and the "/healthz" liveness check
│   ├── auth/
│   │   ├── __init__.py               # Marks auth/ as a Python package
│   │   ├── routes.py                  # /login and /logout pages
│   │   ├── ldap_client.py              # Checks a username/password against Active Directory
│   │   └── decorators.py                # @login_required, used to protect pages
│   ├── playbooks/
│   │   ├── __init__.py               # Marks playbooks/ as a Python package
│   │   ├── routes.py                  # /playbooks/generate, /history, /history/<id>
│   │   ├── claude_client.py            # Calls the Anthropic Claude API
│   │   ├── prompts.py                   # Builds the system/user prompts, lists incident types
│   │   └── rendering.py                  # Safely converts Claude's Markdown reply to HTML
│   ├── templates/
│   │   ├── index.html                # The homepage
│   │   ├── login.html                 # The login form (with CSRF token)
│   │   └── playbooks/
│   │       ├── generate.html            # The playbook generator form + result (with CSRF token)
│   │       ├── history.html              # "My Playbooks" -- this user's saved playbooks
│   │       └── detail.html                # A single saved playbook
│   └── static/
│       └── style.css                  # Styling for all pages
├── run.py                     # Dev entry point ("python run.py"); also what Gunicorn imports in production
├── gunicorn.conf.py            # Production WSGI server configuration
├── requirements.txt             # List of Python packages this project needs
├── .env.example                  # Local-dev environment variable template (no real secrets)
├── deploy/
│   ├── systemd/ir-playbook-generator.service   # Install under /etc/systemd/system/
│   ├── nginx/ir-playbook-generator.conf         # Install under /etc/nginx/sites-available/
│   └── ir-playbook-generator.env.example         # Production env file template (see below)
├── conftest.py                  # Lets pytest find the "app" package
├── tests/
│   ├── conftest.py               # Shared test setup (a test client, a test database, CSRF off)
│   ├── test_home.py               # Tests for the homepage/login redirect
│   ├── test_auth.py                # Tests for login/logout
│   ├── test_models.py               # Tests for the Playbook database model
│   ├── test_playbooks.py             # Tests for the playbook generator page (incl. saving)
│   ├── test_playbook_history.py       # Tests for "My Playbooks" and the detail page
│   ├── test_csrf.py                    # Tests that CSRF protection actually rejects/accepts correctly
│   ├── test_security.py                 # Cookie settings, debug-off, no-stack-trace-leak
│   └── test_health.py                    # Tests for the /healthz endpoint
├── .github/workflows/ci.yml    # Runs the tests on Python 3.12 and 3.14 on every push/PR
├── .gitignore                   # Tells Git which files/folders to never track
└── README.md                     # This file
```

## Local development quickstart

These steps are for running the app on your own laptop for
development/testing -- see **Production deployment on Ubuntu** below
for the real lab server setup.

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
```

### 2. Install the required packages

```bash
pip install -r requirements.txt
```

Installs Flask, pytest, ldap3, Flask-SQLAlchemy, psycopg2-binary,
anthropic, Markdown, bleach, Flask-WTF (CSRF protection), and gunicorn
(the production WSGI server).

### 3. Configure Active Directory (optional here)

Defaults already match this project's lab domain
(`AD_DOMAIN=seniorproj25.local`, `AD_SERVER_HOST=dc01.seniorproj25.local`,
`AD_LDAPS_PORT=636`) — override via environment variables only if
needed; see `.env.example`.

### 4. Set up PostgreSQL and the database

```bash
sudo -u postgres psql -c "CREATE ROLE ir_playbook_app WITH LOGIN PASSWORD 'choose-a-real-password-here';"
sudo -u postgres psql -c "CREATE DATABASE ir_playbook_db OWNER ir_playbook_app;"
export DB_PASSWORD='the-password-you-chose-above'
flask --app run.py init-db
```

`init-db` is safe to run again later — it only creates missing tables.

### 5. Configure the Claude API

```bash
export ANTHROPIC_API_KEY='your-real-api-key-here'
```

Without it, everything else still works; the generator page shows a
friendly "not configured yet" message instead of an error.

### 6. Run the application (development server)

```bash
python run.py
```

Then open `http://127.0.0.1:5000` — you'll be redirected to `/login`
first. This uses Flask's built-in development server, which is fine
for local testing but is never what production runs (see below).

### 7. Run the automated tests

```bash
python -m pytest
```

No test ever contacts a real Active Directory server, a real
PostgreSQL database, or the real Claude API — everything external is
mocked or swapped for an in-memory SQLite database. This is exactly
what CI (`.github/workflows/ci.yml`) runs on Python 3.12 **and**
3.14 on every push and pull request.

## Production deployment on Ubuntu

This section is the actual Stage 6 deliverable: turning the app above
into a service that starts on boot, restarts on failure, and is only
reachable through a reverse proxy. Replace
`ir-playbook.seniorproj25.local` and any `192.168.x.x`-style address
below with your lab's real values — none of this project's source
code hardcodes them.

Steps are grouped so it's clear what's already done for you in this
repository versus what you run by hand on the Ubuntu server.

### Already done in this repository (nothing to write yourself)

- `gunicorn.conf.py` — binds Gunicorn to `127.0.0.1:8000` only, sets a
  sensible worker count, logs to stdout/stderr (which systemd/journald
  capture).
- `deploy/systemd/ir-playbook-generator.service` — the systemd unit.
- `deploy/nginx/ir-playbook-generator.conf` — the Nginx reverse-proxy
  config, HTTP now / HTTPS ready to enable later.
- `deploy/ir-playbook-generator.env.example` — a template for the real
  production environment file (placeholders only, safe to commit).

### A. Install system packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx postgresql
```

(Skip `postgresql` if it's already installed and set up from an
earlier stage.)

### B. Create a dedicated service account

Never run the app as root or as your own login user:

```bash
sudo useradd --system --home /opt/ir-playbook-generator --shell /usr/sbin/nologin ir-playbook-app
```

### C. Deploy the code

```bash
sudo mkdir -p /opt/ir-playbook-generator
sudo git clone <this-repository-url> /opt/ir-playbook-generator
# or: copy your working tree there some other way
sudo chown -R ir-playbook-app:ir-playbook-app /opt/ir-playbook-generator
```

### D. Create the virtual environment and install dependencies

```bash
sudo -u ir-playbook-app python3 -m venv /opt/ir-playbook-generator/venv
sudo -u ir-playbook-app /opt/ir-playbook-generator/venv/bin/pip install -r /opt/ir-playbook-generator/requirements.txt
```

### E. Create the real production environment file — without exposing secrets in shell history

The production secrets (`SECRET_KEY`, `DB_PASSWORD`, `ANTHROPIC_API_KEY`)
must never be typed as a command-line argument (like `echo KEY=value`)
— arguments are recorded in your shell's history file in plain text.
Instead, open the file directly in an editor running as root, which
never touches shell history:

```bash
sudo mkdir -p /etc/ir-playbook-generator
sudo install -m 640 -o root -g ir-playbook-app /dev/null /etc/ir-playbook-generator/ir-playbook-generator.env
sudo nano /etc/ir-playbook-generator/ir-playbook-generator.env
```

Paste in the contents of `deploy/ir-playbook-generator.env.example`
and replace every `REPLACE_WITH_...` placeholder with a real value,
then save and exit. Generate a real `SECRET_KEY` value ahead of time
with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

(Run that on any machine — it doesn't need network access, and the
output is safe to select-and-copy into the editor; it just shouldn't
be typed as a shell *argument* anywhere it would be logged.)

Then lock down the file's permissions (the `install -m 640` above
already set them, but confirm):

```bash
sudo chmod 640 /etc/ir-playbook-generator/ir-playbook-generator.env
sudo chown root:ir-playbook-app /etc/ir-playbook-generator/ir-playbook-generator.env
```

`640` (`rw-r-----`) means: root can read/write it, the
`ir-playbook-app` group (and so the service, which systemd runs as
that user) can read it, and nobody else on the system can read it at
all — not even other unprivileged accounts.

### F. Create the database tables (first deployment only)

```bash
cd /opt/ir-playbook-generator
sudo -u ir-playbook-app bash -c 'set -a; source /etc/ir-playbook-generator/ir-playbook-generator.env; set +a; venv/bin/flask --app run.py init-db'
```

This only creates missing tables — it never touches or drops existing
data, so it's also safe to re-run after future deployments.

### G. Install and start the systemd service

```bash
sudo cp deploy/systemd/ir-playbook-generator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ir-playbook-generator
sudo systemctl status ir-playbook-generator
```

`enable --now` both starts it immediately and makes it start
automatically on every future boot. Confirm it's actually listening:

```bash
curl -s http://127.0.0.1:8000/healthz
# expected: {"status":"ok"}
```

### H. Install and start Nginx (HTTP first)

```bash
sudo cp deploy/nginx/ir-playbook-generator.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/ir-playbook-generator.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default   # avoid the stock "Welcome to nginx" page colliding
sudo nginx -t
sudo systemctl reload nginx
```

Edit `server_name` in that file to match the real hostname lab clients
will use before running `nginx -t`. At this point, visiting
`http://<the-server's-hostname-or-IP>/` from another lab machine
should show the login page.

### I. Issue and install an HTTPS certificate from the lab's AD CS Enterprise CA

This lab has no public DNS name and no internet-facing certificate
authority, so Let's Encrypt doesn't apply here — the Windows Server's
AD CS Enterprise Root CA is the right tool, and since it's an
*Enterprise* CA, domain-joined lab clients already trust it
automatically (via Group Policy), with no manual per-client trust step
needed once the cert is issued.

On the Ubuntu server, generate a private key and certificate signing
request (CSR) — **do not** use any key/cert you find in an example
online; generate your own:

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -new -newkey rsa:2048 -nodes \
  -keyout /tmp/ir-playbook-generator.key \
  -out /tmp/ir-playbook-generator.csr \
  -subj "/CN=ir-playbook.seniorproj25.local"
```

Submit `/tmp/ir-playbook-generator.csr` to the Enterprise CA — the
simplest path from a lab Ubuntu box is the CA's web enrollment page,
typically at `https://<dc-or-ca-hostname>/certsrv`, using the "Web
Server" (or an equivalent server-authentication) certificate template;
paste the CSR's contents there, request it, and download the issued
certificate (and, if offered separately, the CA chain).

Then move the key and the issued certificate into place and lock down
the private key so only root (which owns the Nginx master process) can
read it:

```bash
sudo mv /tmp/ir-playbook-generator.key /etc/nginx/ssl/ir-playbook-generator.key
sudo mv /path/to/downloaded/certificate.crt /etc/nginx/ssl/ir-playbook-generator.crt
sudo chmod 600 /etc/nginx/ssl/ir-playbook-generator.key
sudo chown root:root /etc/nginx/ssl/ir-playbook-generator.key /etc/nginx/ssl/ir-playbook-generator.crt
sudo shred -u /tmp/ir-playbook-generator.csr   # the CSR itself has no secret in it, but tidy up anyway
```

Now follow the numbered steps inside
`deploy/nginx/ir-playbook-generator.conf`'s "Stage B" comment block:
uncomment the HTTPS `server` block, change the HTTP block's `location /`
to redirect to HTTPS, `nginx -t && systemctl reload nginx`, **then**
set `SESSION_COOKIE_SECURE=true` in
`/etc/ir-playbook-generator/ir-playbook-generator.env` (same `sudo
nano` approach as step E) and `sudo systemctl restart
ir-playbook-generator`. Do this in that order — turning on `Secure`
cookies before HTTPS actually works would silently break login, since
browsers refuse to send `Secure` cookies over plain HTTP.

Do not enable the commented-out `Strict-Transport-Security` (HSTS)
header until you've confirmed HTTPS works correctly for every lab
client that needs access — HSTS tells browsers to refuse plain HTTP to
this hostname for the header's `max-age`, with no easy way to undo it
early if something's still wrong with the certificate.

## What each new/changed Stage 6 file does (plain English)

- **`gunicorn.conf.py`** — Production WSGI server config: binds to
  `127.0.0.1:8000` only (never the LAN directly), a CPU-based worker
  count, and logging to stdout/stderr for systemd to capture. Never
  logs request bodies or headers, so form fields like passwords are
  never written here.
- **`deploy/systemd/ir-playbook-generator.service`** — Runs Gunicorn
  as the unprivileged `ir-playbook-app` account, restarts it on
  failure, starts it on boot, and reads all secrets from
  `/etc/ir-playbook-generator/ir-playbook-generator.env` (a file that
  lives only on the server, never in Git).
- **`deploy/nginx/ir-playbook-generator.conf`** — Reverse-proxies to
  Gunicorn, sets `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, and a `Content-Security-Policy` on every response,
  and documents (as a clearly-marked, commented-out second `server`
  block) exactly how to switch on HTTPS once a certificate is
  installed.
- **`deploy/ir-playbook-generator.env.example`** — Documents every
  variable the production environment file needs (`SECRET_KEY`,
  `DB_PASSWORD`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, the AD/LDAP
  variables, `SESSION_COOKIE_SECURE`), with placeholders only.
- **`app/extensions.py`** — Now also creates the shared `CSRFProtect`
  instance (`csrf`), alongside the existing `db`.
- **`app/__init__.py`** — Wires up `CSRFProtect` (protects every
  POST/PUT/PATCH/DELETE request against cross-site request forgery),
  `ProxyFix` (so Flask correctly detects HTTPS when running behind
  Nginx), and explicit session cookie settings: `HttpOnly` always on,
  `SameSite=Lax` always on, `Secure` controlled by
  `SESSION_COOKIE_SECURE`.
- **`app/config.py`** — Adds `SESSION_COOKIE_SECURE`, read from the
  environment and defaulting to `false` so local development over
  plain HTTP keeps working; flip it to `true` in production only once
  HTTPS is confirmed working (see step I above).
- **`app/routes.py`** — Adds `GET /healthz`: no login required, no
  database/AD/Claude API call, returns only `{"status": "ok"}`. Meant
  for systemd/monitoring to confirm the process is alive — it's
  deliberately incapable of leaking any configuration or secret.
- **`app/templates/login.html`, `app/templates/playbooks/generate.html`** —
  Each POST form now includes a hidden `csrf_token` field, required by
  the new CSRF protection.
- **`tests/conftest.py`** — The shared test fixture now also sets
  `WTF_CSRF_ENABLED: False`, so the rest of the suite (which posts test
  form data directly) doesn't need to fetch a token first; CSRF itself
  is tested separately, with it deliberately left on.
- **`tests/test_csrf.py`** — Builds its own app instance with CSRF at
  its real, enabled default. Confirms a POST to `/login` or
  `/playbooks/generate` without a token is rejected (400), a POST to
  `/login` with a valid token reaches the real login logic instead,
  and that `/healthz` (a GET route) is never affected.
- **`tests/test_security.py`** — Confirms the session cookie config
  (`HttpOnly` True, `SameSite` "Lax"), that debug mode is off by
  default, and that a deliberately-raised exception in a
  production-like configuration (`TESTING`/`DEBUG`/
  `PROPAGATE_EXCEPTIONS` all off) returns a generic 500 page with no
  exception message or traceback in the body.
- **`tests/test_health.py`** — Confirms `/healthz` needs no login and
  returns exactly `{"status": "ok"}`.
- **`.github/workflows/ci.yml`** — Now runs the suite on a matrix of
  Python 3.12 *and* 3.14 (3.14 is the version actually installed on
  the Ubuntu deployment target), so a dependency that fails to build
  on 3.14 (as `psycopg2-binary` briefly did — see its version history
  in `requirements.txt`) is caught in CI, not on the server.
- **`requirements.txt`** — Adds `Flask-WTF` (CSRF protection) and
  `gunicorn` (the production WSGI server).

*(Every Stage 1–5 file and its description are unchanged; see the
prior sections above and the git history for those.)*

## A note on secrets

This project never hardcodes a password, API key, or session secret
in the code. `SECRET_KEY`, `DB_PASSWORD`, and `ANTHROPIC_API_KEY` are
all read from environment variables with no hardcoded default (except
`SECRET_KEY`, which falls back to a freshly-generated random value —
fine for local testing, not persistent enough for production, so set
a real one). In production, all of these come from
`/etc/ir-playbook-generator/ir-playbook-generator.env`, a file that is
never committed to Git (only its placeholder template is), is created
by hand directly in an editor rather than via a shell command
argument (so it never appears in shell history), and is restricted to
`640` permissions owned by `root:ir-playbook-app` so only root and the
service's own group can read it. None of these values are ever
written to a log file, Gunicorn's access log, or an exception message
shown to a user.

## A note on CSRF protection

Both of the app's state-changing forms (`/login` and
`/playbooks/generate`) are now protected by Flask-WTF's
`CSRFProtect`. Every POST must carry a valid `csrf_token`, generated
per-session and embedded as a hidden form field; a request without
one (or with a stale/mismatched one) is rejected with `400 Bad
Request` before it ever reaches the view function. This closes what
was, before Stage 6, a real gap: neither form had any CSRF defense.

## A note on cookies and security headers

Session cookies are `HttpOnly` (JavaScript can never read them),
`SameSite=Lax` (never sent on a cross-site POST, which together with
CSRF protection is the app's defense against forged requests from
another site), and `Secure` once `SESSION_COOKIE_SECURE=true` is set
in production (see step I above) — meaning the browser will only ever
send the cookie over HTTPS. `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`, and a `Content-Security-Policy`
are set on every response by Nginx (see
`deploy/nginx/ir-playbook-generator.conf`); the CSP is a strict
`default-src 'self'` since the app uses no inline scripts/styles and
loads nothing from another origin.

## A note on the organization profile and AI safety

The "organization profile" textarea is free-text input from whoever
is logged in, and the system prompt sent to Claude explicitly treats
it as **untrusted, descriptive context only** — it tells the model to
ignore anything in that text that looks like an instruction, command,
or attempt to change its behavior, and to only ever produce playbook
text, never take or claim to take any action. On the way back, the
generated Markdown is converted to HTML and passed through an
allowlist sanitizer before being displayed, so nothing in a model
response (accidental or adversarial) can inject a script or other live
HTML into the page.

## A note on per-user access control

Every playbook row records who generated it (`created_by_username`).
"My Playbooks" and the detail page both filter by that column against
`session["username"]` -- the ID in the URL is never enough on its own
to see a playbook; it also has to belong to whoever is currently
logged in. Requesting someone else's playbook ID and requesting an ID
that doesn't exist produce the identical 404 response, so the app
never confirms or denies whether a given ID belongs to another user.

## Optional future enhancement: continuous deployment

GitHub Actions CI (`.github/workflows/ci.yml`) runs the test suite on
every push/PR, but it does **not** deploy to the Ubuntu VM
automatically, and it shouldn't be made to as-is: GitHub-hosted
runners have no network path to a private `192.168.x.x`-style lab
address, so any automatic deploy step would simply fail to connect.
The standard fix -- and a reasonable future enhancement beyond this
project's current scope -- is a **self-hosted GitHub Actions runner**
installed on the lab network (or on the Ubuntu server itself), which
polls GitHub over an outbound connection it initiates, so it can reach
the VM without any inbound firewall changes. That's intentionally not
implemented here; today's process is the manual deployment steps
above.

## Troubleshooting

**Login fails / hangs for everyone, even with correct credentials**
- Check DC01/DNS reachability from the Ubuntu server:
  `ping dc01.seniorproj25.local` and `nslookup dc01.seniorproj25.local`.
  If DNS resolution fails, the Ubuntu server's `/etc/resolv.conf` (or
  netplan config) likely isn't pointed at the domain controller.
- Confirm LDAPS itself is reachable and the certificate is trusted:
  `openssl s_client -connect dc01.seniorproj25.local:636 -CAfile /etc/ssl/certs/ca-certificates.crt`
  should end with `Verify return code: 0 (ok)`. If not, the
  domain controller's certificate chain isn't in the Ubuntu server's
  trust store yet (the app deliberately refuses to skip this check).
- Check the service logs for the actual error:
  `sudo journalctl -u ir-playbook-generator -n 100 --no-pager`.

**"Something went wrong generating the playbook" every time**
- Almost always a missing/invalid `ANTHROPIC_API_KEY`. Confirm it's
  set: `sudo systemctl show ir-playbook-generator --property=Environment`
  won't show the env-file contents directly (by design), so instead
  check the file itself is present and non-empty:
  `sudo test -s /etc/ir-playbook-generator/ir-playbook-generator.env && echo "file exists and is non-empty"`.
  If you suspect the key itself is wrong/expired, generate a new one
  at console.anthropic.com and update the env file (step E above),
  then `sudo systemctl restart ir-playbook-generator`.
- Check `sudo journalctl -u ir-playbook-generator -n 100 --no-pager`
  for the specific Anthropic exception class (the app logs the
  exception type, never the key or the organization profile text).

**Generating a playbook works but "My Playbooks" is empty or errors out**
- Almost always PostgreSQL being unreachable. Check it's running:
  `sudo systemctl status postgresql`. Check the app can actually
  connect with the configured role:
  `PGPASSWORD='...' psql -h localhost -U ir_playbook_app -d ir_playbook_db -c '\dt'`
  (run this manually with the real password, then clear your shell
  history of that command: `history -d $(history 1)` or simply don't
  leave the terminal open where others can scroll back).
- If tables are missing entirely, re-run step F above (`flask
  --app run.py init-db` as the service account) -- it's always
  safe to re-run.

**The service won't start / keeps restarting**
- `sudo systemctl status ir-playbook-generator` shows the last failure
  reason at a glance.
- `sudo journalctl -u ir-playbook-generator -n 100 --no-pager` shows
  the full Gunicorn/Flask startup log. Common causes: the venv path in
  the `.service` file doesn't match where you actually created it, the
  environment file path is wrong or unreadable by the service account
  (check with `sudo -u ir-playbook-app cat /etc/ir-playbook-generator/ir-playbook-generator.env`
  — it should succeed), or `SECRET_KEY`/`DB_PASSWORD` weren't actually
  set (the app will still start, since neither has a *crashing*
  default, but login or the database will then fail at request time).

**Nginx shows a 502 Bad Gateway**
- This means Nginx is running but Gunicorn isn't reachable behind it.
  Check Gunicorn/the service is actually up:
  `curl -s http://127.0.0.1:8000/healthz` from the Ubuntu server
  itself. If that fails, see "the service won't start" above. If that
  succeeds but the 502 persists, check
  `sudo nginx -t` for a config error and
  `sudo tail -n 50 /var/log/nginx/error.log`.

## Final end-to-end verification checklist

Run through this on the actual lab environment after a fresh
deployment (or after a reboot, to confirm persistence):

- [ ] `sudo reboot` the Ubuntu server, wait for it to come back, then
      confirm both services came up on their own with no manual
      intervention: `sudo systemctl is-active postgresql nginx ir-playbook-generator`
      (all three should print `active`).
- [ ] From another machine on the lab network, `curl -Ik
      https://ir-playbook.seniorproj25.local/` (or `http://` if HTTPS
      isn't enabled yet) returns a redirect to `/login`, not a
      connection error.
- [ ] If HTTPS is enabled: the browser shows a trusted padlock with no
      certificate warning, on a client that's domain-joined (or has
      the lab's Enterprise Root CA trusted some other way).
- [ ] Log in with a real AD account's username and password — success
      redirects to the homepage and shows that username.
- [ ] Log in with a wrong password — shows the generic "Invalid
      username or password" message, not a stack trace or a different
      error for valid-vs-invalid usernames.
- [ ] Generate a playbook (pick an incident type, describe an
      organization, click Generate) — a formatted playbook appears,
      referencing NIST SP 800-61 Rev. 3 / CSF 2.0.
- [ ] Open "My Playbooks" — the playbook just generated appears at the
      top of the list with the right incident type and timestamp.
- [ ] Click into it — the detail page shows the same incident type,
      the organization profile you typed, the creation time, and the
      full playbook content.
- [ ] Log out, then try to visit the homepage, the generator page, and
      "My Playbooks" directly by URL — each redirects to `/login`
      rather than showing any content.
- [ ] Log in as a **second** AD account and confirm "My Playbooks"
      shows an empty list (or only that second account's own
      playbooks) — never the first account's playbooks — and that
      manually visiting the first account's playbook detail URL
      returns a 404, not the playbook.
- [ ] `curl -s http://127.0.0.1:8000/healthz` (run directly on the
      Ubuntu server) returns `{"status":"ok"}`.

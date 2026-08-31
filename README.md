# Incident Response Playbook Generator

The app now has three pieces: a basic Flask site (Stage 1), Active
Directory login protecting it (Stage 2), and a PostgreSQL database for
storing generated playbooks (Stage 3, this update). There is still
**no** Claude API integration — that comes in a later stage. Nothing
generates playbooks yet; this stage only adds the place they'll be
stored.

## What's in this project so far

```
.
├── app/
│   ├── __init__.py            # Builds the Flask application
│   ├── config.py               # Reads AD/session/database settings from environment variables
│   ├── extensions.py            # The shared SQLAlchemy database object
│   ├── models.py                 # The Playbook database table
│   ├── commands.py                # The "flask init-db" command
│   ├── routes.py                   # The homepage ("/"), login-protected
│   ├── auth/
│   │   ├── __init__.py               # Marks auth/ as a Python package
│   │   ├── routes.py                  # /login and /logout pages
│   │   ├── ldap_client.py              # Checks a username/password against Active Directory
│   │   └── decorators.py                # @login_required, used to protect pages
│   ├── templates/
│   │   ├── index.html                # The homepage
│   │   └── login.html                 # The login form
│   └── static/
│       └── style.css                  # Styling for both pages
├── run.py                     # The file you run to start the server
├── requirements.txt           # List of Python packages this project needs
├── .env.example                # Documents the environment variables the app reads (no real secrets)
├── conftest.py                  # Lets pytest find the "app" package
├── tests/
│   ├── conftest.py               # Shared test setup (a test client, a test database)
│   ├── test_home.py               # Tests for the homepage/login redirect
│   ├── test_auth.py                # Tests for login/logout
│   └── test_models.py               # Tests for the Playbook database model
├── .github/workflows/ci.yml    # Runs the tests automatically on GitHub
├── .gitignore                   # Tells Git which files/folders to never track
└── README.md                     # This file
```

## How to run it (step by step)

These steps assume you are working in a terminal in this project's
folder, on a computer that already has Python 3 installed.

### 1. Create a virtual environment

A "virtual environment" is a private, isolated folder where Python
packages for this project get installed, so they don't clash with
anything else on your computer.

```bash
python3 -m venv venv
```

This creates a new folder called `venv/`. You will not need to open it
— Git already knows to ignore it (see `.gitignore`).

### 2. Activate the virtual environment

**On Linux or macOS:**
```bash
source venv/bin/activate
```

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

You'll know it worked because your terminal prompt will now start
with `(venv)`.

### 3. Install the required packages

```bash
pip install -r requirements.txt
```

This reads `requirements.txt` and installs Flask, pytest, ldap3,
Flask-SQLAlchemy, and psycopg2-binary (the PostgreSQL driver) into
your virtual environment.

### 4. Configure Active Directory settings (optional on this VM)

The app already defaults to this project's real values:
`AD_DOMAIN=seniorproj25.local`, `AD_SERVER_HOST=dc01.seniorproj25.local`,
`AD_LDAPS_PORT=636`. You only need to set environment variables if
you want to override one of those — see `.env.example` for the full
list and how to set a real `SECRET_KEY` for production use.

**Important:** logging in requires network access to
`dc01.seniorproj25.local` on port 636 (LDAPS), and that domain
controller's TLS certificate must be trusted by this machine's system
CA store (the same store `ca-certificates`/`update-ca-certificates`
manages on Ubuntu). On a laptop with no route to that domain
controller, login attempts will correctly fail — that's expected; use
`pytest` (see below) to verify the code without a real AD server.

### 5. Set up PostgreSQL and the database

This assumes PostgreSQL is already installed on the Ubuntu server
(`sudo apt install postgresql`). Create the application's database and
a dedicated, low-privilege role for the Flask app to connect as
(rather than using the powerful `postgres` superuser):

```bash
sudo -u postgres psql -c "CREATE ROLE ir_playbook_app WITH LOGIN PASSWORD 'choose-a-real-password-here';"
sudo -u postgres psql -c "CREATE DATABASE ir_playbook_db OWNER ir_playbook_app;"
```

Then tell the app that password by setting `DB_PASSWORD` as an
environment variable (never write it into a file that gets committed
to Git) — see `.env.example`. The database name (`ir_playbook_db`)
and app role (`ir_playbook_app`) already match the app's defaults, so
you don't need to set `DB_NAME` or `DB_USER` unless you chose
different values above.

```bash
export DB_PASSWORD='the-password-you-chose-above'
```

Now create the app's tables:

```bash
flask --app run.py init-db
```

This is safe to run again later — it only creates tables that don't
already exist yet, and never deletes or overwrites data.

### 6. Run the application

```bash
python run.py
```

You should see output that looks like:

```
 * Running on http://127.0.0.1:5000
```

### 7. View it in your browser

Open a web browser and go to:

```
http://127.0.0.1:5000
```

You'll be redirected to `/login` first. Signing in with a valid AD
username and password takes you to the homepage, which now shows who
you're logged in as and a "Log out" link.

To stop the server, go back to the terminal and press `Ctrl+C`.

### 8. Run the automated tests

```bash
python -m pytest
```

These tests never contact a real Active Directory server or a real
PostgreSQL database — login checks use a mocked (fake) version of the
AD check, and database tests run against a throwaway in-memory SQLite
database created fresh for each test. That means the full suite can
run anywhere, including in GitHub Actions, without needing a domain
controller or a PostgreSQL server available. This is also what the CI
workflow (`.github/workflows/ci.yml`) runs automatically on every push
and pull request targeting `main`.

## What each file does (plain English)

- **`run.py`** — The "start button" for the whole application.
- **`app/__init__.py`** — Builds the Flask app (the `create_app`
  factory): sets the session signing key, points SQLAlchemy at the
  database, connects the database extension, registers the models,
  registers the main page and the login/logout pages, and registers
  the `flask init-db` command. Accepts an optional `config_overrides`
  dictionary so the test suite can swap in a test database before the
  database connection is set up.
- **`app/config.py`** — Reads all the non-code settings (AD domain,
  domain controller hostname, LDAPS port, CA bundle path, session
  secret key, database host/port/name/user/password) from environment
  variables, with defaults matching this project's real environment.
  Nothing here is a hardcoded secret — see the note below.
- **`app/extensions.py`** — Creates the shared `db` (SQLAlchemy)
  object in its own file. This avoids a circular import: models.py
  needs to import `db` to define tables, and `__init__.py` needs to
  import models.py so those tables get registered.
- **`app/models.py`** — Defines the `Playbook` database table:
  `id`, `created_by_username` (the AD username of whoever generated
  it), `incident_type`, `organization_profile`, `content` (the
  generated playbook text), `created_at`, and `updated_at`
  (`updated_at` refreshes automatically whenever a row is edited).
- **`app/commands.py`** — Adds the `flask init-db` command, which
  creates any missing database tables. It's deliberately a manual,
  explicit step rather than something that runs automatically every
  time the app starts, so table creation never happens as a surprise
  side effect of just running the server.
- **`app/routes.py`** — The homepage (`/`). Decorated with
  `@login_required`, so it can't be viewed without logging in first.
- **`app/auth/ldap_client.py`** — The only file that actually talks to
  Active Directory. It opens an LDAPS (LDAP-over-TLS) connection to
  the domain controller and attempts to log in *as the user* with the
  username/password they typed — this is called a "direct bind." If
  Active Directory accepts it, the credentials are correct; if not,
  the function just says so. No password is ever written to disk or
  logged.
- **`app/auth/routes.py`** — The `/login` and `/logout` pages. On a
  successful login, it stores the username in the session (a signed
  cookie) and sends the user on to whichever page they originally
  wanted. On failure, it shows a generic "Invalid username or
  password" message — deliberately generic, so it doesn't help an
  attacker figure out whether a given username exists.
- **`app/auth/decorators.py`** — Defines `@login_required`, a
  reusable guard you can put on any route that should require login.
- **`app/templates/login.html`** — The login form.
- **`app/templates/index.html`** — The homepage, showing the
  logged-in username and a logout link.
- **`app/static/style.css`** — Styling shared by both pages.
- **`.env.example`** — Documents every environment variable the app
  reads, with safe placeholder/default values. It is committed to Git
  on purpose (it holds no real secrets); a real `.env` file, if you
  create one, is excluded by `.gitignore`.
- **`conftest.py`** (project root) — An empty file that helps pytest
  find the `app` package no matter how it's run.
- **`tests/conftest.py`** — Shared test setup: builds a test copy of
  the Flask app (pointed at an in-memory SQLite database instead of
  real PostgreSQL) and a test client that tests can use to make fake
  requests. Creates the database tables before each test and drops
  them afterward, so every test starts from a clean, empty database.
- **`tests/test_home.py`** — Confirms the homepage redirects to login
  when nobody's signed in, and loads normally once they are.
- **`tests/test_auth.py`** — Confirms the login page loads, that a
  valid login sets the session and redirects, that an invalid login
  shows an error, and that logout clears the session.
- **`tests/test_models.py`** — Confirms a `Playbook` row can be saved
  and read back with all its fields intact, and that `updated_at`
  advances when a saved playbook is later edited.
- **`requirements.txt`** — The exact list of Python packages this
  project depends on: Flask (web framework), pytest (testing), ldap3
  (talks to Active Directory), Flask-SQLAlchemy (database models),
  and psycopg2-binary (the PostgreSQL driver).
- **`.gitignore`** — Tells Git which files/folders to never commit,
  such as the `venv/` folder, `.pytest_cache/`, and any real `.env`
  file containing secrets.
- **`.github/workflows/ci.yml`** — Runs `pytest` automatically on
  GitHub every time code is pushed to `main` or a pull request targets
  `main`.

## A note on secrets

This project never hardcodes a password, API key, or session secret
in the code. The "secrets" the app relies on — `SECRET_KEY` (signs
session cookies) and `DB_PASSWORD` (the PostgreSQL app role's
password) — are both read from environment variables and have no
hardcoded default. If `SECRET_KEY` isn't set, a temporary one is
generated automatically each time you run the app (fine for local
testing, but it means everyone gets logged out if you restart the
app; set a real one for anything beyond local testing). `DB_PASSWORD`
has no fallback at all — without it, the app will simply fail to
connect to PostgreSQL, which is the correct, safe failure mode rather
than silently trying a blank or guessable password. Your actual AD
password is never stored anywhere either — it's used once, in memory,
to attempt the LDAPS login, and then discarded.

## What's coming in later stages

1. Claude API integration (to actually generate playbooks and save
   them into the `playbooks` table added in this stage)
2. Deployment onto the Ubuntu Server VM

We will tackle these one at a time, in separate steps.

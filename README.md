# Incident Response Playbook Generator

The app now has two pieces: a basic Flask site (Stage 1) and Active
Directory login protecting it (Stage 2, this update). There is still
**no** database and **no** Claude API integration — those come in
later stages.

## What's in this project so far

```
.
├── app/
│   ├── __init__.py            # Builds the Flask application
│   ├── config.py               # Reads AD/session settings from environment variables
│   ├── routes.py                # The homepage ("/"), now login-protected
│   ├── auth/
│   │   ├── __init__.py           # Marks auth/ as a Python package
│   │   ├── routes.py              # /login and /logout pages
│   │   ├── ldap_client.py          # Checks a username/password against Active Directory
│   │   └── decorators.py            # @login_required, used to protect pages
│   ├── templates/
│   │   ├── index.html            # The homepage
│   │   └── login.html             # The login form
│   └── static/
│       └── style.css              # Styling for both pages
├── run.py                     # The file you run to start the server
├── requirements.txt           # List of Python packages this project needs
├── .env.example                # Documents the environment variables the app reads (no real secrets)
├── conftest.py                  # Lets pytest find the "app" package
├── tests/
│   ├── conftest.py               # Shared test setup (a test client, etc.)
│   ├── test_home.py               # Tests for the homepage/login redirect
│   └── test_auth.py                # Tests for login/logout
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

This reads `requirements.txt` and installs Flask, pytest, and ldap3
into your virtual environment.

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
`pytest` (next section) to verify the code without a real AD server.

### 5. Run the application

```bash
python run.py
```

You should see output that looks like:

```
 * Running on http://127.0.0.1:5000
```

### 6. View it in your browser

Open a web browser and go to:

```
http://127.0.0.1:5000
```

You'll be redirected to `/login` first. Signing in with a valid AD
username and password takes you to the homepage, which now shows who
you're logged in as and a "Log out" link.

To stop the server, go back to the terminal and press `Ctrl+C`.

### 7. Run the automated tests

```bash
python -m pytest
```

These tests never contact a real Active Directory server — they use a
mocked (fake) version of the login check so they can run anywhere,
including in GitHub Actions. This is also what the CI workflow
(`.github/workflows/ci.yml`) runs automatically on every push and
pull request targeting `main`.

## What each file does (plain English)

- **`run.py`** — The "start button" for the whole application.
- **`app/__init__.py`** — Builds the Flask app (the `create_app`
  factory), sets the session signing key, and registers both the
  main page and the login/logout pages.
- **`app/config.py`** — Reads all the non-code settings (AD domain,
  domain controller hostname, LDAPS port, CA bundle path, session
  secret key) from environment variables, with defaults matching this
  project's real AD environment. Nothing here is a hardcoded secret —
  see the `SECRET_KEY` note below.
- **`app/routes.py`** — The homepage (`/`). Now decorated with
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
- **`app/templates/index.html`** — The homepage, now showing the
  logged-in username and a logout link.
- **`app/static/style.css`** — Styling shared by both pages.
- **`.env.example`** — Documents every environment variable the app
  reads, with safe placeholder/default values. It is committed to Git
  on purpose (it holds no real secrets); a real `.env` file, if you
  create one, is excluded by `.gitignore`.
- **`conftest.py`** (project root) — An empty file that helps pytest
  find the `app` package no matter how it's run.
- **`tests/conftest.py`** — Shared test setup: builds a test copy of
  the Flask app and a test client that tests can use to make fake
  requests.
- **`tests/test_home.py`** — Confirms the homepage redirects to login
  when nobody's signed in, and loads normally once they are.
- **`tests/test_auth.py`** — Confirms the login page loads, that a
  valid login sets the session and redirects, that an invalid login
  shows an error, and that logout clears the session.
- **`requirements.txt`** — The exact list of Python packages this
  project depends on: Flask (web framework), pytest (testing), and
  ldap3 (talks to Active Directory over LDAP/LDAPS).
- **`.gitignore`** — Tells Git which files/folders to never commit,
  such as the `venv/` folder, `.pytest_cache/`, and any real `.env`
  file containing secrets.
- **`.github/workflows/ci.yml`** — Runs `pytest` automatically on
  GitHub every time code is pushed to `main` or a pull request targets
  `main`.

## A note on secrets

This project never hardcodes a password, API key, or session secret
in the code. The only "secret" the app itself holds is `SECRET_KEY`
(used to sign session cookies), and even that is read from an
environment variable — if you don't set one, a temporary one is
generated automatically each time you run the app (fine for local
testing, but it means everyone gets logged out if you restart the
app; set a real `SECRET_KEY` for anything beyond local testing). Your
actual AD password is never stored anywhere — it's used once, in
memory, to attempt the LDAPS login, and then discarded.

## What's coming in later stages

1. PostgreSQL database setup (for storing generated playbooks)
2. Claude API integration (to actually generate playbooks)
3. Deployment onto the Ubuntu Server VM

We will tackle these one at a time, in separate steps.

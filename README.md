# Incident Response Playbook Generator

The app now has five pieces: a basic Flask site (Stage 1), Active
Directory login protecting it (Stage 2), a PostgreSQL database
(Stage 3), AI-generated playbooks using the Claude API (Stage 4), and
saved playbook history (Stage 5, this update). A logged-in user can
pick an incident type, describe their organization, generate a
NIST-aligned draft playbook, and it's now automatically saved to
PostgreSQL under their username — visible on a "My Playbooks" page
that only ever shows that user's own playbooks.

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
│   ├── playbooks/
│   │   ├── __init__.py               # Marks playbooks/ as a Python package
│   │   ├── routes.py                  # /playbooks/generate page
│   │   ├── claude_client.py            # Calls the Anthropic Claude API
│   │   ├── prompts.py                   # Builds the system/user prompts, lists incident types
│   │   └── rendering.py                  # Safely converts Claude's Markdown reply to HTML
│   ├── templates/
│   │   ├── index.html                # The homepage
│   │   ├── login.html                 # The login form
│   │   └── playbooks/
│   │       ├── generate.html            # The playbook generator form + result
│   │       ├── history.html              # "My Playbooks" -- this user's saved playbooks
│   │       └── detail.html                # A single saved playbook
│   └── static/
│       └── style.css                  # Styling for all pages
├── run.py                     # The file you run to start the server
├── requirements.txt           # List of Python packages this project needs
├── .env.example                # Documents the environment variables the app reads (no real secrets)
├── conftest.py                  # Lets pytest find the "app" package
├── tests/
│   ├── conftest.py               # Shared test setup (a test client, a test database)
│   ├── test_home.py               # Tests for the homepage/login redirect
│   ├── test_auth.py                # Tests for login/logout
│   ├── test_models.py               # Tests for the Playbook database model
│   ├── test_playbooks.py             # Tests for the playbook generator page (incl. saving)
│   └── test_playbook_history.py       # Tests for "My Playbooks" and the detail page
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
Flask-SQLAlchemy, psycopg2-binary (the PostgreSQL driver), anthropic
(the Claude API SDK), and Markdown + bleach (used to safely display
generated playbooks) into your virtual environment.

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

### 6. Configure the Claude API (for the playbook generator)

The playbook generator page needs an Anthropic API key. Get one from
[console.anthropic.com](https://console.anthropic.com/) and set it as
an environment variable — never write it into a file that gets
committed to Git:

```bash
export ANTHROPIC_API_KEY='your-real-api-key-here'
```

That's the only required setting. `ANTHROPIC_MODEL` is optional and
defaults to `claude-sonnet-5`; set it only if you want to use a
different model:

```bash
export ANTHROPIC_MODEL='claude-sonnet-5'
```

If `ANTHROPIC_API_KEY` isn't set, the rest of the app (login, the
homepage, the database) still works completely normally — only the
"Generate Playbook" button shows a friendly "not configured yet"
message instead of an error page.

### 7. Run the application

```bash
python run.py
```

You should see output that looks like:

```
 * Running on http://127.0.0.1:5000
```

### 8. View it in your browser

Open a web browser and go to:

```
http://127.0.0.1:5000
```

You'll be redirected to `/login` first. Signing in with a valid AD
username and password takes you to the homepage, which now shows who
you're logged in as, a "Log out" link, and links to **Generate an
Incident Response Playbook** and **My Playbooks**. The generator page
lets you pick an incident type (Ransomware, Business Email
Compromise, or Data Exfiltration), describe the organization, and
click **Generate Playbook** to get a draft playbook back from Claude
-- which is now automatically saved. **My Playbooks** lists every
playbook *you've* generated (never anyone else's), newest first;
clicking one opens a detail page showing the incident type,
organization profile, creation time, and the full generated playbook.

To stop the server, go back to the terminal and press `Ctrl+C`.

### 9. Run the automated tests

```bash
python -m pytest
```

These tests never contact a real Active Directory server, a real
PostgreSQL database, or the real Claude API — login checks use a
mocked (fake) version of the AD check, database tests run against a
throwaway in-memory SQLite database created fresh for each test, and
playbook-generation tests mock the Claude API call entirely. That
means the full suite can run anywhere, including in GitHub Actions,
without needing a domain controller, a PostgreSQL server, or a real
`ANTHROPIC_API_KEY` available. This is also what the CI workflow
(`.github/workflows/ci.yml`) runs automatically on every push and pull
request targeting `main`.

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
  secret key, database host/port/name/user/password, Anthropic API
  key/model) from environment variables, with defaults matching this
  project's real environment. Nothing here is a hardcoded secret — see
  the note below.
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
- **`app/playbooks/routes.py`** — Three pages, all protected by
  `@login_required`:
  - `/playbooks/generate` — on GET, shows the form; on POST,
    re-validates the submitted incident type and organization profile
    on the server (never trusting that the browser enforced them),
    calls the Claude client, and **only on success** saves a new
    `Playbook` row (username, incident type, organization profile,
    generated content) before converting the result to safe HTML and
    re-rendering the page. A validation failure or a Claude API
    failure never touches the database.
  - `/playbooks/history` ("My Playbooks") — queries `Playbook` rows
    filtered to `created_by_username == <the logged-in user>`, newest
    first. There is no way to pass in a different username; it always
    comes from the session, never from the request.
  - `/playbooks/history/<id>` (the detail page) — looks up a playbook
    by *both* its ID and `created_by_username` in the same query. If
    the ID doesn't exist, or exists but belongs to someone else, the
    query returns nothing either way and the route responds with the
    same generic 404 -- nothing in the response reveals which case it
    was, so it can't be used to confirm whether another user has a
    playbook with that ID.
- **`app/playbooks/claude_client.py`** — The only file that talks to
  the Anthropic API. Builds the request with the Anthropic Python SDK
  (`anthropic.Anthropic(...).messages.create(...)`), using the API key
  and model from `app/config.py`. Raises `ClaudeNotConfiguredError` if
  no API key is set, or `ClaudeGenerationError` for any API/network
  failure — both are caught by `routes.py` and turned into a friendly
  message, never a stack trace. The model's response is only ever
  treated as text to display; nothing it returns is executed.
- **`app/playbooks/prompts.py`** — Defines the three allowed incident
  types (Ransomware, Business Email Compromise, Data Exfiltration),
  the maximum organization-profile length, and the system/user prompt
  text sent to Claude. The system prompt tells Claude to align the
  playbook with NIST SP 800-61 Rev. 3 and the NIST Cybersecurity
  Framework 2.0 (explicitly *not* the outdated Rev. 2), and explicitly
  instructs it to treat the organization profile as untrusted
  descriptive text only — never as instructions that could override
  the system prompt.
- **`app/playbooks/rendering.py`** — Converts Claude's Markdown
  response into HTML for display. The conversion always goes through
  an allowlist sanitizer (`bleach`) afterward, which strips anything
  not on a small list of safe formatting tags (headings, lists,
  paragraphs, tables, etc.) — so even if a model response contained
  raw `<script>` tags or similar, none of it can reach the page as
  live HTML.
- **`app/templates/login.html`** — The login form.
- **`app/templates/index.html`** — The homepage, showing the
  logged-in username, a logout link, and links to the playbook
  generator and "My Playbooks."
- **`app/templates/playbooks/generate.html`** — The playbook generator
  form (incident type dropdown, organization profile textarea,
  "Generate Playbook" button) and, once generated, the playbook itself
  rendered below it, with a note confirming it was saved.
- **`app/templates/playbooks/history.html`** — "My Playbooks": a table
  of the logged-in user's saved playbooks (incident type, created
  date/time), each linking to its detail page, or a friendly empty
  state if they haven't generated any yet.
- **`app/templates/playbooks/detail.html`** — One saved playbook:
  incident type, organization profile (shown as plain escaped text,
  not interpreted as Markdown -- it's the user's own raw input, not a
  Claude response), creation date/time, and the generated playbook
  content, re-rendered through the same safe Markdown pipeline used on
  the generator page.
- **`app/static/style.css`** — Styling shared by all pages.
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
- **`tests/test_playbooks.py`** — Confirms the generator page requires
  login; rejects an invalid incident type, an empty organization
  profile, and an overly long one (and that none of those save a
  database row); shows a friendly message when no API key is
  configured (using the real "not configured" code path, since no
  real key is present in this test environment either, and that this
  doesn't save a row); renders a mocked Claude response as safe HTML
  *and* confirms it was saved with the correct username/incident
  type/profile/content; shows a generic error message (never the
  underlying exception detail, and no row saved) when the Claude call
  fails; and confirms unsafe HTML (like a `<script>` tag) never
  survives the rendering step.
- **`tests/test_playbook_history.py`** — Confirms both "My Playbooks"
  and the detail page require login; that the history page shows one
  user's playbooks but never another user's (two users' playbooks are
  seeded directly in the test database, then checked from one user's
  logged-in session); that a user can open their own playbook's detail
  page and see the right content; that requesting another user's
  playbook ID returns a 404 without leaking that user's data anywhere
  in the response; and that a nonexistent ID also returns a 404.
- **`requirements.txt`** — The exact list of Python packages this
  project depends on: Flask (web framework), pytest (testing), ldap3
  (talks to Active Directory), Flask-SQLAlchemy (database models),
  psycopg2-binary (the PostgreSQL driver), anthropic (the Claude API
  SDK), and Markdown + bleach (safely render generated playbooks).
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
defaults to an empty string rather than a guessable value — without a
real one set, PostgreSQL will simply reject the connection, which is
the correct, safe failure mode. Your actual AD password is never
stored anywhere either — it's used once, in memory, to attempt the
LDAPS login, and then discarded.

`ANTHROPIC_API_KEY` follows the same pattern: it's read only from the
environment, has no default at all, and is never written to a log —
if it's missing, the app checks for that explicitly and shows a
friendly message rather than letting a missing-key error escape as a
raw exception.

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

## What's coming in later stages

1. Deployment onto the Ubuntu Server VM

We will tackle these one at a time, in separate steps.

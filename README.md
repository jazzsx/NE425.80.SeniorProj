# Incident Response Playbook Generator — Stage 1: Basic Flask App

This is the very first stage of the project. All it does right now is
prove that a Flask web application can start up and show a homepage.
There is **no** Active Directory login, **no** database, and **no**
Claude API integration yet — those come in later stages.

## What's in this project so far

```
.
├── app/
│   ├── __init__.py       # Builds the Flask application
│   ├── routes.py         # Defines the homepage web address ("/")
│   ├── templates/
│   │   └── index.html    # The HTML shown on the homepage
│   └── static/
│       └── style.css     # Basic styling for the homepage
├── run.py                # The file you run to start the server
├── requirements.txt      # List of Python packages this project needs
├── .gitignore             # Tells Git which files/folders to never track
└── README.md              # This file
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

This reads `requirements.txt` and installs Flask (the web framework)
into your virtual environment.

### 4. Run the application

```bash
python run.py
```

You should see output that looks like:

```
 * Running on http://127.0.0.1:5000
```

### 5. View it in your browser

Open a web browser and go to:

```
http://127.0.0.1:5000
```

You should see a dark page that says **"Incident Response Playbook
Generator"** and confirms the Flask application is running.

To stop the server, go back to the terminal and press `Ctrl+C`.

## What each file does (plain English)

- **`run.py`** — The "start button" for the whole application. You run
  this file, and it launches a small web server on your computer.
- **`app/__init__.py`** — Contains the code that actually builds the
  Flask application. It's written as a function (`create_app`) so
  that later stages (database, login, etc.) can be added cleanly.
- **`app/routes.py`** — Defines what web addresses ("routes") exist and
  what happens when someone visits them. Right now there's only one:
  the homepage (`/`).
- **`app/templates/index.html`** — The actual HTML page a visitor sees.
  Flask's `render_template` function reads files from this
  `templates` folder.
- **`app/static/style.css`** — CSS styling (colors, spacing, fonts) for
  the homepage. Files in `static/` are served as-is, unlike templates.
- **`requirements.txt`** — A plain list of Python packages this project
  depends on, so anyone (or any server) can install the exact same
  setup with one command.
- **`.gitignore`** — Tells Git which files/folders to never commit,
  such as the `venv/` folder and any future `.env` file containing
  secrets.

## What's coming in later stages

1. PostgreSQL database setup (for storing generated playbooks)
2. Active Directory authentication (login against the Windows Server)
3. Claude API integration (to actually generate playbooks)
4. Deployment onto the Ubuntu Server VM

We will tackle these one at a time, in separate steps.

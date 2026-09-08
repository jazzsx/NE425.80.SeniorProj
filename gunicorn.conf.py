"""
Gunicorn configuration for running this app in production.

Usage (from the project's root directory, inside its virtual
environment):

    gunicorn -c gunicorn.conf.py run:app

"run:app" points Gunicorn at the "app" object that run.py already
builds via create_app() -- no separate WSGI entry point is needed.
Gunicorn importing run.py never triggers its "if __name__ ==
'__main__'" block, so this never starts Flask's own development
server; Gunicorn is the only thing serving requests.

In production this is meant to be launched by the systemd service in
deploy/systemd/ir-playbook-generator.service, not run by hand.
"""

import multiprocessing

# Only listen on localhost. Nginx (see deploy/nginx/) is the only
# thing that should ever talk to Gunicorn directly -- it's never
# exposed to the LAN on its own.
bind = "127.0.0.1:8000"
timeout = 120
# A common, conservative starting point: enough worker processes to
# use the available CPU cores without over-committing memory on a lab
# VM. Adjust based on the VM's actual CPU count and observed load.
workers = multiprocessing.cpu_count() * 2 + 1

# Restarting a worker occasionally guards against slow memory leaks in
# long-running processes; a few hundred requests of jitter avoids all
# workers restarting at the same moment.
max_requests = 500
max_requests_jitter = 50

# Log to stdout/stderr rather than files -- systemd/journald captures
# both automatically (see the .service unit), which is simpler to
# manage than rotating log files by hand on a lab VM.
accesslog = "-"
errorlog = "-"

# Gunicorn's access log records the request line, status, and timing
# -- never headers or the POST body, so login/API-key form fields are
# never written here. Nothing in this file should ever be changed to
# log request bodies or headers.

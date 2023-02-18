import os

import waitress

from flask import Flask

# Server arguments:
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = os.environ.get("PORT", "80")
SERVER_THREADS = os.environ.get("SERVER_THREADS", "8")
SERVER_IDENTITY = os.environ.get("SERVER_IDENTITY", "basaran")
SERVER_CONNECTION_LIMIT = os.environ.get("SERVER_CONNECTION_LIMIT", "1024")
SERVER_CHANNEL_TIMEOUT = os.environ.get("SERVER_CHANNEL_TIMEOUT", "300")


# Create and configure application.
app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
app.json.compact = True


# Start serving the WSGI application.
if __name__ == "__main__":
    waitress.serve(
        app,
        host=HOST,
        port=int(PORT),
        threads=int(SERVER_THREADS),
        ident=SERVER_IDENTITY,
        connection_limit=int(SERVER_CONNECTION_LIMIT),
        channel_timeout=int(SERVER_CHANNEL_TIMEOUT),
    )

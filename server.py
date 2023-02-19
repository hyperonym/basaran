import os

import waitress

from flask import Flask, abort, jsonify

MODEL = os.environ.get("MODEL", "bigscience/bloomz-7b1-mt")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = os.environ.get("PORT", "80")

# Server arguments:
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
SERVER_THREADS = os.environ.get("SERVER_THREADS", "8")
SERVER_IDENTITY = os.environ.get("SERVER_IDENTITY", "basaran")
SERVER_CONNECTION_LIMIT = os.environ.get("SERVER_CONNECTION_LIMIT", "1024")
SERVER_CHANNEL_TIMEOUT = os.environ.get("SERVER_CHANNEL_TIMEOUT", "300")
SERVER_MODEL_NAME = os.environ.get("SERVER_MODEL_NAME", MODEL)


# Create and configure application.
app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
app.json.compact = True
app.url_map.strict_slashes = False


@app.route("/v1/models")
def list_models():
    info = {"id": SERVER_MODEL_NAME, "object": "model"}
    return jsonify(data=[info], object="list")


@app.route("/v1/models/<path:name>")
def retrieve_model(name):
    if name != SERVER_MODEL_NAME:
        abort(404, description="model does not exist")
    return jsonify(id=SERVER_MODEL_NAME, object="model")


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=e.description), 400


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=e.description), 404


@app.errorhandler(500)
def internal_server_error(_):
    return jsonify(error="internal_server_error"), 500


# Start serving the WSGI application.
if __name__ == "__main__":
    print(f"start listening on {HOST}:{PORT}")
    waitress.serve(
        app,
        host=HOST,
        port=int(PORT),
        threads=int(SERVER_THREADS),
        ident=SERVER_IDENTITY,
        connection_limit=int(SERVER_CONNECTION_LIMIT),
        channel_timeout=int(SERVER_CHANNEL_TIMEOUT),
    )

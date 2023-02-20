import os
import sys

import waitress

from flask import Flask, abort, jsonify

from model import download_snapshot, load_model


MODEL = os.environ.get("MODEL", "bigscience/bloomz-560m")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = os.environ.get("PORT", "80")

# Model arguments:
MODEL_CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", "models")
MODEL_LOAD_IN_8BIT = os.environ.get("MODEL_LOAD_IN_8BIT", "false")
MODEL_LOCAL_FILES_ONLY = os.environ.get("MODEL_LOCAL_FILES_ONLY", "false")

# Server arguments:
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
SERVER_THREADS = os.environ.get("SERVER_THREADS", "8")
SERVER_IDENTITY = os.environ.get("SERVER_IDENTITY", "basaran")
SERVER_CONNECTION_LIMIT = os.environ.get("SERVER_CONNECTION_LIMIT", "1024")
SERVER_CHANNEL_TIMEOUT = os.environ.get("SERVER_CHANNEL_TIMEOUT", "300")
SERVER_MODEL_NAME = os.environ.get("SERVER_MODEL_NAME", "") or MODEL


# Load model from local files or download from Hugging Face Hub.
if __name__ == "__main__":
    local_files_only = MODEL_LOCAL_FILES_ONLY.lower() in ("1", "true")
    load_in_8bit = MODEL_LOAD_IN_8BIT.lower() in ("1", "true")
    if not os.path.isdir(MODEL) and not local_files_only:
        download_snapshot(MODEL, MODEL_CACHE_DIR)
    # Use the --download-only argument to download a model without loading
    # into memory. This allows CI/CD runners with limited memory to build
    # container images with bundled models.
    if "--download-only" in sys.argv[1:]:
        sys.exit(0)
    model = load_model(MODEL, MODEL_CACHE_DIR, load_in_8bit)


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
    return jsonify(error="internal server error"), 500


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

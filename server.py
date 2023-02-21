import choice
import json
import os
import secrets
import sys
import time
import waitress

from flask import Flask, Response, abort, jsonify, request
from model import download_snapshot, load_model


MODEL = os.environ.get("MODEL", "bigscience/bloomz-560m")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "80"))

# Model arguments:
MODEL_CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", "models")
MODEL_LOAD_IN_8BIT = os.environ.get("MODEL_LOAD_IN_8BIT", "false")
MODEL_LOCAL_FILES_ONLY = os.environ.get("MODEL_LOCAL_FILES_ONLY", "false")

# Server arguments:
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
SERVER_THREADS = int(os.environ.get("SERVER_THREADS", "8"))
SERVER_IDENTITY = os.environ.get("SERVER_IDENTITY", "basaran")
SERVER_CONNECTION_LIMIT = int(os.environ.get("SERVER_CONNECTION_LIMIT", "512"))
SERVER_CHANNEL_TIMEOUT = int(os.environ.get("SERVER_CHANNEL_TIMEOUT", "300"))
SERVER_MODEL_NAME = os.environ.get("SERVER_MODEL_NAME", "") or MODEL

# Completion arguments:
COMPLETION_MAX_PROMPT_LENGTH = int(
    os.environ.get("COMPLETION_MAX_PROMPT_LENGTH", "4096")
)
COMPLETION_MAX_TOKENS = int(os.environ.get("COMPLETION_MAX_TOKENS", "4096"))
COMPLETION_MAX_N = int(os.environ.get("COMPLETION_MAX_N", "5"))
COMPLETION_MAX_LOGPROBS = int(os.environ.get("COMPLETION_MAX_LOGPROBS", "5"))
COMPLETION_MAX_STREAM_INTERVAL_MS = int(
    os.environ.get("COMPLETION_MAX_STREAM_INTERVAL_MS", "100")
)


def str_to_bool(v):
    """Convert from string to boolean."""
    return str(v).lower() in ("yes", "true", "t", "1")


def parse_options(schema):
    """Parse options in the request body and query parameters."""
    options = {}
    payload = request.get_json(silent=True)
    for key, dtype in schema.items():
        if dtype == float:
            dtypes = (int, float)
        else:
            dtypes = (dtype,)
        if dtype == bool:
            dtype_fn = str_to_bool
        else:
            dtype_fn = dtype
        if key in request.args:
            options[key] = request.args.get(key, dtype(), type=dtype_fn)
        elif payload and key in payload and isinstance(payload[key], dtypes):
            options[key] = dtype(payload[key])
    return options


# Load model from local files or download from Hugging Face Hub.
if __name__ == "__main__":
    local_files_only = str_to_bool(MODEL_LOCAL_FILES_ONLY)
    load_in_8bit = str_to_bool(MODEL_LOAD_IN_8BIT)
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


@app.route("/v1/completions", methods=["GET", "POST"])
def create_completion():
    schema = {
        "prompt": str,
        "min_tokens": int,
        "max_tokens": int,
        "temperature": float,
        "top_p": int,
        "n": int,
        "stream": bool,
        "logprobs": int,
        "echo": bool,
    }
    options = parse_options(schema)
    if "prompt" not in options:
        options["prompt"] = ""

    # Limit maximum resource usage.
    if len(options["prompt"]) > COMPLETION_MAX_PROMPT_LENGTH:
        options["prompt"] = options["prompt"][:COMPLETION_MAX_PROMPT_LENGTH]
    if options.get("min_tokens", 0) > COMPLETION_MAX_TOKENS:
        options["min_tokens"] = COMPLETION_MAX_TOKENS
    if options.get("max_tokens", 0) > COMPLETION_MAX_TOKENS:
        options["max_tokens"] = COMPLETION_MAX_TOKENS
    if options.get("n", 0) > COMPLETION_MAX_N:
        options["n"] = COMPLETION_MAX_N
    if options.get("logprobs", 0) > COMPLETION_MAX_LOGPROBS:
        options["logprobs"] = COMPLETION_MAX_LOGPROBS

    # Create response body template.
    template = {
        "id": f"cmpl-{secrets.token_hex(12)}",
        "object": "text_completion",
        "created": round(time.time()),
        "model": SERVER_MODEL_NAME,
        "choices": [],
    }

    # Return in event stream or plain JSON.
    stream = options.pop("stream", False)
    if stream:
        return create_completion_stream(options, template)
    else:
        return create_completion_json(options, template)


def create_completion_stream(options, template):
    # Format message for event stream.
    def format(data):
        data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"data: {data}\n\n"

    def stream():
        n_buffer = {}
        n_time = {}
        for c in model(**options):
            now = time.time_ns()
            index = c["index"]
            if index not in n_buffer:
                n_buffer[index] = []
            if index not in n_time:
                n_time[index] = now
            n_buffer[index].append(c)

            # Yield data when exceeded the buffering interval.
            elapsed = (now - n_time[index]) // 1_000_000
            if elapsed > COMPLETION_MAX_STREAM_INTERVAL_MS:
                data = template.copy()
                data["choices"] = [choice.reduce(n_buffer[index])]
                yield format(data)
                n_buffer[index] = []
                n_time[index] = now

        # Yield remaining data in the buffers.
        for _, buffer in n_buffer.items():
            if buffer:
                data = template.copy()
                data["choices"] = [choice.reduce(buffer)]
                yield format(data)

        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream")


def create_completion_json(options, template):
    # Tokenize the prompt before passing to the model to count token usage.
    options["prompt"] = model.tokenize(options["prompt"])
    prompt_tokens = options["prompt"].shape[-1]
    completion_tokens = 0

    # Add data to the corresponding buffer according to index.
    n_buffer = {}
    for c in model(**options):
        completion_tokens += 1
        index = c["index"]
        if index not in n_buffer:
            n_buffer[index] = []
        n_buffer[index].append(c)

    # Merge choices with the same index.
    data = template.copy()
    for _, buffer in n_buffer.items():
        if buffer:
            data["choices"].append(choice.reduce(buffer))

    # Include token usage info.
    data["usage"] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }

    return jsonify(data)


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
        port=PORT,
        threads=SERVER_THREADS,
        ident=SERVER_IDENTITY,
        connection_limit=SERVER_CONNECTION_LIMIT,
        channel_timeout=SERVER_CHANNEL_TIMEOUT,
    )

"""
Basaran API server.
"""
import json
import secrets
import time

import waitress
from flask import Flask, Response, abort, jsonify, render_template, request

from . import is_true
from .choice import reduce_choice
from .model import load_model

# Configurations from environment variables.
from . import MODEL
from . import HOST
from . import PORT
from . import MODEL_REVISION
from . import MODEL_CACHE_DIR
from . import MODEL_LOAD_IN_8BIT
from . import MODEL_LOCAL_FILES_ONLY
from . import MODEL_TRUST_REMOTE_CODE
from . import MODEL_HALF_PRECISION
from . import SERVER_THREADS
from . import SERVER_IDENTITY
from . import SERVER_CONNECTION_LIMIT
from . import SERVER_CHANNEL_TIMEOUT
from . import SERVER_MODEL_NAME
from . import SERVER_NO_PLAYGROUND
from . import COMPLETION_MAX_PROMPT
from . import COMPLETION_MAX_TOKENS
from . import COMPLETION_MAX_N
from . import COMPLETION_MAX_LOGPROBS
from . import COMPLETION_MAX_INTERVAL

# Load the language model to be served.
stream_model = load_model(
    name_or_path=MODEL,
    revision=MODEL_REVISION,
    cache_dir=MODEL_CACHE_DIR,
    load_in_8bit=MODEL_LOAD_IN_8BIT,
    local_files_only=MODEL_LOCAL_FILES_ONLY,
    trust_remote_code=MODEL_TRUST_REMOTE_CODE,
    half_precision=MODEL_HALF_PRECISION,
)

# Create and configure application.
app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
app.json.compact = True
app.url_map.strict_slashes = False


def parse_options(schema):
    """Parse options specified in query parameters and request body."""
    options = {}
    payload = request.get_json(silent=True)
    for key, dtype in schema.items():
        # Allow casting from int to float.
        if dtype == float:
            dtypes = (int, float)
        else:
            dtypes = (dtype,)

        # Use custom function to convert string to bool correctly.
        if dtype == bool:
            dtype_fn = is_true
        else:
            dtype_fn = dtype

        # If an option appears in both the query parameters and the request
        # body, the former takes precedence.
        if key in request.args:
            options[key] = request.args.get(key, dtype(), type=dtype_fn)
        elif payload and key in payload and isinstance(payload[key], dtypes):
            options[key] = dtype(payload[key])

    return options


@app.route("/")
def render_playground():
    """Render model playground."""
    if SERVER_NO_PLAYGROUND:
        abort(404)
    return render_template("playground.html", model=SERVER_MODEL_NAME)


@app.route("/v1/models")
def list_models():
    """List the currently available models."""
    info = {"id": SERVER_MODEL_NAME, "object": "model"}
    return jsonify(data=[info], object="list")


@app.route("/v1/models/<path:name>")
def retrieve_model(name):
    """Retrieve basic information about the model."""
    if name != SERVER_MODEL_NAME:
        abort(404, description="model does not exist")
    return jsonify(id=SERVER_MODEL_NAME, object="model")


@app.route("/v1/completions", methods=["GET", "POST"])
def create_completion():
    """Create a completion for the provided prompt and parameters."""
    schema = {
        "prompt": str,
        "min_tokens": int,
        "max_tokens": int,
        "temperature": float,
        "top_p": float,
        "n": int,
        "stream": bool,
        "logprobs": int,
        "echo": bool,
    }
    options = parse_options(schema)
    if "prompt" not in options:
        options["prompt"] = ""

    # Limit maximum resource usage.
    if len(options["prompt"]) > COMPLETION_MAX_PROMPT:
        options["prompt"] = options["prompt"][:COMPLETION_MAX_PROMPT]
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
    if options.pop("stream", False):
        return create_completion_stream(options, template)
    else:
        return create_completion_json(options, template)


def create_completion_stream(options, template):
    """Return text completion results in event stream."""

    # Serialize data for event stream.
    def serialize(data):
        data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"data: {data}\n\n"

    def stream():
        buffers = {}
        times = {}
        for choice in stream_model(**options):
            index = choice["index"]
            now = time.time_ns()
            if index not in buffers:
                buffers[index] = []
            if index not in times:
                times[index] = now
            buffers[index].append(choice)

            # Yield data when exceeded the maximum buffering interval.
            elapsed = (now - times[index]) // 1_000_000
            if elapsed > COMPLETION_MAX_INTERVAL:
                data = template.copy()
                data["choices"] = [reduce_choice(buffers[index])]
                yield serialize(data)
                buffers[index].clear()
                times[index] = now

        # Yield remaining data in the buffers.
        for _, buffer in buffers.items():
            if buffer:
                data = template.copy()
                data["choices"] = [reduce_choice(buffer)]
                yield serialize(data)

        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream")


def create_completion_json(options, template):
    """Return text completion results in plain JSON."""

    # Tokenize the prompt beforehand to count token usage.
    options["prompt"] = stream_model.tokenize(options["prompt"])
    prompt_tokens = options["prompt"].shape[-1]
    completion_tokens = 0

    # Add data to the corresponding buffer according to the index.
    buffers = {}
    for choice in stream_model(**options):
        completion_tokens += 1
        index = choice["index"]
        if index not in buffers:
            buffers[index] = []
        buffers[index].append(choice)

    # Merge choices with the same index.
    data = template.copy()
    for _, buffer in buffers.items():
        if buffer:
            data["choices"].append(reduce_choice(buffer))

    # Include token usage info.
    data["usage"] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }

    return jsonify(data)


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def http_error_handler(error):
    """Handler function for all expected HTTP errors."""
    return jsonify(error={"message": error.description}), error.code


def main():
    """Start serving API requests."""
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


if __name__ == "__main__":
    main()

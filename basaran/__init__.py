"""
Configurations and general functions for serving models.
"""
import os

import torch


def is_true(value):
    """Convert from string to boolean."""
    return str(value).lower() in ("yes", "true", "1")


# bigscience/bloomz-560m was chosen as the default model because it is
# multilingual and requires less than 8GB of memory for inference.
MODEL = os.getenv("MODEL", "bigscience/bloomz-560m")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "80"))

# Model-related arguments:
MODEL_REVISION = os.getenv("MODEL_REVISION", "")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "models")
MODEL_LOAD_IN_8BIT = is_true(os.getenv("MODEL_LOAD_IN_8BIT", ""))
MODEL_LOCAL_FILES_ONLY = is_true(os.getenv("MODEL_LOCAL_FILES_ONLY", ""))
MODEL_TRUST_REMOTE_CODE = is_true(os.getenv("MODEL_TRUST_REMOTE_CODE", ""))
MODEL_HALF_PRECISION = is_true(os.getenv("MODEL_HALF_PRECISION", ""))

# Server-related arguments:
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
SERVER_THREADS = int(os.getenv("SERVER_THREADS", "8"))
SERVER_IDENTITY = os.getenv("SERVER_IDENTITY", "basaran")
SERVER_CONNECTION_LIMIT = int(os.getenv("SERVER_CONNECTION_LIMIT", "512"))
SERVER_CHANNEL_TIMEOUT = int(os.getenv("SERVER_CHANNEL_TIMEOUT", "300"))
SERVER_MODEL_NAME = os.getenv("SERVER_MODEL_NAME", "") or MODEL
SERVER_NO_PLAYGROUND = is_true(os.getenv("SERVER_NO_PLAYGROUND", ""))

# Completion-related arguments:
COMPLETION_MAX_PROMPT = int(os.getenv("COMPLETION_MAX_PROMPT", "4096"))
COMPLETION_MAX_TOKENS = int(os.getenv("COMPLETION_MAX_TOKENS", "4096"))
COMPLETION_MAX_N = int(os.getenv("COMPLETION_MAX_N", "5"))
COMPLETION_MAX_LOGPROBS = int(os.getenv("COMPLETION_MAX_LOGPROBS", "5"))
COMPLETION_MAX_INTERVAL = int(os.getenv("COMPLETION_MAX_INTERVAL", "50"))

# CUDA-related arguments:
CUDA_MEMORY_FRACTION = float(os.getenv("CUDA_MEMORY_FRACTION", "1.0"))

# Set memory fraction for the process if specified.
if torch.cuda.is_available() and CUDA_MEMORY_FRACTION < 1:
    torch.cuda.set_per_process_memory_fraction(CUDA_MEMORY_FRACTION)

"""
Use this script to download a model without loading it into memory.
This allows memory-constrained CI/CD runners to build container images
with large bundled models. See ../deployments/bundle/ for examples.
"""
import os
import sys

import huggingface_hub

if len(sys.argv) <= 1:
    sys.exit("error: must specify the model to be downloaded")

# Get cache directory from arguments or environment variables.
if len(sys.argv) >= 3:
    MODEL_CACHE_DIR = sys.argv[2]
elif "MODEL_CACHE_DIR" in os.environ and os.environ["MODEL_CACHE_DIR"]:
    MODEL_CACHE_DIR = os.environ["MODEL_CACHE_DIR"]
else:
    MODEL_CACHE_DIR = None

# Get model revision from environment variables.
if "MODEL_REVISION" in os.environ and os.environ["MODEL_REVISION"]:
    MODEL_REVISION = os.environ["MODEL_REVISION"]
else:
    MODEL_REVISION = None

# Download a snapshot of the specified model from Hugging Face Hub.
huggingface_hub.snapshot_download(
    sys.argv[1],
    cache_dir=MODEL_CACHE_DIR,
    revision=MODEL_REVISION,
    resume_download=True,
)

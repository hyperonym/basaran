import huggingface_hub
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer


class Model:
    """Model wraps around a causal LM to provide stream decoding."""

    def __init__(self, model, tokenizer, **kwargs):
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.kwargs = kwargs
        self.device = "cuda" if torch.cuda.is_available() else "cpu"


def download_snapshot(repo_id, cache_dir):
    """Download a snapshot of the specified model to the cache directory."""
    huggingface_hub.snapshot_download(repo_id, cache_dir=cache_dir)


def load_model(model_name_or_path, cache_dir, load_in_8bit):
    """Load and initialize a model from local files."""
    kwargs = {"cache_dir": cache_dir, "local_files_only": True}
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, **kwargs)
    if torch.cuda.is_available():
        kwargs = kwargs.copy()
        kwargs["device_map"] = "auto"
        kwargs["load_in_8bit"] = load_in_8bit
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, **kwargs)
    return Model(model, tokenizer)

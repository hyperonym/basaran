def map(
    text,
    index,
    token=None,
    token_logprob=None,
    top_logprobs=None,
    text_offset=None,
    finish_reason=None,
):
    """Create a choice object from predictions."""
    choice = {
        "text": text,
        "index": index,
        "logprobs": None,
        "finish_reason": finish_reason,
    }
    if (
        token is not None
        and token_logprob is not None
        and top_logprobs is not None
        and text_offset is not None
    ):
        choice["logprobs"] = {
            "tokens": [token],
            "token_logprobs": [token_logprob],
            "top_logprobs": [top_logprobs],
            "text_offset": [text_offset],
        }
    return choice


def reduce(choices):
    """Merge a list of choices into a single choice object."""
    text_buffer = []
    index = 0
    finish_reason = None
    tokens = []
    token_logprobs = []
    top_logprobs = []
    text_offset = []

    # All choice objects are expected to have the same shape.
    for choice in choices:
        text_buffer.append(choice["text"])
        index = choice["index"]
        finish_reason = choice["finish_reason"]
        logprobs = choice["logprobs"]
        if logprobs is not None:
            tokens += logprobs["tokens"]
            token_logprobs += logprobs["token_logprobs"]
            top_logprobs += logprobs["top_logprobs"]
            text_offset += logprobs["text_offset"]

    # Create reduced object based on the last seen index and finish reason.
    reduced = {
        "text": "".join(text_buffer),
        "index": index,
        "logprobs": None,
        "finish_reason": finish_reason,
    }
    if tokens:
        reduced["logprobs"] = {
            "tokens": tokens,
            "token_logprobs": token_logprobs,
            "top_logprobs": top_logprobs,
            "text_offset": text_offset,
        }

    return reduced

import copy

import huggingface_hub
import torch

from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    LogitsProcessorList,
    MinNewTokensLengthLogitsProcessor,
    TemperatureLogitsWarper,
    TopPLogitsWarper,
)


DEFAULT_MIN_TOKENS = 0
DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.5
DEFAULT_N = 1
DEFAULT_ECHO = False

NUCLEUS_SAMPLING_EPSILON = 1e-6


class Model:
    """Model wraps around a causal LM to provide stream decoding."""

    def __init__(self, model, tokenizer):
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def __call__(
        self,
        prompt,
        min_token=DEFAULT_MIN_TOKENS,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        n=DEFAULT_N,
        echo=DEFAULT_ECHO,
    ):
        inputs = self.tokenizer(
            [prompt] * n,
            return_tensors="pt",
            return_offsets_mapping=True,
        ).to(self.device)

        # TODO(peakji): check input length.
        input_ids = inputs["input_ids"]
        input_length = input_ids.shape[-1]
        if input_length == 0:
            # TODO(peakji): yield stop token
            return

        # TODO(peakji): echo prompt tokens (echo).

        stream = self.generate(
            input_ids,
            min_new_tokens=min_token,
            max_length=max_tokens + input_length,
            temperature=temperature,
            top_p=top_p,
        )
        for tokens, logprobs, finish_reason in stream:
            # TODO(peakji): handle multiple completions.
            text = self.tokenizer.decode(tokens[0], skip_special_tokens=True)
            # logprob = round(float(logprobs[0]), 8)
            print(text, sep=" ", end="", flush=True)

    def logits_processor(self, config, input_length):
        processor = LogitsProcessorList()

        # Add processor for enforcing a min-length of new tokens.
        if (
            config.min_new_tokens is not None
            and config.min_new_tokens > 0
            and config.eos_token_id is not None
        ):
            processor.append(
                MinNewTokensLengthLogitsProcessor(
                    prompt_length_to_skip=input_length,
                    min_new_tokens=config.min_new_tokens,
                    eos_token_id=config.eos_token_id,
                )
            )

        # Add processor for scaling output probability distribution.
        if (
            config.temperature is not None
            and config.temperature > 0
            and config.temperature != 1.0
        ):
            processor.append(TemperatureLogitsWarper(config.temperature))

        # Add processor for nucleus-sampling (top-p) decoding.
        if config.top_p is not None:
            top_p = float(config.top_p)
            if top_p >= 1.0:
                top_p = 1.0 - NUCLEUS_SAMPLING_EPSILON
            elif top_p <= 0:
                top_p = NUCLEUS_SAMPLING_EPSILON
            processor.append(TopPLogitsWarper(top_p))

        return processor

    def generate(self, input_ids, **kwargs):
        # Separate model arguments from generation config.
        config = self.model.generation_config
        config = copy.deepcopy(config)
        kwargs = config.update(**kwargs)
        kwargs["output_attentions"] = False
        kwargs["output_hidden_states"] = False
        kwargs["use_cache"] = config.use_cache

        # Collect special token IDs.
        pad_token_id = config.pad_token_id
        bos_token_id = config.bos_token_id
        eos_token_id = config.eos_token_id
        if pad_token_id is None:
            pad_token_id = config.eos_token_id
        if isinstance(eos_token_id, int):
            eos_token_id = [eos_token_id]

        # Prepare inputs for encoder-decoder generation.
        if self.model.config.is_encoder_decoder:
            # Get output from the encoder.
            encoder = self.model.get_encoder()
            encoder_kwargs = kwargs.copy()
            encoder_kwargs.pop("use_cache", None)
            encoder_kwargs["input_ids"] = input_ids
            encoder_kwargs["return_dict"] = True
            kwargs["encoder_outputs"] = encoder(**encoder_kwargs)

            # Create input for the decoder.
            decoder_start_token_id = config.decoder_start_token_id
            if decoder_start_token_id is None:
                decoder_start_token_id = bos_token_id
            input_ids = input_ids[:, 0:1] * 0 + decoder_start_token_id

        # Set up logits processors.
        processor = self.logits_processor(config, input_ids.shape[-1])

        # Keep track of which sequences are already finished.
        unfinished = input_ids.new(input_ids.shape[0]).fill_(1)

        # Start auto-regressive generation.
        while True:
            inputs = self.model.prepare_inputs_for_generation(
                input_ids, **kwargs
            )  # noqa: E501
            outputs = self.model(
                **inputs,
                return_dict=True,
                output_attentions=False,
                output_hidden_states=False,
            )

            # Pre-process distribution and select the next tokens.
            logits = outputs.logits[:, -1, :]
            logits = processor(input_ids, logits)
            probs = torch.nn.functional.softmax(logits, dim=-1)
            tokens = torch.multinomial(probs, num_samples=1).squeeze(1)

            # Compute log probabilities of the selected tokens.
            logprobs = torch.gather(probs, 1, tokens[None, :]).squeeze(0)
            logprobs = torch.log(logprobs)

            # Finished sentences should have their next token be a padding.
            if eos_token_id is not None:
                tokens = tokens * unfinished + pad_token_id * (1 - unfinished)

            # Append selected tokens to the inputs.
            input_ids = torch.cat([input_ids, tokens[:, None]], dim=-1)

            # Extract past key values from model output.
            if "past_key_values" in outputs:
                kwargs["past_key_values"] = outputs.past_key_values
            elif "mems" in outputs:
                kwargs["past_key_values"] = outputs.mems
            elif "past_buckets_states" in outputs:
                kwargs["past_key_values"] = outputs.past_buckets_states

            # Mark sentences with eos tokens as finished.
            if eos_token_id is not None:
                unfinished = unfinished.mul(
                    (sum(tokens != i for i in eos_token_id)).long()
                )

            # Yield token and stop when finished or exceeded the max length.
            finish_reason = None
            if unfinished.max() == 0:
                finish_reason = "stop"
            elif input_ids.shape[-1] >= config.max_length:
                finish_reason = "length"
            yield tokens, logprobs, finish_reason
            if finish_reason:
                break


def download_snapshot(repo_id, cache_dir):
    """Download a snapshot of the specified model to the cache directory."""
    huggingface_hub.snapshot_download(repo_id, cache_dir=cache_dir)


def load_model(name_or_path, cache_dir, load_in_8bit):
    """Load and initialize a model from local files."""
    kwargs = {"cache_dir": cache_dir, "local_files_only": True}
    tokenizer = AutoTokenizer.from_pretrained(name_or_path, **kwargs)
    if torch.cuda.is_available():
        kwargs = kwargs.copy()
        kwargs["device_map"] = "auto"
        kwargs["load_in_8bit"] = load_in_8bit
    try:
        model = AutoModelForCausalLM.from_pretrained(name_or_path, **kwargs)
    except ValueError:
        model = AutoModelForSeq2SeqLM.from_pretrained(name_or_path, **kwargs)
    if not model.can_generate():
        raise TypeError(f"{name_or_path} is not a text generation model")
    return Model(model, tokenizer)

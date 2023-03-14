"""
Test text generation model with stream decoding.
"""
from basaran.model import load_model


class TestModel:
    """Test text generation model with stream decoding."""

    def assert_stochastic(self, model):
        """Test completion using stochastic decoding."""
        prompt = "once upon a time"
        n = 2
        text = [""] * n
        finish_reasons = [None] * n
        for choice in model(
            prompt=prompt,
            min_tokens=10,
            max_tokens=16,
            temperature=0.95,
            top_p=0.95,
            n=n,
            logprobs=2,
            echo=True,
        ):
            index = choice["index"]
            text[index] += choice["text"]
            finish_reasons[index] = choice["finish_reason"]

        for i in range(n):
            if i > 0:
                assert text[i] != text[i - 1]
            assert prompt in text[i]
            assert finish_reasons[i] is not None

    def assert_deterministic(self, model):
        """Test completion using deterministic decoding."""
        n = 3
        text = [""] * n
        counts = [0] * n
        for choice in model(
            prompt=model.tokenize(""),
            min_tokens=10,
            max_tokens=16,
            temperature=0,
            n=n,
        ):
            index = choice["index"]
            text[index] += choice["text"]
            counts[index] += 1

        for i in range(n):
            if i > 0:
                assert text[i] == text[i - 1]
            assert counts[i] >= 10 and counts[i] <= 16


class TestDecoderOnlyModel(TestModel):
    """Test text generation using decoder-only models."""

    def test_stochastic(self):
        """Test completion using stochastic decoding."""
        model = load_model("./tests/data/tiny-random-bloom")
        self.assert_stochastic(model)

    def test_deterministic(self):
        """Test completion using deterministic decoding."""
        model = load_model("./tests/data/tiny-random-bloom")
        self.assert_deterministic(model)


class TestEncoderDecoderModel(TestModel):
    """Test text generation using encoder-decoder models."""

    def test_stochastic(self):
        """Test completion using stochastic decoding."""
        model = load_model("./tests/data/tiny-random-t5")
        self.assert_stochastic(model)

    def test_deterministic(self):
        """Test completion using deterministic decoding."""
        model = load_model("./tests/data/tiny-random-t5")
        self.assert_deterministic(model)

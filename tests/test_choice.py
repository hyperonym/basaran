"""
Test functions for creating and merging choice objects.
"""
from basaran.choice import map_choice, reduce_choice


class TestChoice:
    """Test functions for creating and merging choice objects."""

    def test_choice(self):
        """Test merging a list of choices into a single choice object."""
        merged = reduce_choice(
            [
                map_choice(
                    "hello",
                    1,
                    token=0,
                    token_logprob=0,
                    top_logprobs={},
                    text_offset=0,
                    finish_reason=None,
                ),
                map_choice(
                    " world",
                    1,
                    token=1,
                    token_logprob=0,
                    top_logprobs={},
                    text_offset=5,
                    finish_reason="stop",
                ),
            ]
        )

        assert merged["text"] == "hello world"
        assert merged["index"] == 1
        assert merged["finish_reason"] == "stop"
        assert len(merged["logprobs"]["tokens"]) == 2

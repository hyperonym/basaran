"""
Test stateful tokenizer for stream decoding.
"""
from transformers import AutoTokenizer

from basaran.decoder import StreamDecoder


class TestDecoder:
    """Test stateful tokenizer for stream decoding."""

    def test_byte_pair_encoding(self):
        """Test with Byte-Pair-Encoding."""
        tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path="./tests/data/tiny-random-bloom",
            local_files_only=True,
        )
        decoder = StreamDecoder(tokenizer)

        expected = "hello world ABC \n 你好"
        tokens = tokenizer.encode(expected)

        actual = ""
        for token in tokens:
            actual += decoder.decode(token)

        assert actual == expected
        assert decoder.end == len(expected)

    def test_sentence_piece(self):
        """Test with SentencePiece."""
        tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path="./tests/data/tiny-random-t5",
            local_files_only=True,
        )
        decoder = StreamDecoder(tokenizer)

        expected = "hello world ABC"
        tokens = tokenizer.encode(expected)

        actual = ""
        for token in tokens:
            actual += decoder.decode(token)

        assert actual == expected
        assert decoder.end == len(expected)

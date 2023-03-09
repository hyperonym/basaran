"""
Test stateful tokenizer for stream decoding.
"""
from transformers import AutoTokenizer

from basaran.tokenizer import StreamTokenizer


class TestTokenizer:
    """Test stateful tokenizer for stream decoding."""

    def test_byte_level_byte_pair_encoding(self):
        """Test with byte-level Byte-Pair-Encoding."""
        tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path="./tests/data/tiny-random-bloom",
            local_files_only=True,
        )
        detokenizer = StreamTokenizer(tokenizer)

        expected = "hello world ABC \n 你好"
        tokens = tokenizer.encode(expected)

        actual = ""
        for token in tokens:
            actual += detokenizer.decode(token)

        assert actual == expected
        assert detokenizer.end == len(expected)

    def test_sentence_piece(self):
        """Test with SentencePiece."""
        tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path="./tests/data/tiny-random-t5",
            local_files_only=True,
        )
        detokenizer = StreamTokenizer(tokenizer)

        expected = "hello world ABC"
        tokens = tokenizer.encode(expected)

        actual = ""
        for token in tokens:
            actual += detokenizer.decode(token)

        assert actual == expected
        assert detokenizer.end == len(expected)

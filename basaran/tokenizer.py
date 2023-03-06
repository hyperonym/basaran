"""
A stateful tokenizer for stream decoding.
"""


class StreamTokenizer:
    """StreamTokenizer wraps around a tokenizer to support stream decoding."""

    def __init__(self, tokenizer):
        super().__init__()
        self.tokenizer = tokenizer
        self.replacement = chr(0xFFFD)
        self.buffer = []
        self.surrogates = 0
        self.start = 0
        self.end = 0

    def decode(self, token):
        """Decode token to string while handling surrogates and whitespace."""

        # <unk>, <pad> and other special tokens will be decoded into ''.
        text = self.tokenizer.decode(token, skip_special_tokens=True)

        # Handle replacement characters caused by multi-byte-pair-encoding or
        # Unicode surrogates or multi-code-point graphemes like emojis.
        if self.replacement in text:
            n = -self.surrogates if self.surrogates > 0 else len(self.buffer)
            tokens = self.buffer[n:] + [token]
            text = self.tokenizer.decode(tokens, skip_special_tokens=True)

            # Check whether the last grapheme was successfully decoded.
            if text and text[-1] != self.replacement:
                text = text.replace(self.replacement, "")
                self.surrogates = 0
            else:
                text = ""
                self.surrogates += 1
        else:
            self.surrogates = 0

        # Handle whitespace between tokens.
        tokens = self.buffer + [token]
        prefix = self.tokenizer.decode(self.buffer, skip_special_tokens=True)
        whole = self.tokenizer.decode(tokens, skip_special_tokens=True)
        if prefix + " " + text == whole:
            text = " " + text

        # Update buffer and offsets.
        self.buffer = self.buffer[-4:] + [token]
        self.start = self.end
        self.end += len(text)

        return text

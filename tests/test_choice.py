"""
Test functions for creating and merging choice objects.
"""
from basaran.choice import map_choice, reduce_choice


class TestChoice:
    """Test functions for creating and merging choice objects."""

    def test_merge(self):
        """Test merging a list of choices into a single choice object."""
        choice_a = map_choice("hello", 0)
        choice_b = map_choice(" world", 0, finish_reason="stop")
        merged = reduce_choice([choice_a, choice_b])
        assert merged["text"] == "hello world"

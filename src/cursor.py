"""
Cursor tracking for constrained generation.

This module provides a multi-cursor automaton that tracks possible
positions within a source text. It is used to validate that generated
tokens can be absorbed by the source prompt, ensuring strings come
from the original input rather than being hallucinated.
"""


class Cursor:
    """
    Multi-cursor tracker for validating token absorption.

    This class maintains a set of possible positions (cursors) within
    a source text. As tokens are generated, cursors advance only if
    the token matches the source text at that position. Cursors that
    cannot advance are removed, effectively pruning invalid paths.

    Attributes:
        source: The target text to match against.
        positions: Set of valid cursor positions within the source.
    """

    def __init__(self, source: str) -> None:
        """
        Initialize the cursor tracker.

        Args:
            source: The target text that generated tokens must match.
        """
        self.source: str = source
        self.positions: set[int] = set(range(len(source) + 1))

    def advance(self, text: str) -> None:
        """
        Advance all cursors by matching the given text.

        For each cursor, check if the text matches the source at that
        position. If it does, the cursor advances past the text. If not,
        the cursor is removed (invalid path).

        Args:
            text: The text to match against the source.
        """
        next_positions: set[int] = set()
        for pos in self.positions:
            end = pos + len(text)
            if end <= len(self.source) and self.source[pos:end] == text:
                next_positions.add(end)
        self.positions = next_positions

    def accepts(self, text: str) -> bool:
        """
        Check if any cursor can absorb the given text.

        Args:
            text: The text to check.

        Returns:
            True if at least one cursor can match the text, False otherwise.
        """
        if not text:
            return False
        for pos in self.positions:
            end = pos + len(text)
            if end <= len(self.source) and self.source[pos:end] == text:
                return True
        return False

    def next_chars(self) -> set[str]:
        """
        Get all characters that can be generated next.

        Returns:
            Set of characters that appear at any valid cursor position.
        """
        chars: set[str] = set()
        for pos in self.positions:
            if pos < len(self.source):
                chars.add(self.source[pos])
        return chars

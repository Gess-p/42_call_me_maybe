"""
Regex validation rules for constrained generation.

This module defines a finite state machine (FSM) that validates
regular expression patterns token by token. It ensures that any
generated regex is syntactically valid.

The FSM handles:
- Literal characters (a, b, 1, 2, ...)
- Character classes ([abc], [a-z])
- Quantifiers (+, *)
- Escapes (\\s, \\d, \\w)
- Ranges ([a-z], [0-9])
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Character sets
# ---------------------------------------------------------------------------

#: All printable ASCII characters (space through tilde).
PRINTABLE_CHARS: frozenset[str] = frozenset(chr(i) for i in range(0x20, 0x7F))

#: Regex metacharacters that require escaping.
META_CHARS: frozenset[str] = frozenset('[]*+?|\\"()$^./')

#: Characters that can appear as literals in a regex.
LITERAL_CHARS: frozenset[str] = PRINTABLE_CHARS - META_CHARS

#: Characters allowed inside a character class ``[...]``.
CLASS_CHARS: frozenset[str] = PRINTABLE_CHARS - frozenset('[]\\"')

#: Characters allowed in a range like ``[a-z]`` (no dash).
RANGE_CHARS: frozenset[str] = CLASS_CHARS - frozenset('-')

#: Characters allowed after a backslash (``\\s``, ``\\d``, ``\\w``).
ESCAPE_CHARS: frozenset[str] = frozenset('sdw')

#: Maximum length of a literal token.
MAX_LITERAL_LEN: int = 8

#: Maximum length of a class token.
MAX_CLASS_LEN: int = 16


# ---------------------------------------------------------------------------
# FSM states
# ---------------------------------------------------------------------------

class RegexState(Enum):
    """States of the regex validation FSM."""

    START = 'start'
    LITERAL_BODY = 'literal_body'
    LITERAL_FULL = 'literal_full'
    AFTER_CLASS = 'after_class'
    AFTER_ESCAPE = 'after_escape'
    AFTER_QUANT = 'after_quant'
    CLASS_OPEN = 'class_open'
    CLASS_BODY = 'class_body'
    CLASS_FULL = 'class_full'
    CLASS_RANGE = 'class_range'
    ESCAPE = 'escape'


#: Characters allowed in each state.
ALLOWED_CHARS: dict[RegexState, frozenset[str]] = {
    RegexState.START: LITERAL_CHARS | frozenset('[\\'),
    RegexState.LITERAL_BODY: LITERAL_CHARS | frozenset('+*'),
    RegexState.LITERAL_FULL: frozenset('+*'),
    RegexState.AFTER_CLASS: frozenset('+'),
    RegexState.AFTER_ESCAPE: frozenset('+*'),
    RegexState.AFTER_QUANT: frozenset(),
    RegexState.CLASS_OPEN: CLASS_CHARS,
    RegexState.CLASS_BODY: CLASS_CHARS | frozenset(']'),
    RegexState.CLASS_FULL: frozenset(']'),
    RegexState.CLASS_RANGE: RANGE_CHARS,
    RegexState.ESCAPE: ESCAPE_CHARS,
}


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def next_state(state: RegexState, ch: str, run_len: int) -> RegexState:
    """
    Compute the next FSM state after consuming a character.

    Args:
        state: Current state of the FSM.
        ch: Character that was consumed.
        run_len: Length of the current run (for length limits).

    Returns:
        The next state.
    """
    if state == RegexState.START:
        if ch == '[':
            return RegexState.CLASS_OPEN
        if ch == '\\':
            return RegexState.ESCAPE
        return RegexState.LITERAL_BODY

    if state == RegexState.LITERAL_BODY:
        if ch in '+*':
            return RegexState.AFTER_QUANT
        if run_len + 1 >= MAX_LITERAL_LEN:
            return RegexState.LITERAL_FULL
        return RegexState.LITERAL_BODY

    if state == RegexState.LITERAL_FULL:
        if ch in '+*':
            return RegexState.AFTER_QUANT
        return state

    if state == RegexState.AFTER_CLASS:
        if ch == '+':
            return RegexState.AFTER_QUANT
        return state

    if state == RegexState.AFTER_ESCAPE:
        if ch in '+*':
            return RegexState.AFTER_QUANT
        return state

    if state == RegexState.CLASS_OPEN:
        return RegexState.CLASS_BODY

    if state == RegexState.CLASS_BODY:
        if ch == ']':
            return RegexState.AFTER_CLASS
        if ch == '-':
            return RegexState.CLASS_RANGE
        if run_len + 1 >= MAX_CLASS_LEN:
            return RegexState.CLASS_FULL
        return RegexState.CLASS_BODY

    if state == RegexState.CLASS_FULL:
        if ch == ']':
            return RegexState.AFTER_CLASS
        return state

    if state == RegexState.CLASS_RANGE:
        if run_len + 1 >= MAX_CLASS_LEN:
            return RegexState.CLASS_FULL
        return RegexState.CLASS_BODY

    if state == RegexState.ESCAPE:
        return RegexState.AFTER_ESCAPE

    return state


def is_accepting(state: RegexState) -> bool:
    """
    Check if a state is accepting (regex can end here).

    Args:
        state: State to check.

    Returns:
        True if the regex can terminate at this state.
    """
    return state in (
        RegexState.LITERAL_BODY,
        RegexState.LITERAL_FULL,
        RegexState.AFTER_CLASS,
        RegexState.AFTER_ESCAPE,
        RegexState.AFTER_QUANT,
    )

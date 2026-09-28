"""
System prompt construction for function calling.

This module builds the system prompt that tells the model which
functions are available and what it should do. The prompt is
intentionally minimal: it only lists function names and descriptions,
because the generator enforces the JSON structure and parameter
types itself.
"""

from src.schema import FunctionDef


def build_system_prompt(functions: list[FunctionDef]) -> str:
    """
    Build the system prompt listing available functions.

    The prompt instructs the model to choose the function whose
    description best matches the user request, then fill in that
    function's arguments. Types and JSON structure are not described
    here because the generator enforces them during decoding.

    Args:
        functions: The function definitions to advertise.

    Returns:
        The system prompt as a single string.
    """
    function_lines: str = '\n'.join(
        f'- {func.name}: {func.description}'
        for func in functions
    )
    return (
        'You output ONLY a JSON function call. No prose.\n'
        'Choose the function whose description matches the request, '
        'then fill each of its arguments.\n'
        '\n'
        'Rules:\n'
        '- Argument values must come from the user request when possible.\n'
        '- For regex arguments, prefer general patterns over literal text '
        '(e.g. [0-9]+ for numbers, [aeiou] for vowels, \\s for whitespace).\n'
        '- For replacement arguments, use the literal symbol when the '
        'request names one (e.g. "*" for asterisks, "_" for underscores).\n'
        '\n'
        'Functions:\n'
        f'{function_lines}'
    )

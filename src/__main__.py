"""
Entry point for the call-me-maybe function calling tool.

This module wires together the command-line interface, the schema
loaders, and the Generator. It reads function definitions and user
prompts from JSON files, runs the generator on each prompt, and
writes the resulting function calls to a JSON output file.

All errors are handled gracefully: missing files, malformed JSON,
and generation failures produce clear messages on stderr and a
non-zero exit code instead of a crash.
"""

import argparse
import json
import os
import sys
import time

from llm_sdk import Small_LLM_Model
from src.schema import FunctionDef, Loader, UserPrompt
from src.generator import FunctionCall, Generator


# ---------------------------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        The parsed namespace with ``functions_definition``, ``input``,
        and ``output`` paths.
    """
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Function calling with constrained decoding"
    )
    arg_parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json",
        help="Path to function definitions JSON file",
    )
    arg_parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json",
        help="Path to input prompts JSON file",
    )
    arg_parser.add_argument(
        "--output",
        default="data/output/function_calling_results.json",
        help="Path to output JSON file",
    )
    return arg_parser.parse_args()


# ---------------------------------------------------------------------------
# Generator setup
# ---------------------------------------------------------------------------

def _build_generator(args: argparse.Namespace) -> Generator | None:
    """
    Build the Generator from the model and function definitions.

    Args:
        args: The parsed command-line arguments.

    Returns:
        A ready-to-use Generator, or ``None`` if setup failed.
    """
    print("Loading model...")
    try:
        model: Small_LLM_Model = Small_LLM_Model()
    except Exception as e:
        print(
            f"Error: failed to load model: {e}",
            file=sys.stderr,
        )
        return None

    functions: list[FunctionDef] = Loader.load_functions(
        args.functions_definition
    )
    if not functions:
        print(
            "Error: no functions loaded, aborting.",
            file=sys.stderr,
        )
        return None

    try:
        return Generator(model, functions)
    except Exception as e:
        print(
            f"Error: failed to initialize generator: {e}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def _run_batch(
    generator: Generator,
    prompts: list[UserPrompt],
) -> list[FunctionCall]:
    """
    Process all prompts and collect the results.

    Args:
        generator: The initialized Generator.
        prompts: The prompts to process.

    Returns:
        A list of ``FunctionCall`` dicts, one per prompt. Failed
        prompts get a placeholder with empty name and parameters.
    """
    results: list[FunctionCall] = []
    failures: list[str] = []
    total_start: float = time.time()

    for prompt_item in prompts:
        print(f"Processing : {prompt_item.prompt}")
        start: float = time.time()
        try:
            result = generator.build_function_call(prompt_item.prompt)
        except Exception as e:
            print(
                f"  Error processing prompt: {e}",
                file=sys.stderr,
            )
            results.append(
                FunctionCall(
                    prompt=prompt_item.prompt,
                    name="",
                    parameters={},
                )
            )
            failures.append(prompt_item.prompt)
            continue
        print(f"  -> name: {result.name}")
        print(f"  -> parameters: {result.parameters}")
        print(f"  ({time.time() - start:.1f}s)\n")
        results.append(result)

    print(
        f"--- {len(results)} prompt(s), "
        f"total processing time: {time.time() - total_start:.1f}s ---"
    )
    if failures:
        print(
            f"{len(failures)} prompt(s) could not be answered:",
            file=sys.stderr,
        )
        for failed in failures:
            print(f"  - {failed}", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _write_results(
    path: str,
    results: list[FunctionCall],
) -> bool:
    """
    Write the results to a JSON file.

    Creates parent directories as needed.

    Args:
        path: Output file path.
        results: The function calls to write.

    Returns:
        True on success, False on error.
    """
    try:
        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [result.model_dump() for result in results],
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"Results written to {path}")
        return True
    except OSError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run the function calling tool.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    args: argparse.Namespace = _parse_args()

    prompts: list[UserPrompt] = Loader.load_prompts(args.input)
    if not prompts:
        print(
            "Error: no prompts loaded, aborting.",
            file=sys.stderr,
        )
        return 1

    generator: Generator | None = _build_generator(args)
    if generator is None:
        return 1

    results = _run_batch(generator, prompts)
    return 0 if _write_results(args.output, results) else 1


if __name__ == "__main__":
    sys.exit(main())

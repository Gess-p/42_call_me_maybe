"""
Data schemas for function calling.

This module defines the Pydantic models used throughout the project:
- Function definitions (name, description, parameters, returns)
- Parameter types (number, string, boolean, integer)
- Prompts loaded from input files

It also provides loaders that read JSON files and validate them
against these schemas, returning empty lists on error so the caller
can decide how to proceed.
"""

import json
import sys

from enum import Enum
from pydantic import BaseModel, ValidationError, model_validator
from typing import Dict


# ---------------------------------------------------------------------------
# Parameter types
# ---------------------------------------------------------------------------

class ParamType(str, Enum):
    """
    Supported parameter types.

    The ``UNSUPPORTED`` member is a fallback: any unknown type in the
    input JSON is mapped here instead of raising a validation error,
    so that the rest of the schema can still be loaded.
    """

    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    UNSUPPORTED = "unsupported"

    @classmethod
    def _missing_(cls, value: object) -> "ParamType":
        """
        Handle unknown values by returning ``UNSUPPORTED``.

        Args:
            value: The raw value that did not match any member.

        Returns:
            The ``UNSUPPORTED`` member.
        """
        return cls.UNSUPPORTED


# ---------------------------------------------------------------------------
# Schema models
# ---------------------------------------------------------------------------

class ParamDef(BaseModel):
    """
    Definition of a single function parameter.

    Attributes:
        type: The parameter type.
        declared_type: The original type string from the JSON file,
            kept for error reporting when the type is unsupported.
    """

    type: ParamType
    declared_type: str = ""

    @model_validator(mode="before")
    @classmethod
    def _keep_declared_type(cls, data: object) -> object:
        """
        Preserve the original type string before enum conversion.

        This runs before Pydantic validates the field, so ``declared_type``
        captures exactly what the JSON file said -- even if it maps to
        ``UNSUPPORTED``.

        Args:
            data: The raw data for this model.

        Returns:
            The (possibly modified) data.
        """
        if isinstance(data, dict) and "type" in data:
            fields = dict(data)
            raw = fields["type"]
            # ParamType subclasses str, so a member already is its own
            # spelling; str() on one would give the repr form
            # "ParamType.UNSUPPORTED" instead of "unsupported".
            fields.setdefault(
                "declared_type", raw if isinstance(raw, str) else str(raw)
            )
            return fields
        return data


class ReturnDef(BaseModel):
    """
    Definition of a function's return type.

    Attributes:
        type: The return type.
    """

    type: ParamType


class FunctionDef(BaseModel):
    """
    Complete definition of a callable function.

    Attributes:
        name: The function name.
        description: Human-readable description used to pick the function.
        parameters: Mapping of parameter name to its definition.
        returns: The function's return type.
    """

    name: str
    description: str
    parameters: Dict[str, ParamDef]
    returns: ReturnDef


class UserPrompt(BaseModel):
    """
    A single natural-language prompt loaded from the input file.

    Attributes:
        prompt: The raw text of the prompt.
    """

    prompt: str


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

class Loader:
    """
    Static helpers to load and validate JSON input files.

    All methods catch file, decoding, and validation errors, print a
    message to stderr, and return an empty list so the caller can
    decide whether to abort.
    """

    @staticmethod
    def load_functions(path: str) -> list[FunctionDef]:
        """
        Load function definitions from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            A list of validated ``FunctionDef`` objects, or an empty
            list on error.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [FunctionDef(**item) for item in data]
        except OSError as e:
            print(
                f"Error : cannot read {path}: {e.strerror}",
                file=sys.stderr,
            )
            return []
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(
                f"Error : cannot decode {path}: {e}",
                file=sys.stderr,
            )
            return []
        except ValidationError as e:
            print(
                f"Error value in {path} :\n{e}",
                file=sys.stderr,
            )
            return []
        except TypeError as e:
            print(
                f"Error : unexpected JSON structure in {path}: {e}",
                file=sys.stderr,
            )
            return []

    @staticmethod
    def load_prompts(path: str) -> list[UserPrompt]:
        """
        Load user prompts from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            A list of validated ``UserPrompt`` objects, or an empty
            list on error.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [UserPrompt(**item) for item in data]
        except OSError as e:
            print(
                f"Error : cannot read {path}: {e.strerror}",
                file=sys.stderr,
            )
            return []
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(
                f"Error : cannot decode {path}: {e}",
                file=sys.stderr,
            )
            return []
        except ValidationError as e:
            print(
                f"Error {path} :\n{e}",
                file=sys.stderr,
            )
            return []
        except TypeError as e:
            print(
                f"Error : unexpected JSON structure in {path}: {e}",
                file=sys.stderr,
            )
            return []

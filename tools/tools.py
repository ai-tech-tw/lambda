"""Function definitions and dispatch for the OpenAI Responses API."""

import json
from collections.abc import Callable
from typing import Any

from .calculator import evaluate_expression
from .clock import current_time
from .content import fetch_content
from .search import perform_search, search_papers_dataframe


ToolFunction = Callable[..., str]


TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "current_time": current_time,
    "evaluate_expression": evaluate_expression,
    "perform_search": perform_search,
    "search_papers_dataframe": search_papers_dataframe,
    "fetch_content": fetch_content,
}


# The Responses API accepts JSON Schema definitions rather than inferring a
# function's parameters from its Python type annotations.
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "current_time",
        "description": "Get the current time in an IANA timezone.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {"time_zone": {"type": "string"}},
        },
    },
    {
        "type": "function",
        "name": "evaluate_expression",
        "description": "Evaluate a basic arithmetic expression safely.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "type": "function",
        "name": "perform_search",
        "description": "Perform a web search using Tavily.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                "timeout": {"type": "integer", "minimum": 1},
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "search_papers_dataframe",
        "description": "Search arXiv and return paper summaries.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {"type": "string"},
                "search_type": {
                    "type": "string",
                    "enum": ["all", "title", "abstract", "author", "cat"],
                },
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["search_query"],
        },
    },
    {
        "type": "function",
        "name": "fetch_content",
        "description": "Fetch readable text from one or more URLs, optionally regex-searching it.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 3, "maximum": 60},
                "max_chars_per_url": {
                    "type": "integer",
                    "minimum": 500,
                    "maximum": 10000,
                },
                "max_depth": {"type": "integer", "minimum": 0, "maximum": 3},
                "regex_pattern": {"type": "string"},
                "regex_ignore_case": {"type": "boolean"},
                "max_matches_per_url": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["urls"],
        },
    },
]


_TOOL_PARAMETERS = {
    tool["name"]: tool["parameters"]
    for tool in TOOLS
    if isinstance(tool.get("name"), str) and isinstance(tool.get("parameters"), dict)
}


def _validate_value(name: str, value: Any, schema: dict[str, Any]) -> None:
    expected_type = schema.get("type")
    valid_type = (
        expected_type is None
        or (expected_type == "string" and isinstance(value, str))
        or (expected_type == "boolean" and isinstance(value, bool))
        or (
            expected_type == "integer"
            and isinstance(value, int)
            and not isinstance(value, bool)
        )
        or (
            expected_type == "number"
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        )
    )
    if not valid_type:
        raise ValueError(f"{name} must be a {expected_type}")

    allowed_values = schema.get("enum")
    if isinstance(allowed_values, list) and value not in allowed_values:
        raise ValueError(f"{name} must be one of {allowed_values}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise ValueError(f"{name} must be at most {maximum}")


def validate_tool_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate model-supplied arguments against the registered JSON Schema."""
    parameters = _TOOL_PARAMETERS.get(name)
    if parameters is None:
        raise ValueError(f"unknown tool '{name}'")

    properties = parameters.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError(f"{name} has an invalid parameter schema")
    unknown_fields = set(arguments) - set(properties)
    if unknown_fields:
        raise ValueError(f"unsupported arguments: {', '.join(sorted(unknown_fields))}")

    required = parameters.get("required", [])
    if not isinstance(required, list):
        raise ValueError(f"{name} has an invalid required-argument schema")
    missing_fields = [field for field in required if field not in arguments]
    if missing_fields:
        raise ValueError(f"missing required arguments: {', '.join(missing_fields)}")

    for field, value in arguments.items():
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict):
            raise ValueError(f"{field} has an invalid schema")
        _validate_value(field, value, field_schema)
    return arguments


def call_tool(name: str, arguments: str) -> str:
    """Run a model-requested tool and return a text result for the API."""
    tool = TOOL_FUNCTIONS.get(name)
    if tool is None:
        return f"Error: unknown tool '{name}'"

    try:
        parsed_arguments = json.loads(arguments)
        if not isinstance(parsed_arguments, dict):
            return "Error: tool arguments must be a JSON object"
        return tool(**validate_tool_arguments(name, parsed_arguments))
    except Exception as exc:
        return f"Error running {name}: {exc}"


def advise_tool_call(text: str) -> tuple[str, str] | None:
    """Turn a JSON-shaped text tool request into a safe internal tool call.

    Some OpenAI-compatible model servers return a tool request as message text
    rather than as a structured ``function_call`` item. A valid JSON answer is
    not necessarily a tool request, so this adapter accepts only the explicit
    lambda tool-call envelope and leaves every other JSON response untouched.
    """
    try:
        payload = json.loads(text.strip())
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    if set(payload) != {"_lambda_tool_call", "name", "arguments"}:
        return None
    if payload.get("_lambda_tool_call") is not True:
        return None

    requested_name = payload.get("name")
    if not isinstance(requested_name, str):
        return None
    name = requested_name
    if name not in TOOL_FUNCTIONS:
        return None

    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        return None

    try:
        validate_tool_arguments(name, arguments)
    except ValueError:
        return None
    return name, json.dumps(arguments)


__all__ = [
    "current_time",
    "evaluate_expression",
    "perform_search",
    "search_papers_dataframe",
    "fetch_content",
    "TOOLS",
    "call_tool",
    "advise_tool_call",
    "validate_tool_arguments",
]

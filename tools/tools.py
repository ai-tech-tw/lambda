"""工具定義、JSON Schema 規範與執行調度模組 / Tool Definitions, JSON Schemas & Dispatcher Module.

[正體中文]
本模組為工具調度中心（Tool Dispatch Center）：
1. 定義提供給 OpenAI Responses API 的工具描述清單（`TOOLS`），遵循標準 JSON Schema 規範。
2. 建立工具名稱與實際 Python 函數的對照表（`TOOL_FUNCTIONS`）。
3. 嚴格參數驗證機制（`validate_tool_arguments`）：在執行前檢查模型傳入的引數型別、列舉值（Enum）
   與數值上下限（min/max），防止模型幻覺造成引數錯誤或異常。
4. 工具執行調度器（`call_tool`）：解析 JSON 字串引數並呼叫對應工具，回傳標準純文字結果。
5. 格式退避轉接器（`advise_tool_call`）：相容非原生 Function Calling 的模型代理服務。

[English]
This module serves as the central hub for tool schemas, validation, and execution:
1. Defines JSON Schema tool definitions (`TOOLS`) for the OpenAI Responses API.
2. Maps tool string names to actual Python functions (`TOOL_FUNCTIONS`).
3. Strict argument validation (`validate_tool_arguments`): Ensures model-supplied parameters
   match required types, enums, and numerical boundaries before execution.
4. Tool dispatcher (`call_tool`): Parses JSON arguments, invokes the target tool, and returns text output.
5. Fallback adapter (`advise_tool_call`): Safely decodes text-based tool requests from compatible gateways.
"""

import json
from collections.abc import Callable
from typing import Any

from .calculator import evaluate_expression
from .clock import current_time
from .content import fetch_content
from .search import perform_search, search_papers_dataframe


# [正體中文] 工具函數型別別名：接受任意關鍵字參數，回傳純文字結果
# [English] Type alias for tool functions: accepts keyword args and returns a text result
ToolFunction = Callable[..., str]


# ==============================================================================
# 工具名稱與對應實作函數對照表 / Tool Name to Function Mapping
# ==============================================================================
TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "current_time": current_time,
    "evaluate_expression": evaluate_expression,
    "perform_search": perform_search,
    "search_papers_dataframe": search_papers_dataframe,
    "fetch_content": fetch_content,
}


# ==============================================================================
# OpenAI Responses API 工具描述清單 / Tool JSON Schema Definitions
# ==============================================================================
# [正體中文] 此處的結構遵循 OpenAI Tools 規範，模型會依據此描述理解何時調用該工具
# [English] Schemas follow OpenAI's function/tool specification; the LLM uses these to decide invocations
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


# [正體中文] 快取各工具的參數 JSON Schema，加速驗證運算
# [English] Cache tool parameter schemas for efficient validation lookup
_TOOL_PARAMETERS = {
    tool["name"]: tool["parameters"]
    for tool in TOOLS
    if isinstance(tool.get("name"), str) and isinstance(tool.get("parameters"), dict)
}


def _validate_value(name: str, value: Any, schema: dict[str, Any]) -> None:
    """依照 Schema 驗證個別參數值的型別與限制條件 / Validate an individual parameter value against its schema."""
    expected_type = schema.get("type")
    # [正體中文] 驗證基本資料型別（字串、布林值、整數、數值）
    # [English] Validate basic data types (string, boolean, integer, number)
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

    # [正體中文] 驗證列舉值（Enum）是否合法
    # [English] Validate whether value belongs to permitted enum list
    allowed_values = schema.get("enum")
    if isinstance(allowed_values, list) and value not in allowed_values:
        raise ValueError(f"{name} must be one of {allowed_values}")

    # [正體中文] 驗證數值範圍（最小值 minimum 與最大值 maximum）
    # [English] Validate numeric boundaries (minimum and maximum)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise ValueError(f"{name} must be at most {maximum}")


def validate_tool_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """嚴格驗證模型傳入的工具引數 / Validate model-supplied arguments against registered JSON Schema.

    [正體中文]
    檢查項目：
    1. 工具名稱是否存在。
    2. 是否有未定義的未知欄位（防止模型幻想額外參數）。
    3. 必填欄位（required）是否皆已提供。
    4. 各欄位的值型別、範圍是否符合規範。

    [English]
    Validation checks:
    1. Verify tool exists.
    2. Disallow unexpected fields not present in schema.
    3. Ensure all required fields are present.
    4. Check value types and constraints against schema properties.
    """
    parameters = _TOOL_PARAMETERS.get(name)
    if parameters is None:
        raise ValueError(f"unknown tool '{name}'")

    properties = parameters.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError(f"{name} has an invalid parameter schema")

    # [正體中文] 檢查是否有未定義的未知欄位
    # [English] Disallow unknown fields
    unknown_fields = set(arguments) - set(properties)
    if unknown_fields:
        raise ValueError(f"unsupported arguments: {', '.join(sorted(unknown_fields))}")

    # [正體中文] 檢查必填欄位
    # [English] Check required arguments
    required = parameters.get("required", [])
    if not isinstance(required, list):
        raise ValueError(f"{name} has an invalid required-argument schema")
    missing_fields = [field for field in required if field not in arguments]
    if missing_fields:
        raise ValueError(f"missing required arguments: {', '.join(missing_fields)}")

    # [正體中文] 逐一驗證每個欄位值
    # [English] Validate each individual argument
    for field, value in arguments.items():
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict):
            raise ValueError(f"{field} has an invalid schema")
        _validate_value(field, value, field_schema)
    return arguments


def call_tool(name: str, arguments: str) -> str:
    """執行模型所請求的工具並回傳字串結果 / Run a model-requested tool and return a text result.

    [正體中文]
    執行流程：
    1. 查找對應的 Python 函數。
    2. 解析傳入的 JSON 字串引數。
    3. 執行參數驗證（`validate_tool_arguments`）。
    4. 執行函數並回傳文字結果；若發生錯誤則回傳包含原因的 Error 字串。

    [English]
    Execution workflow:
    1. Look up corresponding Python function from mapping.
    2. Parse the arguments JSON string into a dictionary.
    3. Run schema validation via `validate_tool_arguments`.
    4. Execute the tool function and return output; catch any exceptions cleanly as text.
    """
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
    """將文字退避格式之工具呼叫轉接為標準呼叫 / Turn a JSON-shaped text tool request into a safe tool call.

    [正體中文]
    部分相容 OpenAI 介面的中繼閘道或小型開源模型，可能直接將工具呼叫以文字形式輸出，
    而非標準的 `function_call` 結構。
    此函數安全解析符合 `_lambda_tool_call` 信封格式的 JSON 文字，完成驗證後回傳 (名稱, JSON字串)；
    若非工具呼叫則回傳 None，確保不影響一般對話文字。

    [English]
    Some OpenAI-compatible gateways or smaller models output tool invocations as raw text
    rather than structured function_call items.
    This adapter safely parses text matching the `_lambda_tool_call` envelope and returns
    (tool_name, arguments_json) upon successful validation, or None for regular text.
    """
    try:
        payload = json.loads(text.strip())
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    # [正體中文] 嚴格檢查封裝鍵值，確保為專屬的 _lambda_tool_call 格式
    # [English] Strictly match the unique _lambda_tool_call envelope
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

"""OpenAI 非同步客戶端與智慧代理（Agent）迴圈模組 / OpenAI Client & Agent Loop Module.

[正體中文]
本模組為 lambda 的 AI 核心代理邏輯所在：
1. 使用 OpenAI 官方提供的 `AsyncOpenAI` 用戶端進行非同步呼叫。
2. 支援 OpenAI Responses API，將工具清單（`TOOLS`）注入請求中。
3. 具備「多輪工具呼叫迴圈（Multi-turn Tool-calling Loop）」：
   - 當模型判斷需要工具時，它會發出 `function_call`；
   - 程式在本地端執行工具（`call_tool`）並將結果（`function_call_output`）回傳給模型；
   - 模型依據結果決定是否需要進一步調用其他工具，或給出最終答覆。
4. 容錯退避機制（Fallback）：若所連接的模型伺服器不支援原生結構化 Function Calling，
   亦支援解析模型輸出的特定 JSON 格式（`advise_tool_call`）並自動執行。
5. 逾時保護：使用 `asyncio.timeout` 防止因工具呼叫或模型延遲而無止境等待。

[English]
This module houses lambda's core autonomous AI agent logic:
1. Utilizes `AsyncOpenAI` for asynchronous, non-blocking API interactions.
2. Supports OpenAI's Responses API, injecting tool schemas (`TOOLS`) into requests.
3. Implements a multi-turn tool calling loop:
   - When the model decides an external tool is required, it returns a `function_call`.
   - The system executes the tool locally (`call_tool`) and feeds the result back.
   - The model iterates until it has sufficient information to form a final answer.
4. Fallback mechanism: Supports parsing text-encoded tool calls (`advise_tool_call`)
   for compatibility with model proxies lacking native function-calling support.
5. Timeout guard: Wrapped in `asyncio.timeout` to avoid infinite hangs.
"""

import asyncio
from typing import Any, TypedDict

from openai import AsyncOpenAI

from config import (
    agent_timeout_seconds,
    openai_api_key,
    openai_base_url,
    openai_chat_model,
    openai_system_prompt,
)
from prompts import DEFAULT_PROMPT
from tools.tools import TOOLS, advise_tool_call, call_tool


class AgentResponse(TypedDict):
    """回傳給 LINE Webhook 處理器的結構化回應 / Response returned to the LINE webhook handler."""

    conversation_id: str
    answer: str
    response: "AgentOutput"


class AgentOutput(TypedDict):
    """序列化模型輸出封裝 / Serializable model output."""

    output: str


# ==============================================================================
# OpenAI 非同步用戶端初始化 / Initialize AsyncOpenAI Client
# ==============================================================================
client = AsyncOpenAI(
    base_url=openai_base_url,
    api_key=openai_api_key,
)

# [正體中文] 模型名稱與系統提示詞設定，若環境變數未提供則使用預設值（預設使用 NVIDIA NIM 之 openai/gpt-oss-20b）
# [English] Model name and system prompt configuration, defaulting to openai/gpt-oss-20b on NVIDIA NIM
MODEL = openai_chat_model or "openai/gpt-oss-20b"
SYSTEM_PROMPT = openai_system_prompt or DEFAULT_PROMPT

# [正體中文] 單次對話允許的最大工具調用輪數，避免無限迴圈
# [English] Maximum allowed tool execution rounds per conversation turn to prevent infinite loops
MAX_TOOL_ROUNDS = 10


async def _create_response(
    input_items: str | list[Any], *, include_tools: bool = True
) -> Any:
    """向 OpenAI Responses API 發送請求 / Send request to OpenAI Responses API.

    [正體中文]
    封裝對 `client.responses.create` 的呼叫。
    - `input_items`: 可以是用戶輸入字串，或是包含歷史對話與工具輸出的物件列表。
    - `include_tools`: 控制是否將可用工具清單傳給模型（總結工具結果時可關閉工具避免重複調用）。

    [English]
    Wraps the call to `client.responses.create`.
    - `input_items`: Can be a raw user string or a list of conversation items and tool outputs.
    - `include_tools`: Controls whether to attach the tool schemas to the request.
    """
    request: dict[str, Any] = {
        "model": MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": input_items,
    }
    if include_tools:
        request["tools"] = TOOLS
    return await client.responses.create(**request)


async def _summarize_advised_tool_result(
    user_text: str, tool_name: str, tool_output: str
) -> Any:
    """針對文字退避（advised）工具呼叫請求最終回答 / Summarize result from a text-encoded tool call.

    [正體中文]
    當模型透過文字格式（而非原生結構化呼叫）請求調用工具時，執行完畢後以此函數
    將工具的真實結果餵回模型，要求模型根據結果回答使用者問題，並關閉工具避免再次觸發。

    [English]
    When a tool is requested via text-encoded JSON, this function sends the verified
    execution result back to the model without tools attached, prompting a final answer.
    """
    return await _create_response(
        (
            "請根據以下已驗證的工具結果回答使用者，勿編造或改變結果。"
            f"\n使用者問題：{user_text}"
            f"\n工具：{tool_name}"
            f"\n工具結果：{tool_output}"
        ),
        include_tools=False,
    )


async def chat_with_ai(
    conversation_id: str | None,
    user_id: str,
    user_text: str,
) -> AgentResponse:
    """與 AI 代理進行完整對話流程（含工具呼叫迴圈） / Complete chat flow with the AI agent loop.

    [正體中文]
    流程說明：
    1. 設定逾時上限（`agent_timeout_seconds`）。
    2. 發送使用者問題給模型。
    3. 進入迴圈（最多 `MAX_TOOL_ROUNDS` 輪）：
       a. 檢查是否為文字退避工具呼叫（`advise_tool_call`）。若是，執行工具並總結後結束。
       b. 檢查模型回傳中是否有原生 `function_call`。
       c. 若沒有任何工具呼叫，代表模型已得出最終文字答覆，跳出迴圈。
       d. 若有工具呼叫，逐一執行本地端工具函數，並將結果以 `function_call_output` 追加至輸入列表。
       e. 將包含工具結果的輸入再次送交模型推論。
    4. 格式化並回傳包含最終回答的結構體。

    [English]
    Workflow overview:
    1. Apply timeout restriction (`agent_timeout_seconds`).
    2. Send user query to the model.
    3. Enter tool execution loop (up to `MAX_TOOL_ROUNDS`):
       a. Check for text-encoded JSON tool advice (`advise_tool_call`); execute and summarize if found.
       b. Check for native `function_call` items in model output.
       c. If no tool calls are present, the model has completed its final answer; break loop.
       d. For each tool call, execute the function locally and append `function_call_output`.
       e. Feed accumulated history back into the model for the next step.
    4. Package and return the structured answer.
    """
    async with asyncio.timeout(agent_timeout_seconds):
        response = await _create_response(user_text)

        # [正體中文] 多輪工具呼叫迴圈
        # [English] Multi-turn tool calling loop
        for _ in range(MAX_TOOL_ROUNDS):
            # [正體中文] 1. 檢查是否有文字退避格式之工具呼叫
            # [English] 1. Check for text-encoded fallback tool calls
            advised_call = advise_tool_call(response.output_text)
            if advised_call is not None:
                advised_name, advised_arguments = advised_call
                response = await _summarize_advised_tool_result(
                    user_text,
                    advised_name,
                    call_tool(advised_name, advised_arguments),
                )
                break

            # [正體中文] 2. 擷取模型輸出的所有原生 function_call
            # [English] 2. Extract all native function_call items from the model's output
            function_calls = [
                item
                for item in response.output
                if getattr(item, "type", None) == "function_call"
            ]

            # [正體中文] 若沒有工具呼叫，表示模型已完成思考並給出最終回答
            # [English] If no function calls are requested, the final text answer is ready
            if not function_calls:
                break

            # [正體中文] 3. 將當前輸出保留，並在後續追加每個工具的執行結果
            # [English] 3. Clone current outputs and append execution results for each tool
            next_input: list[Any] = list(response.output)
            for function_call in function_calls:
                # [正體中文] 在本地端安全執行對應的工具並取得字串結果
                # [English] Safely execute the requested tool locally and get the output string
                tool_result = call_tool(function_call.name, function_call.arguments)
                next_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": tool_result,
                    }
                )

            # [正體中文] 4. 將工具結果送回模型，進行下一輪推論
            # [English] 4. Submit tool outputs back to the model for the next reasoning step
            response = await _create_response(next_input)
        else:
            # [正體中文] 超過最大工具調用輪數時拋出例外
            # [English] Raise exception if the model exceeds the maximum allowed rounds
            raise RuntimeError("Model exceeded the maximum number of tool-call rounds")

    # [正體中文] 取得模型最終純文字回答，並做基本空白清理
    # [English] Retrieve the final text answer and strip surrounding whitespace
    output = response.output_text.strip()
    if not output:
        output = "Sorry, I couldn't generate a response."

    next_conversation_id = conversation_id or user_id
    return {
        "conversation_id": next_conversation_id,
        "answer": output,
        "response": {"output": output},
    }

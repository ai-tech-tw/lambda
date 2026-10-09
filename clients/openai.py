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
    """Response returned to the LINE webhook handler."""

    conversation_id: str
    answer: str
    response: "AgentOutput"


class AgentOutput(TypedDict):
    """Serializable model output."""

    output: str


client = AsyncOpenAI(
    base_url=openai_base_url,
    api_key=openai_api_key,
)

MODEL = openai_chat_model or "gpt-3.5-turbo"
SYSTEM_PROMPT = openai_system_prompt or DEFAULT_PROMPT
MAX_TOOL_ROUNDS = 10


async def _create_response(
    input_items: str | list[Any], *, include_tools: bool = True
) -> Any:
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
    """Ask for a final answer after executing a text-encoded tool request."""
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
    async with asyncio.timeout(agent_timeout_seconds):
        response = await _create_response(user_text)
        for _ in range(MAX_TOOL_ROUNDS):
            advised_call = advise_tool_call(response.output_text)
            if advised_call is not None:
                advised_name, advised_arguments = advised_call
                response = await _summarize_advised_tool_result(
                    user_text,
                    advised_name,
                    call_tool(advised_name, advised_arguments),
                )
                break

            function_calls = [
                item
                for item in response.output
                if getattr(item, "type", None) == "function_call"
            ]
            if not function_calls:
                break

            next_input: list[Any] = list(response.output)
            for function_call in function_calls:
                next_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": call_tool(function_call.name, function_call.arguments),
                    }
                )
            response = await _create_response(next_input)
        else:
            raise RuntimeError("Model exceeded the maximum number of tool-call rounds")

    output = response.output_text.strip()
    if not output:
        output = "Sorry, I couldn't generate a response."
    next_conversation_id = conversation_id or user_id
    return {
        "conversation_id": next_conversation_id,
        "answer": output,
        "response": {"output": output},
    }

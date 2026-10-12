"""AI 模型回應處理與思維標籤過濾工具模組 / AI Response Formatting & Thinking Block Stripper.

[正體中文]
本模組負責處理現代推理型語言模型（Reasoning Models，如 DeepSeek-R1 等）的特殊輸出格式：
【初學者背景說明】
新一代推理模型在給出最終回答之前，會在 `<think>...</think>` 標籤中輸出冗長的「內部思考／推理鏈（Chain of Thought）」。
這些內部思維過程對於終端 LINE 使用者而言通常過於冗長且不是直接答案。
本模組利用正規表示式自動將 `<think>...</think>` 區塊移除，僅保留最終結論回覆給使用者。

[English]
This module cleans up outputs from modern reasoning models (such as DeepSeek-R1):
[Context for Beginners]
Reasoning models often emit their internal chain-of-thought within `<think>...</think>` tags
before producing the final response. For chat app users, these verbose reasoning traces
clutter the conversation. This module uses regex to strip thinking blocks cleanly.
"""

import re

# [正體中文] 比對跨行 <think> 標籤及其內部所有推理內容的正規表示式
# [English] Regular expression matching multiline <think>...</think> reasoning blocks
_THINKING_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_thinking(text: str) -> str:
    """移除模型輸出中的內部推理過程標籤區塊 / Remove model reasoning blocks from a response string.

    [正體中文]
    將所有 `<think>...</think>` 內容替換為空字串，保留乾淨的最終回應。

    [English]
    Replaces all `<think>...</think>` blocks with an empty string, retaining only the final answer.
    """
    return _THINKING_BLOCK_RE.sub("", text)

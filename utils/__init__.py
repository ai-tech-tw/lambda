"""共用工具函數導出套件 / Shared Application Utilities Package.

[正體中文]
導出專案通用的字串處理與格式化工具：
- `strip_markdown`: 移除 Markdown 語法符號以適配純文字介面
- `strip_thinking`: 過濾推理模型之內部思維標籤（<think>）

[English]
Exports shared formatting and text-sanitization utilities:
- `strip_markdown`: Strips Markdown syntax for clean plain-text messaging
- `strip_thinking`: Filters out chain-of-thought blocks (<think>) from reasoning models
"""

from .markdown import strip_markdown
from .response import strip_thinking

__all__ = [
    "strip_markdown",
    "strip_thinking",
]

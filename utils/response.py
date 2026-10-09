"""Utilities for preparing AI responses for plain-text channels."""

import re


_THINKING_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_thinking(text: str) -> str:
    """Remove model reasoning blocks from a response."""
    return _THINKING_BLOCK_RE.sub("", text)

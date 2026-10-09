"""Utilities for turning Markdown responses into plain text."""

import re


_FENCED_CODE_RE = re.compile(r"```[^\n]*\n?(.*?)```", re.DOTALL)
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_HEADING_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+", re.MULTILINE)
_QUOTE_RE = re.compile(r"^[ \t]{0,3}>[ \t]?", re.MULTILINE)
_LIST_RE = re.compile(r"^[ \t]*(?:[-+*]|\d+[.)])[ \t]+", re.MULTILINE)
_HORIZONTAL_RULE_RE = re.compile(r"^[ \t]*(?:[-*_][ \t]*){3,}$", re.MULTILINE)
_EMPHASIS_RE = re.compile(
    r"(?<!\\)(\*{1,3}|_{1,3}|~~)(.+?)(?<!\\)\1"
)
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_ESCAPED_MARKDOWN_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!~-])")


def strip_markdown(text: str) -> str:
    """Remove common Markdown formatting while preserving readable content."""
    plain_text = _FENCED_CODE_RE.sub(lambda match: match.group(1).strip(), text)
    plain_text = _IMAGE_RE.sub(r"\1", plain_text)
    plain_text = _LINK_RE.sub(r"\1", plain_text)
    plain_text = _HEADING_RE.sub("", plain_text)
    plain_text = _QUOTE_RE.sub("", plain_text)
    plain_text = _LIST_RE.sub("", plain_text)
    plain_text = _HORIZONTAL_RULE_RE.sub("", plain_text)
    plain_text = _INLINE_CODE_RE.sub(r"\1", plain_text)

    while _EMPHASIS_RE.search(plain_text):
        plain_text = _EMPHASIS_RE.sub(r"\2", plain_text)

    plain_text = _ESCAPED_MARKDOWN_RE.sub(r"\1", plain_text)
    return re.sub(r"\n{3,}", "\n\n", plain_text).strip()

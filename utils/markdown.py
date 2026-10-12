"""Markdown 語法清理與純文字轉換工具模組 / Markdown-to-Plain-Text Stripper Utility Module.

[正體中文]
本模組提供將 Markdown 格式文字轉換為乾淨純文字之功能：
【初學者背景說明】
大型語言模型（LLM）通常習慣以 Markdown 格式輸出回答（例如加粗 `**粗體**`、程式碼區塊 ````...````、標題 `# 標題`）。
然而在 LINE 的一般文字訊息介面中，這些 Markdown 標記符號可能無法正確渲染，導致使用者閱讀體驗不佳。
本模組透過正規表示式（Regex）逐一清除各類 Markdown 特殊符號，同時保留有意義的文字內容與段落結構。

[English]
This module converts Markdown formatted text into clean plain text for messaging apps:
[Context for Beginners]
LLMs commonly respond with Markdown formatting (e.g. `**bold**`, code fences, `# headers`).
In standard LINE text messages, unrendered Markdown syntax can look cluttered.
This module uses regular expressions to strip out formatting symbols while preserving
readable content and clean paragraph structure.
"""

import re

# ==============================================================================
# Markdown 語法比對正規表示式編譯 / Compiled Markdown Regular Expressions
# ==============================================================================
# [正體中文] 程式碼區塊（```code```）
# [English] Fenced code blocks (```code```)
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n?(.*?)```", re.DOTALL)

# [正體中文] 圖片標記（![alt](url)）
# [English] Image tags (![alt](url))
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")

# [正體中文] 超連結標記（[text](url)）
# [English] Hyperlink tags ([text](url))
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")

# [正體中文] 標題前綴（# 標題）
# [English] Heading markers (# heading)
_HEADING_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+", re.MULTILINE)

# [正體中文] 引用區塊前綴（> 引用）
# [English] Blockquote markers (> quote)
_QUOTE_RE = re.compile(r"^[ \t]{0,3}>[ \t]?", re.MULTILINE)

# [正體中文] 清單項目符號（-、*、1.）
# [English] List bullets or numbered markers
_LIST_RE = re.compile(r"^[ \t]*(?:[-+*]|\d+[.)])[ \t]+", re.MULTILINE)

# [正體中文] 水平分隔線（---、***）
# [English] Horizontal rules (---, ***)
_HORIZONTAL_RULE_RE = re.compile(r"^[ \t]*(?:[-*_][ \t]*){3,}$", re.MULTILINE)

# [正體中文] 強調語法（**粗體**、*斜體*、~~刪除線~~）
# [English] Emphasis markers (**bold**, *italic*, ~~strikethrough~~)
_EMPHASIS_RE = re.compile(r"(?<!\\)(\*{1,3}|_{1,3}|~~)(.+?)(?<!\\)\1")

# [正體中文] 行內程式碼（`code`）
# [English] Inline code ticks (`code`)
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")

# [正體中文] 反斜線跳脫字元（\*、\#）
# [English] Escaped markdown characters (\*, \#)
_ESCAPED_MARKDOWN_RE = re.compile(r"\\([\\`*_{}\[\]()#+.!~-])")


def strip_markdown(text: str) -> str:
    """去除 Markdown 格式並保留可讀純文字 / Remove common Markdown formatting while preserving readable text.

    [正體中文]
    清理步驟：
    1. 保留程式碼區塊內的原始文字，移除三個反引號。
    2. 將圖片替換為替代文字（Alt text）。
    3. 將超連結替換為連結文字。
    4. 移除標題符號、引用符號、清單符號與分隔線。
    5. 移除粗體、斜體與行內程式碼標記。
    6. 還原反斜線跳脫字元。
    7. 將超過兩行的多餘空行壓縮為雙換行。

    [English]
    Processing steps:
    1. Retain code content within code fences while stripping tick delimiters.
    2. Replace images with their alt text.
    3. Replace hyperlinks with the anchor text.
    4. Strip heading markers, quote prefixes, list bullets, and horizontal rules.
    5. Strip bold, italic, and inline code formatting.
    6. Restore escaped characters.
    7. Collapse excess consecutive blank lines.
    """
    plain_text = _FENCED_CODE_RE.sub(lambda match: match.group(1).strip(), text)
    plain_text = _IMAGE_RE.sub(r"\1", plain_text)
    plain_text = _LINK_RE.sub(r"\1", plain_text)
    plain_text = _HEADING_RE.sub("", plain_text)
    plain_text = _QUOTE_RE.sub("", plain_text)
    plain_text = _LIST_RE.sub("", plain_text)
    plain_text = _HORIZONTAL_RULE_RE.sub("", plain_text)
    plain_text = _INLINE_CODE_RE.sub(r"\1", plain_text)

    # [正體中文] 遞迴清除巢狀強調語法（例如 ***粗斜體***）
    # [English] Loop to clean nested emphasis formatting (e.g. ***bold-italic***)
    while _EMPHASIS_RE.search(plain_text):
        plain_text = _EMPHASIS_RE.sub(r"\2", plain_text)

    plain_text = _ESCAPED_MARKDOWN_RE.sub(r"\1", plain_text)

    # [正體中文] 收合過多連續換行
    # [English] Collapse excessive consecutive newlines
    return re.sub(r"\n{3,}", "\n\n", plain_text).strip()

"""網頁內容爬取與文字分析工具模組 / Web Content Scraping & Text Extraction Tool Module.

[正體中文]
本模組提供針對網頁內容的爬取與擷取工具：
1. 支援從單一或多個 URL 下載網頁內容。
2. 透過 Scrapy Selector 與 XPath 語法過濾掉 `<script>` 與 `<style>` 標籤，保留乾淨純文字。
3. 支援廣度優先搜尋（BFS）深度爬取（可設定 `max_depth`），並限定在同網域內追蹤超連結。
4. 支援正規表示式（Regex）篩選比對，可直接從網頁中抽出符合特定模式的字串（如電子郵件、訂單編號或特定關鍵字）。

[English]
This module provides web page crawling, extraction, and regex analysis tools:
1. Downloads web content from one or multiple URLs.
2. Strips `<script>` and `<style>` tags via Scrapy Selector and XPath to retain clean human-readable text.
3. Supports Breadth-First Search (BFS) crawling within the same domain up to `max_depth`.
4. Supports Regular Expression (Regex) matching to extract specific patterns (emails, IDs, keywords).
"""

import re
from collections import deque
from urllib.parse import urlparse

import requests
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector


def _extract_text(html: str) -> str:
    """使用 Scrapy Selector 從 HTML 提取純文字 / Extract readable text from HTML via Scrapy Selector.

    [正體中文]
    透過 XPath 選取 body 內的所有文字節點，並明確排除 script 與 style 區塊，再將連續空白收合為單一空白。

    [English]
    Selects all text nodes within <body> excluding <script> and <style> elements, collapsing whitespace.
    """
    selector = Selector(text=html)
    text_nodes = selector.xpath(
        "//body//text()[not(ancestor::script) and not(ancestor::style)]"
    ).getall()
    return re.sub(r"\s+", " ", " ".join(text_nodes)).strip()


def _normalize_urls(urls: str) -> list[str]:
    """將逗號或換行分隔的 URL 字串正規化為清單 / Normalize comma/newline separated URL strings into a list.

    [正體中文]
    自動補上缺少之 `https://` 協定，並驗證網址結構是否合法。

    [English]
    Prepends missing `https://` scheme and validates URL structure.
    """
    candidates = [x.strip() for x in re.split(r"[\n,]", urls) if x.strip()]
    normalized: list[str] = []
    for raw in candidates:
        normalized_url = (
            raw if raw.startswith(("http://", "https://")) else f"https://{raw}"
        )
        parsed = urlparse(normalized_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            normalized.append(normalized_url)
    return normalized


def fetch_content(
    urls: str,
    timeout: int = 20,
    max_chars_per_url: int = 4000,
    max_depth: int = 2,
    regex_pattern: str = "",
    regex_ignore_case: bool = True,
    max_matches_per_url: int = 20,
) -> str:
    """擷取指定網頁純文字內容，可選進行正則搜尋 / Fetch readable text from URLs with optional regex search.

    [正體中文]
    參數說明：
    - `urls`: 欲抓取的 URL 字串（多個 URL 可用換行或逗號分隔）。
    - `timeout`: 每次 HTTP 請求的逾時上限秒數（3 至 60 秒）。
    - `max_chars_per_url`: 每個網址最多擷取的字元數（500 至 10000 字元）。
    - `max_depth`: 追蹤站內連結的深度上限（0 代表僅抓當前頁面，最大為 3）。
    - `regex_pattern`: 用於在網頁內文中搜尋的正規表示式模式（選填）。
    - `regex_ignore_case`: 正規表示式是否忽略大小寫（預設為 True）。
    - `max_matches_per_url`: 每個網址最多回傳的正則匹配個數。

    回傳說明：
    - 依 URL 格式化的純文字內容區塊或正規表示式匹配結果清單。

    [English]
    Parameters:
    - `urls`: Target URLs separated by newlines or commas.
    - `timeout`: Request timeout in seconds (bounded 3 to 60s).
    - `max_chars_per_url`: Character cap per page (bounded 500 to 10,000).
    - `max_depth`: BFS link traversal depth cap (0 for target page only, up to 3).
    - `regex_pattern`: Optional regex pattern to filter or match in extracted text.
    - `regex_ignore_case`: Whether regex matching is case-insensitive (default True).
    - `max_matches_per_url`: Maximum number of regex matches returned per URL.

    Returns:
    - Text blocks per URL containing extracted readable text or regex matching items.
    """
    targets = _normalize_urls(urls)
    if not targets:
        return "Error: no valid URLs provided"

    # [正體中文] 數值界限保護，避免外部參數過大造成負載過高
    # [English] Safeguard parameter boundaries against excessive resource usage
    timeout = max(3, min(timeout, 60))
    max_chars_per_url = max(500, min(max_chars_per_url, 10000))
    max_depth = max(0, min(max_depth, 3))
    max_matches_per_url = max(1, min(max_matches_per_url, 100))

    # [正體中文] 若有指定 regex_pattern，先預先編譯正則物件
    # [English] Precompile regex pattern if provided
    regex_obj = None
    if regex_pattern.strip():
        flags = re.IGNORECASE if regex_ignore_case else 0
        try:
            regex_obj = re.compile(regex_pattern, flags)
        except re.error as exc:
            return f"Error: invalid regex pattern: {exc}"

    blocks: list[str] = []
    headers = {"User-Agent": "lambda/1.0"}
    # [正體中文] 使用佇列進行廣度優先搜尋（BFS），元素格式為 (網址, 當前深度)
    # [English] Queue for Breadth-First Search (BFS) containing (url, depth) tuples
    queue: deque[tuple[str, int]] = deque((target, 0) for target in targets[:5])
    seen: set[str] = set()

    # [正體中文] 限制最多抓取 12 個網頁區塊，避免回應過長
    # [English] Limit to at most 12 content blocks to prevent excessive payload
    while queue and len(blocks) < 12:
        current_url, depth = queue.popleft()
        if current_url in seen:
            continue
        seen.add(current_url)

        try:
            resp = requests.get(current_url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            content_type = (resp.headers.get("content-type") or "").lower()

            # [正體中文] 非 HTML 頁面（例如 JSON 或純文字檔）直接截取內容
            # [English] For non-HTML pages (e.g., plain text or JSON), extract raw text directly
            if "text/html" not in content_type:
                text = (resp.text or "").strip()[:max_chars_per_url]
                if regex_obj is None:
                    blocks.append(
                        f"URL: {current_url}\n{text or '(Empty text content)'}"
                    )
                else:
                    matches = [m.group(0) for m in regex_obj.finditer(text or "")][
                        :max_matches_per_url
                    ]
                    match_section = (
                        "\n".join(f"- {m}" for m in matches)
                        if matches
                        else "(No regex match)"
                    )
                    blocks.append(
                        f"URL: {current_url}\nRegex matches ({len(matches)}):\n{match_section}"
                    )
                continue

            # [正體中文] HTML 頁面：透過 _extract_text 提取過濾後的內文純文字
            # [English] HTML page: parse readable text via _extract_text
            html = resp.text
            text = _extract_text(html)[:max_chars_per_url]
            if regex_obj is None:
                blocks.append(f"URL: {current_url}\n{text or '(Empty text content)'}")
            else:
                matches = [m.group(0) for m in regex_obj.finditer(text or "")][
                    :max_matches_per_url
                ]
                match_section = (
                    "\n".join(f"- {m}" for m in matches)
                    if matches
                    else "(No regex match)"
                )
                blocks.append(
                    f"URL: {current_url}\nRegex matches ({len(matches)}):\n{match_section}"
                )

            # [正體中文] 若已達深度上限，則不再探索該頁面中的超連結
            # [English] Skip link exploration if maximum depth limit is reached
            if depth >= max_depth:
                continue

            # [正體中文] 使用 Scrapy LinkExtractor 解析同網域內的超連結，加入 BFS 佇列
            # [English] Use Scrapy LinkExtractor to discover same-domain links and enqueue them
            response = HtmlResponse(
                url=current_url,
                body=resp.content,
                encoding=resp.encoding or "utf-8",
            )
            current_host = urlparse(current_url).hostname or ""
            extractor = (
                LinkExtractor(allow_domains=[current_host])
                if current_host
                else LinkExtractor()
            )
            for link in extractor.extract_links(response):
                if link.url not in seen:
                    queue.append((link.url, depth + 1))
        except Exception as exc:
            # [正體中文] 捕捉連線或解析例外並記錄錯誤訊息
            # [English] Record connection or extraction errors gracefully
            blocks.append(f"URL: {current_url}\nError: {exc}")

    return "\n\n".join(blocks)

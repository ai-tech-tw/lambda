"""即時網路搜尋與 arXiv 學術論文檢索工具模組 / Web & Academic Search Tools Module.

[正體中文]
本模組提供兩種關鍵的資訊檢索工具，幫助 AI 克服知識截止（Knowledge Cutoff）限制：
1. `perform_search`: 透過 Tavily API 進行即時網路搜尋，取得精準的網頁標題、網址與內容摘要。
2. `search_papers_dataframe`: 透過官方 arXiv API 查詢學術預印本論文，提供標題、作者群、發表日期、連結與摘要。

[English]
This module provides two vital information retrieval tools to overcome LLM knowledge cutoff:
1. `perform_search`: Conducts real-time web searches using the Tavily API, returning titles, URLs, and snippets.
2. `search_papers_dataframe`: Queries the arXiv academic repository, returning paper titles, authors, publication dates, and abstracts.
"""

from typing import cast

import arxiv
from tavily import TavilyClient

from config import tavily_api_key

# [正體中文] arXiv 查詢欄位前綴對照表
# [English] Field prefixes mapping for arXiv search queries
_SEARCH_PREFIX = {
    "all": "",
    "title": "ti:",
    "abstract": "abs:",
    "author": "au:",
    "cat": "cat:",
}


def _string_value(value: object | None) -> str:
    """輔助函數：安全取得字串並去除頭尾空白 / Helper: safely extract and strip string value."""
    return value.strip() if isinstance(value, str) else ""


def perform_search(
    query: str,
    max_results: int = 5,
    timeout: int = 8,
) -> str:
    """使用 Tavily API 進行即時網路搜尋 / Perform a real-time web search using Tavily.

    [正體中文]
    參數說明：
    - `query`: 搜尋關鍵字或問題字串。
    - `max_results`: 最多回傳的搜尋結果數量（限制在 1 至 10 筆之間）。
    - `timeout`: 請求逾時秒數（保留參數）。

    回傳說明：
    - 格式化後的 Markdown 清單，包含網頁標題、URL 與精簡內文摘要。

    [English]
    Parameters:
    - `query`: The search query or question string.
    - `max_results`: Maximum number of search results to return (bounded between 1 and 10).
    - `timeout`: Timeout duration in seconds.

    Returns:
    - Formatted Markdown list containing webpage titles, URLs, and text snippets.
    """
    # [正體中文] 驗證查詢字串不可為空
    # [English] Ensure search query is not empty
    if not query.strip():
        return "Error: query is empty"

    # [正體中文] 檢查是否有設定 Tavily API 金鑰
    # [English] Check if Tavily API key is configured
    if not tavily_api_key or not tavily_api_key.strip():
        return "Error: TAVILY_API_KEY is not configured."

    _ = timeout
    max_results = max(1, min(max_results, 10))

    try:
        # [正體中文] 初始化 TavilyClient 並呼叫搜尋
        # [English] Initialize TavilyClient and execute search
        client = TavilyClient(api_key=tavily_api_key)
        data = cast(
            object,
            client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_raw_content=False,
            ),
        )
    except Exception as exc:
        return f"Error: Tavily search failed: {exc}"

    # [正體中文] 解析回傳資料字典中的 results 清單
    # [English] Parse the 'results' list from the returned response dictionary
    result_data = cast(dict[str, object], data) if isinstance(data, dict) else {}
    results = result_data.get("results")
    if not isinstance(results, list) or not results:
        return "No results found."

    lines: list[str] = []
    result_items = cast(list[object], results)
    for raw_item in result_items[:max_results]:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, object], raw_item)
        title = _string_value(item.get("title"))
        url = _string_value(item.get("url"))
        content = _string_value(item.get("content"))

        # [正體中文] 格式化單一搜尋結果項目
        # [English] Format single search result entry
        if title and url:
            lines.append(f"- {title} ({url})")
            if content:
                # [正體中文] 內容摘要擷取前 240 字元避免洗版
                # [English] Truncate snippet to 240 chars for concise output
                lines.append(f"  {content[:240]}{'...' if len(content) > 240 else ''}")
        elif title:
            lines.append(f"- {title}")

    return "\n".join(lines) if lines else "No results found."


def search_papers_dataframe(
    search_query: str,
    search_type: str = "all",
    max_results: int = 10,
) -> str:
    """搜尋 arXiv 並回傳學術論文摘要報告 / Search arXiv and return paper summaries.

    [正體中文]
    參數說明：
    - `search_query`: 論文搜尋關鍵字。
    - `search_type`: 搜尋欄位分類，可選值為 "all"（全文）、"title"（標題）、"abstract"（摘要）、"author"（作者）、"cat"（學科分類代碼）。
    - `max_results`: 最多回傳的論文篇數（限制在 1 至 20 篇）。

    回傳說明：
    - 包含論文編號、標題、作者群、發表日期、arXiv 連結與簡短摘要的純文字報告。

    [English]
    Parameters:
    - `search_query`: Keywords for academic paper search.
    - `search_type`: Query target field; choices: 'all', 'title', 'abstract', 'author', 'cat'.
    - `max_results`: Maximum number of papers to retrieve (bounded between 1 and 20).

    Returns:
    - Text report listing paper index, title, authors, publication date, URL, and summary.
    """
    if not search_query.strip():
        return "Error: search_query is empty"

    if search_type not in _SEARCH_PREFIX:
        search_type = "all"

    max_results = max(1, min(max_results, 20))
    # [正體中文] 依照搜尋類型組合 arXiv 查詢語法（例如 ti:transformer）
    # [English] Build arXiv query syntax according to search field (e.g. ti:transformer)
    query = (
        f"{_SEARCH_PREFIX[search_type]}{search_query}"
        if _SEARCH_PREFIX[search_type]
        else search_query
    )

    try:
        # [正體中文] 建立 arXiv Search 物件並透過 Client 檢索
        # [English] Create arXiv Search object and query via Client
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        client = arxiv.Client()
        papers = list(client.results(search))
    except Exception as exc:
        return f"Error: arXiv request failed: {exc}"

    if not papers:
        return "No arXiv results found."

    rows: list[str] = []
    for idx, paper in enumerate(papers, start=1):
        title = (paper.title or "").strip().replace("\n", " ")
        summary = (paper.summary or "").strip().replace("\n", " ")
        published = paper.published.isoformat() if paper.published else ""
        link = paper.entry_id or ""
        authors = ", ".join(author.name for author in paper.authors[:5])
        if len(paper.authors) > 5:
            authors += ", ..."

        # [正體中文] 摘要截取前 300 字元避免超出對話上下文
        # [English] Truncate summary to 300 chars to avoid overwhelming model context
        short_summary = summary[:300] + ("..." if len(summary) > 300 else "")
        rows.append(
            (
                f"{idx}. {title}\n"
                f"   authors: {authors}\n"
                f"   published: {published}\n"
                f"   url: {link}\n"
                f"   summary: {short_summary}"
            )
        )

    return "\n\n".join(rows)

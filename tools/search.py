"""Web and academic search tools."""

from typing import cast

import arxiv
from tavily import TavilyClient

from config import tavily_api_key


_SEARCH_PREFIX = {
    "all": "",
    "title": "ti:",
    "abstract": "abs:",
    "author": "au:",
    "cat": "cat:",
}


def _string_value(value: object | None) -> str:
    return value.strip() if isinstance(value, str) else ""


def perform_search(
    query: str,
    max_results: int = 5,
    timeout: int = 8,
) -> str:
    """Perform a web search using Tavily."""
    if not query.strip():
        return "Error: query is empty"
    if not tavily_api_key or not tavily_api_key.strip():
        return "Error: TAVILY_API_KEY is not configured."

    _ = timeout
    max_results = max(1, min(max_results, 10))

    try:
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
        if title and url:
            lines.append(f"- {title} ({url})")
            if content:
                lines.append(f"  {content[:240]}{'...' if len(content) > 240 else ''}")
        elif title:
            lines.append(f"- {title}")

    return "\n".join(lines) if lines else "No results found."


def search_papers_dataframe(
    search_query: str,
    search_type: str = "all",
    max_results: int = 10,
) -> str:
    """Search arXiv and return paper summaries."""
    if not search_query.strip():
        return "Error: search_query is empty"

    if search_type not in _SEARCH_PREFIX:
        search_type = "all"

    max_results = max(1, min(max_results, 20))
    query = (
        f"{_SEARCH_PREFIX[search_type]}{search_query}"
        if _SEARCH_PREFIX[search_type]
        else search_query
    )

    try:
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
